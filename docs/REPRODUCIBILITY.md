# Reproducibility and configuration

## Dataset preparation

The original dataset collection is available at [LeWM datasets and checkpoints](https://huggingface.co/collections/quentinll/lewm), linked from the [upstream codebase](https://github.com/lucas-maes/le-wm). Obtain and extract the corresponding HDF5 training datasets, respecting their source terms. For `.tar.zst` archives, the upstream extraction command is `tar --zstd -xvf archive.tar.zst`.

Place the actual files under the names expected by the evaluation entry point:

| Environment | Relative dataset path | Action dimension | World environment |
|---|---|---:|---|
| TwoRoom | `tworoom.h5` | 2 | `swm/TwoRoom-v1` |
| PushT | `pusht_expert_train.h5` | 2 | `swm/PushT-v1` |
| Cube | `ogbench/cube_single_expert.h5` | 5 | `swm/OGBCube-v0` |
| Reacher | `reacher.h5` | 2 | `swm/ReacherDMControl-v0` |

The stored root IDs refer to these source datasets, not arbitrary replacement datasets. The complete fixed selections are in `results/S1/<environment>/split.json`. Source training episodes used by each retrieval bank are listed in `resources/<environment>/retrieval_items.json`. Do not redraw roots or choose the best seed when reproducing the table.

The public collection may package data under different archive names. Check the extracted HDF5 schema and episode ordering; renaming unrelated files does not make the stored roots compatible. This distribution does not mirror the large HDF5 archives.

## Exact checkpoint files

The companion `TGR_world_model_checkpoints.zip` contains the four frozen models used for the recorded results. Extract it inside the source repository so that `checkpoints/<environment>/weights_epoch_10.pt` exists. The checkpoints are model artifacts, separate from the source ZIP. Their manifests are checked against `configs/experiment.json` before evaluation.

The packaged architecture classes match the upstream model source revision. Only load trusted checkpoints. Substituting a public checkpoint with another SHA changes the experiment; the evaluation entry point rejects that mismatch rather than silently attributing new results to the recorded model.

## Fixed planning settings

| Setting | Registered value |
|---|---|
| Horizon / command block / episode budget | 25 / 25 / 50 commands |
| Model action grouping | 5 model steps × 5 commands |
| Library / current-image prefilter / priors | 256 / 16 / 4 |
| Independent branch | 300 candidates, 30 elites |
| Trajectory branch, each prior | 75 candidates, 8 elites |
| Residual coordinates | 5 knots, then 25 commands |
| Residual initial standard deviation | 0.25, physical units |
| Final candidate pool | 1 independent + 4 coarse + 4 fine means |
| High iterations (PushT / others) | 30 / 10 per stage |
| Low iterations (PushT / others) | 10 / 4 per stage |
| Planning seeds | 7601, 7602; add `100 × root_index` inside each run |
| Learned-head seeds | 2131, 2132, 2133; all included |
| Simulator reset seed | `16903000 + root_index` |

World models, endpoint heads, library, and settings are fixed across the S1 evaluation. Cubic physical states are used for paired initialization and audit, not as planner input. The process-local Cube adapter preserves seed propagation; it is required for the recorded setup.

## Method-name mapping

The user-facing entry point accepts `tgr`, `cem300`, `cem900`, `coarse`, and `extra_coarse`. Archived result rows retain their original identifiers for SHA consistency:

| Public description | Stored identifier |
|---|---|
| TGR | `refined_jev` |
| CEM300 / CEM900 | `lewm300` / `lewm900` |
| Retrieval600 / Retrieval900 | `retrieval600` / `retrieval900` |
| iCEM900 | `icem900` |
| Coarse trajectory | `r6_jev` |
| Extra coarse search | `r6extra_jev` |
| Geometric / self / temporal guide | `refined_e0` / `refined_self` / `refined_temporal` |
| No current-image prefilter | `abl_context_jev` |
| No goal ranking | `abl_rank_none` |
| Direct fine search | `abl_direct_jev` |
| No retained coarse candidates | `abl_retain_jev` |

These identifiers are implementation provenance, not separate rows selected from different batches.

## Scope of reproduction

The historical S1 and S2 output files are immutable inputs to this release. `verify_release.py` verifies hashes and recomputes only simple aggregations from the stored rows; it never reruns bootstrap analysis.

The portable runner writes new results to a new directory. Its rollout setup, normalization, root selection, method factory, and seeds follow the frozen evaluator. The packaging checks include synthetic solver equivalence and input/runtime checks; they do not claim a new full physical reproduction of all 38,912 episodes. Full evaluation additionally requires the large datasets and a compatible CUDA/EGL installation.

The original study used one frozen world-model seed per environment. Independent episode roots and planning seeds are not independent world-model training replicas.
