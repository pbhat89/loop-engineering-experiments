"""Experiment 7: the notebook, the written rule book and the precedent file."""
from __future__ import annotations

import itertools

from src.underwriting.cases import build_dataset
from src.underwriting.memory import EMPTY_RULEBOOK, Notebook, RuleBook
from src.underwriting.precedent import PrecedentFile, distance, feature_vector, summarise


# --------------------------------------------------------------------------- notebook


def test_the_notebook_recalls_newest_first_and_never_the_current_case(tmp_path):
    notebook = Notebook(tmp_path)
    for i, case_id in enumerate(("UW-T01", "UW-T02", "UW-T03"), start=1):
        notebook.append(i, case_id, f"markup {i}", "2026-09-11T00:00:00+00:00")
    block = notebook.memory_block(exclude_case_id="UW-T03")
    assert block["size"] == 2
    assert [e["markup"] for e in block["entries"]] == ["markup 2", "markup 1"]
    assert notebook.memory_block()["size"] == 3


# --------------------------------------------------------------------------- rule book


def test_the_rule_book_starts_empty_and_keeps_a_version_history(tmp_path):
    book = RuleBook(tmp_path)
    assert book.read() == EMPTY_RULEBOOK
    assert book.version() == 0
    assert book.write("# Book\n- one thing") == 1
    assert book.write("# Book\n- one thing\n- another") == 2
    assert book.version() == 2
    assert "another" in book.read()
    assert sorted(p.name for p in book.history.glob("v*.md")) == ["v01.md", "v02.md"]


def test_an_empty_rewrite_does_not_wipe_the_book(tmp_path):
    book = RuleBook(tmp_path)
    book.write("# Book\n- one thing")
    book.write("   ")
    assert book.read().strip() == EMPTY_RULEBOOK.strip()


# --------------------------------------------------------------------------- precedent


def test_precedent_distance_is_zero_on_self_and_symmetric():
    cases, _ = build_dataset()
    vectors = [feature_vector(c) for c in cases]
    for v in vectors:
        assert distance(v, v) == 0.0
    for a, b in itertools.combinations(vectors[:12], 2):
        assert distance(a, b) == distance(b, a)
        assert distance(a, b) >= 0.0


def test_precedent_returns_the_three_nearest_with_their_answers(tmp_path):
    cases, goldens = build_dataset()
    filed = PrecedentFile(tmp_path)
    for case, golden in list(zip(cases, goldens))[:10]:
        filed.append(case, golden)
    block = filed.memory_block(cases[12], k=3)
    assert block["size"] == 3
    assert block["nearest_distance"] == block["entries"][0]["distance"]
    assert block["entries"][0]["distance"] <= block["entries"][1]["distance"] <= block["entries"][2]["distance"]
    for entry in block["entries"]:
        assert set(entry["correct_answer"]) == {"decision", "rating_class", "modifiers", "drivers"}
        assert "tier" not in entry and "fired_rule_ids" not in entry


def test_precedent_never_returns_the_case_being_decided(tmp_path):
    cases, goldens = build_dataset()
    filed = PrecedentFile(tmp_path)
    for case, golden in list(zip(cases, goldens))[:10]:
        filed.append(case, golden)
    block = filed.memory_block(cases[3], k=3)
    assert all(cases[3]["case_id"] not in e["summary"] for e in block["entries"])


def test_precedent_summary_is_ascii_and_carries_no_answer():
    cases, _ = build_dataset()
    for case in cases[:8]:
        text = summarise(case)
        assert text.isascii()
        assert "Table" not in text and "accept" not in text
