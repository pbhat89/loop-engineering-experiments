# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_006` / condition `feedback_memory`, attempt 1: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T1, T3, T4, T7; missing: none
- Findings with values extracted: 11

### brief_sections

- Sections: key_findings, model_results, limitations, next_steps; causal_language=avoid; cite_artifacts=False
- Word count: 241
- Numeric statements cited: 0 / 11 = 0.000000

## Artifacts

- `artifacts/tasks/run_006/feedback_memory/T8/attempt_1/findings.json`
- `artifacts/tasks/run_006/feedback_memory/T8/attempt_1/executive_brief.md`
- `artifacts/tasks/run_006/feedback_memory/T8/attempt_1/metrics.json`
- `artifacts/tasks/run_006/feedback_memory/T8/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `601f055aa3849c924a0e1448372bae510ef7fad6eb27ea5adc3d8512bcb8f5ac`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T1', 'T3', 'T4', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': False}`
- `write_report` params: `{'caveats': ['synthetic_data', 'sample_preview', 'association_not_causation', 'small_groups', 'model_limitations', 'no_operational_use'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'sample_preview', 'association_not_causation', 'small_groups', 'model_limitations', 'no_operational_use'].
