"""Verify the exact planning API version used for the stored results."""
import hashlib
import inspect
import json
from pathlib import Path

def check_runtime():
    import stable_worldmodel
    root=Path(inspect.getfile(stable_worldmodel)).parent
    meta=json.loads((Path(__file__).resolve().parents[1]/'provenance/tested_environment.json').read_text())
    for relative, record in meta['runtime_files'].items():
        file=root/relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=record['sha256']:
            raise RuntimeError(f'Runtime differs at {relative}; install the pinned Git commit in requirements.txt.')
    return {'runtime_source_hashes':'passed','files':len(meta['runtime_files'])}

if __name__=='__main__':print(json.dumps(check_runtime()))
