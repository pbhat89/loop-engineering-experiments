"""Deterministic analysis modules for T1-T8 (A6).

Every module exposes ``HANDLERS = {component_id: fn(ctx, params)}``; the shared
components (``load_tables``, ``join_check``, ``write_report``) live in ``common``.
No module executes model-generated code, touches the network, or writes outside
the run's output directory.
"""
