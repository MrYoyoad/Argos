"""MBR-anchored per-word confidence sidecar (word_confidence_mbr.json).

Production display method is ``hyp_mbr`` (May 2 2026), but the pipeline's
``word_confidence.json`` is anchored on the TOP-1 text. This tool re-anchors
per-word probability + beam agreement + joint band on the **MBR display
words**, so downstream consumers (subtitle videos, transcript HTML, phonetic
substitution) can swap the sidecar file 1:1.

Inputs
  --aggregated  aggregated.json from lib/nbest_aggregate.py
                (uses hyp_mbr.text, hyp_mbr.word_confs — near-Bayesian
                posteriors from the chosen beam's own tokens — plus
                hyp_mbr.word_confs_calibrated if present, and rank_chosen)
  --nbest       nbest-{fid}.json from decode (all beams w/ sequence_score)
  --out         output word_confidence_mbr.json

Per-word beam agreement is recomputed anchored on the MBR words: each of the
OTHER beams (all hypotheses except ``rank_chosen``) is aligned to the MBR word
list and we count the fraction that emit the same word at the aligned
position. Semantics mirror compute_word_agreement.beam_agreement_per_position
exactly (same tokenization via _alignment.split_words, same lowercased
comparison, empty beams stay in the denominator, no-other-beams -> 1.0).

Band rule is the existing joint conf+agreement rule (classify_joint):
green iff prob>=0.95 AND agreement>=0.80; yellow iff >=0.65 AND >=0.50;
else red; numerics never green. Segments missing from the nbest file get
agreement=None per word, which classify_joint resolves to the plain
prob-only classify() fallback — same behavior as compute_word_confidence.py.

Output schema mirrors word_confidence.json so consumers can swap files:
  {utt_id: {sequence_score,            # copied from the chosen beam, else null
            words: [{word, prob, conf_class, agreement, is_numeric
                     [, prob_calibrated]}],
            summary: {max_word_prob, min_word_prob, mean_word_prob,
                      n_words, n_high, n_med, n_low}}}

Run with the VSP venv python: /home/ubuntu/vsp-llm-yoad-venv/bin/python
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Reused primitives (NOT reimplemented) ────────────────────────────────────
# Layout-aware path setup: EC2 dev tree first, container tree as fallback.
_VSP_SCRIPTS_CANDIDATES = [
    Path("/home/ubuntu/VSP-LLM/scripts"),
    Path("/workspace/VSP-LLM/scripts"),
]
_GEN_CANDIDATES = [
    Path("/home/ubuntu/docs/_research-tools/generators"),
    Path("/workspace/VSP-LLM/scripts"),
]
_VSP_SCRIPTS = next((p for p in _VSP_SCRIPTS_CANDIDATES if p.is_dir()), None)
_GEN = next((p for p in _GEN_CANDIDATES if p.is_dir()), None)
if _VSP_SCRIPTS is None:
    sys.exit("make_word_confidence_mbr: cannot locate VSP-LLM/scripts")
for _p in (_GEN, _VSP_SCRIPTS):
    if _p is not None and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# compute_word_agreement self-inserts the generators dir for its own imports
# (_alignment, analyze_beam_variance); beam_agreement_per_position carries the
# canonical alignment semantics for "fraction of other beams that agree".
from compute_word_agreement import beam_agreement_per_position  # noqa: E402
from _alignment import split_words  # noqa: E402

# compute_word_confidence.py exists BOTH in VSP-LLM/scripts (canonical, has
# classify_joint) and in docs/_research-tools/generators (an older prob-only
# copy). compute_word_agreement pushes the generators dir to the front of
# sys.path, so a bare import would pick the stale copy — pin by file path.
_cwc_spec = importlib.util.spec_from_file_location(
    "_cwc_pinned", str(_VSP_SCRIPTS / "compute_word_confidence.py"))
_cwc = importlib.util.module_from_spec(_cwc_spec)
_cwc_spec.loader.exec_module(_cwc)
classify_joint = _cwc.classify_joint
is_numeric = _cwc.is_numeric


def _zeros_summary() -> dict:
    return {
        "max_word_prob": None,
        "min_word_prob": None,
        "mean_word_prob": None,
        "n_words": 0,
        "n_high": 0,
        "n_med": 0,
        "n_low": 0,
    }


def _summarize(words: List[dict]) -> dict:
    """Mirror compute_word_confidence.aggregate_segment_records' summary."""
    probs = [w["prob"] for w in words if w["prob"] is not None]
    return {
        "max_word_prob": max(probs) if probs else None,
        "min_word_prob": min(probs) if probs else None,
        "mean_word_prob": (sum(probs) / len(probs)) if probs else None,
        "n_words": len(words),
        "n_high": sum(1 for w in words if w["conf_class"] == "conf-high"),
        "n_med": sum(1 for w in words if w["conf_class"] == "conf-med"),
        "n_low": sum(1 for w in words if w["conf_class"] == "conf-low"),
    }


