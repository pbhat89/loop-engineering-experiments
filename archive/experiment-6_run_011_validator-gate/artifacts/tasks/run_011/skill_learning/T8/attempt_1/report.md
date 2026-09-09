# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_011` / condition `skill_learning`, attempt 1: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T4, T5, T6, T7; missing: T5, T6
- Findings with values extracted: 10

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=allow; cite_artifacts=False
- Word count: 279
- Numeric statements cited: 0 / 11 = 0.000000

## Artifacts

- `artifacts/tasks/run_011/skill_learning/T8/attempt_1/findings.json`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_1/executive_brief.md`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_1/metrics.json`
- `artifacts/tasks/run_011/skill_learning/T8/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `21954ca85c8bd5f7f67a0c9ee108fbc3c53098f02e8e53e6f845c9b25e2b2d2f`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T4', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'allow', 'cite_artifacts': False}`
- `write_report` params: `{'caveats': ['synthetic_data', 'model_limitations'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'model_limitations'].
