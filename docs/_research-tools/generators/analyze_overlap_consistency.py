#!/usr/bin/env python3
"""Overlap-consistency analysis (Workstream X): did twice-decoded overlap regions help?

The 1,497-segment English baseline set was pre-cut upstream into <=12 s segments
with ~2 s overlap between consecutive segments of the same source video. Every
overlap region was therefore decoded twice. This script measures, against
references:

  1. How often the two decodes of the same overlap region disagree (word level,
     after aligning both segments' overlap spans).
  2. When they disagree, who wins vs the reference (fixed / broke / both-wrong),
     i.e. how often the NEIGHBOR's reading is correct where the primary's is
     wrong -- the direct "did the second reading help" answer.
  3. Re-examination of Mission 6's hyp_xseg_merge on this set (it was a no-op:
     neighbors_considered == 0 for all utts because segment_metadata.json is
     per-video, not the per-utt {video_id,start,end} format the loader expects).
     We SIMULATE what xseg_merge would have done with a correct neighbor map
     (same function, anchored on hyp_top1 + raw word confs, exactly as shipped)
     and score its swaps vs refs.
  4. Evidence for/against an L4 overlap-neighbor candidate layer in the
     phonetic-substitution module (win rates conditional on neighbor conf).

Word positions are approximated uniformly over the segment duration (word i of
n spans [i/n, (i+1)/n] of the segment's time range; a word belongs to the
overlap window if its midpoint falls inside). No word timestamps exist for
these decodes. Two built-in checks bound the approximation error:
  - sensitivity: the overlap window is shrunk/grown +-20% and all rates are
    recomputed;
  - ref-vs-ref calibration: the same window extraction applied to the two
    segments' REFERENCE transcripts (same audio heard twice by Whisper) gives
    an upper bound on achievable agreement under this position approximation.

CPU-only; reads existing artifacts, no decode. Run with the VSP venv:
  /home/ubuntu/vsp-llm-yoad-venv/bin/python analyze_overlap_consistency.py
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.expanduser("~/lib"))

from _alignment import align_word_lists, split_words  # noqa: E402
from nbest_aggregate import xseg_merge  # noqa: E402  (shipped code, reused as-is)

# ---------------------------------------------------------------------------
# Paths (1,497-segment English baseline artifacts)
# ---------------------------------------------------------------------------
SEG_META = os.path.expanduser("~/english_full_results/segment_metadata.json")
HYPO_JSON = os.path.expanduser("~/english_full_nbest_eval/decode_output/hypo-172610.json")
AGG_JSON = os.path.expanduser("~/english_full_nbest_eval/aggregated.json")
REPORT_CSV = os.path.expanduser("~/english_full_nbest_eval/report/report.csv")

UTT_PAT = re.compile(r"^(.*)_(\d{2})_(\d{6})_(\d{6})$")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_all():
    meta = json.load(open(SEG_META))
    hypo = json.load(open(HYPO_JSON))
    agg = json.load(open(AGG_JSON))
    refs = dict(zip(hypo["utt_id"], hypo["ref"]))
    hyps = dict(zip(hypo["utt_id"], hypo["hypo"]))  # == hyp_top1 (verified 1497/1497)
    is_score: Dict[str, float] = {}
    with open(REPORT_CSV) as f:
        for row in csv.DictReader(f):
            try:
                is_score[row["utt_id"]] = float(row["is_score"])
            except (ValueError, KeyError):
                pass
    return meta, refs, hyps, agg, is_score


def build_pairs(meta: dict) -> List[dict]:
    """Consecutive same-video segment pairs with a positive frame overlap.

    Frame numbers in the utt name are in the SOURCE video's native fps; each
    segment's actual duration in seconds is metadata original_duration, so
    fps_est = (end_frame - start_frame) / duration converts the shared frame
    overlap into each segment's local seconds.
    """
    groups: Dict[str, List[Tuple[int, int, int, float, str]]] = defaultdict(list)
    for utt, info in meta.items():
        m = UTT_PAT.match(utt)
        if not m:
            continue
        base, seg, s, e = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        groups[base].append((seg, s, e, float(info["original_duration"]), utt))

    pairs = []
    for base, segs in groups.items():
        segs.sort()
        for (i1, s1, e1, d1, u1), (i2, s2, e2, d2, u2) in zip(segs, segs[1:]):
            if s2 >= e1 or d1 <= 0 or d2 <= 0:
                continue  # no source-frame overlap
            fps1 = (e1 - s1) / d1
            fps2 = (e2 - s2) / d2
            ov_frames = e1 - s2
            pairs.append({
                "base": base,
                "utt_a": u1, "utt_b": u2,
                "dur_a": d1, "dur_b": d2,
                "ov_a": ov_frames / fps1,   # overlap length in A's local seconds
                "ov_b": ov_frames / fps2,   # overlap length in B's local seconds
            })
    return pairs


# ---------------------------------------------------------------------------
# Overlap-span extraction (uniform word-position approximation)
# ---------------------------------------------------------------------------
def overlap_indices(words: List[str], dur: float, ov: float, side: str) -> List[int]:
    """Indices of words whose uniform-position midpoint falls in the overlap
    window: [dur - ov, dur] for the earlier segment ('tail'), [0, ov] for the
    later segment ('head')."""
    n = len(words)
    if n == 0 or dur <= 0 or ov <= 0:
        return []
    out = []
    for i in range(n):
        mid = (i + 0.5) / n * dur
        if side == "tail" and mid >= dur - ov:
            out.append(i)
        elif side == "head" and mid <= ov:
            out.append(i)
    return out


def ref_alignment_flags(ref: str, hyp_words: List[str]) -> List[Tuple[Optional[str], bool]]:
    """Per hyp word: (aligned ref word or None, correct?)."""
    rs = ref.strip().lower().split()
    pairs = align_word_lists(rs, [w.lower() for w in hyp_words])
    out: List[Tuple[Optional[str], bool]] = [(None, False)] * len(hyp_words)
    for ri, hi in pairs:
        if hi < 0:
            continue
        if ri >= 0:
            out[hi] = (rs[ri], rs[ri] == hyp_words[hi].strip().lower())
    return out


# ---------------------------------------------------------------------------
# Core analysis for one text source (top1 or mbr)
# ---------------------------------------------------------------------------
def analyze(pairs, texts, confs, refs, is_score, scale=1.0, collect_examples=False,
            agree_map=None):
    """texts: {utt: str}; confs: {utt: {word_index: conf}} or None;
    agree_map: {utt: [per-word beam agreement]} aligned to the same words."""
    stats = Counter()
    per_tier = defaultdict(Counter)   # rescue rates keyed by primary segment NIV bucket
    conf_cond = Counter()             # xseg-rule conditioning (nb_conf > self_conf)
    rescue_positions = []             # (primary_utt, word_idx, winning_word) for part-3 capture
    examples = []
    pairs_with_alignment = 0

    for p in pairs:
        ua, ub = p["utt_a"], p["utt_b"]
        wa, wb = split_words(texts.get(ua, "")), split_words(texts.get(ub, ""))
        ia = overlap_indices(wa, p["dur_a"], p["ov_a"] * scale, "tail")
        ib = overlap_indices(wb, p["dur_b"], p["ov_b"] * scale, "head")
        A = [wa[i] for i in ia]
        B = [wb[i] for i in ib]
        stats["ov_words_a"] += len(A)
        stats["ov_words_b"] += len(B)
        if not A or not B:
            stats["pairs_empty_span"] += 1
            continue
        pairs_with_alignment += 1

        flags_a = ref_alignment_flags(refs.get(ua, ""), wa)
        flags_b = ref_alignment_flags(refs.get(ub, ""), wb)

        al = align_word_lists(A, B)
        pair_ex = {"base": p["base"], "utt_a": ua, "utt_b": ub, "rows": [],
                   "A": A, "B": B,
                   "ref_a_tail": None, "ref_b_head": None}
        for si, ni in al:
            if si < 0 or ni < 0:
                stats["gaps"] += 1
                continue
            stats["aligned_pairs"] += 1
            a_w, b_w = A[si], B[ni]
            a_idx, b_idx = ia[si], ib[ni]
            a_ref, a_ok = flags_a[a_idx]
            b_ref, b_ok = flags_b[b_idx]
            agree = a_w.strip().lower() == b_w.strip().lower()
            if agree:
                stats["agree"] += 1
            else:
                stats["disagree"] += 1
                if a_ok and not b_ok:
                    stats["dis_a_right"] += 1
                elif b_ok and not a_ok:
                    stats["dis_b_right"] += 1
                elif not a_ok and not b_ok:
                    stats["dis_both_wrong"] += 1
                else:
                    stats["dis_both_right"] += 1
                if confs is not None:
                    ca = confs.get(ua, {}).get(a_idx)
                    cb = confs.get(ub, {}).get(b_idx)
                    if ca is not None and cb is not None:
                        # directed instances: (primary, neighbor) both ways —
                        # mirrors how xseg / an L4 layer would run per segment
                        for pc, nc, p_ok, n_ok in ((ca, cb, a_ok, b_ok), (cb, ca, b_ok, a_ok)):
                            key = "nbconf_higher" if nc > pc else "nbconf_lower"
                            conf_cond[key] += 1
                            if n_ok and not p_ok:
                                conf_cond[key + "_nb_right"] += 1
                            if p_ok and not n_ok:
                                conf_cond[key + "_self_right"] += 1
                            # L4-rule slice: neighbor word at green-level conf
                            for thr, tag in ((0.90, "nb90"), (0.95, "nb95")):
                                if nc >= thr:
                                    conf_cond[tag] += 1
                                    if n_ok and not p_ok:
                                        conf_cond[tag + "_nb_right"] += 1
                                    if p_ok and not n_ok:
                                        conf_cond[tag + "_self_right"] += 1
                        # production green band: conf >= 0.95 AND agreement >= 0.80
                        if agree_map is not None:
                            for n_utt, n_idx, nc, p_ok, n_ok in (
                                    (ub, b_idx, cb, a_ok, b_ok),
                                    (ua, a_idx, ca, b_ok, a_ok)):
                                ag_list = agree_map.get(n_utt, [])
                                ag = ag_list[n_idx] if n_idx < len(ag_list) else None
                                if ag is not None and nc >= 0.95 and ag >= 0.80:
                                    conf_cond["nbgreen"] += 1
                                    if n_ok and not p_ok:
                                        conf_cond["nbgreen_nb_right"] += 1
                                    if p_ok and not n_ok:
                                        conf_cond["nbgreen_self_right"] += 1
                if collect_examples:
                    pair_ex["rows"].append({
                        "a_word": a_w, "b_word": b_w,
                        "a_ref": a_ref, "b_ref": b_ref,
                        "a_ok": a_ok, "b_ok": b_ok,
                        "a_idx": a_idx, "b_idx": b_idx,
                    })
            # "did the neighbor help" per direction. Denominator: primary word
            # wrong at an aligned overlap position. A rescue requires the
            # neighbor's word to DIFFER and be correct (an identical word,
            # right or wrong, offers nothing new).
            if not a_ok:
                stats["a_wrong"] += 1
                if b_ok and not agree:
                    stats["a_wrong_b_right"] += 1
                    rescue_positions.append((ua, a_idx, b_w))
                    per_tier[niv_bucket(is_score.get(ua))]["rescued"] += 1
                per_tier[niv_bucket(is_score.get(ua))]["wrong"] += 1
            if not b_ok:
                stats["b_wrong"] += 1
                if a_ok and not agree:
                    stats["b_wrong_a_right"] += 1
                    rescue_positions.append((ub, b_idx, a_w))
                    per_tier[niv_bucket(is_score.get(ub))]["rescued"] += 1
                per_tier[niv_bucket(is_score.get(ub))]["wrong"] += 1
        if collect_examples and pair_ex["rows"]:
            # attach the reference words in the same windows for display
            ra = refs.get(ua, "").strip().split()
            rb = refs.get(ub, "").strip().split()
            ira = overlap_indices(ra, p["dur_a"], p["ov_a"] * scale, "tail")
            irb = overlap_indices(rb, p["dur_b"], p["ov_b"] * scale, "head")
            pair_ex["ref_a_tail"] = " ".join(ra[i] for i in ira)
            pair_ex["ref_b_head"] = " ".join(rb[i] for i in irb)
            examples.append(pair_ex)

    stats["pairs_with_alignment"] = pairs_with_alignment
    return stats, per_tier, conf_cond, rescue_positions, examples


def niv_bucket(is_val: Optional[float]) -> str:
    if is_val is None:
        return "unknown"
    if is_val >= 3.80:
        return "Y (IS>=3.80)"
    if is_val >= 2.00:
        return "P (2.00<=IS<3.80)"
    return "N (IS<2.00)"


# ---------------------------------------------------------------------------
# Ref-vs-ref calibration (upper bound for the position approximation)
# ---------------------------------------------------------------------------
def ref_ref_agreement(pairs, refs, scale=1.0):
    agree = paired = gaps = 0
    for p in pairs:
        ra = refs.get(p["utt_a"], "").strip().split()
        rb = refs.get(p["utt_b"], "").strip().split()
        ia = overlap_indices(ra, p["dur_a"], p["ov_a"] * scale, "tail")
        ib = overlap_indices(rb, p["dur_b"], p["ov_b"] * scale, "head")
        A, B = [ra[i] for i in ia], [rb[i] for i in ib]
        if not A or not B:
            continue
        for si, ni in align_word_lists(A, B):
            if si < 0 or ni < 0:
                gaps += 1
                continue
            paired += 1
            if A[si].lower() == B[ni].lower():
                agree += 1
    return agree, paired, gaps


# ---------------------------------------------------------------------------
# Part 3: simulate the shipped xseg_merge with a correct neighbor map
# ---------------------------------------------------------------------------
def simulate_xseg(pairs, agg, refs):
    """Run lib/nbest_aggregate.py::xseg_merge exactly as shipped (top1 anchor,
    raw word confs, LCS>=3 gate, conf-comparison swap rule) with the neighbor
    map segment_metadata.json failed to provide."""
    wc = {u: [(w, c) for w, c in agg[u]["hyp_top1_word_confs"]] for u in agg}
    # true overlap window per utt (for the swaps-inside-window diagnostic)
    window = {}
    for p in pairs:
        window[p["utt_a"]] = ("tail", p["dur_a"], p["ov_a"])
        window[p["utt_b"]] = ("head", p["dur_b"], p["ov_b"])
    results = {"swaps": [], "pairs_gated_out": 0, "pairs_fired": 0}
    seen_edges = set()
    for p in pairs:
        ua, ub = p["utt_a"], p["utt_b"]
        for self_u, nb_u, side in ((ua, ub, "next"), (ub, ua, "prev")):
            neighbors = [{"utt_id": nb_u, "side": side, "words_with_conf": wc[nb_u]}]
            merged, meta = xseg_merge(self_u, agg[self_u]["hyp_top1"], wc[self_u], neighbors)
            edge = (self_u, nb_u)
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            if meta["swaps"]:
                results["pairs_fired"] += 1
            else:
                # distinguish 'gate blocked' from 'no conf-favoured disagreement'
                self_words = [w for w, _ in wc[self_u]]
                nb_words = [w for w, _ in wc[nb_u]]
                from nbest_aggregate import _lcs_length, XSEG_MIN_OVERLAP
                if side == "next":
                    se = self_words[-min(len(self_words), 60):]
                    ne = nb_words[:min(len(nb_words), 60)]
                else:
                    se = self_words[:min(len(self_words), 60)]
                    ne = nb_words[-min(len(nb_words), 60):]
                if _lcs_length(se, ne) < XSEG_MIN_OVERLAP:
                    results["pairs_gated_out"] += 1
            for sw in meta["swaps"]:
                sw = dict(sw)
                sw["self_utt"] = self_u
                results["swaps"].append(sw)
    # score swaps vs the segment's own ref (alignment on the ORIGINAL top1)
    fixed = broke = neutral = in_window = 0
    scored = []
    for sw in results["swaps"]:
        u = sw["self_utt"]
        words = [w for w, _ in agg[u]["hyp_top1_word_confs"]]
        side, dur, ov = window[u]
        if sw["pos"] in overlap_indices(words, dur, ov, side):
            in_window += 1
            sw["in_window"] = True
        else:
            sw["in_window"] = False
        flags = ref_alignment_flags(refs.get(u, ""), words)
        ref_w, _ = flags[sw["pos"]]
        frm = sw["from"].strip().lower()
        to = sw["to"].strip().lower()
        if ref_w is None:
            verdict = "neutral"       # hyp word aligned to a gap: both unmatched
        elif to == ref_w and frm != ref_w:
            verdict = "fixed"
        elif frm == ref_w and to != ref_w:
            verdict = "broke"
        else:
            verdict = "neutral"
        if verdict == "fixed":
            fixed += 1
        elif verdict == "broke":
            broke += 1
        else:
            neutral += 1
        scored.append({**sw, "ref_word": ref_w, "verdict": verdict})
    results.update({"fixed": fixed, "broke": broke, "neutral": neutral,
                    "in_window": in_window, "scored": scored})
    return results


def xseg_capture(rescues, scored_swaps):
    """Of the part-2 'neighbor right where primary wrong' positions, how many
    does simulated xseg swap to the winning word?"""
    swap_map = {(s["self_utt"], s["pos"]): s["to"].strip().lower() for s in scored_swaps}
    captured = 0
    for utt, idx, win_word in rescues:
        if swap_map.get((utt, idx)) == win_word.strip().lower():
            captured += 1
    return captured, len(rescues)


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------
def pct(a, b):
    return f"{100.0 * a / b:.1f}%" if b else "n/a"


def print_stats(label, stats, per_tier, conf_cond):
    ap, ag, dis = stats["aligned_pairs"], stats["agree"], stats["disagree"]
    print(f"\n== {label} ==")
    print(f"  pairs with non-empty spans: {stats['pairs_with_alignment']}")
    print(f"  overlap words: A={stats['ov_words_a']}  B={stats['ov_words_b']}")
    print(f"  aligned word pairs: {ap}  (gaps: {stats['gaps']})")
    print(f"  agree: {ag} ({pct(ag, ap)})   disagree: {dis} ({pct(dis, ap)})")
    print(f"  disagreements: A-right/B-wrong {stats['dis_a_right']} ({pct(stats['dis_a_right'], dis)}), "
          f"B-right/A-wrong {stats['dis_b_right']} ({pct(stats['dis_b_right'], dis)}), "
          f"both-wrong {stats['dis_both_wrong']} ({pct(stats['dis_both_wrong'], dis)}), "
          f"both-right {stats['dis_both_right']} ({pct(stats['dis_both_right'], dis)})")
    print(f"  neighbor-rescue: A wrong {stats['a_wrong']} -> B right {stats['a_wrong_b_right']} "
          f"({pct(stats['a_wrong_b_right'], stats['a_wrong'])})")
    print(f"                   B wrong {stats['b_wrong']} -> A right {stats['b_wrong_a_right']} "
          f"({pct(stats['b_wrong_a_right'], stats['b_wrong'])})")
    both_wrong = stats["a_wrong"] + stats["b_wrong"]
    both_rescued = stats["a_wrong_b_right"] + stats["b_wrong_a_right"]
    print(f"  pooled rescue rate: {both_rescued}/{both_wrong} ({pct(both_rescued, both_wrong)})")
    if per_tier:
        print("  rescue rate by primary segment NIV bucket:")
        for tier in sorted(per_tier):
            c = per_tier[tier]
            print(f"    {tier:22s}: {c['rescued']}/{c['wrong']} ({pct(c['rescued'], c['wrong'])})")
    if conf_cond:
        print("  conf-conditioned directed disagreements (2 per aligned pair; both confs known):")
        for key, lab in (("nbconf_higher", "nb_conf > self_conf (xseg swap rule)"),
                         ("nbconf_lower", "nb_conf <= self_conf (xseg keeps self)"),
                         ("nb90", "nb_conf >= 0.90"),
                         ("nb95", "nb_conf >= 0.95 (green level)"),
                         ("nbgreen", "nb GREEN band (conf>=0.95 AND agree>=0.80)")):
            if key == "nbgreen" and key not in conf_cond:
                continue
            n = conf_cond[key]
            print(f"    {lab}: n={n}  neighbor right {conf_cond[key + '_nb_right']} "
                  f"({pct(conf_cond[key + '_nb_right'], n)}), self right {conf_cond[key + '_self_right']} "
                  f"({pct(conf_cond[key + '_self_right'], n)}), "
                  f"neither {n - conf_cond[key + '_nb_right'] - conf_cond[key + '_self_right']} "
                  f"({pct(n - conf_cond[key + '_nb_right'] - conf_cond[key + '_self_right'], n)})")


def spot_check(pairs, texts, refs, n=5, seed=13):
    rng = random.Random(seed)
    sample = rng.sample(pairs, min(n, len(pairs)))
    print("\n== SPOT CHECK: segment A tail vs segment B head (raw, last/first 12 words) ==")
    for p in sample:
        wa, wb = split_words(texts[p["utt_a"]]), split_words(texts[p["utt_b"]])
        ra, rb = refs[p["utt_a"]].split(), refs[p["utt_b"]].split()
        print(f"\n  video: {p['base']}")
        print(f"    A={p['utt_a']} dur={p['dur_a']:.2f}s   B={p['utt_b']} dur={p['dur_b']:.2f}s   "
              f"overlap={p['ov_a']:.2f}s (A-local) / {p['ov_b']:.2f}s (B-local)")
        print(f"    A hyp tail : {' '.join(wa[-12:])}")
        print(f"    B hyp head : {' '.join(wb[:12])}")
        print(f"    A ref tail : {' '.join(ra[-12:])}")
        print(f"    B ref head : {' '.join(rb[:12])}")


def print_examples(examples, k=8, seed=7):
    rng = random.Random(seed)
    ex = [e for e in examples if any((r["a_ok"] != r["b_ok"]) for r in e["rows"])]
    rng.shuffle(ex)
    print(f"\n== EXAMPLES (disagreeing overlap spans with a winner; {min(k, len(ex))} of {len(ex)}) ==")
    for e in ex[:k]:
        print(f"\n  video: {e['base']}")
        print(f"    A ({e['utt_a']}) overlap span: {' '.join(e['A'])}")
        print(f"    B ({e['utt_b']}) overlap span: {' '.join(e['B'])}")
        print(f"    ref (A tail window): {e['ref_a_tail']}")
        print(f"    ref (B head window): {e['ref_b_head']}")
        for r in e["rows"]:
            who = ("A right" if r["a_ok"] and not r["b_ok"] else
                   "B right" if r["b_ok"] and not r["a_ok"] else
                   "both right" if r["a_ok"] else "both wrong")
            print(f"      A:'{r['a_word']}' vs B:'{r['b_word']}'  refA:'{r['a_ref']}' refB:'{r['b_ref']}'  -> {who}")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--examples", type=int, default=8, help="disagreement examples to print")
    ap.add_argument("--spot-check", type=int, default=5, help="videos for the raw tail/head spot check")
    args = ap.parse_args()

    meta, refs, hyps, agg, is_score = load_all()
    pairs = build_pairs(meta)
    n_multi_utts = len({u for p in pairs for u in (p["utt_a"], p["utt_b"])})
    print(f"videos: {len({UTT_PAT.match(u).group(1) for u in meta})} | utts: {len(meta)} | "
          f"overlapping consecutive pairs: {len(pairs)} | utts in a pair: {n_multi_utts}")
    ovs = [p["ov_a"] for p in pairs]
    print(f"overlap secs (A-local): mean {sum(ovs)/len(ovs):.2f}, min {min(ovs):.2f}, max {max(ovs):.2f}")
    dur_b = sorted(p["dur_b"] for p in pairs)
    print(f"B-segment durations: median {dur_b[len(dur_b)//2]:.2f}s, "
          f"<6s: {sum(1 for d in dur_b if d < 6)}/{len(dur_b)} "
          f"(B is the short remainder cut; its 2 s overlap is a large share of it)")

    # coverage framing: what fraction of the whole set's words sit in an
    # overlap window at all (bounds any possible benefit)
    total_words = sum(len(split_words(h)) for h in hyps.values())
    ov_words = 0
    for p in pairs:
        for u, side, dur, ov in ((p["utt_a"], "tail", p["dur_a"], p["ov_a"]),
                                 (p["utt_b"], "head", p["dur_b"], p["ov_b"])):
            ov_words += len(overlap_indices(split_words(hyps[u]), dur, ov, side))
    print(f"coverage: {ov_words} of {total_words} hyp words ({pct(ov_words, total_words)}) "
          f"lie in any overlap window")

    # sanity: xseg no-op on disk
    nc = Counter(v["hyp_xseg_merge"].get("neighbors_considered", 0) for v in agg.values())
    n_sw = sum(len(v["hyp_xseg_merge"].get("swaps", [])) for v in agg.values())
    same_top1 = sum(1 for v in agg.values() if v["hyp_xseg_merge"]["text"] == v["hyp_top1"])
    print(f"\nON-DISK hyp_xseg_merge: neighbors_considered dist {dict(nc)}, total swaps {n_sw}, "
          f"text==hyp_top1 for {same_top1}/{len(agg)}  -> shipped merge was a NO-OP on this set")

    # ref-vs-ref calibration
    for sc in (0.8, 1.0, 1.2):
        agr, npair, gaps = ref_ref_agreement(pairs, refs, scale=sc)
        print(f"ref-vs-ref overlap agreement @ window x{sc}: {agr}/{npair} ({pct(agr, npair)}), gaps {gaps}")

    # confidences: raw top1 word confs by word index
    confs = {}
    for u, v in agg.items():
        confs[u] = {i: (c if c is not None else 0.0) for i, (w, c) in enumerate(v["hyp_top1_word_confs"])}

    # per-word beam agreement for the top-1 words (green-band conditioning)
    agree_path = os.path.expanduser(
        "~/english_full_nbest_eval/decode_output/agreement-172610.json")
    agree_map = json.load(open(agree_path)) if os.path.isfile(agree_path) else None

    # main analysis on hyp_top1 (the actual decode; anchor of xseg) + sensitivity
    rescues_main = None
    examples_main = None
    for sc in (0.8, 1.0, 1.2):
        stats, per_tier, conf_cond, rescues, examples = analyze(
            pairs, hyps, confs, refs, is_score, scale=sc, collect_examples=(sc == 1.0),
            agree_map=agree_map if sc == 1.0 else None)
        print_stats(f"hyp_top1, overlap window x{sc}", stats,
                    per_tier if sc == 1.0 else {}, conf_cond if sc == 1.0 else {})
        if sc == 1.0:
            rescues_main, examples_main = rescues, examples

    # secondary: production display text (hyp_mbr)
    mbr_texts = {u: v["hyp_mbr"]["text"] for u, v in agg.items()}
    mbr_confs = {u: {i: (c if c is not None else 0.0)
                     for i, (w, c) in enumerate(v["hyp_mbr"].get("word_confs", []))}
                 for u, v in agg.items()}
    stats, per_tier, conf_cond, _, _ = analyze(pairs, mbr_texts, mbr_confs, refs, is_score, scale=1.0)
    print_stats("hyp_mbr (production display text), overlap window x1.0", stats, {}, conf_cond)

    # part 3: simulate xseg_merge with a correct neighbor map
    sim = simulate_xseg(pairs, agg, refs)
    print("\n== SIMULATED xseg_merge (shipped function, corrected neighbor map) ==")
    print(f"  directed edges: {2 * len(pairs)}  fired (>=1 swap): {sim['pairs_fired']}  "
          f"LCS<3 gated out: {sim['pairs_gated_out']}  "
          f"no-swap-but-gate-passed: {2 * len(pairs) - sim['pairs_fired'] - sim['pairs_gated_out']}")
    print(f"  swaps: {len(sim['swaps'])}  fixed {sim['fixed']}, broke {sim['broke']}, neutral {sim['neutral']}")
    print(f"  swaps inside the true ~2 s overlap window: {sim['in_window']}/{len(sim['swaps'])} "
          f"({pct(sim['in_window'], len(sim['swaps']))}) — the 60-word edge alignment swaps far outside the overlap")
    inw = [s for s in sim["scored"] if s["in_window"]]
    if inw:
        f_in = sum(1 for s in inw if s["verdict"] == "fixed")
        b_in = sum(1 for s in inw if s["verdict"] == "broke")
        print(f"  in-window swaps only: {len(inw)}  fixed {f_in}, broke {b_in}, neutral {len(inw) - f_in - b_in}")
    cap, tot = xseg_capture(rescues_main, sim["scored"])
    print(f"  capture of part-2 neighbor-rescue positions: {cap}/{tot} ({pct(cap, tot)})")
    if sim["scored"]:
        print("  swap examples:")
        for s in sim["scored"][:8]:
            print(f"    {s['self_utt']}: pos {s['pos']} '{s['from']}' -> '{s['to']}' "
                  f"(self {s['self_conf']:.2f} vs nb {s['nb_conf']:.2f}) ref='{s['ref_word']}' [{s['verdict']}]")

    if args.spot_check:
        spot_check(pairs, hyps, refs, n=args.spot_check)
    if args.examples:
        print_examples(examples_main, k=args.examples)


if __name__ == "__main__":
    main()
