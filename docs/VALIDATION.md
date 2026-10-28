# Distribution validation

Validated during source packaging on 2026-10-28. These are engineering checks, not new benchmark experiments.

| Check | Outcome |
|---|---|
| Core source conversion | Original file SHA verified; relative imports and AST-equivalent formatting only |
| Original-versus-packaged solver | 24 CPU cases, each with two consecutive solves; exact selected actions, final candidate tensors, costs, and audit records |
| Cases covered | Action dimensions 2/5; four guide settings; coarse-only, extra-coarse, and fine refinement modes |
| Lift / retention | Lifted actions within 1e-6 of the coarse actions; the first five candidates are retained exactly |
| Fixed resources | All four banks and all 36 heads verified against their recorded SHA |
| Installed runtime | Five solver/policy/world source hashes match the recorded revision |
| Checkpoint loading | All four exact world models load successfully on CPU using the bundled compatibility classes |
| Main-result matrix | 38,912 rows; every registered root/method/budget/head/planner key present exactly once |
| Main-result aggregation | Every method/budget table mean matches its underlying rows; macro 88.7044270833% |
| Manuscript-aligned display | All 80 method/budget entries use upward integer rounding; main display 98/94/83/83%, macro 89%; original records and intervals unchanged |
| Fixed statistics | S1/S2 evidence manifests verified; no bootstrap re-executed |
| Portable input check | PushT dataset and exact model inputs accepted by `evaluate.py --check-only` |

The CPU parity check uses a deterministic synthetic cost; it is not a physical task or an additional performance measurement. The new portable evaluation wrapper has not been used to rerun the full CUDA/simulator matrix in this packaging task. A clean-machine dependency installation was not repeated; the pinned packages and source hashes were checked against the existing experimental runtime.

The runtime emits an optional ALE/Atari dependency warning. The four registered environments do not use Atari. No GPU rollout, model fitting, API labeling, or background monitoring was started during packaging.

Run `python scripts/verify_release.py` after extracting the source archive to validate the included files and fixed results. `python tests/test_solver_parity.py` repeats the CPU conversion checks after dependencies are installed.
