# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_006` / condition `self_refine_memory`, attempt 4: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T4, T7; missing: none
- Findings with values extracted: 8

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=allow; cite_artifacts=True
- Word count: 270
- Numeric statements cited: 8 / 8 = 1.000000

## Artifacts

- `artifacts/tasks/run_006/self_refine_memory/T8/attempt_4/findings.json`
- `artifacts/tasks/run_006/self_refine_memory/T8/attempt_4/executive_brief.md`
- `artifacts/tasks/run_006/self_refine_memory/T8/attempt_4/metrics.json`
- `artifacts/tasks/run_006/self_refine_memory/T8/attempt_4/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `a95d2b50bf8ccadf907c5ae72e4cf9267eab60a08d2ae31d57954c57da2729dd`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T4', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'allow', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'model_limitations'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'model_limitations'].
