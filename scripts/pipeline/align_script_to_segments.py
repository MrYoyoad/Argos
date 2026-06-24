#!/usr/bin/env python3
"""Attach a known dialogue script to decoded stream segments as scoring references.

The footage has no audio, so we cannot Whisper-align. Instead we exploit two facts: (1) the
script is an ordered, strictly-alternating two-character dialogue, and (2) the model's lip-read
hypotheses, though noisy, follow the same temporal order. We monotonically align the SEGMENT
sequence to the SCRIPT-TURN sequence (global Needleman–Wunsch), scoring each (segment, turn) by
hypothesis↔turn token similarity plus a side→character bonus. The alignment is order-preserving
by construction, tolerates missed/spurious turns via gaps, and yields a per-segment reference
plus an alignment confidence. See work/eval/INTERFACES.md §5.

Pure functions (toks, token_sim, align_segments_to_turns) are unit-tested in tests/egla_kafe/.
"""
import argparse
import json
import os
import re
from difflib import SequenceMatcher
from html import escape

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def toks(s):
    return TOKEN_RE.findall((s or "").strip().lower())


def token_sim(a_tokens, b_tokens):
    """Order-sensitive similarity in [0,1] (difflib ratio over token lists)."""
    if not a_tokens and not b_tokens:
        return 1.0
    if not a_tokens or not b_tokens:
        return 0.0
    return SequenceMatcher(None, a_tokens, b_tokens).ratio()


