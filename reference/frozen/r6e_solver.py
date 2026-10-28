"""Recorded trajectories with low-dimensional residual CEM; original E0 final means."""
import torch
import torch.nn.functional as F
from stable_worldmodel.planning.solver import CEMSolver
from stable_worldmodel.planning.solver.utils import prepare_init_action
from r5_solver import expanded
class TrajectorySolver(CEMSolver):
 def __init__(self,*args,bank,metric,scale,scaler,**kwargs):
  super().__init__(*args,**kwargs);self.bank=bank;self.metric=metric;self.scale=scale;self.scaler=scaler;self.audit=[]
  self.res_gen=torch.Generator(device=self.device).manual_seed(int(kwargs['seed'])+4000001)
 def configure(self,*,action_space,n_envs,config):
  super().configure(action_space=action_space,n_envs=n_envs,config=config);self.d=self.scaler.n_features_in_;assert self.action_dim==self.d*5 and self.horizon==5 and n_envs==1
  self.lo=torch.as_tensor(action_space.low.reshape(-1,self.d)[0],device=self.device);self.hi=torch.as_tensor(action_space.high.reshape(-1,self.d)[0],device=self.device)
  assert torch.all(self.lo==-1) and torch.all(self.hi==1),'Unexpected physical action units'
  self.sm=torch.as_tensor(self.scaler.mean_,device=self.device,dtype=self.dtype);self.ss=torch.as_tensor(self.scaler.scale_,device=self.device,dtype=self.dtype)
 def residual_actions(self,reference,delta):
  modes,pop,knots,dim=delta.shape;assert (modes,knots,dim)==(4,5,self.d)
  residual=F.interpolate(delta.reshape(modes*pop,knots,dim).transpose(1,2),size=25,mode='linear',align_corners=True).transpose(1,2).reshape(modes,pop,25,self.d)
  raw=(reference[:,None]+residual).clamp(self.lo,self.hi)
  return ((raw-self.sm)/self.ss).reshape(1,modes*pop,5,self.action_dim)
 @torch.inference_mode()
 def solve(self,info_dict,init_action=None):
  assert set(info_dict)<={'pixels','goal','action','_needs_flush'}
  c=self.cost;before=c.transitions;total=len(info_dict['pixels']);assert total==1
  px=info_dict['pixels'].to(self.device);goal=info_dict['goal'].to(self.device)
  zs=c.base.encode({'pixels':px})['emb'][:,-1];zg=c.base.encode({'pixels':goal})['emb'][:,-1]
  near=((self.bank['start']-zs[0]).square().sum(-1)).argsort(stable=True)[:16]
  ends=self.bank['end'][near]
  rank=((ends-zg[0]).square().sum(-1) if self.metric is None else self.metric.distance(ends,zg[0],self.scale)).argsort(stable=True)
  chosen=near[rank[:4]];reference=self.bank['action'][chosen].reshape(4,25,self.d)*self.ss+self.sm
  init=prepare_init_action(c,info_dict,init_action,self.horizon,n_envs=1,action_dim=self.action_dim,device=self.device)
  mean,std=self.init_action_distrib(1,init);mean=mean.to(self.device);std=std.to(self.device)
  rm=torch.zeros(4,5,self.d,device=self.device,dtype=self.dtype);rs=torch.full_like(rm,.25);ex=expanded(info_dict,300,self.device)
  for i in range(self.n_steps):
   # Original RNG, population, batch shape, cost and elite update stay separate.
   eps=torch.randn(1,300,self.horizon,self.action_dim,generator=self.torch_gen,device=self.device,dtype=self.dtype)
   acts=mean[:,None]+std[:,None]*eps;acts[:,0]=mean
   e=c.get_cost(ex,acts);ix=e.topk(30,dim=1,largest=False).indices;elite=acts[torch.arange(1,device=self.device)[:,None],ix];mean=elite.mean(1);std=elite.std(1,correction=0)
   epsr=torch.randn(4,75,5,self.d,generator=self.res_gen,device=self.device,dtype=self.dtype);delta=rm[:,None]+rs[:,None]*epsr;delta[:,0]=rm
   ra=self.residual_actions(reference,delta);re=c.get_cost(ex,ra).reshape(4,75);ri=re.topk(8,dim=1,largest=False).indices;rel=delta[torch.arange(4,device=self.device)[:,None],ri];rm=rel.mean(1);rs=rel.std(1,correction=0)
  self.last_original_mean=mean.clone();self.last_chosen=chosen.clone();self.last_reference=reference.clone();self.last_residual_mean=rm.clone()
  finals=torch.cat([mean[:,None],self.residual_actions(reference,rm[:,None])],dim=1);scores=c.get_cost(expanded(info_dict,5,self.device),finals);which=scores.argmin(1);answer=finals[torch.arange(1,device=self.device),which]
  self.audit.append({'selected_original_cost':scores[0,which].cpu().tolist(),'guard_original_cost':scores[:,0].cpu().tolist(),'final_original_costs':scores.cpu().tolist(),'selected_mode':int(which[0]),'bank_ids':chosen.cpu().tolist(),'original_branch_unchanged':True,'transitions':c.transitions-before,'iterations':self.n_steps,'candidate_population':600,'final_candidates':5})
  return {'actions':answer.detach().cpu(),'costs':scores[0,which].cpu().tolist()}
