"""Pinned-revision download of the HLT-008 sample dataset (A2, data steward).

Downloads each CSV of the public Hugging Face dataset ``xpertsystems/hlt008-sample``
*individually* with :func:`huggingface_hub.hf_hub_download` at a pinned commit,
verifies byte sizes against the values recorded when the revision was pinned,
computes SHA-256 per file and writes ``data/raw/download_record.json``.

This module is the **only** place in the project that may touch the network, and
it does so once. Everything downstream (profiling, goldens, task execution) reads
the local files and the manifest.

CLI::

    uv run python -m src.download_data            # idempotent: skips complete files
    uv run python -m src.download_data --force    # re-download everything

Public helpers used by other modules::

    from src.download_data import load_manifest, load_download_record, RAW_DIR
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from src.utils import (
    DATA_DIR,
    atomic_write_json,
    ensure_dir,
    rel,
    sha256_file,
    utc_now,
)

# --------------------------------------------------------------------------- #
# Pinned source                                                               #
# --------------------------------------------------------------------------- #
REPO_ID = "xpertsystems/hlt008-sample"
REPO_TYPE = "dataset"
REVISION = "7309ddb30e67468748b7aa9182d8517fe28c2f9c"
LICENSE = "cc-by-nc-4.0"
PRETTY_NAME = "HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview)"
PUBLISHER = "XpertSystems.ai"
DATASET_URL = f"https://huggingface.co/datasets/{REPO_ID}"

# Byte sizes verified by the lead for the pinned revision. A pinned commit is
# immutable, so any deviation means we did not receive the intended snapshot.
EXPECTED_BYTES: dict[str, int] = {
    "adherence.csv": 520053,
    "medical_claims.csv": 3525830,
    "members.csv": 79935,
    "pharmacy_claims.csv": 4335821,
    "providers.csv": 10610,
}
CARD_FILENAME = "README.md"          # name inside the Hub repository
CARD_LOCAL_NAME = "DATASET_CARD.md"  # name we keep it under (attribution)
EXPECTED_CARD_BYTES = 19082

# Logical table name -> CSV file name (order is the profiling order).
TABLE_FILES: dict[str, str] = {
    "members": "members.csv",
    "providers": "providers.csv",
    "medical_claims": "medical_claims.csv",
    "pharmacy_claims": "pharmacy_claims.csv",
    "adherence": "adherence.csv",
}

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DOWNLOAD_RECORD_PATH = RAW_DIR / "download_record.json"
MANIFEST_PATH = PROCESSED_DIR / "manifest.json"
CARD_PATH = RAW_DIR / CARD_LOCAL_NAME


class DataIntegrityError(RuntimeError):
    """A downloaded file is missing or does not match the pinned revision."""


# --------------------------------------------------------------------------- #
# Loading helpers (no network)                                                #
# --------------------------------------------------------------------------- #
def load_download_record(path: Path | str = DOWNLOAD_RECORD_PATH) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{rel(p)} not found - run `uv run python -m src.download_data` first"
        )
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest(path: Path | str = MANIFEST_PATH) -> dict[str, Any]:
    """Return the data contract (``data/processed/manifest.json``).

    The manifest is produced by ``src.profile_data`` after the download; it is
    the single source of truth for table paths, hashes, columns, keys and
    relationships. Raises ``FileNotFoundError`` with the commands to run.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{rel(p)} not found - run `uv run python -m src.download_data` and then "
            "`uv run python -m src.profile_data`"
        )
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def raw_files_present(raw_dir: Path | str = RAW_DIR) -> bool:
    """True when all five CSV files exist (used by tests to skip cleanly)."""
    d = Path(raw_dir)
    return all((d / f).is_file() for f in TABLE_FILES.values())


def verify_local_files(raw_dir: Path | str = RAW_DIR) -> list[str]:
    """Return a list of problems (empty when every file exists with the pinned size)."""
    d = Path(raw_dir)
    problems: list[str] = []
    for fname, expected in EXPECTED_BYTES.items():
        p = d / fname
        if not p.is_file():
            problems.append(f"missing {rel(p)}")
        elif p.stat().st_size != expected:
            problems.append(f"{rel(p)} has {p.stat().st_size} bytes, expected {expected}")
    return problems


