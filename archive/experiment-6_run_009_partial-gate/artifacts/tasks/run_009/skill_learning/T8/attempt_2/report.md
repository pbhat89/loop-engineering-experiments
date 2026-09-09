# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_009` / condition `skill_learning`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T5, T6, T7; missing: T5, T6 [source: artifacts/tasks/run_009/skill_learning/T8/attempt_2/findings.json]
- Findings with values extracted: 9 [source: artifacts/tasks/run_009/skill_learning/T8/attempt_2/findings.json]

### brief_sections

- Sections: key_findings, model_results, limitations, synthetic_caveats, next_steps; causal_language=avoid; cite_artifacts=True [source: artifacts/tasks/run_009/skill_learning/T8/attempt_2/executive_brief.md]
- Word count: 290 [source: metrics.json#brief.word_count]
- Numeric statements cited: 1.000000 [source: metrics.json#brief]

## Artifacts

- `artifacts/tasks/run_009/skill_learning/T8/attempt_2/findings.json`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `ce9dc6420a74e5d3ff694a86bd6fe816f2a2528e04d1bb1171088e5ffcd0171d`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T5', 'T6', 'T7']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'synthetic_caveats', 'next_steps'], 'cite_artifacts': True, 'causal_language': 'avoid'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'model_limitations'], 'cite_artifacts': True, 'show_denominators': False}`
- Report options: show_denominators=False, cite_artifacts=True, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'model_limitations'].
