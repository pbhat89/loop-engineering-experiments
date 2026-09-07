# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_002` / condition `skill_learning`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T3, T4, T5, T6, T7; missing: none
- Findings with values extracted: 16

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=avoid; cite_artifacts=True
- Word count: 359
- Numeric statements cited: 16 / 16 = 1.000000

## Artifacts

- `artifacts/tasks/run_002/skill_learning/T8/attempt_2/findings.json`
- `artifacts/tasks/run_002/skill_learning/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_002/skill_learning/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_002/skill_learning/T8/attempt_2/report.md`

## Caveats

- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.

## Method

- Seed: 42; plan sha256: `8a60f722b389a3150903564e2b05496585f9585e66176e7134296c62b451e8d0`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['association_not_causation', 'class_imbalance', 'no_operational_use', 'synthetic_data', 'sample_preview'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['association_not_causation', 'class_imbalance', 'no_operational_use', 'synthetic_data', 'sample_preview'].
