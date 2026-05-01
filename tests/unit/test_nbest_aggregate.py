"""Tests for lib/nbest_aggregate.py.

Covers each aggregation method on hand-crafted hypotheses, edge cases
(empty / single-beam / all-identical), N=1 equivalence to top-1, determinism,
and cross-segment overlap fusion.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[2] / "lib"
GENERATORS_DIR = Path(__file__).resolve().parents[2] / "docs" / "_research-tools" / "generators"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(GENERATORS_DIR))

import nbest_aggregate as A  # noqa: E402

W = "▁"  # SentencePiece word-start


def _tok(text, prob=0.9):
    return [{"token": W + w, "prob": prob, "entropy": None, "top3": None} for w in text.split()]


def _hyps(*specs):
    """specs is a list of (rank, text, score, prob_or_token_list)."""
    out = []
    for rank, text, score, p in specs:
        toks = _tok(text, p) if isinstance(p, (int, float)) else p
        out.append({"rank": rank, "text": text, "sequence_score": score, "tokens": toks})
    return out


# ──────────────────────────────────────────────────────────────────────────────
# words_with_conf — sub-token aggregation
# ──────────────────────────────────────────────────────────────────────────────

def test_words_with_conf_min_aggregation():
    # "wo" + "rld" join into "world" with min-conf 0.20
    tokens = [
        {"token": W + "hello", "prob": 0.95},
        {"token": W + "wo",    "prob": 0.40},
        {"token": "rld",       "prob": 0.20},
    ]
    out = A.words_with_conf(tokens)
    assert out == [("hello", 0.95), ("world", 0.20)]


def test_words_with_conf_handles_none_probs():
    out = A.words_with_conf([{"token": W + "hi", "prob": None}])
    assert out == [("hi", None)]


def test_words_with_conf_filters_special_tokens():
    """LLaMA / SentencePiece special tokens (<s>, </s>, <unk>, <pad>) must be
    excluded from word aggregation. The decode path strips them via
    `tokenizer.batch_decode(skip_special_tokens=True)` for the canonical
    `text` field, but the per-token records preserve them. If the aggregator
    forwards them as words, the voted hypothesis becomes literally
    `"<s> the cat sat </s> <unk> <unk>"`, which inflates WER catastrophically.
    Regression caught on the 107-segment tuning set 2026-05-01."""
    tokens = [
        {"token": "<s>",       "prob": 1.0},
        {"token": W + "hello", "prob": 0.95},
        {"token": W + "world", "prob": 0.85},
        {"token": "</s>",      "prob": 0.99},
        {"token": "<unk>",     "prob": 0.0},
        {"token": "<unk>",     "prob": 0.0},
    ]
    out = A.words_with_conf(tokens)
    assert out == [("hello", 0.95), ("world", 0.85)]


def test_aggregate_one_strips_special_tokens_in_voted_output():
    """End-to-end regression: voted/safe outputs should never contain literal
    "<s>" or "</s>" strings, even when the per-token records do."""
    def with_specials(text, prob):
        toks = [{"token": "<s>", "prob": 1.0}]
        for w in text.split():
            toks.append({"token": W + w, "prob": prob})
        toks.append({"token": "</s>", "prob": 0.99})
        return toks
    hyps = [
        {"rank": 0, "text": "the cat sat", "sequence_score": -1.0,
         "tokens": with_specials("the cat sat", 0.9)},
        {"rank": 1, "text": "the bat sat", "sequence_score": -1.1,
         "tokens": with_specials("the bat sat", 0.85)},
    ]
    out = A.aggregate_one({"hypotheses": hyps})
    for method in ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe"]:
        v = out[method]
        text = v if isinstance(v, str) else v.get("text", "")
        assert "<s>" not in text, f"{method}: special token leaked → {text!r}"
        assert "</s>" not in text, f"{method}: special token leaked → {text!r}"
        assert "<unk>" not in text, f"{method}: special token leaked → {text!r}"


# ──────────────────────────────────────────────────────────────────────────────
# softmax_scores
# ──────────────────────────────────────────────────────────────────────────────

def test_softmax_scores_uniform_when_all_none():
    w = A.softmax_scores([None, None, None])
    assert all(abs(x - 1/3) < 1e-9 for x in w)


def test_softmax_scores_skews_to_better_score():
    w = A.softmax_scores([-0.5, -2.0, -3.0])
    # Higher (less negative) score gets more weight.
    assert w[0] > w[1] > w[2]
    assert abs(sum(w) - 1.0) < 1e-9


# ──────────────────────────────────────────────────────────────────────────────
# MBR
# ──────────────────────────────────────────────────────────────────────────────

def test_mbr_consensus_wins_over_outlier():
    # 4 of 5 beams agree on "dog"; the outlier "cat" has only a slight score
    # advantage. The consensus weight (4×) dominates — MBR picks dog.
    hyps = _hyps(
        (0, "the cat sat",  -1.0, 0.9),   # outlier (highest score)
        (1, "the dog sat",  -1.05, 0.85),
        (2, "the dog sat",  -1.1, 0.85),
        (3, "the dog sat",  -1.15, 0.85),
        (4, "the dog sat",  -1.2, 0.85),
    )
    text, meta = A.mbr(hyps)
    assert "dog" in text  # consensus chosen


def test_mbr_dedup_by_text():
    hyps = _hyps(
        (0, "hello",  -0.5, 0.9),
        (1, "hello",  -0.6, 0.9),
        (2, "world",  -1.5, 0.5),
    )
    _, meta = A.mbr(hyps)
    # Two duplicates of "hello" merge → 2 unique
    assert meta["n_unique"] == 2


def test_mbr_singleton():
    hyps = _hyps((0, "hi", -0.1, 0.99))
    text, meta = A.mbr(hyps)
    assert text == "hi"
    assert meta["rank_chosen"] == 0


def test_mbr_empty():
    text, meta = A.mbr([])
    assert text == ""
    assert meta["rank_chosen"] == -1


# ──────────────────────────────────────────────────────────────────────────────
# weighted_vote
# ──────────────────────────────────────────────────────────────────────────────

def test_vote_majority_wins():
    hyps = _hyps(
        (0, "the cat sat", -1.0, 0.9),
        (1, "the bat sat", -1.1, 0.9),
        (2, "the bat sat", -1.2, 0.9),
        (3, "the bat sat", -1.3, 0.9),
    )
    text, meta = A.weighted_vote(hyps, "score")
    # 3 vs 1 → bat wins
    assert "bat" in text


def test_vote_score_x_conf_breaks_tie():
    # 2 vs 2 in counts; score weights equal; conf-mode tiebreaks toward higher conf.
    # Pair 1: "cat" with high conf
    # Pair 2: "bat" with low conf
    hyps = [
        {"rank": 0, "text": "the cat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.9}, {"token": W+"cat", "prob": 0.95}]},
        {"rank": 1, "text": "the cat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.9}, {"token": W+"cat", "prob": 0.90}]},
        {"rank": 2, "text": "the bat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.9}, {"token": W+"bat", "prob": 0.30}]},
        {"rank": 3, "text": "the bat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.9}, {"token": W+"bat", "prob": 0.20}]},
    ]
    # In score-only mode (counts equal, all conf used uniformly), it's a tie that
    # favors anchor (cat). In score×conf, cat clearly wins.
    text_conf, _ = A.weighted_vote(hyps, "score_x_conf")
    assert "cat" in text_conf


def test_vote_singleton():
    hyps = _hyps((0, "hello world", -0.1, 0.99))
    text, _ = A.weighted_vote(hyps, "score")
    assert text == "hello world"


def test_vote_empty():
    text, _ = A.weighted_vote([], "score")
    assert text == ""


# ──────────────────────────────────────────────────────────────────────────────
# safe_topk (bias-preference)
# ──────────────────────────────────────────────────────────────────────────────

def test_vote_conf_emits_agreement_higher_than_individual_beams():
    """When 4 of 5 beams agree on the same word with moderate per-beam conf,
    the conf-weighted voter's *agreement score* for that word must be
    substantially higher than any single beam's raw confidence. NOTE: this
    score is NOT a true Bayesian posterior — beams share prefix history and
    are highly correlated. See nbest_aggregate.weighted_vote() docstring for
    citations. We test the agreement-share property only."""
    hyps = [
        {"rank": 0, "text": "cat", "sequence_score": -1.0,
         "tokens": [{"token": W + "cat", "prob": 0.30}]},  # outlier wrong word
        {"rank": 1, "text": "bat", "sequence_score": -1.05,
         "tokens": [{"token": W + "bat", "prob": 0.60}]},
        {"rank": 2, "text": "bat", "sequence_score": -1.10,
         "tokens": [{"token": W + "bat", "prob": 0.65}]},
        {"rank": 3, "text": "bat", "sequence_score": -1.15,
         "tokens": [{"token": W + "bat", "prob": 0.70}]},
        {"rank": 4, "text": "bat", "sequence_score": -1.20,
         "tokens": [{"token": W + "bat", "prob": 0.55}]},
    ]
    text, meta = A.weighted_vote(hyps, "score_x_conf")
    assert text == "bat"
    word_confs = meta["word_confs"]
    assert len(word_confs) == 1 and word_confs[0][0] == "bat"
    agreement = word_confs[0][1]
    individual_confs = [0.60, 0.65, 0.70, 0.55]
    assert agreement is not None
    # Agreement-share for the consensus word should exceed any individual
    # contributing beam's raw confidence — the agreement mass dominates.
    assert agreement > max(individual_confs), (
        f"agreement {agreement:.3f} should exceed max individual conf {max(individual_confs):.3f}"
    )


def test_temperature_scale_identity_at_T_one():
    """T=1 should be a no-op (preserves input exactly)."""
    for p in [0.1, 0.5, 0.9, 0.999]:
        assert A._temperature_scale(p, 1.0) == pytest.approx(p, abs=1e-9)


def test_temperature_scale_flattens_overconfident():
    """T>1 should pull a high probability toward 0.5."""
    high = 0.99
    flattened = A._temperature_scale(high, 5.0)
    assert flattened is not None
    assert 0.5 < flattened < high  # pulled down but still > 0.5


def test_temperature_scale_sharpens_underconfident():
    """T<1 should push a moderate probability toward the extremes."""
    moderate = 0.7
    sharpened = A._temperature_scale(moderate, 0.5)
    assert sharpened is not None
    assert sharpened > moderate  # pushed toward 1


def test_temperature_scale_handles_none():
    assert A._temperature_scale(None, 2.0) is None


def test_load_calibration_full_format(tmp_path):
    """Output of calibrate_temperature.py uses {'methods': {m: {'T_pool': ...}}}"""
    cal = {"methods": {
        "hyp_top1": {"T_pool": 2.5, "ece_uncalibrated": 0.16},
        "hyp_vote_conf": {"T_pool": 14.0},
    }}
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(cal))
    T = A._load_calibration(str(p))
    assert T["hyp_top1"] == 2.5
    assert T["hyp_vote_conf"] == 14.0
    # Methods not in the file get T=1.0 default
    assert T["hyp_mbr"] == 1.0


def test_load_calibration_flat_format(tmp_path):
    """Also accept a flat {method: T} mapping."""
    cal = {"hyp_top1": 2.0, "hyp_safe": 3.0}
    p = tmp_path / "cal_flat.json"
    p.write_text(json.dumps(cal))
    T = A._load_calibration(str(p))
    assert T["hyp_top1"] == 2.0
    assert T["hyp_safe"] == 3.0


def test_load_calibration_missing_file_returns_unit_temperatures():
    T = A._load_calibration("/no/such/path.json")
    assert all(t == 1.0 for t in T.values())


def test_run_with_calibration_writes_calibrated_word_confs(tmp_path):
    """End-to-end: aggregator output should carry both raw and calibrated
    word_confs when --calibration is provided."""
    nbest = {
        "u": {"hypotheses": [
            {"rank": 0, "text": "the cat sat", "sequence_score": -1.0,
             "tokens": [{"token": W + "the", "prob": 0.95},
                        {"token": W + "cat", "prob": 0.99},
                        {"token": W + "sat", "prob": 0.95}]},
            {"rank": 1, "text": "the cat sat", "sequence_score": -1.1,
             "tokens": [{"token": W + "the", "prob": 0.92},
                        {"token": W + "cat", "prob": 0.96},
                        {"token": W + "sat", "prob": 0.92}]},
        ]}
    }
    cal = {"methods": {
        "hyp_top1":       {"T_pool": 2.5},
        "hyp_vote_conf":  {"T_pool": 10.0},
    }}
    nb_p = tmp_path / "nb.json";  nb_p.write_text(json.dumps(nbest))
    cal_p = tmp_path / "cal.json"; cal_p.write_text(json.dumps(cal))
    out_p = tmp_path / "agg.json"
    A.run(str(nb_p), str(out_p), None, str(cal_p))
    out = json.loads(out_p.read_text())["u"]
    # top-1 calibrated confs should be lower than raw (T>1 flattens overconfidence).
    raw = dict(out["hyp_top1_word_confs"])
    cal_confs = dict(out["hyp_top1_word_confs_calibrated"])
    assert cal_confs["cat"] < raw["cat"]
    # vote_conf with T=10 should be much more compressed
    vc = out["hyp_vote_conf"]
    assert "word_confs" in vc and "word_confs_calibrated" in vc
    assert vc["calibration_T"] == 10.0


def test_safe_swap_promotes_to_agreement_rate():
    """When safe-mode swaps, the new word's reported confidence is the
    agreement rate K/(N-1) among other beams (NOT a posterior probability —
    see safe_topk docstring re: beam non-independence). Unswapped slots keep
    top-1's raw conf."""
    hyps = [
        {"rank": 0, "text": "the cat sat", "sequence_score": -1.0,
         "tokens": [{"token": W + "the", "prob": 0.95},
                    {"token": W + "cat", "prob": 0.30},   # low-conf wrong word
                    {"token": W + "sat", "prob": 0.95}]},
        {"rank": 1, "text": "the bat sat", "sequence_score": -1.1,
         "tokens": [{"token": W + "the", "prob": 0.9},
                    {"token": W + "bat", "prob": 0.6},
                    {"token": W + "sat", "prob": 0.9}]},
        {"rank": 2, "text": "the bat sat", "sequence_score": -1.2,
         "tokens": [{"token": W + "the", "prob": 0.9},
                    {"token": W + "bat", "prob": 0.55},
                    {"token": W + "sat", "prob": 0.9}]},
        {"rank": 3, "text": "the bat sat", "sequence_score": -1.3,
         "tokens": [{"token": W + "the", "prob": 0.9},
                    {"token": W + "bat", "prob": 0.5},
                    {"token": W + "sat", "prob": 0.9}]},
    ]
    text, meta = A.safe_topk(hyps)
    assert "bat" in text
    word_confs = dict(meta["word_confs"])
    # 3 of 3 other beams agreed on 'bat' → agreement rate = 1.0
    # (Caveat: not a true posterior — see docstring on beam non-independence)
    assert word_confs.get("bat") == 1.0, f"expected 1.0, got {word_confs.get('bat')}"
    # Unswapped words keep their top-1 conf
    assert word_confs.get("the") == 0.95
    assert word_confs.get("sat") == 0.95


