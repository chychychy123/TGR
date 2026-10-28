"""R6 unchanged superclass plus a separately seeded second residual stage."""
import torch
import torch.nn.functional as F
from .coarse import TrajectorySolver
from .baselines import expanded

class RefinementSolver(TrajectorySolver):

    def __init__(self, *args, refine_knots=25, **kwargs):
        super().__init__(*args, **kwargs)
        assert refine_knots in [0, 5, 25]
        self.refine_knots = refine_knots
        self.fine_gen = torch.Generator(device=self.device).manual_seed(int(kwargs['seed']) + 8000001)

    def fine_actions(self, reference, delta):
        modes, pop, knots, dim = delta.shape
        assert modes == 4 and knots == self.refine_knots and (dim == self.d)
        residual = F.interpolate(delta.reshape(modes * pop, knots, dim).transpose(1, 2), size=25, mode='linear', align_corners=True).transpose(1, 2).reshape(modes, pop, 25, self.d)
        raw = (reference[:, None] + residual).clamp(self.lo, self.hi)
        return ((raw - self.sm) / self.ss).reshape(1, modes * pop, 5, self.action_dim)

    @torch.inference_mode()
    def solve(self, info_dict, init_action=None):
        before = self.cost.transitions
        old = super().solve(info_dict, init_action=init_action)
        coarse = torch.cat([self.last_original_mean[:, None], self.residual_actions(self.last_reference, self.last_residual_mean[:, None])], dim=1)
        scores = torch.as_tensor(self.audit[-1]['final_original_costs'], device=self.device, dtype=self.dtype)
        self.last_coarse_finals = coarse.clone()
        self.last_coarse_costs = scores.clone()
        self.last_finals = coarse.clone()
        if self.refine_knots:
            rm = self.last_residual_mean.clone()
            if self.refine_knots == 25:
                rm = F.interpolate(rm.transpose(1, 2), size=25, mode='linear', align_corners=True).transpose(1, 2)
            incumbent = rm.clone()
            self.last_lifted_initial = incumbent.clone()
            rs = torch.full_like(rm, 0.25)
            ex = expanded(info_dict, 300, self.device)
            self.last_lifted_actions = self.fine_actions(self.last_reference, rm[:, None]).clone()
            for _ in range(self.n_steps):
                noise = torch.randn(4, 75, self.refine_knots, self.d, generator=self.fine_gen, device=self.device, dtype=self.dtype)
                delta = rm[:, None] + rs[:, None] * noise
                delta[:, 0] = incumbent
                delta[:, 1] = rm
                actions = self.fine_actions(self.last_reference, delta)
                costs = self.cost.get_cost(ex, actions).reshape(4, 75)
                ix = costs.topk(8, dim=1, largest=False).indices
                elite = delta[torch.arange(4, device=self.device)[:, None], ix]
                rm = elite.mean(1)
                rs = elite.std(1, correction=0)
            fine = self.fine_actions(self.last_reference, rm[:, None])
            fine_scores = self.cost.get_cost(expanded(info_dict, 4, self.device), fine)
            self.last_finals = torch.cat([coarse, fine], dim=1)
            scores = torch.cat([scores, fine_scores], dim=1)
        which = scores.argmin(1)
        answer = self.last_finals[torch.arange(1, device=self.device), which]
        self.audit[-1].update(final_original_costs=scores.cpu().tolist(), selected_mode=int(which[0]), selected_original_cost=scores[0, which].cpu().tolist(), guard_original_cost=scores[:, 0].cpu().tolist(), refinement_knots=self.refine_knots, transitions=self.cost.transitions - before, final_candidates=self.last_finals.shape[1], candidate_population=900 if self.refine_knots else 600, coarse_candidate_set_preserved=True)
        if not self.refine_knots:
            assert torch.equal(answer.cpu(), old['actions']) and scores[0, which].cpu().tolist() == old['costs']
        return {'actions': answer.detach().cpu(), 'costs': scores[0, which].cpu().tolist()}
