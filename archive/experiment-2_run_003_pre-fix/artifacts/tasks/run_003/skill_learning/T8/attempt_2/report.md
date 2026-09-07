# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_003` / condition `skill_learning`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T3, T4, T5, T6, T7; missing: none
- Findings with values extracted: 16

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=avoid; cite_artifacts=True
- Word count: 359
- Numeric statements cited: 16 / 16 = 1.000000

## Artifacts

- `artifacts/tasks/run_003/skill_learning/T8/attempt_2/findings.json`
- `artifacts/tasks/run_003/skill_learning/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_003/skill_learning/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_003/skill_learning/T8/attempt_2/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `099ef2477c11b68ad35f01984d80fc60890c8e4c22523a0da082579cf03fc66a`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['descriptive_only', 'small_groups', 'association_not_causation', 'class_imbalance', 'no_operational_use', 'synthetic_data', 'sample_preview', 'model_limitations'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['descriptive_only', 'small_groups', 'association_not_causation', 'class_imbalance', 'no_operational_use', 'synthetic_data', 'sample_preview', 'model_limitations'].