def test_safe_swap_only_when_low_conf_and_consensus():
    # Top-1 has 'cat' at conf 0.30 (low); 3/3 others say 'bat' → swap.
    hyps = [
        {"rank": 0, "text": "the cat sat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.95},
                    {"token": W+"cat", "prob": 0.30},
                    {"token": W+"sat", "prob": 0.95}]},
        {"rank": 1, "text": "the bat sat", "sequence_score": -1.1, "tokens": _tok("the bat sat", 0.85)},
        {"rank": 2, "text": "the bat sat", "sequence_score": -1.2, "tokens": _tok("the bat sat", 0.80)},
        {"rank": 3, "text": "the bat sat", "sequence_score": -1.3, "tokens": _tok("the bat sat", 0.70)},
    ]
    text, meta = A.safe_topk(hyps)
    assert "bat" in text
    assert len(meta["swaps"]) == 1
    assert meta["swaps"][0]["from"] == "cat"
    assert meta["swaps"][0]["to"] == "bat"


def test_safe_keeps_topk_when_confident():
    # Top-1 confident (0.95), other beams disagree but top-1 stays.
    hyps = [
        {"rank": 0, "text": "the cat sat", "sequence_score": -1.0, "tokens": _tok("the cat sat", 0.95)},
        {"rank": 1, "text": "the bat sat", "sequence_score": -1.1, "tokens": _tok("the bat sat", 0.50)},
        {"rank": 2, "text": "the bat sat", "sequence_score": -1.2, "tokens": _tok("the bat sat", 0.50)},
    ]
    text, meta = A.safe_topk(hyps)
    assert text.split()[1] == "cat"  # not swapped
    assert meta["swaps"] == []


