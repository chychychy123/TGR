"""Search-only metric branches; original cost exclusively decides the output."""
import time
import numpy as np, torch
from gymnasium.spaces import Box
from stable_worldmodel.planning.solver import CEMSolver, ICEMSolver
from .metric import Metric

class DualCost(torch.nn.Module):

    def __init__(self, base, metric, scale, deadline):
        super().__init__()
        self.base = base
        self.metric = metric
        self.scale = scale
        self.deadline = deadline
        self.mode = 'original'
        self.calls = 0
        self.transitions = 0
        self.best_action = None
        self.best_score = None

    def reset_pool(self):
        self.best_action = None
        self.best_score = None

    def get_cost(self, info, actions):
        assert time.time() < self.deadline - 5, 'R5 deadline reached'
        self.calls += 1
        self.transitions += int(np.prod(actions.shape[:3]))
        assert set(info) <= {'pixels', 'goal', 'action', '_needs_flush'}
        px = info['pixels'].to(actions.device)
        goal = info['goal'].to(actions.device)
        g = self.base.encode({'pixels': goal[:, 0]})['emb'][:, -1]
        z = self.base.rollout({'pixels': px}, actions)['predicted_emb'][:, :, -1]
        e = (z - g[:, None]).square().sum(-1)
        v, ix = e.min(1)
        a = actions[torch.arange(len(actions), device=actions.device), ix]
        if self.best_score is None:
            self.best_score = v.clone()
            self.best_action = a.clone()
        else:
            better = v < self.best_score
            self.best_score = torch.where(better, v, self.best_score)
            self.best_action = torch.where(better[:, None, None], a, self.best_action)
        if self.mode == 'original':
            return e
        assert self.metric is not None
        return self.metric.distance(z, g[:, None], self.scale)

def expanded(info, n, device):
    return {k: v.to(device).unsqueeze(1).expand(len(v), n, *v.shape[1:]) for k, v in info.items() if k in ['pixels', 'goal']}

class SearchSolver:

    def __init__(self, cost, kind, budget, seed, device, bank=None):
        self.cost = cost
        self.kind = kind
        self.budget = budget
        self.seed = seed
        self.device = device
        self.bank = bank
        self.audit = []
        n = budget if kind == 'cem_best' else budget // 2
        self.first = CEMSolver(cost=cost, num_samples=300, topk=30, n_steps=n, seed=seed, device=device)
        self.second = None if kind == 'cem_best' else CEMSolver(cost=cost, num_samples=300, topk=30, n_steps=n, seed=seed + 1000003, device=device)

    def configure(self, **kwargs):
        self.first.configure(**kwargs)
        if self.second:
            self.second.configure(**kwargs)

    @property
    def n_envs(self):
        return self.first.n_envs

    @property
    def action_dim(self):
        return self.first.action_dim

    @property
    def horizon(self):
        return self.first.horizon

    def __call__(self, *a, **kw):
        return self.solve(*a, **kw)

    @torch.inference_mode()
    def solve(self, info_dict, init_action=None):
        c = self.cost
        c.reset_pool()
        c.mode = 'original'
        before = c.transitions
        first = self.first.solve(info_dict, init_action)
        a = first['actions'].to(self.device)
        guard = c.get_cost(expanded(info_dict, 1, self.device), a[:, None])[:, 0].clone()
        if self.second:
            init = init_action
            if self.kind == 'retrieval':
                px = info_dict['pixels'].to(self.device)
                goal = info_dict['goal'].to(self.device)
                zs = c.base.encode({'pixels': px})['emb'][:, -1]
                zg = c.base.encode({'pixels': goal})['emb'][:, -1]
                dist = (zs[:, None] - self.bank['start'][None]).square().mean(-1) + (zg[:, None] - self.bank['end'][None]).square().mean(-1)
                init = self.bank['action'][dist.argmin(1)]
            c.mode = 'guide' if self.kind in ['jev_search', 'temporal_search', 'self_search'] else 'original'
            second = self.second.solve(info_dict, init)
            c.mode = 'original'
            c.get_cost(expanded(info_dict, 1, self.device), second['actions'].to(self.device)[:, None])
        assert torch.all(c.best_score <= guard + 1e-05)
        self.audit.append({'guard_original_cost': guard.cpu().tolist(), 'selected_original_cost': c.best_score.cpu().tolist(), 'transitions': c.transitions - before, 'kind': self.kind})
        return {'actions': c.best_action.detach().cpu(), 'costs': c.best_score.cpu().tolist()}

class NormalizedICEM(ICEMSolver):

    def __init__(self, *args, scaler, **kwargs):
        self.scaler = scaler
        super().__init__(*args, **kwargs)

    def configure(self, *, action_space, n_envs, config):
        lo = ((action_space.low - self.scaler.mean_) / self.scaler.scale_).astype(np.float32)
        hi = ((action_space.high - self.scaler.mean_) / self.scaler.scale_).astype(np.float32)
        assert np.all(lo < hi)
        super().configure(action_space=Box(lo, hi, dtype=np.float32), n_envs=n_envs, config=config)
        assert np.allclose(lo * self.scaler.scale_ + self.scaler.mean_, action_space.low, atol=0.0001)
        assert np.allclose(hi * self.scaler.scale_ + self.scaler.mean_, action_space.high, atol=0.0001)
