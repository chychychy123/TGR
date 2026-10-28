"""Recorded trajectories with low-dimensional residual CEM; original E0 final means."""
import torch
import torch.nn.functional as F
from stable_worldmodel.planning.solver import CEMSolver
from stable_worldmodel.planning.solver.utils import prepare_init_action
from r5_solver import expanded
class ComponentTrajectorySolver(CEMSolver):
 def __init__(self,*args,bank,metric,scale,scaler,first_knots=5,prefilter=16,random_rank=False,**kwargs):
  super().__init__(*args,**kwargs);self.bank=bank;self.metric=metric;self.scale=scale;self.scaler=scaler;self.audit=[]
  self.first_knots=first_knots;self.prefilter=prefilter;self.random_rank=random_rank
  self.rank_gen=torch.Generator(device=self.device).manual_seed(int(kwargs['seed'])+12000001)
  self.res_gen=torch.Generator(device=self.device).manual_seed(int(kwargs['seed'])+4000001)
 def configure(self,*,action_space,n_envs,config):
  super().configure(action_space=action_space,n_envs=n_envs,config=config);self.d=self.scaler.n_features_in_;assert self.action_dim==self.d*5 and self.horizon==5 and n_envs==1
  self.lo=torch.as_tensor(action_space.low.reshape(-1,self.d)[0],device=self.device);self.hi=torch.as_tensor(action_space.high.reshape(-1,self.d)[0],device=self.device)
  assert torch.all(self.lo==-1) and torch.all(self.hi==1),'Unexpected physical action units'
  self.sm=torch.as_tensor(self.scaler.mean_,device=self.device,dtype=self.dtype);self.ss=torch.as_tensor(self.scaler.scale_,device=self.device,dtype=self.dtype)
 def residual_actions(self,reference,delta):
  modes,pop,knots,dim=delta.shape;assert (modes,knots,dim)==(4,self.first_knots,self.d)
  residual=F.interpolate(delta.reshape(modes*pop,knots,dim).transpose(1,2),size=25,mode='linear',align_corners=True).transpose(1,2).reshape(modes,pop,25,self.d)
  raw=(reference[:,None]+residual).clamp(self.lo,self.hi)
  return ((raw-self.sm)/self.ss).reshape(1,modes*pop,5,self.action_dim)
 @torch.inference_mode()
 def solve(self,info_dict,init_action=None):
  assert set(info_dict)<={'pixels','goal','action','_needs_flush'}
  c=self.cost;before=c.transitions;total=len(info_dict['pixels']);assert total==1
  px=info_dict['pixels'].to(self.device);goal=info_dict['goal'].to(self.device)
  zs=c.base.encode({'pixels':px})['emb'][:,-1];zg=c.base.encode({'pixels':goal})['emb'][:,-1]
  near=((self.bank['start']-zs[0]).square().sum(-1)).argsort(stable=True)[:self.prefilter]
  ends=self.bank['end'][near]
  rank=((ends-zg[0]).square().sum(-1) if self.metric is None else self.metric.distance(ends,zg[0],self.scale)).argsort(stable=True)
  if self.random_rank:rank=torch.randperm(len(near),device=self.device,generator=self.rank_gen)
  chosen=near[rank[:4]];reference=self.bank['action'][chosen].reshape(4,25,self.d)*self.ss+self.sm
  init=prepare_init_action(c,info_dict,init_action,self.horizon,n_envs=1,action_dim=self.action_dim,device=self.device)
  mean,std=self.init_action_distrib(1,init);mean=mean.to(self.device);std=std.to(self.device)
  rm=torch.zeros(4,self.first_knots,self.d,device=self.device,dtype=self.dtype);rs=torch.full_like(rm,.25);ex=expanded(info_dict,300,self.device)
  for i in range(self.n_steps):
   # Original RNG, population, batch shape, cost and elite update stay separate.
   eps=torch.randn(1,300,self.horizon,self.action_dim,generator=self.torch_gen,device=self.device,dtype=self.dtype)
   acts=mean[:,None]+std[:,None]*eps;acts[:,0]=mean
   e=c.get_cost(ex,acts);ix=e.topk(30,dim=1,largest=False).indices;elite=acts[torch.arange(1,device=self.device)[:,None],ix];mean=elite.mean(1);std=elite.std(1,correction=0)
   epsr=torch.randn(4,75,self.first_knots,self.d,generator=self.res_gen,device=self.device,dtype=self.dtype);delta=rm[:,None]+rs[:,None]*epsr;delta[:,0]=rm
   ra=self.residual_actions(reference,delta);re=c.get_cost(ex,ra).reshape(4,75);ri=re.topk(8,dim=1,largest=False).indices;rel=delta[torch.arange(4,device=self.device)[:,None],ri];rm=rel.mean(1);rs=rel.std(1,correction=0)
  self.last_original_mean=mean.clone();self.last_chosen=chosen.clone();self.last_reference=reference.clone();self.last_residual_mean=rm.clone()
  finals=torch.cat([mean[:,None],self.residual_actions(reference,rm[:,None])],dim=1);scores=c.get_cost(expanded(info_dict,5,self.device),finals);which=scores.argmin(1);answer=finals[torch.arange(1,device=self.device),which]
  self.audit.append({'selected_original_cost':scores[0,which].cpu().tolist(),'guard_original_cost':scores[:,0].cpu().tolist(),'final_original_costs':scores.cpu().tolist(),'selected_mode':int(which[0]),'bank_ids':chosen.cpu().tolist(),'original_branch_unchanged':True,'transitions':c.transitions-before,'iterations':self.n_steps,'candidate_population':600,'final_candidates':5})
  return {'actions':answer.detach().cpu(),'costs':scores[0,which].cpu().tolist()}

