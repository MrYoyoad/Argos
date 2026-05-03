#!/usr/bin/env python3
"""Cross-reference the 25-candidate decode results with the per-speaker source
videos: emit a markdown report (`realtalk_analysis.md`) plus per-candidate
representative-frame thumbnails so the deck reviewer can see what each segment
*looked like* alongside the numbers.

For each candidate row in realtalk_candidates.csv we extract:
  - utt_id (resolved by matching `{per_speaker_id}__win{start:04d}` against report.csv)
  - reference (Whisper) text from the candidates CSV
  - displayed hypothesis (`hyp` column — MBR by default in n-best mode)
  - WER, IS, sentence_conf, NIV outcome
  - 3 representative frames from the per-speaker face MP4 sampled at start, mid, end

Then writes a markdown report grouping candidates into Clearly-Conveyed (IS≥3.80),
Salvage (2.0≤IS<3.80), and Failed (IS<2.0), with a short per-row observation hook
the curator can fill in by hand. Aggregate stats summarized at the top.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from pathlib import Path

PER_SPEAKER_DIR = Path("/home/ubuntu/vsp_input_realtalk_demo/_per_speaker")
CANDIDATES_CSV = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk_candidates.csv")
DEFAULT_OUT_DIR = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk")
ARCHIVE_ROOT = Path("/home/ubuntu/flat_runs_archive")

NIV_Y_THRESHOLD = 3.80
NIV_P_THRESHOLD = 2.00


def latest_report_dir(archive_root: Path = ARCHIVE_ROOT) -> Path:
    runs = sorted(archive_root.glob("2026*/client_outputs/report"))
    if not runs:
        raise SystemExit(f"no client_outputs/report dir under {archive_root}")
    return runs[-1]


def find_decode_row(report_rows: list[dict], per_speaker_id: str, start_sec: float) -> dict | None:
    expected = f"{per_speaker_id}__win{int(start_sec):04d}"
    for r in report_rows:
        uid = r.get("utt_id", "")
        if uid.startswith(expected):
            return r
    return None


def extract_frames(face_mp4: Path, start_sec: float, out_dir: Path, basename: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []
    for ts_off, label in [(1.0, "early"), (6.0, "mid"), (11.0, "late")]:
        out = out_dir / f"{basename}__{label}.jpg"
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{start_sec + ts_off:.3f}",
            "-i", str(face_mp4),
            "-frames:v", "1",
            "-q:v", "3",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True)
            out_paths.append(out)
        except subprocess.CalledProcessError:
            pass
    return out_paths


def niv_label(is_score: float) -> str:
    if is_score >= NIV_Y_THRESHOLD:
        return "Y (clearly conveyed)"
    if is_score >= NIV_P_THRESHOLD:
        return "P (any useful)"
    return "N (not useful)"


def safe_float(v) -> float | None:
    try:
        return float(v) if v not in ("", None) else None
    except (ValueError, TypeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates-csv", type=Path, default=CANDIDATES_CSV)
    ap.add_argument("--report-dir", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--frames-dir-name", default="frames")
    args = ap.parse_args()

    report_dir = args.report_dir or latest_report_dir()
    print(f"using report: {report_dir}")
    report_rows = list(csv.DictReader((report_dir / "report.csv").open()))
    candidates = list(csv.DictReader(args.candidates_csv.open()))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = args.out_dir / args.frames_dir_name
    frames_dir.mkdir(parents=True, exist_ok=True)

    enriched: list[dict] = []
    for c in candidates:
        per_id = c["per_speaker_id"]
        start = float(c["start_sec"])
        d = find_decode_row(report_rows, per_id, start)
        face_mp4 = PER_SPEAKER_DIR / f"{per_id}.mp4"
        if d is None or not face_mp4.exists():
            continue
        is_score = safe_float(d.get("is_score"))
        sconf = safe_float(d.get("sentence_confidence"))
        wer = safe_float(d.get("wer_%"))
        wer_mbr = safe_float(d.get("wer_hyp_mbr_%"))
        hyp = d.get("hyp", "").strip() or "[empty]"
        hyp_mbr = (d.get("hyp_mbr") or hyp).strip() or "[empty]"
        ref = d.get("ref", "").strip() or c.get("transcript", "").strip()
        basename = f"{per_id}__win{int(start):04d}"
        frames = extract_frames(face_mp4, start, frames_dir, basename)
        enriched.append({
            "per_speaker_id": per_id,
            "start_sec": start,
            "end_sec": float(c["end_sec"]),
            "score": float(c["score"]),
            "named_entities": c.get("named_entities", ""),
            "ref": ref,
            "hyp": hyp,
            "hyp_mbr": hyp_mbr,
            "wer": wer,
            "wer_mbr": wer_mbr,
            "is_score": is_score,
            "is_label": d.get("is_label", ""),
            "sentence_conf": sconf,
            "min_word_conf": safe_float(d.get("min_word_conf")),
            "n_low_conf_words": d.get("n_low_conf_words", ""),
            "trust_tier": d.get("tier", ""),
            "frames": [str(f.relative_to(args.out_dir)) for f in frames],
            "burn_path": f"{basename}__burned.mp4",
        })

    # Summary stats
    iss = [e["is_score"] for e in enriched if e["is_score"] is not None]
    wers = [e["wer"] for e in enriched if e["wer"] is not None]
    mbrs = [e["wer_mbr"] for e in enriched if e["wer_mbr"] is not None]
    sconfs = [e["sentence_conf"] for e in enriched if e["sentence_conf"] is not None]

    def bucket(e):
        s = e["is_score"]
        if s is None:
            return "Unknown"
        if s >= NIV_Y_THRESHOLD:
            return "Clearly Conveyed"
        if s >= NIV_P_THRESHOLD:
            return "Salvage"
        return "Failed"

    buckets = {"Clearly Conveyed": [], "Salvage": [], "Failed": [], "Unknown": []}
    for e in enriched:
        buckets[bucket(e)].append(e)

    md = []
    md.append("# RealTalk demo candidates — analysis vs source video\n")
    md.append(f"_Pipeline run report dir: `{report_dir}`_\n")
    md.append(f"_Candidates evaluated: **{len(enriched)}** of {len(candidates)} from triage._\n")
    md.append("\n## Aggregate\n")
    md.append("| metric | mean | median | min | max |")
    md.append("|---|---|---|---|---|")
    for label, vals in [("WER (top-1)", wers), ("WER (MBR)", mbrs),
                        ("IS", iss), ("sentence_conf", sconfs)]:
        if vals:
            md.append(f"| {label} | {statistics.mean(vals):.2f} | "
                      f"{statistics.median(vals):.2f} | {min(vals):.2f} | {max(vals):.2f} |")
    md.append("\n| outcome (NIV) | count | % |")
    md.append("|---|---|---|")
    total = max(len(enriched), 1)
    for k in ("Clearly Conveyed", "Salvage", "Failed", "Unknown"):
        n = len(buckets[k])
        md.append(f"| {k} | {n} | {100*n/total:.0f}% |")

    for k in ("Clearly Conveyed", "Salvage", "Failed"):
        md.append(f"\n## {k} (IS "
                  + ({"Clearly Conveyed": "≥ 3.80",
                      "Salvage": "2.00–3.79",
                      "Failed": "< 2.00"}[k]) + ")\n")
        rows = sorted(buckets[k], key=lambda e: -(e["is_score"] or -999))
        if not rows:
            md.append("_(none)_\n")
            continue
        def _f(v, fmt="{:.2f}"):
            return fmt.format(v) if isinstance(v, (int, float)) else "—"
        for e in rows:
            md.append(f"### {e['per_speaker_id']} @ {e['start_sec']:.0f}s")
            is_score = e["is_score"] if isinstance(e["is_score"], (int, float)) else None
            niv = niv_label(is_score) if is_score is not None else "—"
            md.append(f"- **IS**: {_f(is_score)} ({niv})  ·  "
                      f"**WER (top1/MBR)**: {_f(e['wer'], '{:.0f}')}% / "
                      f"{_f(e['wer_mbr'], '{:.0f}')}%  ·  "
                      f"**sentence_conf**: {_f(e['sentence_conf'], '{:.3f}')} → trust **{e['trust_tier'] or '—'}**")
            md.append(f"- **named entities (triage)**: `{e['named_entities']}`")
            md.append(f"- **REF**: {e['ref']}")
            md.append(f"- **HYP (displayed = MBR)**: {e['hyp_mbr']}")
            if e["frames"]:
                md.append(f"- **frames**: " + " ".join(f"![]({f})" for f in e["frames"]))
            md.append(f"- **burned clip**: [`{e['burn_path']}`]({e['burn_path']})")
            md.append("- **observation**: _(curator: head pose / lip visibility / "
                      "speaking rate / why it succeeded/failed)_")
            md.append("")

    out_md = args.out_dir / "realtalk_analysis.md"
    out_md.write_text("\n".join(md))
    out_json = args.out_dir / "realtalk_analysis.json"
    out_json.write_text(json.dumps(enriched, indent=2, default=str))
    print(f"wrote {out_md}")
    print(f"wrote {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
