# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_006` / condition `reflection_only`, attempt 1: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T3, T4, T6; missing: T6
- Findings with values extracted: 7

### brief_sections

- Sections: key_findings, model_results, limitations, next_steps; causal_language=allow; cite_artifacts=False
- Word count: 221
- Numeric statements cited: 0.000000

## Artifacts

- `artifacts/tasks/run_006/reflection_only/T8/attempt_1/findings.json`
- `artifacts/tasks/run_006/reflection_only/T8/attempt_1/executive_brief.md`
- `artifacts/tasks/run_006/reflection_only/T8/attempt_1/metrics.json`
- `artifacts/tasks/run_006/reflection_only/T8/attempt_1/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `d1366a3144f5aea8f4b22fed97bea240ab593d6f9af33a7957d06866d9e31686`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T3', 'T4', 'T6']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'next_steps'], 'causal_language': 'allow', 'cite_artifacts': False}`
- `write_report` params: `{'caveats': ['descriptive_only', 'association_not_causation', 'model_limitations'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['descriptive_only', 'association_not_causation', 'model_limitations'].
