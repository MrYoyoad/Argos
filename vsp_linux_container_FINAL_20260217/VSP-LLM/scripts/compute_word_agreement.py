"""Per-word beam-agreement sidecar.

For each utterance in nbest-{fid}.json, computes the fraction of the other
beams that emit the same word as top-1 at each top-1 position (after
edit-distance alignment). Emits a JSON shaped as
``{utt_id: [agreement_per_word, ...]}`` aligned to the top-1 word order
returned by ``_word_confs_for_utt`` on the matching confidence-{fid}.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

# Reuse the diagnostic helpers — do NOT reimplement.
_GEN = Path(__file__).resolve().parent.parent.parent / "docs" / "_research-tools" / "generators"
sys.path.insert(0, str(_GEN))
from _alignment import align_word_lists, split_words  # noqa: E402
from analyze_beam_variance import _word_confs_for_utt  # noqa: E402


def beam_agreement_per_position(top1_words: List[str], beam_words_list: List[List[str]]) -> List[float]:
    """Fraction of non-top-1 beams whose aligned position emits the same word."""
    n = len(top1_words)
    if n == 0:
        return []
    counts = [0] * n
    other_beams = beam_words_list[1:]
    n_beams = len(other_beams)
    if n_beams == 0:
        return [1.0] * n
    top1_lc = [w.lower() for w in top1_words]
    for beam in other_beams:
        if not beam:
            continue
        pairs = align_word_lists(top1_lc, [w.lower() for w in beam])
        for ti, bi in pairs:
            if ti < 0 or bi < 0:
                continue
            if top1_lc[ti] == beam[bi].lower():
                counts[ti] += 1
    return [c / n_beams for c in counts]


def compute_agreement(nbest: Dict[str, dict], conf: Dict[str, dict]) -> Dict[str, List[float]]:
    """Return {utt_id: [agreement_per_word, ...]} aligned to confidence-derived word order."""
    out: Dict[str, List[float]] = {}
    for utt_id, rec in nbest.items():
        hyps = rec.get("hypotheses") or []
        if not hyps:
            out[utt_id] = []
            continue
        nbest_top1_words = split_words(hyps[0].get("text", ""))
        beam_words_list = [split_words(h.get("text", "")) for h in hyps]
        nbest_agreement = beam_agreement_per_position(nbest_top1_words, beam_words_list)

        # Align to the confidence-derived word order (what compute_word_confidence emits)
        # so the consumer can index by position 1:1. The two lists usually match in
        # length but may differ on rare whitespace edge cases — align by edit distance.
        conf_words = [w for w, _ in _word_confs_for_utt(conf.get(utt_id))]
        if not conf_words:
            out[utt_id] = []
            continue
        if not nbest_top1_words:
            out[utt_id] = [1.0] * len(conf_words)
            continue
        pairs = align_word_lists(
            [w.lower() for w in conf_words],
            [w.lower() for w in nbest_top1_words],
        )
        agree = [None] * len(conf_words)
        for ci, ni in pairs:
            if ci < 0 or ni < 0:
                continue
            if ni < len(nbest_agreement):
                agree[ci] = nbest_agreement[ni]
        # Fill any unaligned slots with 0.0 (no support found)
        out[utt_id] = [float(a) if a is not None else 0.0 for a in agree]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nbest", required=True, help="nbest-{fid}.json from decode")
    ap.add_argument("--confidence", required=True, help="confidence-{fid}.json from decode")
    ap.add_argument("--out", required=True, help="output agreement-{fid}.json path")
    args = ap.parse_args()

    nbest = json.loads(Path(args.nbest).read_text(encoding="utf-8"))
    conf = json.loads(Path(args.confidence).read_text(encoding="utf-8"))
    agreement = compute_agreement(nbest, conf)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(agreement, f, indent=2, ensure_ascii=False)
    n_words = sum(len(v) for v in agreement.values())
    print(f"Wrote {out_path} ({len(agreement)} segments, {n_words} words)")


if __name__ == "__main__":
    main()
