"""Frozen search-guide objective; no online label calls."""
import torch
import torch.nn.functional as F

def objective(m, z, f, t, q, w, scale, kind):
    if kind == 'temporal_search':
        dt = (t[:, :2] - t[:, 2:3]).abs()
        q = (dt[:, 0] < dt[:, 1]).float() + 0.5 * (dt[:, 0] == dt[:, 1]).float()
        w = torch.ones_like(q)
    if kind == 'self_search':
        d = (z[:, :2] - z[:, 2:3]).square().sum(-1) / scale
        q = torch.sigmoid(d[:, 1] - d[:, 0])
        w = torch.ones_like(q)
    d = m.distance(z[:, :2], z[:, 2:3], scale)
    df = m.distance(f, z[:, None, 2:3], scale)
    l1 = F.binary_cross_entropy_with_logits(d[:, 1] - d[:, 0], q, reduction='none')
    l2 = F.binary_cross_entropy_with_logits(df[:, :, 1] - df[:, :, 0], q[:, None].expand(-1, 3), reduction='none').mean(1)
    return ((l1 + l2) * 0.5 * w).sum() / w.sum().clamp_min(1e-08) + 0.001 * (m.M - torch.eye(192, device=z.device)).square().mean()
