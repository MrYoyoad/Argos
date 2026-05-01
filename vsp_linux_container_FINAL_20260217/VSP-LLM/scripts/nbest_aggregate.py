"""N-best beam aggregation for VSP-LLM lip-reading output.

Reads `nbest-{fid}.json` (and optionally `confidence-{fid}.json` and
`segment_metadata.json`); produces `aggregated-{fid}.json` with five aggregated
hypotheses per utterance:

  - hyp_top1        : rank-0 of the beam (baseline)
  - hyp_mbr         : Minimum Bayes Risk consensus
  - hyp_vote_score  : score-weighted multi-way ROVER-style vote
  - hyp_vote_conf   : score × per-word-confidence weighted vote
  - hyp_safe        : top-1 with conservative low-confidence word swaps
  - hyp_xseg_merge  : cross-segment overlap fusion (if --seg-meta given)

Pure Python, CPU-only, container-compatible. Imports only from numpy,
the standard library, and the local `_alignment` helper.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

# Make the alignment helper importable across all known layouts:
#   - EC2 dev:   /home/ubuntu/lib/                           (this file's dir)
#                /home/ubuntu/docs/_research-tools/generators/   (helper lives here)
#   - Container: /workspace/VSP-LLM/scripts/                 (this file co-located with helper)
_HERE = os.path.dirname(os.path.abspath(__file__))
_candidates = [
    _HERE,
    os.path.join(os.path.dirname(_HERE), "docs", "_research-tools", "generators"),
    os.path.join(_HERE, "..", "docs", "_research-tools", "generators"),
]
for _p in _candidates:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from _alignment import align_word_lists, split_words, wer  # noqa: E402

# SentencePiece word-start marker used by the LLaMA tokenizer.
_SP_WORD_START = "▁"  # ▁

# LLaMA / SentencePiece special tokens. The decode path applies
# `tokenizer.batch_decode(..., skip_special_tokens=True)` for the canonical
# `text` field, but the per-token records preserve them so consumers that need
# raw probs can see them. The aggregator must filter them out before voting,
# or special tokens leak into the merged hypothesis as literal words.
_SPECIAL_TOKENS = frozenset({"<s>", "</s>", "<unk>", "<pad>", "<|begin_of_text|>", "<|end_of_text|>"})


def _is_special_token(tstr: str) -> bool:
    """True if this token string should be excluded from word aggregation."""
    if not tstr:
        return True
    s = tstr.lstrip(_SP_WORD_START)
    return s in _SPECIAL_TOKENS


# Threshold for "low confidence" word in safe-mode swaps. Matches CONF_MED in
# compute_word_confidence.py (tightened 2026-04-30).
SAFE_LOW_CONF = 0.40
# Minimum fraction of OTHER beams that must agree on a different word for safe
# mode to swap.
SAFE_AGREE_FRAC = 0.60
# Minimum overlap length (in words) for cross-segment merge to fire.
XSEG_MIN_OVERLAP = 3


# ──────────────────────────────────────────────────────────────────────────────
# Per-word confidence aggregation (sub-tokens → words via SentencePiece markers)
# ──────────────────────────────────────────────────────────────────────────────

def words_with_conf(tokens: Sequence[dict]) -> List[Tuple[str, Optional[float]]]:
    """Group sub-tokens into words, return [(word, min-prob), ...].

    Mirrors compute_word_confidence.py's aggregation: a new word starts on a
    sub-token whose string begins with the SentencePiece marker (▁). The word's
    probability is the *minimum* sub-token probability (conservative — flag the
    word if any piece is uncertain). Probs that are None are ignored.
    """
    words: List[Tuple[str, Optional[float]]] = []
    cur_chars: List[str] = []
    cur_min: Optional[float] = None
    for rec in tokens:
        tstr = rec.get("token") or ""
        if not tstr:
            continue
        # Skip special tokens (BOS/EOS/UNK/PAD). They appear in the per-token
        # records but never in the canonical decoded text — leaking them into
        # the voted hypothesis would inflate WER catastrophically.
        if _is_special_token(tstr):
            # Boundary effect: a special token between real word pieces should
            # also flush whatever sub-tokens were accumulating, so we don't
            # accidentally splice across a special-token boundary.
            if cur_chars:
                words.append(("".join(cur_chars), cur_min))
                cur_chars = []
                cur_min = None
            continue
        is_word_start = tstr.startswith(_SP_WORD_START)
        piece = tstr.lstrip(_SP_WORD_START)
        if is_word_start and cur_chars:
            words.append(("".join(cur_chars), cur_min))
            cur_chars = []
            cur_min = None
        cur_chars.append(piece)
        p = rec.get("prob")
        if p is not None and math.isfinite(float(p)):
            cur_min = float(p) if cur_min is None else min(cur_min, float(p))
    if cur_chars:
        words.append(("".join(cur_chars), cur_min))
    # Some hypotheses might decode to empty / whitespace-only — filter out.
    return [(w, p) for w, p in words if w.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# Score normalization
# ──────────────────────────────────────────────────────────────────────────────

def softmax_scores(scores: Sequence[Optional[float]], temperature: float = 1.0) -> List[float]:
    """Stable softmax over sequence_scores. None or non-finite scores get
    weight 0; if all scores are None, returns uniform weights.
    """
    finite = [(i, s) for i, s in enumerate(scores) if s is not None and math.isfinite(float(s))]
    if not finite:
        n = len(scores)
        return [1.0 / max(1, n)] * n
    vals = [s / max(temperature, 1e-9) for _, s in finite]
    m = max(vals)
    exps = [math.exp(v - m) for v in vals]
    Z = sum(exps)
    weights = [0.0] * len(scores)
    for (i, _), e in zip(finite, exps):
        weights[i] = e / Z
    return weights


# ──────────────────────────────────────────────────────────────────────────────
# Method 1: MBR (Minimum Bayes Risk)
# ──────────────────────────────────────────────────────────────────────────────

def mbr(hypotheses: List[dict]) -> Tuple[str, dict]:
    """Pick the hypothesis with lowest expected WER under the score-weighted
    distribution over the others. Dedupes by exact text first, summing weights.

    Per-word confidence reported in `word_confs` comes from the chosen
    hypothesis's own beam-conditioned per-token probs (sub-token min). MBR
    operates at the sentence level, so it doesn't update per-word confidences
    via consensus — it just inherits them from whichever beam won.
    """
    if not hypotheses:
        return "", {"rank_chosen": -1, "expected_wer": None, "n_unique": 0, "word_confs": []}
    if len(hypotheses) == 1:
        wc = words_with_conf(hypotheses[0].get("tokens") or [])
        return hypotheses[0].get("text", ""), {"rank_chosen": 0, "expected_wer": 0.0, "n_unique": 1, "word_confs": list(wc)}

    weights = softmax_scores([h.get("sequence_score") for h in hypotheses])

    # Dedupe by text; sum weights; keep the lowest-rank instance for each unique text.
    by_text: Dict[str, dict] = {}
    for h, w in zip(hypotheses, weights):
        key = h.get("text", "").strip()
        if key not in by_text:
            by_text[key] = {"text": h.get("text", ""), "weight": w, "first_rank": h.get("rank", -1)}
        else:
            by_text[key]["weight"] += w
            by_text[key]["first_rank"] = min(by_text[key]["first_rank"], h.get("rank", -1))
    unique = list(by_text.values())

    # Pre-tokenize once.
    tokenized = [split_words(u["text"]) for u in unique]
    expected_wer = []
    for i, words_i in enumerate(tokenized):
        # MBR risk: E_j[ WER(hyp_i, hyp_j) ] under the (score-weighted) dist.
        # Crucially: do NOT normalize by sum-of-other-weights — that flattens
        # the comparison whenever WER between candidates is symmetric, which
        # is the common case. Raw expected risk is what favors consensus.
        exp_wer = 0.0
        for j, words_j in enumerate(tokenized):
            if i == j:
                continue
            exp_wer += unique[j]["weight"] * wer(words_j, words_i)
        expected_wer.append(exp_wer)

    best_idx = min(range(len(unique)), key=lambda k: expected_wer[k])
    chosen_rank = int(unique[best_idx]["first_rank"])
    # Inherit per-word conf from the chosen beam's own token records.
    chosen_hyp = next((h for h in hypotheses if h.get("rank") == chosen_rank), hypotheses[0])
    chosen_word_confs = words_with_conf(chosen_hyp.get("tokens") or [])
    return unique[best_idx]["text"], {
        "rank_chosen": chosen_rank,
        "expected_wer": float(expected_wer[best_idx]),
        "n_unique": len(unique),
        "word_confs": list(chosen_word_confs),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Method 2: Anchor-based weighted ROVER vote
# ──────────────────────────────────────────────────────────────────────────────

def _vote_for_position(votes: Dict[str, float]) -> Tuple[Optional[str], float, float]:
    """Pick the highest-weight candidate; return (word_or_None, weight, total).

    A None pseudo-word represents 'no word at this position' (gap); when None
    wins, the position contributes nothing to the merged hypothesis.
    """
    if not votes:
        return None, 0.0, 0.0
    total = sum(votes.values())
    word, w = max(votes.items(), key=lambda kv: kv[1])
    return (None if word == "" else word), w, total


def weighted_vote(
    hypotheses: List[dict],
    weight_mode: str = "score",  # "score" or "score_x_conf"
    word_confs: Optional[List[List[Tuple[str, Optional[float]]]]] = None,
) -> Tuple[str, dict]:
    """Multi-way ROVER-style vote.

    Anchors on the highest-weight (top-1) hypothesis to keep this simple and
    deterministic. For each anchor word, we look at what each other hypothesis
    aligned to it (a word, or a gap), and vote weighted.

    weight_mode:
      - "score": weight = softmax(sequence_score)
      - "score_x_conf": weight = softmax(sequence_score) × per-word confidence
        of the candidate word from that hypothesis (uses min-of-subtoken probs).

    Returns (text, meta). `meta["word_confs"]` is the per-word *agreement
    score* for each emitted word — the vote share `weight_chosen / total`.

    NOTE: this is NOT a valid Bayesian posterior probability. Beams in HF beam
    search share encoder, decoder, and prefix histories — they are highly
    correlated, not independent samples. Eikema & Aziz (2020) show beam search
    is mode-seeking and biased; Spagnolo et al. (2025) treat the beam-weighted
    estimator as biased and use it only for variance reduction. So a value
    near 1.0 here means "all surviving beams agree" (a useful relative
    confidence signal), but it does NOT mean "probability ≈ 1.0 of being
    correct" — that requires temperature scaling on a labeled held-out set.
    """
    if not hypotheses:
        return "", {"breakdown": [], "word_confs": []}
    if len(hypotheses) == 1:
        single = hypotheses[0]
        wc = word_confs[0] if word_confs else words_with_conf(single.get("tokens") or [])
        return single.get("text", ""), {"breakdown": [], "word_confs": list(wc)}

    score_weights = softmax_scores([h.get("sequence_score") for h in hypotheses])

    # word_confs[h] = list of (word, prob) for hypothesis h.
    if word_confs is None:
        word_confs = [words_with_conf(h.get("tokens") or []) for h in hypotheses]
    # Pre-tokenize and align to top-1 (rank 0).
    word_lists = [[w for w, _ in wc] for wc in word_confs]
    if not word_lists[0]:
        # Top-1 is empty: fall back to top-1 text directly.
        return hypotheses[0].get("text", ""), {"breakdown": [], "word_confs": []}

    n_anchor = len(word_lists[0])
    # accumulators: votes[a] = {word: total_weight}
    votes: List[Dict[str, float]] = [defaultdict(float) for _ in range(n_anchor)]

    for h_idx, hyp_words in enumerate(word_lists):
        sw = score_weights[h_idx]
        if sw <= 0:
            continue
        if h_idx == 0:
            # Anchor votes for itself with full score weight (×conf if conf-mode).
            for a in range(n_anchor):
                w = hyp_words[a]
                conf = word_confs[0][a][1] if word_confs[0][a][1] is not None else 1.0
                weight = sw * (conf if weight_mode == "score_x_conf" else 1.0)
                votes[a][w] += weight
            continue

        pairs = align_word_lists(word_lists[0], hyp_words)
        for a_idx, h_pos in pairs:
            if a_idx < 0:
                # Insertion in hyp h relative to anchor — ignore (no anchor slot).
                continue
            if h_pos < 0:
                # Deletion in hyp h relative to anchor — vote for "" (gap).
                votes[a_idx][""] += sw
            else:
                w = hyp_words[h_pos]
                conf = word_confs[h_idx][h_pos][1]
                conf = conf if conf is not None else 1.0
                weight = sw * (conf if weight_mode == "score_x_conf" else 1.0)
                votes[a_idx][w] += weight

    # Decode anchor positions and emit posterior conf per kept word.
    out_words: List[str] = []
    out_word_confs: List[Tuple[str, Optional[float]]] = []
    breakdown: List[dict] = []
    for a in range(n_anchor):
        word, w_chosen, total = _vote_for_position(votes[a])
        anchor_word = word_lists[0][a]
        agreement = (w_chosen / total) if total > 0 else None
        breakdown.append({
            "anchor_pos": a,
            "anchor_word": anchor_word,
            "chosen": word,
            "weight": float(w_chosen),
            "total": float(total),
            "agreement": float(agreement) if agreement is not None else None,
            "swapped": (word is not None and word != anchor_word),
        })
        if word is not None and word.strip():
            out_words.append(word)
            out_word_confs.append((word, agreement))

    return " ".join(out_words), {
        "breakdown": breakdown,
        "weight_mode": weight_mode,
        "word_confs": out_word_confs,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Method 3: Safe (top-1 with backoff)
# ──────────────────────────────────────────────────────────────────────────────

def safe_topk(
    hypotheses: List[dict],
    word_confs: Optional[List[List[Tuple[str, Optional[float]]]]] = None,
) -> Tuple[str, dict]:
    """Start from top-1; for each word with conf < SAFE_LOW_CONF, look at the
    same aligned position across other beams. If ≥ SAFE_AGREE_FRAC of them
    agree on a *different* word, swap.

    Conservative: only swaps when the model is uncertain AND there's strong
    consensus disagreement. Designed as a low-risk drop-in that should never
    make output dramatically worse.
    """
    if not hypotheses:
        return "", {"swaps": [], "word_confs": []}
    if len(hypotheses) == 1:
        wc = word_confs[0] if word_confs else words_with_conf(hypotheses[0].get("tokens") or [])
        return hypotheses[0].get("text", ""), {"swaps": [], "word_confs": list(wc)}

    if word_confs is None:
        word_confs = [words_with_conf(h.get("tokens") or []) for h in hypotheses]
    word_lists = [[w for w, _ in wc] for wc in word_confs]
    if not word_lists[0]:
        return hypotheses[0].get("text", ""), {"swaps": [], "word_confs": []}

    n_anchor = len(word_lists[0])
    swaps: List[dict] = []
    out = list(word_lists[0])
    # Start with top-1's per-word confidences; rewrite slots where we swap.
    out_confs: List[Optional[float]] = [word_confs[0][a][1] for a in range(n_anchor)]

    for a in range(n_anchor):
        anchor_word = word_lists[0][a]
        anchor_conf = word_confs[0][a][1]
        if anchor_conf is None or anchor_conf >= SAFE_LOW_CONF:
            continue
        # Tally what the OTHER beams say at the aligned position.
        other_votes: Dict[str, int] = defaultdict(int)
        n_other = 0
        for h_idx in range(1, len(hypotheses)):
            pairs = align_word_lists(word_lists[0], word_lists[h_idx])
            mapped = None
            for a_idx, h_pos in pairs:
                if a_idx == a:
                    mapped = (word_lists[h_idx][h_pos] if h_pos >= 0 else None)
                    break
            if mapped is not None:
                other_votes[mapped] += 1
            n_other += 1
        # Find the dominant alternative among the others.
        if not other_votes:
            continue
        alt, alt_count = max(other_votes.items(), key=lambda kv: kv[1])
        if alt == anchor_word:
            continue  # Others mostly agree with top-1 — leave it.
        agree_frac = alt_count / max(1, n_other)
        if agree_frac >= SAFE_AGREE_FRAC:
            out[a] = alt
            # New conf = agreement rate K/(N-1) among other beams. NOTE: this
            # is an agreement signal, not a true posterior — beams are not
            # independent (see vote-method docstring above for citations).
            out_confs[a] = float(agree_frac)
            swaps.append({
                "pos": a,
                "from": anchor_word,
                "to": alt,
                "from_conf": float(anchor_conf),
                "to_agreement": float(agree_frac),
                "agree_count": int(alt_count),
                "n_other": int(n_other),
            })
    return " ".join(out), {"swaps": swaps, "word_confs": list(zip(out, out_confs))}


# ──────────────────────────────────────────────────────────────────────────────
# Method 4: Cross-segment overlap fusion
# ──────────────────────────────────────────────────────────────────────────────

def _lcs_length(a: List[str], b: List[str]) -> int:
    """Length of LCS (case-insensitive). Used as a threshold to detect 'is
    there a real overlap region between these two edges?'."""
    an = [w.strip().lower() for w in a]
    bn = [w.strip().lower() for w in b]
    n, m = len(an), len(bn)
    if n == 0 or m == 0:
        return 0
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            if an[i] == bn[j]:
                L[i + 1][j + 1] = L[i][j] + 1
            else:
                L[i + 1][j + 1] = max(L[i][j + 1], L[i + 1][j])
    return int(L[n][m])


