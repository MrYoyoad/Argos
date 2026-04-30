"""Tests for compute_word_confidence.py (B2).

Covers:
  - B2.t1: deterministic synthetic 5-token / 3-word input
  - B2.t2: edge cases — empty / 1-word / punctuation-only / contraction
  - B2.t3: idempotency — running twice on same input gives byte-identical JSON
"""

import json
import sys
from pathlib import Path

import pytest

GENERATORS_DIR = Path(__file__).resolve().parents[2] / "docs" / "_research-tools" / "generators"
sys.path.insert(0, str(GENERATORS_DIR))

from compute_word_confidence import (  # noqa: E402
    aggregate_segment_records,
    aggregate_subtokens_to_words,
    classify,
    overall_confidence_badge,
)

# LLaMA / SentencePiece word-start marker
W = "▁"


# ---------- B2.t1: synthetic deterministic ----------


def test_synthetic_three_words_min_aggregation():
    """5 sub-tokens → 3 words. The middle word's confidence must be the
    minimum across its two sub-tokens (conservative aggregation)."""
    tokens = [
        {"token": f"{W}hello", "prob": 0.95},
        {"token": f"{W}wo", "prob": 0.40},
        {"token": "rld", "prob": 0.20},  # joins "wo" → "world"
        {"token": f"{W}friend", "prob": 0.85},
        {"token": "s", "prob": 0.55},  # joins "friend" → "friends"
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 3
    assert words[0] == {
        "word": "hello", "prob": 0.95, "conf_class": "conf-high", "n_subtokens": 1,
    }
    assert words[1]["word"] == "world"
    assert words[1]["prob"] == 0.20
    assert words[1]["conf_class"] == "conf-low"  # 0.20 < 0.40
    assert words[1]["n_subtokens"] == 2
    assert words[2]["word"] == "friends"
    # min(0.85, 0.55) == 0.55
    assert words[2]["prob"] == pytest.approx(0.55)
    assert words[2]["conf_class"] == "conf-med"  # 0.40 <= 0.55 < 0.85
    assert words[2]["n_subtokens"] == 2


def test_classify_thresholds():
    # Thresholds tightened on 2026-04-30 to high>=0.85, med>=0.40, see
    # compute_word_confidence.py for rationale.
    assert classify(0.99) == "conf-high"
    assert classify(0.85) == "conf-high"  # boundary inclusive
    assert classify(0.84) == "conf-med"
    assert classify(0.40) == "conf-med"   # boundary inclusive
    assert classify(0.39) == "conf-low"
    assert classify(0.0) == "conf-low"
    assert classify(None) == "conf-unknown"


# ---------- B2.t2: edge cases ----------


def test_empty_token_list():
    assert aggregate_subtokens_to_words([]) == []


def test_single_word():
    tokens = [{"token": f"{W}hello", "prob": 0.9}]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 1
    assert words[0]["word"] == "hello"
    assert words[0]["prob"] == 0.9


def test_special_tokens_skipped():
    """BOS / EOS / PAD-style angle-bracketed tokens must be dropped."""
    tokens = [
        {"token": "<s>", "prob": 1.0},
        {"token": f"{W}hello", "prob": 0.9},
        {"token": "</s>", "prob": 1.0},
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 1
    assert words[0]["word"] == "hello"


def test_contraction_dont():
    """LLaMA tokenizes 'don't' as `▁don` + `'t`. The `'t` lacks the word-start
    marker, so it must continue the previous word."""
    tokens = [
        {"token": f"{W}don", "prob": 0.8},
        {"token": "'t", "prob": 0.6},
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 1
    assert words[0]["word"] == "don't"
    assert words[0]["prob"] == pytest.approx(0.6)
    assert words[0]["n_subtokens"] == 2


def test_punctuation_attaches_to_previous_word():
    """A bare period without a word-start marker should attach to the previous word."""
    tokens = [
        {"token": f"{W}hello", "prob": 0.9},
        {"token": ".", "prob": 0.99},
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 1
    assert words[0]["word"] == "hello."
    # min(0.9, 0.99) == 0.9
    assert words[0]["prob"] == pytest.approx(0.9)


def test_none_prob_propagates_to_word():
    """If any sub-token has prob=None (compute_transition_scores failed),
    the resulting word prob is None and class is conf-unknown."""
    tokens = [
        {"token": f"{W}hello", "prob": None},
        {"token": f"{W}world", "prob": 0.9},
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert words[0]["prob"] is None
    assert words[0]["conf_class"] == "conf-unknown"
    assert words[1]["prob"] == 0.9


def test_no_word_start_marker_first_token():
    """Some decode configs don't emit a leading marker on the very first token.
    The first non-special token always starts the first word regardless."""
    tokens = [
        {"token": "hello", "prob": 0.9},
        {"token": f"{W}world", "prob": 0.5},
    ]
    words = aggregate_subtokens_to_words(tokens)
    assert len(words) == 2
    assert words[0]["word"] == "hello"
    assert words[1]["word"] == "world"


# ---------- B2.t3: idempotency ----------


def test_idempotent_on_same_input(tmp_path):
    """Two consecutive runs against the same confidence sidecar must yield
    byte-identical JSON output."""
    sidecar = {
        "utt_a": {
            "sequence_score": -1.23,
            "tokens": [
                {"token": f"{W}hello", "prob": 0.95},
                {"token": f"{W}world", "prob": 0.5},
            ],
        },
        "utt_b": {
            "sequence_score": -2.11,
            "tokens": [
                {"token": f"{W}don", "prob": 0.6},
                {"token": "'t", "prob": 0.4},
                {"token": f"{W}know", "prob": 0.2},
            ],
        },
    }
    a = aggregate_segment_records(sidecar)
    b = aggregate_segment_records(sidecar)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---------- aggregate_segment_records summary ----------


def test_aggregate_segment_records_summary():
    # Probs chosen to land one in each band under 0.85/0.40 thresholds:
    #   0.90 → high, 0.50 → med, 0.10 → low.
    sidecar = {
        "utt_a": {
            "sequence_score": -1.0,
            "tokens": [
                {"token": f"{W}good", "prob": 0.9},
                {"token": f"{W}meh", "prob": 0.5},
                {"token": f"{W}bad", "prob": 0.1},
            ],
        }
    }
    out = aggregate_segment_records(sidecar)
    assert out["utt_a"]["summary"]["n_words"] == 3
    assert out["utt_a"]["summary"]["n_high"] == 1
    assert out["utt_a"]["summary"]["n_med"] == 1
    assert out["utt_a"]["summary"]["n_low"] == 1
    assert out["utt_a"]["summary"]["max_word_prob"] == 0.9
    assert out["utt_a"]["summary"]["min_word_prob"] == 0.1
    assert out["utt_a"]["summary"]["mean_word_prob"] == pytest.approx(0.5)


def test_overall_badge_fraction_high():
    # Badge = fraction of all words at conf-high across all segments.
    sidecar = {
        "a": {"sequence_score": None, "tokens": [
            {"token": f"{W}x", "prob": 0.95},  # high
            {"token": f"{W}y", "prob": 0.50},  # med
        ]},
        "b": {"sequence_score": None, "tokens": [
            {"token": f"{W}z", "prob": 0.20},  # low
            {"token": f"{W}w", "prob": 0.90},  # high
        ]},
    }
    per_segment = aggregate_segment_records(sidecar)
    badge = overall_confidence_badge(per_segment)
    # 2 high out of 4 total = 0.50
    assert badge == pytest.approx(0.5)


def test_overall_badge_returns_none_when_all_unknown():
    sidecar = {
        "a": {"sequence_score": None, "tokens": [{"token": f"{W}x", "prob": None}]},
    }
    per_segment = aggregate_segment_records(sidecar)
    assert overall_confidence_badge(per_segment) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
