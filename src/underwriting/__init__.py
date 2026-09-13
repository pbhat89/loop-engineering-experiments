"""Experiment 7 - the Underwriting Apprentice.

One job repeated thirty-eight times: rate a life-insurance application. Five loop
designs (arms) differ only in what the agent is handed before it decides and what is
kept afterwards. The approved design is ``docs/underwriting-apprentice-design.md``; the
rationale is decision D-01 in ``docs/decision-log.md``.

Nothing in this package calls a model. Operator answers arrive through the same
manual-mode request/response file protocol the claims experiment uses
(``src/underwriting/provider.py``, ``docs/OPERATOR_PROTOCOL.md``), or from the deterministic
stub operators in :mod:`src.underwriting.stub`.
"""