def xseg_merge(
    utt_id: str,
    top1_text: str,
    word_confs_top1: List[Tuple[str, Optional[float]]],
    neighbors: List[dict],
) -> Tuple[str, dict]:
    """Merge with neighbors that share an overlapping source-time window.

    Approach: align this segment's edge to the neighbor's opposite edge with
    Levenshtein. The pair list includes substitutions (different words at the
    same column), not just LCS matches. Gate on LCS length ≥ XSEG_MIN_OVERLAP
    so we only fire when the segments genuinely share enough vocabulary to
    look like real overlap (avoids spurious swaps on unrelated content).
    For each paired position (substitution), keep the higher-confidence word.
    """
    out_words = list(word_confs_top1)
    swaps: List[dict] = []
    if not neighbors or not out_words:
        return top1_text, {"swaps": [], "neighbors_considered": 0}

    for nb in neighbors:
        nb_words = nb["words_with_conf"]
        if not nb_words:
            continue
        side = nb.get("side", "next")
        if side == "next":
            # End-of-self vs start-of-next: take last K self-words, first K nb-words.
            self_edge = out_words[-min(len(out_words), 60):]
            nb_edge = nb_words[: min(len(nb_words), 60)]
            self_edge_offset = len(out_words) - len(self_edge)
        else:  # 'prev': start-of-self vs end-of-prev
            self_edge = out_words[: min(len(out_words), 60)]
            nb_edge = nb_words[-min(len(nb_words), 60):]
            self_edge_offset = 0

        if _lcs_length([w for w, _ in self_edge], [w for w, _ in nb_edge]) < XSEG_MIN_OVERLAP:
            continue

        pairs = align_word_lists([w for w, _ in self_edge], [w for w, _ in nb_edge])
        for si, ni in pairs:
            if si < 0 or ni < 0:
                continue  # gap on one side — leave it alone
            self_idx = self_edge_offset + si
            self_word, self_conf = out_words[self_idx]
            nb_word, nb_conf = nb_edge[ni]
            if self_word.strip().lower() == nb_word.strip().lower():
                continue
            sc = self_conf if self_conf is not None else 0.0
            nc = nb_conf if nb_conf is not None else 0.0
            if nc > sc:
                out_words[self_idx] = (nb_word, nb_conf)
                swaps.append({
                    "pos": self_idx,
                    "from": self_word,
                    "to": nb_word,
                    "self_conf": float(sc),
                    "nb_conf": float(nc),
                    "neighbor_utt": nb.get("utt_id"),
                    "side": side,
                })

    kept = [(w, p) for w, p in out_words if w.strip()]
    merged = " ".join(w for w, _ in kept)
    return merged, {"swaps": swaps, "neighbors_considered": len(neighbors), "word_confs": kept}


