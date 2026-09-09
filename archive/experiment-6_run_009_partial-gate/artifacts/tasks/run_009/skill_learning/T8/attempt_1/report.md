# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_009` / condition `skill_learning`, attempt 1: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T2, T6; missing: T6 [source: artifacts/tasks/run_009/skill_learning/T8/attempt_1/findings.json]
- Findings with values extracted: 4 [source: artifacts/tasks/run_009/skill_learning/T8/attempt_1/findings.json]

### brief_sections

- Sections: key_findings, model_results, limitations, next_steps; causal_language=allow; cite_artifacts=True [source: artifacts/tasks/run_009/skill_learning/T8/attempt_1/executive_brief.md]
- Word count: 189 [source: metrics.json#brief.word_count]
- Numeric statements cited: 1.000000 [source: metrics.json#brief]

## Artifacts

- `artifacts/tasks/run_009/skill_learning/T8/attempt_1/findings.json`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_1/executive_brief.md`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_1/metrics.json`
- `artifacts/tasks/run_009/skill_learning/T8/attempt_1/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `b77a08d3b896be54439af9f820cf0839e3bdbd0a2294eba34128e9a9c7301ecd`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T2', 'T6']}`
- `brief_sections` params: `{'sections': ['key_findings', 'model_results', 'limitations', 'next_steps'], 'cite_artifacts': True, 'causal_language': 'allow'}`
- `write_report` params: `{'caveats': ['descriptive_only', 'association_not_causation', 'model_limitations'], 'cite_artifacts': True, 'show_denominators': False}`
- Report options: show_denominators=False, cite_artifacts=True, caveats=['descriptive_only', 'association_not_causation', 'model_limitations'].
