"""Experiment 7 - the Underwriting Apprentice.

One job repeated thirty-eight times: rate a life-insurance application. Five loop
designs (arms) differ only in what the agent is handed before it decides and what is
kept afterwards. The spec is ``docs/underwriting-build-brief.md``; the approved design
is ``docs/underwriting-apprentice-design.md``; the rationale is decision D-27.

Nothing in this package calls a model. Operator answers arrive through the same
manual-mode request/response file protocol the claims experiment uses
(``src/llm_provider.py``, ``docs/OPERATOR_PROTOCOL.md``), or from the deterministic
stub operators in :mod:`src.underwriting.stub`.
"""