def test_safe_keeps_topk_when_low_conf_but_no_consensus():
    # Top-1 has low-conf word but other beams disagree among themselves → no swap.
    hyps = [
        {"rank": 0, "text": "the cat sat", "sequence_score": -1.0,
         "tokens": [{"token": W+"the", "prob": 0.9},
                    {"token": W+"cat", "prob": 0.30},
                    {"token": W+"sat", "prob": 0.9}]},
        {"rank": 1, "text": "the bat sat", "sequence_score": -1.1, "tokens": _tok("the bat sat", 0.5)},
        {"rank": 2, "text": "the dog sat", "sequence_score": -1.2, "tokens": _tok("the dog sat", 0.5)},
        {"rank": 3, "text": "the rat sat", "sequence_score": -1.3, "tokens": _tok("the rat sat", 0.5)},
    ]
    text, meta = A.safe_topk(hyps)
    # No alternative reaches 60% agreement among others — keep cat.
    assert text.split()[1] == "cat"
    assert meta["swaps"] == []


# ──────────────────────────────────────────────────────────────────────────────
# N=1 equivalence — every method returns top-1 when only one hyp exists
# ──────────────────────────────────────────────────────────────────────────────

def test_n_equals_one_equivalence():
    hyps = _hyps((0, "the only one", -0.5, 0.95))
    out = A.aggregate_one({"hypotheses": hyps})
    expected = "the only one"
    assert out["hyp_top1"] == expected
    assert out["hyp_mbr"]["text"] == expected
    assert out["hyp_vote_score"]["text"] == expected
    assert out["hyp_vote_conf"]["text"] == expected
    assert out["hyp_safe"]["text"] == expected