# ──────────────────────────────────────────────────────────────────────────────
# Segment metadata loader (for cross-segment merge)
# ──────────────────────────────────────────────────────────────────────────────

def load_segment_neighbors(seg_meta_path: Optional[str], aggregated_records: Dict[str, dict]) -> Dict[str, List[dict]]:
    """Build a {utt_id: [neighbor_dict, ...]} map from segment_metadata.json.

    A neighbor is included if (a) its source video matches and (b) the source
    time window overlaps (start_b < end_a or vice versa). If seg_meta_path is
    not given or the file doesn't exist, returns an empty dict (xseg merge
    becomes a no-op).
    """
    if not seg_meta_path or not os.path.isfile(seg_meta_path):
        return {}
    try:
        with open(seg_meta_path) as f:
            meta = json.load(f)
    except Exception:
        return {}

    # Format expected: {utt_id: {"video_id": str, "start_frame": int, "end_frame": int, ...}}
    # If the on-disk format differs, callers can pre-normalize. We try a couple
    # of likely shapes here.
    by_video: Dict[str, List[dict]] = defaultdict(list)
    for utt, info in meta.items() if isinstance(meta, dict) else []:
        vid = info.get("video_id") or info.get("source") or info.get("video")
        if not vid:
            continue
        start = info.get("start_frame", info.get("start", 0))
        end = info.get("end_frame", info.get("end", 0))
        if utt not in aggregated_records:
            continue
        by_video[vid].append({"utt_id": utt, "start": int(start), "end": int(end)})

    for vid in by_video:
        by_video[vid].sort(key=lambda r: r["start"])

    neighbors: Dict[str, List[dict]] = defaultdict(list)
    for vid, segs in by_video.items():
        for i, seg in enumerate(segs):
            # Adjacent overlapping neighbors only — left and right.
            if i + 1 < len(segs):
                nxt = segs[i + 1]
                if nxt["start"] < seg["end"]:  # source-time overlap
                    neighbors[seg["utt_id"]].append({"utt_id": nxt["utt_id"], "side": "next"})
                    neighbors[nxt["utt_id"]].append({"utt_id": seg["utt_id"], "side": "prev"})
    return neighbors


