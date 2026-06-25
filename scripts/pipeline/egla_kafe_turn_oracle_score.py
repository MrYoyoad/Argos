#!/usr/bin/env python3
"""Monotonic many-to-one oracle alignment + per-turn scoring.

Disentangles model error from alignment/over-segmentation error. The visual turn detector
over-segments (e.g. 51 detected turns vs 48 script lines), so a single script line is sometimes
split across consecutive clips. This realigns each conversation's ORDERED segment hypotheses to
its script turns with a monotonic many-to-one DP (consecutive segments may group onto one turn,
turns may stay empty), then scores at the natural per-turn level (each turn vs the concatenated
hyp of its group). This is BOTH the alignment ceiling and the drift fix.
"""
import argparse
import json
import os
import re
import subprocess
from difflib import SequenceMatcher

TOK = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
def toks(s): return TOK.findall((s or "").lower())
def sim(a, b):
    if not a and not b: return 0.0
    if not a or not b: return 0.0
    return SequenceMatcher(None, a, b).ratio()


def align_many_to_one(seg_hyps, turns):
    """Monotonic DP: assign each (ordered) segment to a turn; consecutive segments may share a turn;
    turns may get none. Maximizes sum of sim(concat(group), turn). Returns groups: list per turn of
    segment indices."""
    segtok = [toks(h) for h in seg_hyps]
    m, n = len(seg_hyps), len(turns)
    NEG = float("-inf")
    dp = [[NEG] * (n + 1) for _ in range(m + 1)]
    bk = [[0] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = 0.0
    for j in range(1, n + 1):
        dp[0][j] = 0.0  # leading empty turns
        bk[0][j] = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            best, bg = NEG, 0
            # turn j-1 absorbs last g segments (g>=0)
            concat = []
            for g in range(0, i + 1):
                if g == 0:
                    s = 0.0; prev = dp[i][j - 1]
                else:
                    concat = segtok[i - g] + concat if g == 1 else segtok[i - g] + concat
                    s = sim(concat, turns[j - 1]["tokens"]); prev = dp[i - g][j - 1]
                if prev == NEG:
                    continue
                if prev + s > best:
                    best, bg = prev + s, g
            dp[i][j] = best; bk[i][j] = bg
    # traceback
    groups = [[] for _ in range(n)]
    i, j = m, n
    while j > 0:
        g = bk[i][j]
        if g > 0:
            groups[j - 1] = list(range(i - g, i))
            i -= g
        j -= 1
    return groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypo", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/hypo_perturn_scene12.json")
    ap.add_argument("--provenance", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_scene12_all/provenance.json")
    ap.add_argument("--scripts-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval")
    ap.add_argument("--out-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_turn_oracle")
    ap.add_argument("--vsp-dir", default="/home/ubuntu/VSP-LLM")
    args = ap.parse_args()

    d = json.load(open(args.hypo)); hyps = {u: h for u, h in zip(d["utt_id"], d["hypo"])}
    prov = json.load(open(args.provenance))
    sc = {s: json.load(open(os.path.join(args.scripts_dir, f"script_{s}.json"))) for s in ("scene1", "scene2")}

    def parse(u):
        m = re.match(r"^(.*)_(\d{2})_(\d{6})_(\d{6})$", u)
        return (m.group(1), int(m.group(3))) if m else (u.rsplit("_", 3)[0], 0)
    conv = {}
    for u, h in hyps.items():
        stem, sf = parse(u)
        conv.setdefault(stem, []).append((sf, h, u))

    rows = {"utt_id": [], "ref": [], "hypo": [], "instruction": []}
    for stem, items in sorted(conv.items()):
        items.sort()
        scene = prov.get(items[0][2], {}).get("scene")
        if scene not in sc:
            continue
        seg_hyps = [h for _, h, _ in items]
        turns = sc[scene]["turns"]
        groups = align_many_to_one(seg_hyps, turns)
        for ti, grp in enumerate(groups):
            concat = " ".join(seg_hyps[k] for k in grp)
            rows["utt_id"].append(f"{stem}_t{ti:02d}")
            rows["ref"].append(turns[ti]["raw"])
            rows["hypo"].append(concat)
            rows["instruction"].append("")
    os.makedirs(args.out_dir, exist_ok=True)
    hp = os.path.join(args.out_dir, "turn_oracle_hypo.json")
    json.dump(rows, open(hp, "w"), ensure_ascii=False, indent=2)
    print(f"[turn-oracle] {len(rows['utt_id'])} turn-level pairs -> {hp}")
    subprocess.run(["python3", os.path.join(args.vsp_dir, "scripts/make_report.py"),
                    "--jsonl", hp, "--out_dir", os.path.join(args.out_dir, "report"), "--compute-is"], check=False)


if __name__ == "__main__":
    main()
