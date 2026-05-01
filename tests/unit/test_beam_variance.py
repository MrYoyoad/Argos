"""Tests for analyze_beam_variance.py per-segment metrics.

Hand-crafted hypothesis sets with known disagreement structure.
"""
import sys
from pathlib import Path

import pytest

GENERATORS_DIR = Path(__file__).resolve().parents[2] / "docs" / "_research-tools" / "generators"
sys.path.insert(0, str(GENERATORS_DIR))

from analyze_beam_variance import (  # noqa: E402
    pairwise_mean_wer,
    word_agreement_rate,
    mean_position_entropy,
    per_position_disagreement,
)


# ──────────────────────────────────────────────────────────────────────────────
# pairwise_mean_wer
# ──────────────────────────────────────────────────────────────────────────────

def test_pairwise_wer_zero_when_all_identical():
    texts = ["the cat sat", "the cat sat", "the cat sat"]
    assert pairwise_mean_wer(texts) == pytest.approx(0.0)


def test_pairwise_wer_known_distance():
    # Two pairs (3,3): "the cat sat" vs "the bat sat" → 1/3 each direction
    texts = ["the cat sat", "the bat sat"]
    # 1 sub / 3 ref words = 0.333... averaged over 1 pair
    assert pairwise_mean_wer(texts) == pytest.approx(1 / 3)


def test_pairwise_wer_singleton_returns_zero():
    assert pairwise_mean_wer(["lonely"]) == pytest.approx(0.0)


def test_pairwise_wer_three_hyps_known():
    # All three differ pairwise on exactly one word out of 3 → each pair WER = 1/3
    # Mean over (3 choose 2) = 3 pairs = 1/3
    texts = ["the cat sat", "the bat sat", "the rat sat"]
    assert pairwise_mean_wer(texts) == pytest.approx(1 / 3)


# ──────────────────────────────────────────────────────────────────────────────
# word_agreement_rate
# ──────────────────────────────────────────────────────────────────────────────

def test_word_agreement_one_when_identical():
    texts = ["the cat sat", "the cat sat", "the cat sat"]
    assert word_agreement_rate(texts) == pytest.approx(1.0)


def test_word_agreement_partial():
    # Anchor "the cat sat". Other beams: "the bat sat", "the cat ran".
    # Position 0 ("the"): 2/2 agree → counted
    # Position 1 ("cat"): 1/2 agree → 50%, threshold ceil((n-1)*0.5) = ceil(1) = 1 → counted
    # Position 2 ("sat"): 1/2 agree → counted (1 ≥ 1)
    texts = ["the cat sat", "the bat sat", "the cat ran"]
    rate = word_agreement_rate(texts)
    assert rate == pytest.approx(1.0)


def test_word_agreement_low_when_all_disagree():
    # Anchor "the cat sat"; other beams completely different but same length.
    texts = ["the cat sat", "a dog ran", "the bus left"]
    rate = word_agreement_rate(texts)
    # Threshold ceil((3-1)*0.5)=1. At position 0, "the" appears in beam 2 (1/2 ≥ 1) → counted.
    # At positions 1,2 nothing matches → not counted.
    assert rate == pytest.approx(1 / 3)


# ──────────────────────────────────────────────────────────────────────────────
# mean_position_entropy
# ──────────────────────────────────────────────────────────────────────────────

def test_position_entropy_zero_when_uniform_agreement():
    texts = ["a b c", "a b c", "a b c"]
    # All beams agree everywhere → distribution is concentrated → entropy 0.
    assert mean_position_entropy(texts) == pytest.approx(0.0)


def test_position_entropy_positive_when_disagreement():
    texts = ["a b c", "a x c", "a y c"]
    # Position 1 has three different words ("b","x","y") → high entropy.
    # Positions 0 and 2 have unanimous agreement → 0.
    e = mean_position_entropy(texts)
    assert e > 0.0


# ──────────────────────────────────────────────────────────────────────────────
# per_position_disagreement
# ──────────────────────────────────────────────────────────────────────────────

def test_per_position_disagreement_shape():
    anchor = ["the", "cat", "sat"]
    hypotheses = [
        anchor,
        ["the", "bat", "sat"],
        ["the", "rat", "sat"],
    ]
    rates = per_position_disagreement(anchor, hypotheses)
    assert len(rates) == 3
    # Position 0 ("the") agrees in both other beams → 0.0
    assert rates[0] == pytest.approx(0.0)
    # Position 1 ("cat") disagrees in both other beams → 1.0
    assert rates[1] == pytest.approx(1.0)
    # Position 2 ("sat") agrees → 0.0
    assert rates[2] == pytest.approx(0.0)


def test_per_position_disagreement_empty_when_singleton():
    rates = per_position_disagreement(["a", "b"], [["a", "b"]])
    assert rates == [0.0, 0.0]