# ──────────────────────────────────────────────────────────────────────────────
# Top-level run
# ──────────────────────────────────────────────────────────────────────────────

def aggregate_one(rec: dict) -> dict:
    """Run all in-beam aggregation methods on one segment's hypotheses.
    Cross-segment merge is applied separately (it needs all segments).
    """
    hyps = rec.get("hypotheses") or []
    if not hyps:
        return {
            "hyp_top1": "",
            "hyp_mbr": {"text": "", "rank_chosen": -1, "expected_wer": None, "n_unique": 0},
            "hyp_vote_score": {"text": "", "breakdown": []},
            "hyp_vote_conf": {"text": "", "breakdown": []},
            "hyp_safe": {"text": "", "swaps": []},
        }

    top1_text = hyps[0].get("text", "")
    word_confs = [words_with_conf(h.get("tokens") or []) for h in hyps]

    mbr_text, mbr_meta = mbr(hyps)
    vs_text, vs_meta = weighted_vote(hyps, "score", word_confs)
    vc_text, vc_meta = weighted_vote(hyps, "score_x_conf", word_confs)
    safe_text, safe_meta = safe_topk(hyps, word_confs)

    return {
        "hyp_top1": top1_text,
        "hyp_top1_word_confs": list(word_confs[0]),
        "hyp_mbr": {"text": mbr_text, **mbr_meta},
        "hyp_vote_score": {"text": vs_text, **vs_meta},
        "hyp_vote_conf": {"text": vc_text, **vc_meta},
        "hyp_safe": {"text": safe_text, **safe_meta},
        "_word_confs_top1": word_confs[0],  # internal — used by xseg merge below
    }


