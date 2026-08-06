"""Tests for the multi-layered confidence trust stack + numeric/currency cap.

Covers:
  1. `is_numeric()` correctly fires on currency words, bare currency
     symbols, plural magnitude words, and 4-digit years.
  2. `_apply_trust_stack()` strips per-word coloring when
     `sentence_confidence` falls below the segment-level floor.
  3. Green band fires only when BOTH conf and agreement gates pass.
  4. Per-video grouping in `_group_by_video()` preserves first-seen order
     and sorts segments within a group.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the VSP-LLM scripts directory importable as a flat module.
SCRIPTS_DIR = Path("/home/ubuntu/VSP-LLM/scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

# A same-named but older compute_word_confidence lives in
# docs/_research-tools/generators/ and is imported by
# test_compute_word_confidence.py; evict any cached copy so this module
# (and generate_client_demo_report's late `from compute_word_confidence
# import ...`) binds to the VSP-LLM/scripts version regardless of which
# test file pytest collected first.
sys.modules.pop("compute_word_confidence", None)
sys.modules.pop("generate_client_demo_report", None)

import compute_word_confidence as cwc  # noqa: E402
import generate_client_demo_report as gen  # noqa: E402


@pytest.fixture(autouse=True)
def _pin_scripts_module(monkeypatch):
    """gen does `from compute_word_confidence import ...` at call time, so
    whatever sys.modules holds when a test RUNS wins — pin it to the
    VSP-LLM/scripts copy for every test in this file, restored after each."""
    monkeypatch.setitem(sys.modules, "compute_word_confidence", cwc)


@pytest.mark.parametrize("word, expected", [
    # Currency words: new in May 2026
    ("dollar", True), ("dollars", True), ("euro", True), ("euros", True),
    ("pound", True), ("pounds", True), ("yen", True),
    ("shekel", True), ("shekels", True), ("cent", True), ("cents", True),
    ("penny", True), ("pence", True),
    # Bare currency symbols
    ("$", True), ("€", True), ("£", True), ("¥", True), ("₪", True),
    # Years 1900–2099 — covered by the "has digit" branch
    ("1900", True), ("2026", True), ("2099", True),
    # Magnitude words + plurals
    ("thousand", True), ("thousands", True),
    ("million", True), ("millions", True),
    ("billion", True), ("billions", True),
    ("trillion", True), ("trillions", True),
    ("hundred", True), ("hundreds", True),
    # Negative controls — should NOT trigger the cap
    ("hello", False), ("world", False), ("and", False), ("Obama", False),
    ("the", False), ("president", False),
])
def test_is_numeric(word, expected):
    assert cwc.is_numeric(word) is expected, (
        f"is_numeric({word!r}) returned {cwc.is_numeric(word)!r}, expected {expected!r}"
    )


def test_strip_gate_below_floor_overrides_per_word_class():
    """Words in a low-confidence segment should land in 'conf-stripped'."""
    words = [
        {"word": "hello", "prob": 0.50, "conf_class": "conf-high"},
        {"word": "world", "prob": 0.30, "conf_class": "conf-low"},
    ]
    sent_conf, stripped, new_words = gen._apply_trust_stack(words, agreement=None)
    # Mean of [0.5, 0.3] = 0.4 < STRIP_TIER_FLOOR (0.65) → stripped.
    assert stripped is True
    assert sent_conf == pytest.approx(0.40)
    assert all(w["conf_class"] == "conf-stripped" for w in new_words)


def test_green_band_requires_both_gates():
    """conf >= 0.95 AND agreement >= 0.80 → green; either short → not green."""
    words = [
        {"word": "alpha", "prob": 0.97},  # high conf + high agree → green
        {"word": "beta",  "prob": 0.97},  # high conf + low  agree → med/low
        {"word": "gamma", "prob": 0.70},  # mid  conf + high agree → med
    ]
    agreement = [0.90, 0.40, 0.85]
    sent_conf, stripped, new_words = gen._apply_trust_stack(words, agreement)
    assert stripped is False  # mean(0.97, 0.97, 0.70) > 0.65
    assert new_words[0]["conf_class"] == "conf-high"
    # Word 'beta' fails the agreement gate → NOT green.
    assert new_words[1]["conf_class"] in ("conf-med", "conf-low")
    # Word 'gamma' passes mid-tier gates → conf-med.
    assert new_words[2]["conf_class"] == "conf-med"


def test_numeric_cap_holds_under_joint_rule():
    """A digit-bearing token at green-tier conf+agree must still cap at yellow."""
    words = [{"word": "2026", "prob": 0.98}]
    _, _, new = gen._apply_trust_stack(words, agreement=[0.95])
    assert new[0]["conf_class"] == "conf-med"


def test_group_by_video_preserves_order_and_sorts_within_group():
    """4 records across 2 videos → 2 ordered groups, segments sorted by index."""
    recs = [
        {"utt_id": "Obama_01_000300_000599", "words": []},
        {"utt_id": "BinLaden_00_000000_000299", "words": []},
        {"utt_id": "Obama_00_000000_000299", "words": []},
        {"utt_id": "BinLaden_01_000200_000499", "words": []},
    ]
    grouped = gen._group_by_video(recs)
    assert [base for base, _ in grouped] == ["Obama", "BinLaden"]
    obama_idxs = [gen.parse_segment_id(r["utt_id"])[1] for r in grouped[0][1]]
    binladen_idxs = [gen.parse_segment_id(r["utt_id"])[1] for r in grouped[1][1]]
    assert obama_idxs == [0, 1]
    assert binladen_idxs == [0, 1]