# ──────────────────────────────────────────────────────────────────────────────
# Determinism
# ──────────────────────────────────────────────────────────────────────────────

def test_aggregate_one_deterministic():
    hyps = _hyps(
        (0, "the cat sat",  -1.0, 0.9),
        (1, "the dog sat",  -1.5, 0.85),
        (2, "the cat ran",  -1.6, 0.85),
        (3, "a cat sat",    -1.7, 0.85),
    )
    rec = {"hypotheses": hyps}
    out1 = A.aggregate_one(rec)
    out2 = A.aggregate_one(rec)
    assert out1["hyp_top1"] == out2["hyp_top1"]
    assert out1["hyp_mbr"]["text"] == out2["hyp_mbr"]["text"]
    assert out1["hyp_vote_score"]["text"] == out2["hyp_vote_score"]["text"]
    assert out1["hyp_vote_conf"]["text"] == out2["hyp_vote_conf"]["text"]
    assert out1["hyp_safe"]["text"] == out2["hyp_safe"]["text"]


# ──────────────────────────────────────────────────────────────────────────────
# Empty / all-identical edge cases
# ──────────────────────────────────────────────────────────────────────────────

def test_aggregate_one_empty():
    out = A.aggregate_one({"hypotheses": []})
    assert out["hyp_top1"] == ""
    assert out["hyp_mbr"]["text"] == ""


