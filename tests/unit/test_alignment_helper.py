"""Tests for the shared word-alignment helper at
docs/_research-tools/generators/_alignment.py.

Three callers depend on this module: the confidence analyzer (ref↔hyp
correctness), the n-best aggregator (hyp↔hyp voting), and the beam-variance
analyzer (per-position disagreement). A regression here breaks all three.
"""
import sys
from pathlib import Path

import pytest

GENERATORS_DIR = Path(__file__).resolve().parents[2] / "docs" / "_research-tools" / "generators"
sys.path.insert(0, str(GENERATORS_DIR))

from _alignment import align_word_lists, hyp_word_correctness, split_words, wer  # noqa: E402


def test_align_identical():
    pairs = align_word_lists(["a", "b", "c"], ["a", "b", "c"])
    assert pairs == [(0, 0), (1, 1), (2, 2)]


def test_align_substitution():
    # Same length; one sub.
    pairs = align_word_lists(["the", "cat", "sat"], ["the", "bat", "sat"])
    # Each position is paired (substitution counts as a pair, not a gap).
    assert pairs == [(0, 0), (1, 1), (2, 2)]


def test_align_insertion_gap():
    pairs = align_word_lists(["the", "cat"], ["the", "fat", "cat"])
    assert (0, 0) in pairs
    assert (-1, 1) in pairs  # 'fat' is an insertion in b
    assert (1, 2) in pairs


def test_align_deletion_gap():
    pairs = align_word_lists(["the", "fat", "cat"], ["the", "cat"])
    assert (0, 0) in pairs
    assert (1, -1) in pairs  # 'fat' is a deletion (a-only)
    assert (2, 1) in pairs


def test_align_empty():
    assert align_word_lists([], []) == []
    assert align_word_lists(["a"], []) == [(0, -1)]
    assert align_word_lists([], ["a"]) == [(-1, 0)]


def test_align_case_insensitive():
    pairs = align_word_lists(["The", "Cat"], ["the", "cat"])
    assert pairs == [(0, 0), (1, 1)]


def test_hyp_word_correctness_basic():
    assert hyp_word_correctness("the cat sat", ["the", "cat", "sat"]) == [1, 1, 1]
    assert hyp_word_correctness("the cat sat", ["the", "fat", "sat"]) == [1, 0, 1]
    assert hyp_word_correctness("the cat sat", ["cat", "sat", "dog"]) == [1, 1, 0]


def test_hyp_word_correctness_handles_extra():
    # Extra hyp word at end → 0
    assert hyp_word_correctness("the cat", ["the", "cat", "sat"]) == [1, 1, 0]
    # Missing hyp word → only correct count for what's present
    assert hyp_word_correctness("the cat sat", ["the", "cat"]) == [1, 1]


def test_wer_zero_distance():
    assert wer(["the", "cat"], ["the", "cat"]) == pytest.approx(0.0)


def test_wer_substitution():
    assert wer(["the", "cat"], ["the", "bat"]) == pytest.approx(0.5)


def test_wer_deletion_normalized_by_ref_len():
    # 1 deletion out of 3 ref words = 1/3
    assert wer(["the", "cat", "sat"], ["the", "cat"]) == pytest.approx(1.0 / 3.0)


def test_wer_empty_ref_with_hyp_words():
    assert wer([], ["hi"]) == pytest.approx(1.0)


def test_wer_both_empty_is_zero():
    assert wer([], []) == pytest.approx(0.0)


def test_split_words_matches_pipeline_convention():
    # Pipeline-wide convention: text.strip().split()
    assert split_words("  hello   world  ") == ["hello", "world"]
    assert split_words("") == []


def test_align_substitution_count_vs_match_count():
    # Sanity check: the number of paired (non-gap) entries equals the LCS
    # length plus the substitution count, never less than max-LCS.
    a = ["cat", "sat", "on", "mat"]
    b = ["cat", "lay", "on", "mat"]
    pairs = align_word_lists(a, b)
    matched = sum(1 for ai, bi in pairs if ai >= 0 and bi >= 0 and a[ai] == b[bi])
    assert matched == 3  # cat, on, mat