def align_segments_to_turns(seg_hyps, seg_sides, turns, side_to_char,
                            match_offset=0.10, side_bonus=0.15, gap=0.0):
    """Global monotonic alignment of segments -> script turns.

    seg_hyps: list[str] hypothesis text per segment (in order)
    seg_sides: list[str] 'left'/'right' per segment
    turns: list[dict] script turns with 'tokens' and 'speaker'
    side_to_char: {'left':char,'right':char}

    Returns list (len == #segments) of dicts {turn_idx|None, conf, sim}. Monotonic: turn_idx is
    non-decreasing across matched segments. score(i,j) = sim - match_offset (+/- side_bonus);
    gaps score `gap`, so a segment whose best sim < match_offset is left unmatched (conf 0).
    """
    m, n = len(seg_hyps), len(turns)
    seg_tok = [toks(h) for h in seg_hyps]
    # score matrix
    def s(i, j):
        sim = token_sim(seg_tok[i], turns[j]["tokens"])
        bonus = side_bonus if side_to_char.get(seg_sides[i]) == turns[j]["speaker"] else -side_bonus
        return sim - match_offset + bonus, sim

    # DP
    NEG = float("-inf")
    H = [[0.0] * (n + 1) for _ in range(m + 1)]
    bt = [[None] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        H[i][0] = H[i - 1][0] + gap
        bt[i][0] = "up"
    for j in range(1, n + 1):
        H[0][j] = H[0][j - 1] + gap
        bt[0][j] = "left"
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            diag = H[i - 1][j - 1] + s(i - 1, j - 1)[0]
            up = H[i - 1][j] + gap          # segment i unmatched (spurious)
            lf = H[i][j - 1] + gap          # turn j skipped (no segment captured it)
            best = max(diag, up, lf)
            H[i][j] = best
            bt[i][j] = "diag" if best == diag else ("up" if best == up else "left")

    # traceback
    res = [None] * m
    i, j = m, n
    while i > 0 and j > 0:
        move = bt[i][j]
        if move == "diag":
            score, sim = s(i - 1, j - 1)
            res[i - 1] = {"turn_idx": j - 1, "sim": round(sim, 4),
                          "conf": round(max(0.0, min(1.0, sim)), 4)}
            i -= 1; j -= 1
        elif move == "up":
            res[i - 1] = {"turn_idx": None, "sim": 0.0, "conf": 0.0}
            i -= 1
        else:
            j -= 1
    while i > 0:
        res[i - 1] = {"turn_idx": None, "sim": 0.0, "conf": 0.0}
        i -= 1
    return res


def build_references(seg_records, script, side_to_char):
    """Returns per-segment dicts with ref text + turn idx + conf."""
    seg_hyps = [r.get("hyp", "") for r in seg_records]
    seg_sides = [r.get("side", "left") for r in seg_records]
    turns = script["turns"]
    aligned = align_segments_to_turns(seg_hyps, seg_sides, turns, side_to_char)
    out = []
    for r, a in zip(seg_records, aligned):
        ti = a["turn_idx"]
        if ti is not None:
            ref = turns[ti]["raw"]
            ref_turns = [ti]
            char = turns[ti]["speaker"]
        else:
            ref, ref_turns, char = "", [], side_to_char.get(r.get("side"))
        out.append({
            "seg_id": r["seg_id"], "side": r.get("side"), "char": char,
            "hyp": r.get("hyp", ""), "ref": ref, "ref_turn_idxs": ref_turns,
            "align_conf": a["conf"], "sim": a["sim"],
        })
    return out


def infer_side_to_char(seg_records, script, override_first_side=None):
    """First segment's side -> script.first_speaker; the other side -> other speaker."""
    speakers = script["speakers"]
    first_char = script["first_speaker"]
    other = [s for s in speakers if s != first_char]
    other_char = other[0] if other else first_char
    if override_first_side:
        first_side = override_first_side
    else:
        first_side = seg_records[0]["side"] if seg_records else "left"
    other_side = "right" if first_side == "left" else "left"
    return {first_side: first_char, other_side: other_char}


def write_wrd_files(records, wrd_dir):
    os.makedirs(wrd_dir, exist_ok=True)
    for r in records:
        path = os.path.join(wrd_dir, f"{r['seg_id']}.wrd")
        with open(path, "w", encoding="utf-8") as f:
            for w in toks(r["ref"]):
                f.write(w + "\n")


def write_review_html(records, meta, path):
    def color(c):
        return "#d6f5d6" if c >= 0.5 else ("#fff3cd" if c >= 0.25 else "#f8d7da")
    rows = []
    for r in records:
        rows.append(
            f"<tr style='background:{color(r['align_conf'])}'>"
            f"<td>{escape(r['seg_id'])}</td><td>{escape(str(r['side']))}</td>"
            f"<td>{escape(str(r['char']))}</td>"
            f"<td><pre style='white-space:pre-wrap;margin:0'>{escape(r['hyp'])}</pre></td>"
            f"<td><pre style='white-space:pre-wrap;margin:0'>{escape(r['ref'])}</pre></td>"
            f"<td>{r['align_conf']:.2f}</td></tr>")
    html = f"""<!doctype html><meta charset=utf-8><title>Alignment review {escape(meta.get('stem',''))}</title>
<style>body{{font:14px system-ui;margin:20px}}table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ccc;padding:6px;vertical-align:top;font-size:13px}}th{{background:#eee}}</style>
<h2>Alignment review — {escape(meta.get('stem',''))} ({escape(str(meta.get('scene')))})</h2>
<p>side→char: {escape(json.dumps(meta.get('side_to_char',{}), ensure_ascii=False))} ·
mean conf {meta.get('mean_align_conf',0):.3f} · unmatched {meta.get('monotonic_gap_rate',0):.1%}</p>
<table><tr><th>seg_id</th><th>side</th><th>char</th><th>hypothesis (model)</th><th>reference (script)</th><th>conf</th></tr>
{''.join(rows)}</table>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hyp", required=True, help="segments_hyp.json: [{seg_id,side,t0,t1,hyp}]")
    ap.add_argument("--script", required=True, help="parsed script JSON")
    ap.add_argument("--wrd-out", required=True, help="dir for per-seg .wrd references")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--first-speaker-side", choices=["left", "right"], default=None)
    args = ap.parse_args()

    seg_records = json.load(open(args.hyp, encoding="utf-8"))
    if isinstance(seg_records, dict) and "segments" in seg_records:
        seg_records = seg_records["segments"]
    seg_records = sorted(seg_records, key=lambda r: r.get("t0", 0))
    script = json.load(open(args.script, encoding="utf-8"))
    side_to_char = infer_side_to_char(seg_records, script, args.first_speaker_side)

    records = build_references(seg_records, script, side_to_char)
    write_wrd_files(records, args.wrd_out)

    matched = [r for r in records if r["ref_turn_idxs"]]
    mean_conf = round(sum(r["align_conf"] for r in records) / max(1, len(records)), 4)
    gap_rate = round(1 - len(matched) / max(1, len(records)), 4)
    side_ok = sum(1 for r in matched
                  if side_to_char.get(r["side"]) == r["char"]) / max(1, len(matched))
    stem = seg_records[0]["seg_id"].rsplit("_", 3)[0] if seg_records else ""
    meta = {"stem": stem, "scene": script.get("scene"), "side_to_char": side_to_char,
            "mean_align_conf": mean_conf, "monotonic_gap_rate": gap_rate,
            "side_char_consistency": round(side_ok, 4), "n_segments": len(records),
            "n_matched": len(matched), "n_script_turns": script["n_turns"]}

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "alignment.json"), "w", encoding="utf-8") as f:
        json.dump({**meta, "segments": records}, f, ensure_ascii=False, indent=2)
    write_review_html(records, meta, os.path.join(args.out_dir, "alignment_review.html"))
    print(f"[align] {stem}: {len(matched)}/{len(records)} segments matched, "
          f"mean_conf={mean_conf}, side_consistency={side_ok:.2f}")


if __name__ == "__main__":
    main()
