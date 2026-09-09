# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_012` / condition `skill_learning`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T5, T6, T7; missing: T5, T6
- Findings with values extracted: 9

### brief_sections

- Sections: key_findings, model_results, limitations, next_steps; causal_language=avoid; cite_artifacts=True
- Word count: 245
- Numeric statements cited: 1.000000

## Artifacts

- `artifacts/tasks/run_012/skill_learning/T8/attempt_2/findings.json`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_012/skill_learning/T8/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `33d715765fdd6fe1ce7c3aa75802f343e4ce5b64d7351ce323bcd06cbdbecfa7`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'no_operational_use'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'no_operational_use'].
