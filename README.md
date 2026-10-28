<div align="center">

# TGR: Trajectory-Guided Refinement

**From coherent motion to local corrections in visual planning**

[Overview](#overview) · [Installation](#installation) · [Data and models](#data-and-models) · [Evaluation](#evaluation) · [Results](#results) · [中文说明](docs/README.zh-CN.md)

</div>

## Overview

Recorded trajectories provide useful motion structure, but adapting them to a new visual goal requires flexible corrections. **TGR** separates these two roles: it first searches for coherent residual adjustments around retrieved action priors, then refines them at command resolution. The earlier plans remain available during final selection.

TGR operates with a **frozen visual world model**. An offline endpoint guide ranks retrieval candidates; the original latent goal cost evaluates all searched plans and selects the action sequence. Deployment uses current RGB, goal RGB, and command history.

<p align="center">
  <img src="assets/framework.png" width="100%" alt="TGR framework: visual retrieval, coarse residual search, command-level refinement, retained candidate selection, and execution.">
</p>

**How it works**

1. **Retrieve:** match the current observation to recorded trajectories, then rank their endpoints against the goal.
2. **Adapt:** search low-dimensional residuals around four retrieved action priors, while an independent CEM branch explores without retrieval.
3. **Refine:** lift each coarse residual into command-level coordinates and continue the search.
4. **Retain and select:** score the independent, coarse, and fine final means with the same world-model goal objective, then execute the selected plan.

The implementation is in [`src/tgr`](src/tgr). The framework is also available as a [vector PDF](assets/framework.pdf). This source distribution contains code, resources, and experiment records; no manuscript or claimed venue acceptance is included.

## Installation

The recorded experiments used **Linux, Python 3.11, PyTorch 2.8.0, CUDA 12.8**, and the pinned `stable-worldmodel` revision below. Use an isolated environment; newer planning APIs may differ.

```bash
# From this repository's root
uv venv --python 3.11 .venv
source .venv/bin/activate

uv pip install torch==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128
uv pip install -r requirements.txt
uv pip install -e . --no-deps

python scripts/check_runtime.py
python scripts/verify_release.py
python tests/test_solver_parity.py
```

`requirements.txt` pins the runtime to commit `21446f1ede6d5284e981bd7b47f432b994e6d812`. The complete observed package inventory is in [`provenance/runtime-lock.txt`](provenance/runtime-lock.txt). Runtime checks compare the installed planning source hashes with the recorded versions. Linux/EGL evaluation is the supported configuration; native Windows simulator evaluation has not been validated.

The release/result verification uses only the Python standard library. The solver parity test runs on CPU with a synthetic cost and does not launch a simulator.

## Data and models

**Included in this repository:**

- Four fixed trajectory banks and action normalization statistics.
- Nine frozen endpoint-guide heads per environment: three preference, three self-supervised, and three temporal heads.
- Offline train/validation latent features and numeric preference targets; no API access is required.
- The exact 128 evaluation roots per environment, complete per-run result rows, fixed confidence intervals, and evidence hashes.

**External inputs:** the original HDF5 datasets and the four matching world-model checkpoints. Dataset preparation and checkpoint compatibility are described in [Reproducibility](docs/REPRODUCIBILITY.md). The companion `TGR_world_model_checkpoints.zip`, when supplied with this local delivery, contains the exact checkpoint files; unpack it into this repository. These files are kept separate from the source archive.

```text
tgr/
├── external_data/                  # Dataset files, downloaded separately
│   ├── pusht_expert_train.h5
│   ├── tworoom.h5
│   ├── reacher.h5
│   └── ogbench/cube_single_expert.h5
├── checkpoints/                    # Exact checkpoint SHA required
│   ├── pusht/weights_epoch_10.pt
│   ├── tworoom/weights_epoch_10.pt
│   ├── reacher/weights_epoch_10.pt
│   └── cube/weights_epoch_10.pt
└── resources/                      # Included banks, heads, statistics, features
    └── <environment>/
```

World-model checkpoint identities are recorded in [`configs/experiment.json`](configs/experiment.json). Public checkpoints with a different SHA are not interchangeable with the models behind the reported table. Guide refitting is optional; use the bundled heads to reproduce the recorded configuration.

## Evaluation

First validate inputs without running an experiment:

```bash
python scripts/evaluate.py \
  --environment pusht \
  --data-root external_data \
  --checkpoint checkpoints/pusht/weights_epoch_10.pt \
  --check-only
```

Evaluate TGR on all 128 roots, three fixed guide heads, and both planning seeds:

```bash
export CUDA_VISIBLE_DEVICES=1
export MUJOCO_EGL_DEVICE_ID=1
export MUJOCO_GL=egl
export SDL_VIDEODRIVER=dummy
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2

nice -n 10 python scripts/evaluate.py \
  --environment pusht --method tgr --budget high \
  --data-root external_data \
  --checkpoint checkpoints/pusht/weights_epoch_10.pt \
  --output runs/pusht_tgr
```

Run the complete registered controls and ablations for one environment:

```bash
nice -n 10 python scripts/evaluate.py \
  --environment cube --suite both \
  --data-root external_data \
  --checkpoint checkpoints/cube/weights_epoch_10.pt \
  --output runs/cube_all
```

The full matrix has 38 configurations × 2 planning seeds × 128 roots = **9,728 episodes per environment**. `--suite high` and `--suite low` run the corresponding fixed subsets. `--root-count 1` is useful for an integration check; it is not a replacement for the full result. Outputs must use a new directory; the runner does not overwrite or silently resume an existing run. No scheduler or remote-control process is started by installation.

Each run saves the selected plans, final candidates when applicable, executed actions, simulator audit states, model-call counts, elapsed time, and per-episode JSON results. Simulator state is used for reset/audit only; the policy receives RGB inputs.

### Optional offline guide fitting

```bash
python scripts/train_guide.py \
  --environment pusht --kind jev_search --seed 2131 \
  --device cpu --output runs/guide_refit/pusht_2131.pt
```

This fits the fixed objective on the included latent features and numeric targets. It makes **zero online model/API requests**. A refitted head is a new artifact and does not automatically replace a bundled evaluation head. Details are in [the code map](docs/CODE_MAP.md).

## Results

Primary results below come from the complete **S1 independent-episode evaluation** of the frozen method. Each environment uses 128 roots, two planning seeds, and all three preference heads. The world model is fixed per environment. Planning uses a 25-command horizon and execution block, with at most 50 commands per episode.

| Environment | TGR success (%) | Root-cluster 95% CI |
|:--|--:|:--|
| TwoRoom | **98** | [94.14, 99.22] |
| PushT | **94** | [89.84, 96.35] |
| Cube | **83** | [75.91, 88.02] |
| Reacher | **83** | [77.21, 86.85] |
| **Macro average** | **89** | — |

The full evaluation contains **38,912 episodes**, including matched planners, four component ablations, alternative guides, and two fixed iteration budgets. The manuscript-aligned display is available in [`results/all_methods_display.csv`](results/all_methods_display.csv); [`results/all_methods.csv`](results/all_methods.csv) retains original precision. Complete fixed statistics and per-run rows are under [`results/S1`](results/S1). [Results and settings](docs/RESULTS.md) contains the matched comparison tables and statistical interpretation. Actual resource use is retained in these files.

Separate first-plan mechanism experiments are included under [`results/S2`](results/S2). They execute each candidate from the same initial condition for up to 25 commands; their rates are separate from the 50-command main evaluation.

## Repository structure

```text
src/tgr/           Core method, costs, controls, component ablations
scripts/           Evaluation, offline guide fitting, input/result verification
tests/             CPU equivalence checks against the frozen solver
configs/           Registered search settings and environment reset configuration
resources/         Fixed banks, guide weights, normalization, training features
results/           Recorded main and mechanism results, rows, confidence intervals
assets/            Current framework figure (PNG and PDF)
reference/frozen/  Original solver files, preserved for code-equivalence checks
third_party/       Checkpoint compatibility modules and upstream licenses
provenance/        Source mappings, package inventory, SHA manifests, validation
```