"""R6 unchanged superclass plus a separately seeded second residual stage."""
import torch
import torch.nn.functional as F

from r5_solver import expanded

class ComponentRefinementSolver(ComponentTrajectorySolver):
 def __init__(self,*args,refine_knots=25,**kwargs):
  super().__init__(*args,**kwargs);assert refine_knots in [0,5,25];self.refine_knots=refine_knots
  self.fine_gen=torch.Generator(device=self.device).manual_seed(int(kwargs['seed'])+8000001)
 def fine_actions(self,reference,delta):
  modes,pop,knots,dim=delta.shape;assert modes==4 and knots==self.refine_knots and dim==self.d
  residual=F.interpolate(delta.reshape(modes*pop,knots,dim).transpose(1,2),size=25,mode='linear',align_corners=True).transpose(1,2).reshape(modes,pop,25,self.d)
  raw=(reference[:,None]+residual).clamp(self.lo,self.hi)
  return ((raw-self.sm)/self.ss).reshape(1,modes*pop,5,self.action_dim)
 @torch.inference_mode()
 def solve(self,info_dict,init_action=None):
  before=self.cost.transitions
  old=super().solve(info_dict,init_action=init_action)
  coarse=torch.cat([self.last_original_mean[:,None],self.residual_actions(self.last_reference,self.last_residual_mean[:,None])],dim=1)
  scores=torch.as_tensor(self.audit[-1]['final_original_costs'],device=self.device,dtype=self.dtype)
  self.last_coarse_finals=coarse.clone();self.last_coarse_costs=scores.clone();self.last_finals=coarse.clone()
  if self.refine_knots:
   rm=self.last_residual_mean.clone()
   if self.refine_knots==25:rm=F.interpolate(rm.transpose(1,2),size=25,mode='linear',align_corners=True).transpose(1,2)
   incumbent=rm.clone();self.last_lifted_initial=incumbent.clone();rs=torch.full_like(rm,.25);ex=expanded(info_dict,300,self.device)
   self.last_lifted_actions=self.fine_actions(self.last_reference,rm[:,None]).clone()
   for _ in range(self.n_steps):
    noise=torch.randn(4,75,self.refine_knots,self.d,generator=self.fine_gen,device=self.device,dtype=self.dtype)
    delta=rm[:,None]+rs[:,None]*noise;delta[:,0]=incumbent;delta[:,1]=rm
    actions=self.fine_actions(self.last_reference,delta);costs=self.cost.get_cost(ex,actions).reshape(4,75)
    ix=costs.topk(8,dim=1,largest=False).indices;elite=delta[torch.arange(4,device=self.device)[:,None],ix]
    rm=elite.mean(1);rs=elite.std(1,correction=0)
   fine=self.fine_actions(self.last_reference,rm[:,None]);fine_scores=self.cost.get_cost(expanded(info_dict,4,self.device),fine)
   self.last_finals=torch.cat([coarse,fine],dim=1);scores=torch.cat([scores,fine_scores],dim=1)
  which=scores.argmin(1);answer=self.last_finals[torch.arange(1,device=self.device),which]
  self.audit[-1].update(final_original_costs=scores.cpu().tolist(),selected_mode=int(which[0]),selected_original_cost=scores[0,which].cpu().tolist(),guard_original_cost=scores[:,0].cpu().tolist(),refinement_knots=self.refine_knots,transitions=self.cost.transitions-before,final_candidates=self.last_finals.shape[1],candidate_population=900 if self.refine_knots else 600,coarse_candidate_set_preserved=True)
  if not self.refine_knots:
   assert torch.equal(answer.cpu(),old['actions']) and scores[0,which].cpu().tolist()==old['costs']
  return {'actions':answer.detach().cpu(),'costs':scores[0,which].cpu().tolist()}

class AblationSolver(ComponentRefinementSolver):
 def __init__(self,*args,intervention=None,**kw):
  assert intervention in [None,'abl_context_jev','abl_rank_none','abl_direct_jev','abl_retain_jev']
  self.intervention=intervention
  super().__init__(*args,first_knots=25 if intervention=='abl_direct_jev' else 5,prefilter=256 if intervention=='abl_context_jev' else 16,random_rank=intervention=='abl_rank_none',**kw)
 @torch.inference_mode()
 def solve(self,*args,**kw):
  answer=super().solve(*args,**kw)
  allowed=[0,5,6,7,8] if self.intervention=='abl_retain_jev' else list(range(9))
  scores=torch.as_tensor(self.audit[-1]['final_original_costs'],device=self.device,dtype=self.dtype)
  mode=allowed[int(scores[0,allowed].argmin())]
  answer={'actions':self.last_finals[:,mode].detach().cpu(),'costs':scores[:,mode].cpu().tolist()}
  self.audit[-1].update(intervention=self.intervention,first_stage_knots=self.first_knots,start_prefilter=self.prefilter,goal_rank_removed=self.random_rank,allowed_final_indices=allowed,selected_mode=mode,selected_original_cost=scores[:,mode].cpu().tolist())
  return answer