def test_aggregate_one_all_identical():
    hyps = _hyps(*[(i, "the same text", -1.0 - 0.01 * i, 0.9) for i in range(5)])
    out = A.aggregate_one({"hypotheses": hyps})
    assert out["hyp_top1"] == "the same text"
    assert out["hyp_mbr"]["text"] == "the same text"
    assert out["hyp_vote_score"]["text"] == "the same text"
    assert out["hyp_vote_conf"]["text"] == "the same text"


# ──────────────────────────────────────────────────────────────────────────────
# Cross-segment merge
# ──────────────────────────────────────────────────────────────────────────────

def test_xseg_merge_swaps_low_conf_word_with_neighbor_higher_conf():
    nbest = {
        "v__seg0": {"hypotheses": [
            {"rank": 0, "text": "the dog ran very slow home", "sequence_score": -1.0,
             "tokens": [{"token": W+"the", "prob": 0.9},
                        {"token": W+"dog", "prob": 0.9},
                        {"token": W+"ran", "prob": 0.6},
                        {"token": W+"very", "prob": 0.6},
                        {"token": W+"slow", "prob": 0.30},   # low-conf wrong word
                        {"token": W+"home", "prob": 0.6}]},
        ]},
        "v__seg1": {"hypotheses": [
            {"rank": 0, "text": "ran very fast home today", "sequence_score": -1.0,
             "tokens": [{"token": W+"ran", "prob": 0.95},
                        {"token": W+"very", "prob": 0.95},
                        {"token": W+"fast", "prob": 0.92},   # higher-conf correct
                        {"token": W+"home", "prob": 0.95},
                        {"token": W+"today", "prob": 0.90}]},
        ]},
    }
    seg_meta = {
        "v__seg0": {"video_id": "v", "start_frame": 0,  "end_frame": 100},
        "v__seg1": {"video_id": "v", "start_frame": 70, "end_frame": 170},
    }
    with tempfile.TemporaryDirectory() as d:
        nb_p = os.path.join(d, "nb.json")
        seg_p = os.path.join(d, "seg.json")
        out_p = os.path.join(d, "agg.json")
        json.dump(nbest, open(nb_p, "w"))
        json.dump(seg_meta, open(seg_p, "w"))
        A.run(nb_p, out_p, seg_p)
        out = json.load(open(out_p))
    assert "fast" in out["v__seg0"]["hyp_xseg_merge"]["text"]
    assert len(out["v__seg0"]["hyp_xseg_merge"]["swaps"]) == 1


