# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_012` / condition `skill_learning`, attempt 1: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T6; missing: T6
- Findings with values extracted: 4

### brief_sections

- Sections: key_findings, model_results, limitations, next_steps; causal_language=avoid; cite_artifacts=False
- Word count: 179
- Numeric statements cited: 0.000000

## Artifacts

- `artifacts/tasks/run_012/skill_learning/T8/attempt_1/findings.json`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_1/executive_brief.md`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_1/metrics.json`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `126c3c45e5815a680773ffc3fb775dd36d383a184b10e644381a8faf54eaf429`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T6']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': False}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'no_operational_use'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'no_operational_use'].
