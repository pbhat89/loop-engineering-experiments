# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_011` / condition `skill_learning`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T4, T5, T6, T7; missing: T5, T6
- Findings with values extracted: 10

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=avoid; cite_artifacts=True
- Word count: 303
- Numeric statements cited: 11 / 11 = 1.000000

## Artifacts

- `artifacts/tasks/run_011/skill_learning/T8/attempt_2/findings.json`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `f530a4f6da9d7e7d3650c6b81f240c1d3e72d42146b02906d52b2cde1b7a39d9`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T4', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['synthetic_data', 'model_limitations'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'model_limitations'].