def test_xseg_merge_no_op_when_no_seg_meta():
    nbest = {
        "u": {"hypotheses": [{"rank": 0, "text": "hello world", "sequence_score": -0.5, "tokens": _tok("hello world", 0.9)}]},
    }
    with tempfile.TemporaryDirectory() as d:
        nb_p = os.path.join(d, "nb.json")
        out_p = os.path.join(d, "agg.json")
        json.dump(nbest, open(nb_p, "w"))
        A.run(nb_p, out_p, None)
        out = json.load(open(out_p))
    assert out["u"]["hyp_xseg_merge"]["text"] == "hello world"
    assert out["u"]["hyp_xseg_merge"]["swaps"] == []


def test_xseg_merge_skips_below_min_overlap():
    # Two segments with only 1 word in common → below XSEG_MIN_OVERLAP=3
    nbest = {
        "v__a": {"hypotheses": [
            {"rank": 0, "text": "alpha beta gamma", "sequence_score": -1.0, "tokens": _tok("alpha beta gamma", 0.9)},
        ]},
        "v__b": {"hypotheses": [
            {"rank": 0, "text": "gamma delta epsilon", "sequence_score": -1.0, "tokens": _tok("gamma delta epsilon", 0.95)},
        ]},
    }
    seg_meta = {
        "v__a": {"video_id": "v", "start_frame": 0,  "end_frame": 100},
        "v__b": {"video_id": "v", "start_frame": 80, "end_frame": 200},
    }
    with tempfile.TemporaryDirectory() as d:
        nb_p = os.path.join(d, "nb.json")
        seg_p = os.path.join(d, "seg.json")
        out_p = os.path.join(d, "agg.json")
        json.dump(nbest, open(nb_p, "w"))
        json.dump(seg_meta, open(seg_p, "w"))
        A.run(nb_p, out_p, seg_p)
        out = json.load(open(out_p))
    # Only 1 word ('gamma') in common — below threshold
    assert out["v__a"]["hyp_xseg_merge"]["swaps"] == []
    assert out["v__a"]["hyp_xseg_merge"]["text"] == "alpha beta gamma"
