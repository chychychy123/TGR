"""Render paper-aligned integer success displays from unchanged recorded data."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVS = ['tworoom', 'pusht', 'cube', 'reacher']
LABELS = {
    'lewm300': 'CEM300', 'lewm900': 'CEM900',
    'retrieval600': 'Retrieval600', 'retrieval900': 'Retrieval900',
    'icem900': 'iCEM900', 'r6_jev': 'Coarse trajectory',
    'r6extra_jev': 'Extra coarse search', 'refined_e0': 'Geometric guide',
    'refined_self': 'Self guide', 'refined_temporal': 'Temporal guide',
    'refined_jev': 'TGR', 'abl_context_jev': 'No current prefilter',
    'abl_rank_none': 'No goal ranking', 'abl_direct_jev': 'Direct fine search',
    'abl_retain_jev': 'No coarse retention',
}
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
ci = lambda x: '[' + ', '.join(f'{v:.2f}' for v in x) + ']'
display = lambda x: str(math.ceil(x))


def replace_table(path, header, table):
    text = path.read_text(encoding='utf-8')
    start = text.index(header)
    end = text.index('\n\n', start)
    path.write_text(text[:start] + table + text[end:], encoding='utf-8')


def main():
    cfg = read(ROOT / 'configs/experiment.json')
    data = {e: read(ROOT / 'results/S1' / e / 'analysis.json') for e in ENVS}
    high = {e: {r['method']: r for r in data[e]['table']
                if r['iterations'] == cfg['planning']['high_iterations'][e]} for e in ENVS}
    main_rows = {e: high[e]['refined_jev'] for e in ENVS}
    macro = sum(r['success_percent'] for r in main_rows.values()) / 4

    english = ['| Environment | TGR success (%) | Root-cluster 95% CI |', '|:--|--:|:--|']
    chinese = ['| 环境 | 成功率 | 95% root 聚类区间 |', '|---|---:|---|']
    titles = {'tworoom': 'TwoRoom', 'pusht': 'PushT', 'cube': 'Cube', 'reacher': 'Reacher'}
    for e, r in main_rows.items():
        english.append(f"| {titles[e]} | **{display(r['success_percent'])}** | {ci(r['success_root95'])} |")
        chinese.append(f"| {titles[e]} | **{display(r['success_percent'])}%** | {ci(r['success_root95'])} |")
    english.append(f'| **Macro average** | **{display(macro)}** | — |')
    chinese.append(f'| 四环境平均 | **{display(macro)}%** | — |')
    replace_table(ROOT / 'README.md', english[0], '\n'.join(english))
    replace_table(ROOT / 'docs/README.zh-CN.md', chinese[0], '\n'.join(chinese))

    lines = [
        '# Complete results', '',
        'All tables below use the complete S1 records. To match the manuscript, success rates '
        'for every method, budget, and cohort are rounded upward to whole percentages (ceiling). '
        'Macro averages are calculated from unrounded rates and then rounded upward for display. '
        'Confidence intervals, percentage-point differences, and statistical bounds retain their '
        'original calculations and are displayed to two decimals. Raw records are unchanged.', '',
        '[Display CSV](../results/all_methods_display.csv) · [Original-precision CSV](../results/all_methods.csv)', '',
        '## Matched high-budget comparison', '',
        '| Method | TwoRoom | PushT | Cube | Reacher | Macro |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for k, label in LABELS.items():
        values = [high[e][k]['success_percent'] for e in ENVS]
        lines.append('| ' + label + ' | ' + ' | '.join(map(display, values)) + ' | ' + display(sum(values)/4) + ' |')
    lines += ['', '## Full per-environment tables', '',
              'Root-cluster intervals preserve head/planner replicates within each root. Budget levels were fixed before evaluation.']
    display_rows = []
    for e in ENVS:
        lines += ['', '### ' + e, '', '| Method | Iterations | Success (%) | 95% CI | A (%) | B (%) |',
                  '|---|---:|---:|---|---:|---:|']
        for r in data[e]['table']:
            lines.append(f"| {LABELS[r['method']]} | {r['iterations']} | {display(r['success_percent'])} | "
                         f"{ci(r['success_root95'])} | {display(r['cohorts']['A'])} | {display(r['cohorts']['B'])} |")
            display_rows.append({
                'environment': e, 'method': r['method'], 'method_label': LABELS[r['method']],
                'budget': 'high' if r['iterations'] == cfg['planning']['high_iterations'][e] else 'low',
                'iterations': r['iterations'], 'success_percent_display': math.ceil(r['success_percent']),
                'ci95_low': r['success_root95'][0], 'ci95_high': r['success_root95'][1],
                'cohort_A_percent_display': math.ceil(r['cohorts']['A']),
                'cohort_B_percent_display': math.ceil(r['cohorts']['B']),
            })
        lines += ['', '| Budget | TGR minus control | Gap (pp) | 95% CI | Family-wise one-sided lower (pp) |',
                  '|---|---|---:|---|---:|']
        for r in data[e]['contrasts']:
            lines.append(f"| {r['panel']} | {LABELS[r['control'][0]]} | {r['success_gap_pp']:.2f} | "
                         f"{ci(r['success_gap_95'])} | {r['simultaneous_four_environment_one_sided_lower_pp']:.2f} |")
    lines += ['', '## Interpretation and additional records', '',
        'The high-budget comparison family contains 56 contrasts; the low-budget family contains 16. '
        'Exploratory two-sided intervals are shown alongside the registered simultaneous lower bounds. '
        'A confidence interval crossing zero does not establish equivalence or non-inferiority.', '',
        'Cube supports a positive high-budget TGR versus CEM900 difference (+8.33 percentage points) '
        'under the registered simultaneous comparison. PushT supports a positive contrast against the '
        'registered mean-return iCEM configuration. These findings do not establish superiority over '
        'every control or the necessity of every component.', '',
        'Per-head, per-planning-seed, cohort, and runtime measurements are retained in '
        'results/S1/<environment>/analysis.json; every episode row is retained in rows.json. '
        'No favorable-head or favorable-budget selection is applied.', '',
        'S2 under results/S2/ evaluates all nine first-plan candidates from matched initial conditions. '
        'Its 25-command candidate-execution outcomes and fixed guide-validation records supplement '
        'mechanism analysis and do not replace the 50-command S1 results.', '']
    (ROOT / 'docs/RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(display_rows[0]))
    writer.writeheader(); writer.writerows(display_rows)
    (ROOT / 'results/all_methods_display.csv').write_text(buffer.getvalue(), encoding='utf-8', newline='')
    policy = {
        'success_display': 'ceil to whole percentage for every method, budget and cohort',
        'macro_display': 'equal-weight mean of raw environment rates, then ceil',
        'confidence_intervals_and_gaps': 'calculated from raw data; display to two decimals',
        'main_display': {e: math.ceil(main_rows[e]['success_percent']) for e in ENVS},
        'macro_display_percent': math.ceil(macro),
        'raw_results_unchanged': True,
        'source_analysis_sha256': {e: hashlib.sha256((ROOT/'results/S1'/e/'analysis.json').read_bytes()).hexdigest() for e in ENVS},
    }
    (ROOT / 'provenance/display_policy.json').write_text(json.dumps(policy, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'rendered', 'main_display': policy['main_display'],
                      'macro_display_percent': math.ceil(macro), 'display_rows': len(display_rows)}))


if __name__ == '__main__':
    main()
