# Complete results

All tables below use the complete S1 records. To match the manuscript, success rates for every method, budget, and cohort are rounded upward to whole percentages (ceiling). Macro averages are calculated from unrounded rates and then rounded upward for display. Confidence intervals, percentage-point differences, and statistical bounds retain their original calculations and are displayed to two decimals. Raw records are unchanged.

[Display CSV](../results/all_methods_display.csv) · [Original-precision CSV](../results/all_methods.csv)

## Matched high-budget comparison

| Method | TwoRoom | PushT | Cube | Reacher | Macro |
|---|---:|---:|---:|---:|---:|
| CEM300 | 96 | 92 | 70 | 86 | 86 |
| CEM900 | 99 | 93 | 74 | 88 | 88 |
| Retrieval600 | 99 | 95 | 74 | 81 | 87 |
| Retrieval900 | 99 | 96 | 79 | 83 | 89 |
| iCEM900 | 100 | 76 | 75 | 84 | 84 |
| Coarse trajectory | 98 | 93 | 82 | 84 | 89 |
| Extra coarse search | 97 | 95 | 83 | 80 | 89 |
| Geometric guide | 97 | 96 | 83 | 84 | 90 |
| Self guide | 98 | 95 | 82 | 86 | 90 |
| Temporal guide | 97 | 95 | 79 | 85 | 89 |
| TGR | 98 | 94 | 83 | 83 | 89 |
| No current prefilter | 99 | 95 | 79 | 80 | 88 |
| No goal ranking | 98 | 93 | 79 | 84 | 89 |
| Direct fine search | 96 | 93 | 81 | 83 | 89 |
| No coarse retention | 97 | 94 | 83 | 86 | 90 |

## Full per-environment tables

Root-cluster intervals preserve head/planner replicates within each root. Budget levels were fixed before evaluation.

### tworoom

| Method | Iterations | Success (%) | 95% CI | A (%) | B (%) |
|---|---:|---:|---|---:|---:|
| No current prefilter | 10 | 99 | [96.09, 100.00] | 99 | 99 |
| Direct fine search | 10 | 96 | [92.45, 98.83] | 96 | 97 |
| No goal ranking | 10 | 98 | [95.70, 99.22] | 97 | 99 |
| No coarse retention | 10 | 97 | [93.62, 99.22] | 96 | 98 |
| iCEM900 | 4 | 100 | [97.66, 100.00] | 100 | 99 |
| iCEM900 | 10 | 100 | [98.83, 100.00] | 100 | 100 |
| CEM300 | 4 | 93 | [87.89, 96.48] | 93 | 93 |
| CEM300 | 10 | 96 | [91.41, 98.44] | 94 | 97 |
| CEM900 | 4 | 99 | [96.09, 100.00] | 99 | 99 |
| CEM900 | 10 | 99 | [95.70, 100.00] | 98 | 99 |
| Coarse trajectory | 10 | 98 | [94.79, 99.35] | 97 | 99 |
| Extra coarse search | 10 | 97 | [93.75, 99.22] | 96 | 99 |
| Geometric guide | 10 | 97 | [93.75, 99.22] | 96 | 99 |
| TGR | 4 | 96 | [91.15, 98.44] | 94 | 97 |
| TGR | 10 | 98 | [94.14, 99.22] | 96 | 99 |
| Self guide | 10 | 98 | [94.01, 99.35] | 98 | 97 |
| Temporal guide | 10 | 97 | [92.97, 99.09] | 95 | 99 |
| Retrieval600 | 10 | 99 | [96.88, 99.61] | 98 | 100 |
| Retrieval900 | 4 | 97 | [93.75, 98.83] | 97 | 97 |
| Retrieval900 | 10 | 99 | [96.88, 99.61] | 99 | 99 |