# --------------------------------------------------------------------------- #
# Download                                                                    #
# --------------------------------------------------------------------------- #
def _fetch_repo_metadata() -> dict[str, Any]:
    """Inspect dataset metadata (licence, card data, file list) at the pinned revision.

    Retrieval rule 1 of the brief: inspect metadata and licence first. Failure
    here is recorded but does not block the per-file download.
    """
    from huggingface_hub import HfApi

    api = HfApi()
    info = api.dataset_info(REPO_ID, revision=REVISION, files_metadata=True)
    card = getattr(info, "card_data", None)
    card_dict = card.to_dict() if card is not None and hasattr(card, "to_dict") else {}
    siblings = {}
    for s in getattr(info, "siblings", None) or []:
        lfs = getattr(s, "lfs", None)
        siblings[s.rfilename] = {
            "size": getattr(s, "size", None),
            "lfs_sha256": (lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None))
            if lfs
            else None,
        }
    return {
        "sha": getattr(info, "sha", None),
        "gated": getattr(info, "gated", None),
        "private": getattr(info, "private", None),
        "license": card_dict.get("license"),
        "pretty_name": card_dict.get("pretty_name"),
        "tags": card_dict.get("tags"),
        "siblings": siblings,
    }


def _download_one(filename: str, raw_dir: Path, force: bool) -> Path:
    from huggingface_hub import hf_hub_download

    local = hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        repo_type=REPO_TYPE,
        revision=REVISION,
        local_dir=str(raw_dir),
        force_download=force,
    )
    return Path(local)


