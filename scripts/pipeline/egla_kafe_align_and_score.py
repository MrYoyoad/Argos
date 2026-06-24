#!/usr/bin/env python3
"""Phase 4: attach script references to decoded segments and score.

Reads the decode output (hypo-{fid}.json: parallel utt_id/ref/hypo lists), groups segments by
source video (stem), runs the monotonic script aligner per video to assign each segment its script
line, then:
  1. writes per-seg .wrd references (persist for any future pipeline re-run);
  2. builds a corrected hypo json (ref := aligned script line) and re-runs make_report.py with the
     decode's confidence/n-best sidecars -> report.csv scored against the CORRECT references
     (no re-decode needed);
  3. emits provenance.json (seg_id -> stem/scene/side/char/angle/speakers/arm/align_conf).

This is also the definitive stream-sanity gate: if the model's lip-read output aligns monotonically
to the script with good confidence, the stacked stream genuinely tracks the right speaker.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_script_to_segments as AL


def newest_hypo(vsp_dir):
    cands = glob.glob(os.path.join(vsp_dir, "decode/vsr/en/hypo-*.json"))
    cands = [c for c in cands if "merged" not in c]
    return max(cands, key=os.path.getmtime) if cands else None


def load_hypo(path):
    d = json.load(open(path, encoding="utf-8"))
    return {u: h for u, h in zip(d["utt_id"], d["hypo"])}


def load_seg_meta(meta_globs):
    meta = {}
    for g in meta_globs:
        for p in glob.glob(g):
            meta.update(json.load(open(p, encoding="utf-8")))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vsp-dir", default="/home/ubuntu/VSP-LLM")
    ap.add_argument("--hypo", default=None, help="hypo-{fid}.json (default: newest)")
    ap.add_argument("--seg-meta", nargs="+",
                    default=["/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_*/seg_meta.json"])
    ap.add_argument("--scripts-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval")
    ap.add_argument("--out-dir", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval")
    ap.add_argument("--arm", default="turnseg", help="provenance arm label")
    ap.add_argument("--face-id", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/face_id.json",
                    help="face_id.json mapping stem+side -> person (for per-PERSON stats)")
    ap.add_argument("--run-report", action="store_true", help="re-run make_report on corrected refs")
    args = ap.parse_args()

    face_person = {}
    if args.face_id and os.path.exists(args.face_id):
        fid = json.load(open(args.face_id, encoding="utf-8"))
        face_person = {k: v.get("person") for k, v in fid.get("per_crop", {}).items()}

    hypo_path = args.hypo or newest_hypo(args.vsp_dir)
    if not hypo_path:
        print("ERROR: no hypo json found", file=sys.stderr); sys.exit(1)
    print(f"[align] using hypo: {hypo_path}", file=sys.stderr)
    hyps = load_hypo(hypo_path)
    seg_meta = load_seg_meta(args.seg_meta)

    # group segs by stem
    by_stem = {}
    for seg_id, hyp in hyps.items():
        m = seg_meta.get(seg_id)
        if not m:
            # stem = strip _NN_NNNNNN_NNNNNN
            stem = seg_id.rsplit("_", 3)[0]
            m = {"stem": stem, "scene": None, "side": "left", "t0": 0, "t1": 0}
        rec = {"seg_id": seg_id, "side": m["side"], "t0": m.get("t0", 0),
               "t1": m.get("t1", 0), "hyp": hyp, "_meta": m}
        by_stem.setdefault(m["stem"], []).append(rec)

    all_aligned = []
    provenance = {}
    os.makedirs(args.out_dir, exist_ok=True)
    wrd_root = os.path.join(args.out_dir, "wrd")
    for stem, recs in sorted(by_stem.items()):
        recs.sort(key=lambda r: r["t0"])
        scene = recs[0]["_meta"].get("scene")
        scene_num = "scene1" if scene == "scene1" else ("scene2" if scene == "scene2" else None)
        if scene_num is None:
            print(f"[skip] {stem}: scene unknown ({scene}); cannot pick script", file=sys.stderr)
            continue
        script = json.load(open(os.path.join(args.scripts_dir, f"script_{scene_num}.json"),
                                 encoding="utf-8"))
        s2c = AL.infer_side_to_char(recs, script)
        aligned = AL.build_references(recs, script, s2c)
        # per-stem outputs
        stem_dir = os.path.join(args.out_dir, "align", stem)
        os.makedirs(stem_dir, exist_ok=True)
        AL.write_wrd_files(aligned, os.path.join(wrd_root, stem))
        matched = [r for r in aligned if r["ref_turn_idxs"]]
        mean_conf = round(sum(r["align_conf"] for r in aligned) / max(1, len(aligned)), 4)
        side_ok = sum(1 for r in matched if s2c.get(r["side"]) == r["char"]) / max(1, len(matched))
        meta = {"stem": stem, "scene": scene_num, "side_to_char": s2c,
                "mean_align_conf": mean_conf, "monotonic_gap_rate": round(1 - len(matched) / max(1, len(aligned)), 4),
                "side_char_consistency": round(side_ok, 4), "n_segments": len(aligned),
                "n_matched": len(matched), "n_script_turns": script["n_turns"]}
        with open(os.path.join(stem_dir, "alignment.json"), "w", encoding="utf-8") as f:
            json.dump({**meta, "segments": aligned}, f, ensure_ascii=False, indent=2)
        AL.write_review_html(aligned, meta, os.path.join(stem_dir, "alignment_review.html"))
        print(f"[align] {stem} ({scene_num}): {len(matched)}/{len(aligned)} matched, "
              f"mean_conf={mean_conf:.3f}, side_consistency={side_ok:.2f}", file=sys.stderr)
        for r in aligned:
            mm = next(x for x in recs if x["seg_id"] == r["seg_id"])["_meta"]
            provenance[r["seg_id"]] = {
                "stem": stem, "scene": scene_num, "side": r["side"], "char": r["char"],
                "person": face_person.get(f"{stem}__{r['side']}"),
                "angle": mm.get("angle"), "speakers_in_name": mm.get("speakers_in_name", []),
                "arm": args.arm, "align_conf": r["align_conf"], "ref_turn_idxs": r["ref_turn_idxs"]}
        all_aligned.extend(aligned)

    with open(os.path.join(args.out_dir, "provenance.json"), "w", encoding="utf-8") as f:
        json.dump(provenance, f, ensure_ascii=False, indent=2)

    # corrected hypo json (ref := aligned script line) for scoring without re-decode
    ref_by_id = {r["seg_id"]: r["ref"] for r in all_aligned}
    src = json.load(open(hypo_path, encoding="utf-8"))
    corrected = {"utt_id": [], "ref": [], "hypo": [], "instruction": src.get("instruction", [])}
    for i, u in enumerate(src["utt_id"]):
        corrected["utt_id"].append(u)
        corrected["hypo"].append(src["hypo"][i])
        corrected["ref"].append(ref_by_id.get(u, src["ref"][i] if "ref" in src else ""))
    corrected_path = os.path.join(args.out_dir, "hypo-corrected.json")
    with open(corrected_path, "w", encoding="utf-8") as f:
        json.dump(corrected, f, ensure_ascii=False, indent=2)
    print(f"[align] wrote corrected hypo ({len(corrected['utt_id'])} segs) -> {corrected_path}",
          file=sys.stderr)

    overall_conf = round(sum(r["align_conf"] for r in all_aligned) / max(1, len(all_aligned)), 4)
    print(f"[align] OVERALL mean align_conf={overall_conf} over {len(all_aligned)} segments",
          file=sys.stderr)

    if args.run_report:
        report_dir = os.path.join(args.out_dir, "report")
        os.makedirs(report_dir, exist_ok=True)
        fid = os.path.basename(hypo_path).replace("hypo-", "").replace(".json", "")
        dd = os.path.join(args.vsp_dir, "decode/vsr/en")
        cmd = ["python3", os.path.join(args.vsp_dir, "scripts/make_report.py"),
               "--jsonl", corrected_path, "--out_dir", report_dir, "--compute-is"]
        # (per-word confidence + n-best aggregation added in the full scaling run via outputs.sh)
        print(f"[align] run make_report: {' '.join(cmd)}", file=sys.stderr)
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
