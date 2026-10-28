"""Public constructors for the frozen planner and registered controls."""
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from stable_worldmodel.planning.solver import CEMSolver

from .metric import Cost, Metric
from .baselines import DualCost, NormalizedICEM, SearchSolver
from .refinement import RefinementSolver
from .ablations import AblationSolver

TGR = RefinementSolver
ALIASES = {
    'tgr': 'refined_jev', 'cem300': 'lewm300', 'cem900': 'lewm900',
    'coarse': 'r6_jev', 'extra_coarse': 'r6extra_jev',
}

def load_resources(directory, device='cpu'):
    """Load the fixed bank, action normalization, and all nine endpoint heads."""
    directory = Path(directory)
    stats = json.loads((directory/'action_stats.json').read_text())
    scaler = StandardScaler()
    scaler.mean_ = np.array(stats['mean'])
    scaler.scale_ = np.array(stats['scale'])
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(scaler.mean_)
    with np.load(directory/'retrieval.npz', allow_pickle=False) as data:
        bank = {k: torch.as_tensor(data[k], device=device) for k in data.files}
    assert bank['start'].shape == bank['end'].shape == (256, 192)
    assert bank['action'].shape == (256, 5, 5*scaler.n_features_in_)
    prepared = json.loads((directory/'prepared.json').read_text())
    heads = {}
    for name in prepared['models']:
        checkpoint = torch.load(directory/'models'/f'{name}.pt', map_location=device, weights_only=True)
        metric = Metric().to(device)
        metric.load_state_dict(checkpoint['M'])
        heads[name] = metric.eval().requires_grad_(False)
    return bank, scaler, heads, prepared['scale']

def make_solver(base, *, bank, scaler, heads, scale, method='tgr',
                head_seed=2131, planning_seed=7601, iterations=10,
                device='cpu', deadline=None):
    """Same populations, random streams, costs, and means as the recorded study.

    The deadline is a new run's wall-clock deadline, never the archived batch's.
    Call configure() through WorldModelPolicy, or provide a batched Box and
    PlanConfig(horizon=5, action_block=5, receding_horizon=5) directly.
    """
    method = ALIASES.get(method, method)
    common = dict(n_steps=iterations, seed=planning_seed, device=device)
    if method in ('lewm300', 'lewm900'):
        cost = Cost(base, deadline=deadline)
        solver = CEMSolver(cost=cost, num_samples=300 if method=='lewm300' else 900, topk=30, **common)
    elif method == 'icem900':
        cost = Cost(base, deadline=deadline)
        solver = NormalizedICEM(cost=cost, scaler=scaler, num_samples=900, topk=30, **common)
    elif method in ('retrieval600', 'retrieval900'):
        cost = DualCost(base, None, scale, float('inf') if deadline is None else deadline)
        solver = SearchSolver(cost, 'retrieval', (2 if method=='retrieval600' else 3)*iterations, planning_seed, device, bank)
    else:
        allowed = {'r6_jev','r6extra_jev','refined_jev','refined_e0','refined_self','refined_temporal',
                   'abl_context_jev','abl_rank_none','abl_direct_jev','abl_retain_jev'}
        if method not in allowed:
            raise ValueError(f'Unknown method: {method}')
        guide = method.rsplit('_', 1)[-1]
        metric = None if guide in ('e0','none') else heads[f'{guide}_search_{head_seed}']
        cost = Cost(base, deadline=deadline)
        cls = AblationSolver if method.startswith('abl_') else RefinementSolver
        extra = {'intervention': method} if method.startswith('abl_') else {}
        solver = cls(cost=cost, num_samples=300, topk=30, bank=bank, scaler=scaler,
                     metric=metric, scale=scale, refine_knots=0 if method=='r6_jev' else 5 if method=='r6extra_jev' else 25,
                     **common, **extra)
    return solver, cost