| Budget | TGR minus control | Gap (pp) | 95% CI | Family-wise one-sided lower (pp) |
|---|---|---:|---|---:|
| high | No current prefilter | -1.43 | [-3.52, 0.13] | -5.08 |
| high | Direct fine search | 1.04 | [0.00, 2.86] | 0.00 |
| high | No goal ranking | -0.65 | [-2.73, 1.17] | -4.05 |
| high | No coarse retention | 0.39 | [0.00, 1.17] | 0.00 |
| high | iCEM900 | -2.60 | [-5.34, -0.52] | -7.29 |
| high | CEM300 | 1.69 | [0.13, 3.91] | 0.00 |
| high | CEM900 | -1.04 | [-2.99, 0.26] | -4.56 |
| high | Coarse trajectory | -0.39 | [-1.17, 0.00] | -1.95 |
| high | Extra coarse search | 0.13 | [-1.04, 1.30] | -1.69 |
| high | Geometric guide | 0.13 | [0.00, 0.39] | 0.00 |
| high | Self guide | 0.00 | [-1.95, 2.08] | -3.39 |
| high | Temporal guide | 0.65 | [0.00, 1.56] | 0.00 |
| high | Retrieval600 | -1.43 | [-4.17, 0.78] | -5.99 |
| high | Retrieval900 | -1.43 | [-4.17, 0.78] | -5.99 |
| low | iCEM900 | -4.17 | [-7.81, -1.04] | -9.64 |
| low | CEM300 | 2.47 | [0.39, 5.21] | -0.39 |
| low | CEM900 | -3.39 | [-6.77, -0.78] | -8.33 |
| low | Retrieval900 | -1.43 | [-5.47, 1.95] | -7.03 |

### pusht

| Method | Iterations | Success (%) | 95% CI | A (%) | B (%) |
|---|---:|---:|---|---:|---:|
| No current prefilter | 30 | 95 | [91.54, 97.40] | 94 | 96 |
| Direct fine search | 30 | 93 | [89.45, 95.96] | 91 | 96 |
| No goal ranking | 30 | 93 | [89.06, 95.70] | 93 | 93 |
| No coarse retention | 30 | 94 | [89.84, 96.35] | 93 | 95 |
| iCEM900 | 10 | 77 | [70.70, 82.03] | 78 | 76 |
| iCEM900 | 30 | 76 | [69.14, 81.64] | 71 | 82 |
| CEM300 | 10 | 90 | [83.98, 93.75] | 86 | 93 |
| CEM300 | 30 | 92 | [86.33, 95.31] | 88 | 95 |
| CEM900 | 10 | 93 | [87.89, 96.09] | 91 | 94 |
| CEM900 | 30 | 93 | [89.06, 96.48] | 91 | 96 |
| Coarse trajectory | 30 | 93 | [89.45, 96.09] | 91 | 96 |
| Extra coarse search | 30 | 95 | [91.02, 97.01] | 96 | 94 |
| Geometric guide | 30 | 96 | [92.58, 98.44] | 95 | 97 |
| TGR | 10 | 91 | [86.72, 94.27] | 89 | 94 |
| TGR | 30 | 94 | [89.84, 96.35] | 93 | 95 |
| Self guide | 30 | 95 | [90.89, 96.74] | 95 | 94 |
| Temporal guide | 30 | 95 | [91.28, 97.27] | 95 | 95 |
| Retrieval600 | 30 | 95 | [91.02, 97.66] | 93 | 97 |
| Retrieval900 | 10 | 94 | [90.23, 96.88] | 91 | 97 |
| Retrieval900 | 30 | 96 | [91.80, 98.05] | 96 | 96 |

| Budget | TGR minus control | Gap (pp) | 95% CI | Family-wise one-sided lower (pp) |
|---|---|---:|---|---:|
| high | No current prefilter | -1.30 | [-3.39, 0.65] | -5.08 |
| high | Direct fine search | 0.39 | [-2.34, 3.12] | -4.04 |
| high | No goal ranking | 0.78 | [-2.21, 3.65] | -3.79 |
| high | No coarse retention | 0.00 | [0.00, 0.00] | 0.00 |
| high | iCEM900 | 17.58 | [11.20, 24.35] | 7.42 |
| high | CEM300 | 2.34 | [-2.08, 6.90] | -4.44 |
| high | CEM900 | 0.39 | [-3.78, 4.43] | -6.64 |
| high | Coarse trajectory | 0.39 | [-2.60, 3.26] | -4.44 |
| high | Extra coarse search | -0.91 | [-2.73, 0.78] | -3.91 |
| high | Geometric guide | -2.34 | [-5.60, 0.52] | -7.56 |
| high | Self guide | -0.65 | [-3.52, 2.21] | -5.35 |
| high | Temporal guide | -1.17 | [-3.26, 0.91] | -4.69 |
| high | Retrieval600 | -1.17 | [-4.95, 2.47] | -7.42 |
| high | Retrieval900 | -1.95 | [-5.21, 0.91] | -7.58 |
| low | iCEM900 | 14.19 | [8.46, 20.05] | 6.12 |
| low | CEM300 | 1.69 | [-3.26, 6.77] | -5.31 |
| low | CEM900 | -1.43 | [-5.73, 3.12] | -7.26 |
| low | Retrieval900 | -2.99 | [-7.03, 0.78] | -8.46 |

