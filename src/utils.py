"""Shared helpers: repo paths, timestamps, hashing, JSON/JSONL/YAML IO.

Kept dependency-free (PyYAML is imported lazily) so every module can import it
without side effects. Nothing here ever reads environment secrets.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
LOGS_DIR = REPO_ROOT / "logs"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def utc_now() -> str:
    """ISO-8601 UTC timestamp with second precision, e.g. ``2026-09-06T15:04:05+00:00``."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path | str) -> str:
    """Repo-relative POSIX path for logs and dashboards (falls back to the input)."""
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sha256_file(path: Path | str, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_yaml(path: Path | str) -> Any:
    import yaml  # lazy: keeps utils importable without PyYAML

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def read_json(path: Path | str, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _replace_with_retry(src: Path, dst: Path, attempts: int = 8) -> None:
    # On Windows a reader (browser, editor) holding the target open makes
    # os.replace raise PermissionError briefly; retry a few times.
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(0.05 * (i + 1))


def atomic_write_text(path: Path | str, text: str) -> Path:
    """Write via a temp file in the same directory + ``os.replace`` (atomic on POSIX and NTFS)."""
    p = Path(path)
    ensure_dir(p.parent)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    _replace_with_retry(tmp, p)
    return p


def atomic_write_json(path: Path | str, data: Any) -> Path:
    return atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n")


def append_jsonl(path: Path | str, record: dict) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    line = json.dumps(record, ensure_ascii=False, default=str)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def read_jsonl(path: Path | str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    records: list[dict] = []
    with open(p, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p}:{lineno}: invalid JSON line ({exc})") from exc
    return records
