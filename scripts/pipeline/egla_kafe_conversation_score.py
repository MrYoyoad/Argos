#!/usr/bin/env python3
"""Conversation-level scoring: concatenate a conversation's segment hypotheses (window or turn)
into the full lip-read transcription and score it against the FULL script.

Used to compare the two input regimes at the level a viewer cares about (the whole conversation):
  - stacked-stream arm: ~12s windows of the continuous active-speaker stream (cuts mid-window)
  - per-turn arm:       isolated single-speaker turn clips
Same reference (full script) for both -> fair comparison of "does feeding it as one stream help?"
"""
import argparse
import glob
import json
import os
import re
import subprocess

STEM_RE = re.compile(r"^(.*)_(\d{2})_(\d{6})_(\d{6})$")


def parse(utt):
    m = STEM_RE.match(utt)
    if m:
        return m.group(1), int(m.group(3))  # stem, start-frame (for ordering)
    return utt.rsplit("_", 3)[0], 0


def script_for(stem, scripts_dir):
    sc = "scene1" if stem.startswith("s1_") else ("scene2" if stem.startswith("s2_") else None)
    if sc is None:
        # auto-detect: pick the script whose tokens overlap the hyp more (resolved by caller)
        return None
    return json.load(open(os.path.join(scripts_dir, f"script_{sc}.json"), encoding="utf-8")), sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypo", required=True)
    ap.add_argument("--scripts-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--vsp-dir", default="/home/ubuntu/VSP-LLM")
    ap.add_argument("--label", default="arm")
    args = ap.parse_args()

    d = json.load(open(args.hypo, encoding="utf-8"))
    hyps = {u: h for u, h in zip(d["utt_id"], d["hypo"])}
    # group by stem, order by start frame
    conv = {}
    for u, h in hyps.items():
        stem, sf = parse(u)
        conv.setdefault(stem, []).append((sf, h))
    os.makedirs(args.out_dir, exist_ok=True)

    rows = {"utt_id": [], "ref": [], "hypo": [], "instruction": []}
    meta = []
    for stem, items in sorted(conv.items()):
        items.sort()
        full_hyp = " ".join(h for _, h in items if h)
        sc = script_for(stem, args.scripts_dir)
        if sc is None:
            # auto-detect script by token overlap (for שפם / masters)
            from difflib import SequenceMatcher
            best = None
            for cand in ("scene1", "scene2"):
                s = json.load(open(os.path.join(args.scripts_dir, f"script_{cand}.json"), encoding="utf-8"))
                ref = " ".join(t["raw"] for t in s["turns"])
                r = SequenceMatcher(None, full_hyp.lower().split(), ref.lower().split()).ratio()
                if best is None or r > best[0]:
                    best = (r, cand, s)
            _, scene, script = best
        else:
            script, scene = sc
        full_ref = " ".join(t["raw"] for t in script["turns"])
        rows["utt_id"].append(stem)
        rows["ref"].append(full_ref)
        rows["hypo"].append(full_hyp)
        rows["instruction"].append("")
        meta.append({"stem": stem, "scene": scene, "n_segments": len(items),
                     "hyp_words": len(full_hyp.split()), "ref_words": len(full_ref.split())})

    conv_hypo = os.path.join(args.out_dir, "conversation_hypo.json")
    json.dump(rows, open(conv_hypo, "w"), ensure_ascii=False, indent=2)
    json.dump(meta, open(os.path.join(args.out_dir, "conversation_meta.json"), "w"), indent=2)
    print(f"[conv-score] {len(meta)} conversations -> {conv_hypo}")

    report_dir = os.path.join(args.out_dir, "report")
    subprocess.run(["python3", os.path.join(args.vsp_dir, "scripts/make_report.py"),
                    "--jsonl", conv_hypo, "--out_dir", report_dir, "--compute-is"], check=False)


if __name__ == "__main__":
    main()