def _probs_for_words(
    words: List[str],
    word_confs: List,
    utt_id: str,
    label: str,
    stats: Dict[str, int],
    examples: List[str],
) -> List[Optional[float]]:
    """Map word_confs ([word, prob] pairs) onto the split display words.

    word_confs comes from the chosen beam's token grouping and the display
    text from the same beam's decoded string — they match 1:1 in practice.
    If they don't (length or spelling drift), log and best-effort zip by
    position.
    """
    conf_words = [str(w) for w, _ in word_confs]
    probs = [None if p is None else float(p) for _, p in word_confs]
    misaligned = (len(conf_words) != len(words)) or any(
        cw.strip().lower() != w.strip().lower()
        for cw, w in zip(conf_words, words)
    )
    if misaligned:
        stats[f"misaligned_{label}"] = stats.get(f"misaligned_{label}", 0) + 1
        if len(examples) < 5:
            examples.append(
                f"  [{label}] {utt_id}: text has {len(words)} words, "
                f"word_confs has {len(conf_words)}: "
                f"text={words[:8]}... confs={conf_words[:8]}..."
            )
    return [probs[i] if i < len(probs) else None for i in range(len(words))]


def build_segment(
    utt_id: str,
    mbr: dict,
    nbest_rec: Optional[dict],
    stats: Dict[str, int],
    examples: List[str],
) -> dict:
    text = mbr.get("text") or ""
    words = split_words(text)
    hyps = (nbest_rec or {}).get("hypotheses") or []
    rank_chosen = mbr.get("rank_chosen", -1)
    chosen = next((h for h in hyps if h.get("rank") == rank_chosen), None)
    seq_score = chosen.get("sequence_score") if chosen else None

    if not words:
        stats["empty"] = stats.get("empty", 0) + 1
        return {"sequence_score": seq_score, "words": [], "summary": _zeros_summary()}

    # Raw (and, when present, calibrated) per-word posteriors from hyp_mbr.
    probs = _probs_for_words(
        words, mbr.get("word_confs") or [], utt_id, "raw", stats, examples)
    wc_cal = mbr.get("word_confs_calibrated")
    probs_cal = (
        _probs_for_words(words, wc_cal, utt_id, "cal", stats, examples)
        if wc_cal else None
    )

    # Beam agreement anchored on the MBR words. "Other beams" = every
    # hypothesis except the one MBR chose. beam_agreement_per_position treats
    # element 0 of its beam list as "self" and scores against the rest, so we
    # pass the MBR words as the self slot.
    if not hyps:
        stats["missing_from_nbest"] = stats.get("missing_from_nbest", 0) + 1
        agreements: List[Optional[float]] = [None] * len(words)
    else:
        other_beams = [
            split_words(h.get("text", ""))
            for h in hyps
            if h.get("rank") != rank_chosen
        ]
        agreements = beam_agreement_per_position(words, [words] + other_beams)

    out_words: List[dict] = []
    for i, w in enumerate(words):
        p = probs[i]
        a = agreements[i]
        num = is_numeric(w)
        entry = {
            "word": w,
            "prob": p,
            "conf_class": classify_joint(p, a, num),
            "agreement": a,
            "is_numeric": num,
        }
        if probs_cal is not None and probs_cal[i] is not None:
            entry["prob_calibrated"] = probs_cal[i]
        out_words.append(entry)

    return {
        "sequence_score": seq_score,
        "words": out_words,
        "summary": _summarize(out_words),
    }


def run(aggregated_path: str, nbest_path: str, out_path: str) -> dict:
    with open(aggregated_path, encoding="utf-8") as f:
        aggregated = json.load(f)
    with open(nbest_path, encoding="utf-8") as f:
        nbest = json.load(f)

    stats: Dict[str, int] = {}
    examples: List[str] = []
    out: Dict[str, dict] = {}
    for utt_id, agg in aggregated.items():
        mbr = agg.get("hyp_mbr") or {}
        out[utt_id] = build_segment(utt_id, mbr, nbest.get(utt_id), stats, examples)
    del nbest  # the 1497 nbest is ~387 MB on disk — free before writing

    op = Path(out_path)
    op.parent.mkdir(parents=True, exist_ok=True)
    with op.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    n_words = sum(len(v["words"]) for v in out.values())
    bands = {"conf-high": 0, "conf-med": 0, "conf-low": 0, "conf-unknown": 0}
    for v in out.values():
        for w in v["words"]:
            bands[w["conf_class"]] = bands.get(w["conf_class"], 0) + 1
    summary = {
        "out": str(op),
        "n_segments": len(out),
        "n_words": n_words,
        "bands": bands,
        **stats,
    }
    print(f"[word_confidence_mbr] wrote {op} "
          f"({len(out)} segments, {n_words} words)")
    print(f"  bands: high={bands['conf-high']} med={bands['conf-med']} "
          f"low={bands['conf-low']} unknown={bands['conf-unknown']}")
    for key in ("empty", "missing_from_nbest", "misaligned_raw", "misaligned_cal"):
        if stats.get(key):
            print(f"  {key}: {stats[key]}")
    for line in examples:
        print(line)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aggregated", required=True,
                    help="aggregated.json from lib/nbest_aggregate.py")
    ap.add_argument("--nbest", required=True,
                    help="nbest-{fid}.json from decode")
    ap.add_argument("--out", required=True,
                    help="output word_confidence_mbr.json path")
    args = ap.parse_args()
    run(args.aggregated, args.nbest, args.out)


if __name__ == "__main__":
    main()