### cube

| Method | Iterations | Success (%) | 95% CI | A (%) | B (%) |
|---|---:|---:|---|---:|---:|
| No current prefilter | 10 | 79 | [72.14, 84.77] | 84 | 74 |
| Direct fine search | 10 | 81 | [74.22, 86.59] | 84 | 79 |
| No goal ranking | 10 | 79 | [72.27, 85.16] | 84 | 75 |
| No coarse retention | 10 | 83 | [76.30, 88.15] | 84 | 82 |
| iCEM900 | 4 | 75 | [67.19, 82.42] | 81 | 70 |
| iCEM900 | 10 | 75 | [66.80, 81.64] | 79 | 70 |
| CEM300 | 4 | 67 | [58.59, 74.22] | 75 | 58 |
| CEM300 | 10 | 70 | [61.72, 77.34] | 80 | 60 |
| CEM900 | 4 | 73 | [64.84, 80.08] | 80 | 66 |
| CEM900 | 10 | 74 | [66.41, 80.86] | 79 | 69 |
| Coarse trajectory | 10 | 82 | [75.39, 87.63] | 83 | 81 |
| Extra coarse search | 10 | 83 | [76.56, 88.41] | 85 | 82 |
| Geometric guide | 10 | 83 | [76.56, 88.28] | 86 | 80 |
| TGR | 4 | 83 | [76.43, 87.89] | 84 | 81 |
| TGR | 10 | 83 | [75.91, 88.02] | 83 | 82 |
| Self guide | 10 | 82 | [75.78, 87.11] | 86 | 78 |
| Temporal guide | 10 | 79 | [71.88, 85.03] | 83 | 76 |
| Retrieval600 | 10 | 74 | [66.41, 80.47] | 79 | 69 |
| Retrieval900 | 4 | 75 | [67.58, 81.64] | 82 | 68 |
| Retrieval900 | 10 | 79 | [71.48, 85.16] | 83 | 75 |

| Budget | TGR minus control | Gap (pp) | 95% CI | Family-wise one-sided lower (pp) |
|---|---|---:|---|---:|
| high | No current prefilter | 3.52 | [-1.95, 8.98] | -4.96 |
| high | Direct fine search | 1.56 | [-2.21, 5.34] | -4.69 |
| high | No goal ranking | 3.26 | [-1.30, 7.94] | -4.18 |
| high | No coarse retention | -0.26 | [-1.56, 0.91] | -2.47 |
| high | iCEM900 | 7.94 | [2.86, 13.28] | -0.00 |
| high | CEM300 | 12.63 | [7.16, 18.36] | 4.30 |
| high | CEM900 | 8.33 | [3.26, 13.54] | 0.77 |
| high | Coarse trajectory | 0.52 | [-1.56, 2.73] | -2.99 |
| high | Extra coarse search | -0.52 | [-2.47, 1.30] | -3.52 |
| high | Geometric guide | -0.26 | [-2.73, 2.08] | -4.04 |
| high | Self guide | 0.52 | [-2.86, 3.78] | -4.83 |
| high | Temporal guide | 3.52 | [-0.52, 7.68] | -2.35 |
| high | Retrieval600 | 8.72 | [2.86, 14.84] | -0.79 |
| high | Retrieval900 | 3.65 | [-1.82, 9.11] | -4.96 |
| low | iCEM900 | 7.29 | [2.34, 12.37] | 0.52 |
| low | CEM300 | 15.89 | [10.03, 22.01] | 7.81 |
| low | CEM900 | 9.64 | [4.17, 15.23] | 2.21 |
| low | Retrieval900 | 7.68 | [2.86, 12.63] | 1.17 |

### reacher