def download_all(raw_dir: Path | str = RAW_DIR, force: bool = False, quiet: bool = False) -> dict[str, Any]:
    """Download the five CSV files and the dataset card; verify; write the download record.

    Idempotent: a file already present with the pinned byte size is skipped
    (its SHA-256 is still recomputed and recorded). ``force`` re-downloads.
    Raises :class:`DataIntegrityError` if any file is missing or the wrong size.
    """
    raw = ensure_dir(raw_dir)
    log = (lambda *a: None) if quiet else (lambda *a: print(*a, file=sys.stderr))

    metadata: dict[str, Any]
    try:
        metadata = _fetch_repo_metadata()
        log(f"[download_data] metadata: licence={metadata.get('license')} sha={metadata.get('sha')} "
            f"gated={metadata.get('gated')} private={metadata.get('private')}")
    except Exception as exc:  # network / API shape problems must not hide the download outcome
        metadata = {"error": f"{type(exc).__name__}: {exc}"}
        log(f"[download_data] metadata lookup failed: {metadata['error']}")

    if metadata.get("sha") and metadata["sha"] != REVISION:
        raise DataIntegrityError(
            f"Hub resolved revision {metadata['sha']} but {REVISION} was requested"
        )
    if metadata.get("license") and metadata["license"] != LICENSE:
        raise DataIntegrityError(
            f"dataset card licence is {metadata['license']!r}, expected {LICENSE!r} - stop and ask the user"
        )

    files: dict[str, Any] = {}
    problems: list[str] = []
    for fname, expected in EXPECTED_BYTES.items():
        target = raw / fname
        action = "skipped"
        if force or not target.is_file() or target.stat().st_size != expected:
            log(f"[download_data] downloading {fname} ...")
            got = _download_one(fname, raw, force)
            if got.resolve() != target.resolve():
                shutil.copyfile(got, target)
            action = "downloaded"
        else:
            log(f"[download_data] {fname} present with {expected} bytes - skipped")
        if not target.is_file():
            problems.append(f"missing {rel(target)} after download")
            continue
        size = target.stat().st_size
        hub_size = (metadata.get("siblings") or {}).get(fname, {}).get("size")
        entry = {
            "path": rel(target),
            "bytes": size,
            "expected_bytes": expected,
            "hub_bytes": hub_size,
            "sha256": sha256_file(target),
            "action": action,
        }
        lfs_sha = (metadata.get("siblings") or {}).get(fname, {}).get("lfs_sha256")
        if lfs_sha:
            entry["hub_lfs_sha256"] = lfs_sha
            entry["sha256_matches_hub"] = lfs_sha == entry["sha256"]
        files[fname] = entry
        if size != expected:
            problems.append(f"{rel(target)} has {size} bytes, expected {expected}")
        if hub_size is not None and hub_size != size:
            problems.append(f"{rel(target)} has {size} bytes but the Hub reports {hub_size}")
        if entry.get("sha256_matches_hub") is False:
            problems.append(f"{rel(target)} SHA-256 differs from the Hub LFS digest")

    # Dataset card (attribution). Kept as DATASET_CARD.md so it is not mistaken for data/README.md.
    card_target = raw / CARD_LOCAL_NAME
    card_action = "skipped"
    if force or not card_target.is_file() or card_target.stat().st_size != EXPECTED_CARD_BYTES:
        log(f"[download_data] downloading {CARD_FILENAME} -> {CARD_LOCAL_NAME} ...")
        got = _download_one(CARD_FILENAME, raw, force)
        shutil.copyfile(got, card_target)
        if got.resolve() != card_target.resolve():
            got.unlink(missing_ok=True)
        card_action = "downloaded"
    card_entry = None
    if card_target.is_file():
        card_entry = {
            "path": rel(card_target),
            "bytes": card_target.stat().st_size,
            "expected_bytes": EXPECTED_CARD_BYTES,
            "sha256": sha256_file(card_target),
            "action": card_action,
        }
        if card_entry["bytes"] != EXPECTED_CARD_BYTES:
            problems.append(f"{rel(card_target)} has {card_entry['bytes']} bytes, expected {EXPECTED_CARD_BYTES}")
    else:
        problems.append(f"missing {rel(card_target)}")

    # hf_hub_download leaves a .cache/huggingface metadata tree inside local_dir; we track
    # completeness ourselves (size + SHA-256), so remove it to keep data/raw clean.
    shutil.rmtree(raw / ".cache", ignore_errors=True)

    record = {
        "source": {
            "repo": REPO_ID,
            "repo_type": REPO_TYPE,
            "revision": REVISION,
            "url": DATASET_URL,
            "license": LICENSE,
            "pretty_name": PRETTY_NAME,
            "publisher": PUBLISHER,
            "retrieved_at": utc_now(),
            "hub_metadata": {k: v for k, v in metadata.items() if k != "siblings"},
        },
        "files": files,
        "dataset_card": card_entry,
        "problems": problems,
        "ok": not problems,
    }
    atomic_write_json(DOWNLOAD_RECORD_PATH if Path(raw_dir) == RAW_DIR else raw / "download_record.json", record)

    if problems:
        raise DataIntegrityError("download incomplete or inconsistent:\n  - " + "\n  - ".join(problems))
    return record


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def _format_table(record: dict[str, Any]) -> str:
    lines = [f"{'file':<22}{'bytes':>10}  {'expected':>10}  {'action':<11}sha256"]
    for fname, e in record["files"].items():
        lines.append(f"{fname:<22}{e['bytes']:>10}  {e['expected_bytes']:>10}  {e['action']:<11}{e['sha256']}")
    c = record.get("dataset_card")
    if c:
        lines.append(f"{CARD_LOCAL_NAME:<22}{c['bytes']:>10}  {c['expected_bytes']:>10}  {c['action']:<11}{c['sha256']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="download_data",
        description=f"Download {REPO_ID} @ {REVISION[:8]} file by file into data/raw (the project's only network access).",
    )
    parser.add_argument("--force", action="store_true", help="re-download files even if present with the pinned size")
    parser.add_argument("--raw-dir", default=str(RAW_DIR), help="target directory (default data/raw)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        record = download_all(Path(args.raw_dir), force=args.force, quiet=args.quiet)
    except DataIntegrityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(_format_table(record))
    print(f"record: {rel(DOWNLOAD_RECORD_PATH)}  revision: {REVISION}  licence: {LICENSE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
