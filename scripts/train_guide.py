"""Optional offline guide fitting. Evaluation uses the bundled frozen heads."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--environment',required=True,choices=['pusht','reacher','cube','tworoom'])
    p.add_argument('--kind',choices=['jev_search','self_search','temporal_search'],default='jev_search')
    p.add_argument('--seed',type=int,choices=[2131,2132,2133],default=2131)
    p.add_argument('--device',default='cpu')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    import numpy as np
    import torch
    from tgr.metric import Metric
    from tgr.guide_objective import objective
    torch.set_num_threads(2)
    source=ROOT/'resources'/a.environment/'training'
    with np.load(source/'features.npz',allow_pickle=False) as d:
        z=torch.tensor(d['observed'],device=a.device)
        f=torch.tensor(d['forecast'],device=a.device)
        t=torch.tensor(d['times'],device=a.device)
    labels=json.loads((source/'targets.json').read_text())
    q=torch.tensor([x['target'] for x in labels],device=a.device)
    w=torch.tensor([x['weight'] for x in labels],device=a.device)
    scale=float((z[:128,:2]-z[:128,2:3]).square().sum(-1).mean())
    torch.manual_seed(a.seed)
    model=Metric().to(a.device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=0)
    gen=torch.Generator(device=a.device).manual_seed(a.seed)
    for _ in range(2000):
        ix=torch.randint(128,(32,),generator=gen,device=a.device)
        loss=objective(model,z[ix],f[ix],t[ix],q[ix],w[ix],scale,a.kind)
        assert torch.isfinite(loss)
        optimizer.zero_grad();loss.backward()
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1)
        assert torch.isfinite(norm)
        optimizer.step()
    with torch.no_grad():
        validation=float(objective(model,z[128:],f[128:],t[128:],q[128:],w[128:],scale,a.kind))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    torch.save({'M':model.state_dict(),'scale':scale,'seed':a.seed,'steps':2000,'kind':a.kind},a.output)
    print(json.dumps({'steps':2000,'validation_loss':validation,'api_requests':0,'output':str(a.output)}))

if __name__=='__main__':main()
