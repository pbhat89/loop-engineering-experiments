# T8 — Executive brief

## Summary

Task T8 (Executive brief) for run `run_006` / condition `self_refine`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.

## Results

### collect_findings

- Sources requested: T1, T2, T3; missing: none [source: artifacts/tasks/run_006/self_refine/T8/attempt_2/findings.json]
- Findings with values extracted: 9 [source: artifacts/tasks/run_006/self_refine/T8/attempt_2/findings.json]

### brief_sections

- Sections: key_findings, limitations, synthetic_caveats, next_steps; causal_language=avoid; cite_artifacts=True [source: artifacts/tasks/run_006/self_refine/T8/attempt_2/executive_brief.md]
- Word count: 241 [source: metrics.json#brief.word_count]
- Numeric statements cited: 9 / 9 = 1.000000 [source: metrics.json#brief]

## Artifacts

- `artifacts/tasks/run_006/self_refine/T8/attempt_2/findings.json`
- `artifacts/tasks/run_006/self_refine/T8/attempt_2/executive_brief.md`
- `artifacts/tasks/run_006/self_refine/T8/attempt_2/metrics.json`
- `artifacts/tasks/run_006/self_refine/T8/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.

## Method

- Seed: 42; plan sha256: `a6b729e6a66f5692957907bd018534773cc3a7588761427dc4f5fd890f7f6448`.
- Components (canonical order): collect_findings, brief_sections, write_report.
- `collect_findings` params: `{'sources': ['T1', 'T2', 'T3']}`
- `brief_sections` params: `{'sections': ['key_findings', 'limitations', 'synthetic_caveats', 'next_steps'], 'causal_language': 'avoid', 'cite_artifacts': True}`
- `write_report` params: `{'caveats': ['synthetic_data', 'model_limitations', 'association_not_causation'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'model_limitations', 'association_not_causation'].