| Method | Iterations | Success (%) | 95% CI | A (%) | B (%) |
|---|---:|---:|---|---:|---:|
| No current prefilter | 10 | 80 | [74.74, 85.03] | 83 | 78 |
| Direct fine search | 10 | 83 | [77.60, 87.50] | 84 | 83 |
| No goal ranking | 10 | 84 | [78.12, 88.28] | 83 | 85 |
| No coarse retention | 10 | 86 | [80.47, 89.19] | 89 | 82 |
| iCEM900 | 4 | 82 | [75.39, 86.72] | 77 | 86 |
| iCEM900 | 10 | 84 | [78.91, 89.06] | 81 | 88 |
| CEM300 | 4 | 86 | [80.08, 89.84] | 79 | 93 |
| CEM300 | 10 | 86 | [80.47, 90.23] | 86 | 86 |
| CEM900 | 4 | 84 | [78.91, 88.67] | 83 | 86 |
| CEM900 | 10 | 88 | [82.42, 91.41] | 84 | 91 |
| Coarse trajectory | 10 | 84 | [77.99, 87.76] | 87 | 80 |
| Extra coarse search | 10 | 80 | [74.35, 84.24] | 84 | 77 |
| Geometric guide | 10 | 84 | [77.73, 88.28] | 87 | 80 |
| TGR | 4 | 85 | [79.95, 88.80] | 85 | 85 |
| TGR | 10 | 83 | [77.21, 86.85] | 85 | 80 |
| Self guide | 10 | 86 | [81.38, 90.23] | 88 | 85 |
| Temporal guide | 10 | 85 | [79.95, 88.54] | 88 | 82 |
| Retrieval600 | 10 | 81 | [75.39, 85.16] | 82 | 80 |
| Retrieval900 | 4 | 79 | [72.66, 83.59] | 75 | 82 |
| Retrieval900 | 10 | 83 | [76.95, 86.72] | 83 | 83 |

| Budget | TGR minus control | Gap (pp) | 95% CI | Family-wise one-sided lower (pp) |
|---|---|---:|---|---:|
| high | No current prefilter | 2.34 | [-3.91, 8.46] | -7.68 |
| high | Direct fine search | -0.52 | [-5.86, 4.82] | -9.38 |
| high | No goal ranking | -0.91 | [-7.03, 5.21] | -10.69 |
| high | No coarse retention | -2.73 | [-6.25, 0.65] | -8.61 |
| high | iCEM900 | -1.69 | [-9.38, 5.73] | -14.19 |
| high | CEM300 | -3.26 | [-10.29, 3.65] | -14.33 |
| high | CEM900 | -4.82 | [-11.46, 1.69] | -15.62 |
| high | Coarse trajectory | -0.78 | [-4.17, 2.47] | -6.38 |
| high | Extra coarse search | 2.73 | [-1.17, 6.51] | -3.52 |
| high | Geometric guide | -0.91 | [-6.77, 5.08] | -10.16 |
| high | Self guide | -3.65 | [-8.20, 0.78] | -11.20 |
| high | Temporal guide | -2.08 | [-7.55, 3.12] | -10.95 |
| high | Retrieval600 | 1.82 | [-4.69, 8.07] | -8.47 |
| high | Retrieval900 | 0.26 | [-6.12, 6.51] | -10.04 |
| low | iCEM900 | 3.26 | [-3.26, 10.03] | -5.60 |
| low | CEM300 | -0.65 | [-7.03, 5.73] | -9.51 |
| low | CEM900 | 0.52 | [-5.86, 6.90] | -8.33 |
| low | Retrieval900 | 6.38 | [0.26, 12.37] | -2.34 |

## Interpretation and additional records

The high-budget comparison family contains 56 contrasts; the low-budget family contains 16. Exploratory two-sided intervals are shown alongside the registered simultaneous lower bounds. A confidence interval crossing zero does not establish equivalence or non-inferiority.

Cube supports a positive high-budget TGR versus CEM900 difference (+8.33 percentage points) under the registered simultaneous comparison. PushT supports a positive contrast against the registered mean-return iCEM configuration. These findings do not establish superiority over every control or the necessity of every component.

Per-head, per-planning-seed, cohort, and runtime measurements are retained in results/S1/<environment>/analysis.json; every episode row is retained in rows.json. No favorable-head or favorable-budget selection is applied.

S2 under results/S2/ evaluates all nine first-plan candidates from matched initial conditions. Its 25-command candidate-execution outcomes and fixed guide-validation records supplement mechanism analysis and do not replace the 50-command S1 results.
