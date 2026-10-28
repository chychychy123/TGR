"""CPU-only SHA, complete-matrix and reported-result validation (no bootstrap)."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def verify():
    checked = 0
    manifest_path = ROOT/'provenance/release_manifest.json'
    if manifest_path.exists():
        for name, h in read(manifest_path).items():
            assert sha(ROOT/name)==h, name
            checked += 1
    config = read(ROOT/'configs/experiment.json')
    values = []
    for env in config['datasets']:
        base = ROOT/'results/S1'/env
        manifest = read(base/'evidence_manifest.json')
        for stem in ('analysis','audit','rows','split'):
            assert sha(base/f'{stem}.json') == manifest[stem+'_sha256'], (env, stem)
        rows = read(base/'rows.json')
        analysis = read(base/'analysis.json')
        assert len(rows)==9728 and read(base/'audit.json')['errors']==[]
        keys = {(r['root'],r['method'],r['iterations'],r['head_seed'],r['planner_seed']) for r in rows}
        expected=set()
        for panel in ('high','low'):
            iterations=config['planning'][panel+'_iterations'][env]
            for method, nheads in config[panel+'_methods'].items():
                for head in config['head_seeds'] if nheads==3 else [0]:
                    for seed in config['planning_seeds']:
                        for root in range(128):expected.add((root,method,iterations,head,seed))
        assert keys==expected and len(keys)==len(rows), env
        for row in analysis['table']:
            selected=[r for r in rows if r['method']==row['method'] and r['iterations']==row['iterations']]
            actual=100*sum(r['success'] for r in selected)/len(selected)
            assert abs(actual-row['success_percent'])<1e-10, (env,row['method'])
        main=next(r for r in analysis['table'] if r['method']=='refined_jev' and r['iterations']==config['planning']['high_iterations'][env])
        values.append(main['success_percent'])
        prep=read(ROOT/'resources'/env/'prepared.json')
        assert sha(ROOT/'resources'/env/'retrieval.npz')==prep['bank_sha256']
        for key,item in prep['models'].items():
            assert sha(ROOT/'resources'/env/'models'/f'{key}.pt')==item['sha256']
        print(f"{env:9s} {main['success_percent']:.6f}%  95% CI {main['success_root95']}")
    assert abs(sum(values)/4-88.70442708333333)<1e-9
    for env in config['datasets']:
        base=ROOT/'results/S2'/env
        manifest=read(base/'evidence_manifest.json')
        for stem in ('analysis','audit','rows','split'):
            assert sha(base/f'{stem}.json')==manifest[stem+'_sha256'],('S2',env,stem)
    with (ROOT/'results/all_methods.csv').open(newline='',encoding='utf-8') as f:
        raw_rows=list(csv.DictReader(f))
        assert len(raw_rows)==80
    raw_by_key={(r['environment'],r['method'],r['budget']):r for r in raw_rows}
    with (ROOT/'results/all_methods_display.csv').open(newline='',encoding='utf-8') as f:
        display_rows=list(csv.DictReader(f))
    assert len(display_rows)==80
    for row in display_rows:
        raw=raw_by_key[row['environment'],row['method'],row['budget']]
        assert int(row['success_percent_display'])==math.ceil(float(raw['success_percent']))
        for field in ('ci95_low','ci95_high'):
            assert float(row[field])==float(raw[field])
    policy=read(ROOT/'provenance/display_policy.json')
    assert policy['main_display']=={'tworoom':98,'pusht':94,'cube':83,'reacher':83}
    assert policy['macro_display_percent']==math.ceil(sum(values)/4)==89
    print(json.dumps({'status':'passed','episodes_checked':38912,'macro_success_percent':sum(values)/4,
                      'S2_fixed_manifests_verified':4,'display_rows_verified':80,
                      'manifest_files_checked':checked,'bootstrap_recomputed':False}))

if __name__=='__main__':verify()
