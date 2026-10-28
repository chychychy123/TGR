"""Portable evaluation entry point for the frozen S1 configuration matrix."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'third_party/lewm'))
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FILES={'pusht':'pusht_expert_train.h5','reacher':'reacher.h5','tworoom':'tworoom.h5','cube':'ogbench/cube_single_expert.h5'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--environment',required=True,choices=FILES)
    ap.add_argument('--data-root',type=Path,required=True)
    ap.add_argument('--checkpoint',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--suite',choices=['high','low','both'],help='Run every registered method in this suite.')
    ap.add_argument('--method',default='tgr',help='Single method, default all three TGR heads and both planning seeds.')
    ap.add_argument('--budget',choices=['high','low'],default='high')
    ap.add_argument('--root-start',type=int,default=0)
    ap.add_argument('--root-count',type=int,default=128)
    ap.add_argument('--device',choices=['cpu','cuda'],default='cuda')
    ap.add_argument('--max-hours',type=float,default=18)
    ap.add_argument('--check-only',action='store_true',help='Check inputs and runtime; do not run any environment.')
    a=ap.parse_args()
    if not 0<=a.root_start<128 or not 1<=a.root_count<=128-a.root_start:ap.error('Root range must lie within [0,128).')
    if not 0<a.max_hours<=18:ap.error('max-hours must lie in (0,18].')
    if not a.check_only and a.output is None:ap.error('--output is required unless --check-only')
    p=read(ROOT/'configs/experiment.json');name=a.environment
    data=a.data_root/FILES[name]
    for f in (a.checkpoint,data):
        if not f.is_file():raise FileNotFoundError(f)
    if sha(a.checkpoint)!=p['models'][name]['checkpoint_sha256']:
        raise ValueError('Checkpoint SHA differs from the recorded model. See docs/REPRODUCIBILITY.md.')
    from check_runtime import check_runtime
    check_runtime()
    from verify_release import verify
    verify()
    if a.check_only:
        print(json.dumps({'status':'inputs_verified','environment':name,'new_episodes':0}));return
    if a.output.exists():raise FileExistsError('Use a new output directory; recorded results are never overwritten.')
    if a.device=='cuda':
        gpu=os.environ.get('CUDA_VISIBLE_DEVICES')
        if gpu not in ('1','2','3') or os.environ.get('MUJOCO_EGL_DEVICE_ID')!=gpu:
            raise ValueError('Set CUDA_VISIBLE_DEVICES and MUJOCO_EGL_DEVICE_ID to the same authorized physical GPU (1,2,3).')
    os.environ.setdefault('MUJOCO_GL','egl');os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    import contextlib,io,types
    import numpy as np
    import torch
    import hdf5plugin  # HDF5 compression registration
    import stable_worldmodel as swm
    from torchvision.transforms import v2 as T
    from tgr.planner import ALIASES,load_resources,make_solver
    from tgr.cube_adapter import install_cube_adapter
    torch.set_num_threads(2);torch.set_num_interop_threads(2)
    if a.device=='cuda':torch.cuda.set_per_process_memory_fraction(.2)
    base=swm.wm.utils.load_pretrained(str(a.checkpoint.resolve())).to(a.device).eval().requires_grad_(False)
    bank,sc,heads,scale=load_resources(ROOT/'resources'/name,a.device)
    cfg=read(ROOT/'configs'/f'{name}_environment.json')
    world=swm.World(**cfg['world'],image_shape=(224,224));env=world.envs.envs[0].unwrapped
    if name=='cube':install_cube_adapter(env)
    dataset=swm.data.load_dataset(str(data.resolve()),keys_to_cache=['action'],cache_dir=a.data_root.resolve())
    records=read(ROOT/'results/S1'/name/'split.json')[a.root_start:a.root_start+a.root_count]
    a.output.mkdir(parents=True)
    deadline=time.time()+a.max_hours*3600
    def dump(path,value):
        path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x)),encoding='utf-8')
    dump(a.output/'run_config.json',{'environment':name,'suite':a.suite,'method':a.method,'budget':a.budget,
         'roots':[r['index'] for r in records],'checkpoint_sha256':sha(a.checkpoint),
         'started':time.time(),'deadline':deadline,'status':'running','device':a.device})
    def physical():
        if name=='pusht':return np.r_[env.agent.position,env.block.position,env.block.angle,env.agent.velocity,env.block.velocity,env.block.angular_velocity]
        if name=='reacher':return np.r_[env.env.physics.data.qpos,env.env.physics.data.qvel]
        if name=='cube':return np.r_[env._data.qpos,env._data.qvel,env._data.joint('object_joint_0').qpos[:3]]
        return np.asarray(env._get_obs(),dtype=float).reshape(-1)
    class RecordingSolver:
        def __init__(self,solver):self.solver=solver;self.plans=[];self.finals=[];self.original=[]
        def configure(self,**kw):self.solver.configure(**kw)
        @property
        def n_envs(self):return self.solver.n_envs
        @property
        def action_dim(self):return self.solver.action_dim
        @property
        def horizon(self):return self.solver.horizon
        def solve(self,*args,**kw):
            result=self.solver.solve(*args,**kw);self.plans.append(result['actions'].clone().numpy())
            if hasattr(self.solver,'last_finals'):
                self.finals.append(self.solver.last_finals.detach().cpu().numpy())
                self.original.append(self.solver.last_original_mean.detach().cpu().numpy())
            return result
        __call__=solve
    class PixelPolicy(swm.policy.WorldModelPolicy):
        seconds=0.
        def get_action(self,info_dict,**kwargs):
            if time.time()>=deadline-5:raise TimeoutError('Evaluation deadline reached')
            if a.device=='cuda':torch.cuda.synchronize()
            start=time.perf_counter();clean={k:info_dict[k] for k in ('pixels','goal')}
            if '_needs_flush' in info_dict:clean['_needs_flush']=info_dict['_needs_flush']
            with contextlib.redirect_stdout(io.StringIO()):action=super().get_action(clean,**kwargs)
            if a.device=='cuda':torch.cuda.synchronize()
            self.seconds+=time.perf_counter()-start
            assert np.isfinite(action).all()
            return action
    tf=T.Compose([T.ToImage(),T.ToDtype(torch.float32,scale=True),T.Normalize(mean=[.485,.456,.406],std=[.229,.224,.225]),T.Resize(224)])
    seedbox=[0];trace={};original_reset=world.reset;original_step=world.envs.step
    def reset(self,seed=None,options=None):return original_reset(seed=seedbox[0],options=options)
    world.reset=types.MethodType(reset,world)
    def step(actions,*args,**kw):
        if not trace['states']:
            trace['states'].append(physical().copy());trace['initial_pixels']=world.infos['pixels'][0,-1].copy()
        trace['actions'].append(np.array(actions[0],copy=True));result=original_step(actions,*args,**kw)
        trace['states'].append(physical().copy());return result
    world.envs.step=step
    jobs=[]
    for panel in (['high','low'] if a.suite=='both' else [a.suite or a.budget]):
        methods=p[panel+'_methods']
        requested=ALIASES.get(a.method,a.method)
        if a.suite is None:
            if requested not in methods:ap.error(f'{requested} is not registered for {panel}')
            methods={requested:methods[requested]}
        for method,nheads in methods.items():
            for hs in p['head_seeds'] if nheads==3 else [0]:
                for ps in p['planning_seeds']:jobs.append((method,p['planning'][panel+'_iterations'][name],hs,ps))
    completed=0
    try:
        for rec in records:
            ordered=list(jobs);np.random.default_rng(16904000+rec['index']).shuffle(ordered)
            for method,iterations,hs,ps in ordered:
                if time.time()>=deadline-5:raise TimeoutError('Evaluation deadline reached')
                torch.manual_seed(ps+rec['index']*100)
                s,cost=make_solver(base,bank=bank,scaler=sc,heads=heads,scale=scale,method=method,
                    head_seed=hs,planning_seed=ps+rec['index']*100,iterations=iterations,device=a.device,deadline=deadline)
                rs=RecordingSolver(s)
                policy=PixelPolicy(solver=rs,config=swm.PlanConfig(horizon=5,receding_horizon=5,action_block=5),
                    process={'action':sc},transform={'pixels':tf,'goal':tf})
                seedbox[0]=16903000+rec['index'];np.random.seed(seedbox[0]);world.set_policy(policy)
                trace={'states':[],'actions':[]};started=time.perf_counter()
                with contextlib.redirect_stdout(io.StringIO()):
                    result=world.evaluate(dataset=dataset,start_steps=[rec['start_step']],goal_offset=25,eval_budget=50,
                        episodes_idx=[rec['episode']],callables=cfg['callables'],video=None)
                elapsed=time.perf_counter()-started;n=len(trace['actions'])
                plans=np.concatenate(rs.plans,axis=0).reshape(-1,25,sc.n_features_in_)
                actions=plans.reshape(-1,sc.n_features_in_)[:n]*sc.scale_+sc.mean_
                action_error=float(np.max(np.abs(actions-np.asarray(trace['actions']))));assert action_error<1e-4
                key=f"root{rec['index']:03d}_{method}_{iterations}_h{hs}_p{ps}"
                dest=a.output/(key+'.npz')
                np.savez_compressed(dest,**{k:np.array(v) for k,v in trace.items()},normalized_plans=plans,
                    final_candidate_plans=np.asarray(rs.finals),original_branch_plans=np.asarray(rs.original))
                row={'root':rec['index'],'episode':rec['episode'],'method':method,'iterations':iterations,
                    'head_seed':hs,'planner_seed':ps,'success':bool(result['episode_successes'][0]),'steps':n,
                    'planning_seconds':policy.seconds,'wall_seconds':elapsed,'predicted_transitions':cost.transitions,
                    'cost_calls':cost.calls,'commit_commands':25,'replans':len(rs.plans),'trajectory_sha256':sha(dest),
                    'action_inverse_transform_max_abs':action_error,'search_audit':getattr(s,'audit',[])}
                dump(a.output/(key+'.json'),row);completed+=1
                print(json.dumps({'completed':completed,'target':len(records)*len(jobs),'last_record':key}),flush=True)
        dump(a.output/'complete.json',{'status':'complete','episodes':completed,'ended':time.time()})
    except Exception as e:
        dump(a.output/'failure.json',{'status':'failed','completed':completed,'error':repr(e),'ended':time.time()})
        raise
    finally:world.close()

if __name__=='__main__':main()