def run(nbest_path: str, out_path: str, seg_meta_path: Optional[str] = None) -> dict:
    with open(nbest_path) as f:
        nbest = json.load(f)

    aggregated: Dict[str, dict] = {}
    for utt_id, rec in nbest.items():
        aggregated[utt_id] = aggregate_one(rec)

    # Cross-segment merge (Phase 2.5).
    neighbors_map = load_segment_neighbors(seg_meta_path, aggregated)
    no_overlap_count = 0
    for utt_id, agg in aggregated.items():
        nb_list = neighbors_map.get(utt_id, [])
        nbs_resolved = []
        for nb in nb_list:
            nb_agg = aggregated.get(nb["utt_id"])
            if not nb_agg:
                continue
            nbs_resolved.append({
                "utt_id": nb["utt_id"],
                "side": nb["side"],
                "words_with_conf": nb_agg["_word_confs_top1"],
            })
        text, meta = xseg_merge(
            utt_id=utt_id,
            top1_text=agg["hyp_top1"],
            word_confs_top1=agg["_word_confs_top1"],
            neighbors=nbs_resolved,
        )
        if not nbs_resolved or not meta["swaps"]:
            no_overlap_count += 1
        agg["hyp_xseg_merge"] = {"text": text, **meta}

    # Strip internal fields before writing.
    for agg in aggregated.values():
        agg.pop("_word_confs_top1", None)

    with open(out_path, "w") as f:
        json.dump(aggregated, f, indent=2)

    # Summary: how does the per-word confidence distribution shift after each
    # aggregation step? When the consensus is strong, posterior confidences
    # should be substantially higher than top-1's per-word probs.
    method_keys = [
        ("hyp_top1", "hyp_top1_word_confs"),
        ("hyp_mbr", "hyp_mbr"),
        ("hyp_vote_score", "hyp_vote_score"),
        ("hyp_vote_conf", "hyp_vote_conf"),
        ("hyp_safe", "hyp_safe"),
        ("hyp_xseg_merge", "hyp_xseg_merge"),
    ]
    conf_summary: Dict[str, dict] = {}
    for method, key in method_keys:
        all_confs: List[float] = []
        for agg in aggregated.values():
            if key == "hyp_top1_word_confs":
                wcs = agg.get(key) or []
            else:
                wcs = (agg.get(key) or {}).get("word_confs") or []
            for _, p in wcs:
                if p is not None:
                    all_confs.append(float(p))
        if all_confs:
            import statistics
            conf_summary[method] = {
                "n_words": len(all_confs),
                "mean": statistics.fmean(all_confs),
                "median": statistics.median(all_confs),
                "p10": sorted(all_confs)[max(0, len(all_confs) // 10 - 1)],
                "p90": sorted(all_confs)[min(len(all_confs) - 1, int(len(all_confs) * 0.9))],
            }

    summary = {
        "n_segments": len(aggregated),
        "n_with_no_overlap": no_overlap_count,
        "out_path": out_path,
        "per_word_conf_summary": conf_summary,
    }
    return summary


def main():
    ap = argparse.ArgumentParser(description="N-best beam aggregation for VSP-LLM")
    ap.add_argument("--nbest", required=True, help="Path to nbest-{fid}.json")
    ap.add_argument("--out", required=True, help="Path to write aggregated-{fid}.json")
    ap.add_argument("--seg-meta", default=None, help="Optional segment_metadata.json for cross-segment merge")
    args = ap.parse_args()

    summary = run(args.nbest, args.out, args.seg_meta)
    print(f"[nbest_aggregate] wrote {summary['out_path']} "
          f"({summary['n_segments']} segments, "
          f"{summary['n_with_no_overlap']} with no usable cross-segment overlap)")
    cs = summary.get("per_word_conf_summary") or {}
    if cs:
        print(f"\n  Per-word confidence shift after aggregation:")
        print(f"  {'method':<18} {'n_words':>8} {'mean':>7} {'median':>8} {'p10':>7} {'p90':>7}")
        for m in ["hyp_top1", "hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]:
            s = cs.get(m)
            if not s:
                continue
            print(f"  {m:<18} {s['n_words']:>8} {s['mean']:>7.3f} {s['median']:>8.3f} {s['p10']:>7.3f} {s['p90']:>7.3f}")


if __name__ == "__main__":
    main()
