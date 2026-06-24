#!/usr/bin/env python3
"""Batch-build active-speaker streams for Egla-Kafe videos listed in the index.

For each indexed entry matching --scenes that has existing L/R crops, run
build_active_speaker_stream.py. (Masters / videos without crops are skipped here; their crops
come from make_speaker_crops.py first.) Writes per-stem dirs under work/streams/ and a
summary work/eval/stream_qc_summary.json.
"""
import argparse
import json
import os
import subprocess
import sys

VENV = "/home/ubuntu/auto_avsr/pre-process-venv/bin/python"
TOOL = "/home/ubuntu/scripts/pipeline/build_active_speaker_stream.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json")
    ap.add_argument("--streams-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/streams")
    ap.add_argument("--scenes", default="scene1,scene2", help="comma list, or 'all'")
    ap.add_argument("--method", default="lipvar")
    ap.add_argument("--overlay", action="store_true")
    args = ap.parse_args()

    idx = json.load(open(args.index))
    scenes = None if args.scenes == "all" else set(args.scenes.split(","))
    summary = []
    for e in idx["entries"]:
        if scenes is not None and e.get("scene") not in scenes:
            continue
        L, R = e["existing_crops"]["left"], e["existing_crops"]["right"]
        if not (L and R):
            print(f"[skip] {e['stem']}: no existing crops", file=sys.stderr)
            continue
        out = os.path.join(args.streams_dir, e["stem"])
        cmd = [VENV, TOOL, "--left", L, "--right", R, "--stem", e["stem"],
               "--out-dir", out, "--method", args.method]
        if args.overlay:
            cmd.append("--overlay")
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0
        qc = {}
        qcp = os.path.join(out, f"{e['stem']}__qc_metrics.json")
        if os.path.exists(qcp):
            qc = json.load(open(qcp))
        print(f"[{'ok' if ok else 'FAIL'}] {e['stem']}: "
              f"turns={qc.get('n_turns')} voiced_cons={qc.get('voiced_consistency')} "
              f"alt={qc.get('alternation_rate')}", file=sys.stderr)
        if not ok:
            print(r.stderr[-400:], file=sys.stderr)
        summary.append({"stem": e["stem"], "scene": e["scene"], "ok": ok, **qc})

    out_summary = os.path.join(os.path.dirname(args.index), "stream_qc_summary.json")
    with open(out_summary, "w") as f:
        json.dump({"n": len(summary), "streams": summary}, f, indent=2)
    n_ok = sum(1 for s in summary if s["ok"])
    print(f"\n[done] {n_ok}/{len(summary)} streams built -> {out_summary}", file=sys.stderr)
    if summary:
        vc = [s.get("voiced_consistency", 0) for s in summary if s["ok"]]
        if vc:
            print(f"[done] voiced_consistency: min={min(vc):.3f} "
                  f"mean={sum(vc)/len(vc):.3f} max={max(vc):.3f}", file=sys.stderr)


if __name__ == "__main__":
    main()
