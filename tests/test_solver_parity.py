"""CPU synthetic checks: package conversion vs immutable recorded solver.

No simulator, model training, API call, or new benchmark result is involved.
"""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
from gymnasium.spaces import Box
from sklearn.preprocessing import StandardScaler
from stable_worldmodel import PlanConfig

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'reference/frozen'))
from r8_solver import RefinementSolver as FrozenSolver
from tgr.refinement import RefinementSolver
from tgr.ablations import AblationSolver
from tgr.metric import Metric
from tgr.planner import load_resources, make_solver

class Encoder(torch.nn.Module):
    def encode(self,info):return {'emb':info['pixels']}

class QuadraticCost(torch.nn.Module):
    def __init__(self):
        super().__init__();self.base=Encoder();self.transitions=0;self.calls=0
    def get_cost(self,info,actions):
        self.transitions+=int(np.prod(actions.shape[:3]));self.calls+=1
        target=torch.linspace(-.2,.3,actions.shape[-1],dtype=actions.dtype)
        return (actions-target).square().sum((-1,-2))

class Parity(unittest.TestCase):
    def test_frozen_parity_and_lift(self):
        torch.set_num_threads(2)
        cases=0
        for dim in [2,5]:
            torch.manual_seed(51)
            bank={'start':torch.randn(256,192),'end':torch.randn(256,192),
                  'action':torch.randn(256,5,dim*5)*.1}
            sc=StandardScaler();sc.n_features_in_=dim
            sc.mean_=np.linspace(-.1,.1,dim);sc.scale_=np.linspace(.8,1.2,dim)
            obs={'pixels':torch.randn(1,1,192),'goal':torch.randn(1,1,192)}
            for guide in range(4):
                metric=None if guide==0 else Metric()
                if metric is not None:
                    with torch.no_grad():metric.M.add_(.001*guide)
                for knots in [0,5,25]:
                    solvers=[]
                    for cls in [FrozenSolver,RefinementSolver]:
                        s=cls(cost=QuadraticCost(),bank=bank,metric=metric,scale=200.,scaler=sc,
                              refine_knots=knots,n_steps=2,num_samples=300,topk=30,seed=7601,device='cpu')
                        s.configure(action_space=Box(-1.,1.,shape=(1,dim),dtype=np.float32),n_envs=1,
                                    config=PlanConfig(horizon=5,receding_horizon=5,action_block=5))
                        solvers.append(s)
                    init=None
                    for _ in range(2):
                        a=solvers[0].solve(obs,init);b=solvers[1].solve(obs,init)
                        self.assertTrue(torch.equal(a['actions'],b['actions']))
                        self.assertEqual(a['costs'],b['costs'])
                        self.assertTrue(torch.equal(solvers[0].last_finals,solvers[1].last_finals))
                        self.assertEqual(solvers[0].audit,solvers[1].audit)
                        if knots:
                            self.assertLessEqual(float((solvers[1].last_lifted_actions-solvers[1].last_coarse_finals[:,1:]).abs().max()),1e-6)
                            self.assertTrue(torch.equal(solvers[1].last_finals[:,:5],solvers[1].last_coarse_finals))
                        init=a['actions'][:,:1]
                    cases+=1
        self.assertEqual(cases,24)
    def test_bundled_resources(self):
        for env in ['pusht','reacher','cube','tworoom']:
            bank,sc,heads,scale=load_resources(ROOT/'resources'/env)
            self.assertEqual(len(heads),9)
            self.assertEqual(sc.n_features_in_,5 if env=='cube' else 2)
            self.assertGreater(scale,0)
            solver,cost=make_solver(Encoder(),bank=bank,scaler=sc,heads=heads,scale=scale)
            self.assertIsInstance(solver,RefinementSolver)

if __name__=='__main__':unittest.main(verbosity=2)
