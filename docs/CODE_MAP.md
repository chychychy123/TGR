# Code map

| Module | Role |
|---|---|
| `src/tgr/coarse.py` | Current-image prefilter, endpoint ranking, independent CEM, and four coarse residual modes. |
| `src/tgr/refinement.py` | Exact residual interpolation, separately seeded fine search, retained final candidate selection. |
| `src/tgr/planner.py` | Public `TGR` alias, resource loader, and constructors for the registered method/control names. |
| `src/tgr/metric.py` | Linear endpoint metric and frozen world-model goal-cost interface. |
| `src/tgr/guide_objective.py` | Actual offline search-guide loss used for the bundled preference/self/temporal heads. |
| `src/tgr/baselines.py` | Recorded retrieval control, normalized iCEM adapter, and batch expansion helper. |
| `src/tgr/ablations.py` | Remove context filtering, remove endpoint ranking, direct fine search, remove coarse retention. |
| `src/tgr/cube_adapter.py` | Seed propagation and cached action space for paired Cube reset. |

## Tensor and action conventions

The solver uses one environment at a time. Bank `start` and `end` have shape `(256,192)`. Bank `action` is standardized and has shape `(256,5,5*d)`: five model action blocks, each containing five physical commands. `d=5` for Cube and `d=2` for the other environments.

Residuals are defined in physical command units. Coarse residuals have shape `(4,5,d)` and are linearly interpolated to 25 commands with `align_corners=True`. The physical action sum is clipped to the Box bounds before standardization. The independent original branch retains its recorded sampling behavior; it is not routed through residual-branch clipping.

Fine search starts from the interpolated residual and uses an independent random stream. Final selection considers one independent mean, four coarse means, and four fine means. Best-visited samples are not used by TGR. The retrieval control retains its own historical best-visited rule; the difference is documented rather than changed during packaging.

## Guide fitting

The preference head is a linear metric initialized to identity. Its ranking objective combines observed-endpoint pairs and frozen forecast pairs. The stored feature file has 160 records: 128 training and 32 validation. Temporal and self targets are computed by the same registered alternatives. No test labels or simulator success outcomes enter this objective.

`train_guide.py` preserves the recorded AdamW learning rate, 2,000 updates, batch size, gradient clipping, identity regularization, and seed choices. CPU refitting is available for inspection but is not claimed bitwise identical to GPU fitting. The included frozen heads and their SHA checks are the reproduction path for the reported results.

## Original implementation mapping

Historical filenames are retained only in `reference/frozen/` and provenance so equivalence can be checked. The packaged modules change imports to relative package imports and format the same parsed code. They do not introduce a new optimizer, adaptive refinement rule, learned final selector, or model-training procedure.

`provenance/source_mapping.json` identifies the exact original and packaged SHA for each module. `tests/test_solver_parity.py` compares outputs and all candidate means against the original files with the same random seeds, for both action dimensions, four guide settings, all three refinement modes, and consecutive planning calls.
