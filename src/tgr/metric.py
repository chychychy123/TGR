"""Fixed small metric and original LeWM forecast interface."""
import torch
import torch.nn.functional as F

class Metric(torch.nn.Module):

    def __init__(self, dim=192):
        super().__init__()
        self.M = torch.nn.Parameter(torch.eye(dim))

    def distance(self, z, g, scale):
        return F.linear(z - g, self.M).square().sum(-1) / scale

class Cost(torch.nn.Module):

    def __init__(self, base, metric=None, scale=1.0, deadline=None):
        super().__init__()
        self.base = base
        self.metric = metric
        self.scale = scale
        self.deadline = deadline
        self.calls = 0
        self.transitions = 0

    def get_cost(self, info, actions):
        import time
        if self.deadline is not None and time.time() >= self.deadline - 5:
            raise RuntimeError('R4 deadline reached')
        self.calls += 1
        self.transitions += int(actions.shape[0] * actions.shape[1] * actions.shape[2])
        clean = {k: info[k] for k in ['pixels', 'goal']}
        clean['action'] = actions[:, :, :1]
        if self.metric is None:
            return self.base.get_cost(clean, actions)
        device = next(self.base.parameters()).device
        px = clean['pixels'].to(device)
        goal = clean['goal'].to(device)
        g = self.base.encode({'pixels': goal[:, 0]})['emb'][:, -1]
        z = self.base.rollout({'pixels': px}, actions)['predicted_emb'][:, :, -1]
        return self.metric.distance(z, g[:, None], self.scale)

def objective(metric, z, f, times, q, w, scale, kind):
    observed = metric.distance(z[:, :2], z[:, 2:3], scale)
    if kind == 'temporal_metric':
        delta = (times[:, :2] - times[:, 2:3]).abs()
        q = (delta[:, 0] < delta[:, 1]).float() + 0.5 * (delta[:, 0] == delta[:, 1]).float()
        w = torch.ones_like(q)
    obs = F.binary_cross_entropy_with_logits(observed[:, 1] - observed[:, 0], q, reduction='none')
    loss = (obs * w).sum() / w.sum().clamp_min(1e-08)
    if kind != 'jev_observation':
        forecast = metric.distance(f, z[:, None, 2:3], scale)
        ll = F.binary_cross_entropy_with_logits(forecast[:, :, 1] - forecast[:, :, 0], q[:, None].expand(-1, 3), reduction='none').mean(1)
        loss = 0.5 * loss + 0.5 * (ll * w).sum() / w.sum().clamp_min(1e-08)
        if kind in ['jev_consistent', 'temporal_metric']:
            loss = loss + (forecast - observed[:, None]).square().mean()
    loss = loss + 0.001 * (metric.M - torch.eye(192, device=z.device)).square().mean()
    return loss
