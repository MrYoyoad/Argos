#!/usr/bin/env python3
"""Drive `burn_demo_subtitles.py` over every row in realtalk_candidates.csv,
producing one face-burned 12 s clip per candidate. Each clip is rendered from
the candidate's per-speaker face MP4 at the candidate's start_sec, with the
ASR/decode results from the latest pipeline run dropped in beneath.

Resolves the latest `flat_runs_archive/{ts}/client_outputs/report` automatically.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

PER_SPEAKER_DIR = Path("/home/ubuntu/vsp_input_realtalk_demo/_per_speaker")
CANDIDATES_CSV = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk_candidates.csv")
ARCHIVE_ROOT = Path("/home/ubuntu/flat_runs_archive")
DEFAULT_OUT = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk")
BURN_SCRIPT = Path("/home/ubuntu/docs/_research-tools/scripts/burn_demo_subtitles.py")


def latest_report_dir(archive_root: Path = ARCHIVE_ROOT) -> Path:
    runs = sorted(archive_root.glob("2026*/client_outputs/report"))
    if not runs:
        raise SystemExit(f"no client_outputs/report dir under {archive_root}")
    return runs[-1]


def find_decode_segment_id(report_csv: Path, per_speaker_id: str, start_sec: float) -> str | None:
    """Resolve a candidate (per_speaker_id, start_sec) to the actual utt_id used
    in the latest pipeline run. The 25-clip workflow trims candidates to 12 s
    inputs so each input file produces exactly one segment named
    `{per_speaker_id}__win{start:04d}_00_000000_000300`.
    """
    expected_prefix = f"{per_speaker_id}__win{int(start_sec):04d}"
    with report_csv.open() as f:
        for r in csv.DictReader(f):
            uid = r.get("utt_id", "")
            if uid.startswith(expected_prefix):
                return uid
    return None


def find_agreement_json(report_dir: Path) -> Path | None:
    files = sorted(report_dir.glob("agreement-*.json"))
    return files[-1] if files else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates-csv", type=Path, default=CANDIDATES_CSV)
    ap.add_argument("--report-dir", type=Path,
                    help="report dir; defaults to latest under flat_runs_archive/")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--show-reference", action="store_true",
                    help="render Whisper reference line below the hypothesis")
    args = ap.parse_args()

    report_dir = args.report_dir or latest_report_dir()
    report_csv = report_dir / "report.csv"
    aggregated_json = report_dir / "aggregated.json"
    agreement_json = find_agreement_json(report_dir)
    if not report_csv.exists():
        raise SystemExit(f"no report.csv at {report_csv}")
    print(f"using report dir: {report_dir}")
    print(f"agreement file:   {agreement_json}")

    args.out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(args.candidates_csv.open()))
    print(f"burning {len(rows)} candidates → {args.out}")

    written = 0
    for r in rows:
        per_id = r["per_speaker_id"]
        start = float(r["start_sec"])
        end = float(r["end_sec"])
        face_mp4 = PER_SPEAKER_DIR / f"{per_id}.mp4"
        if not face_mp4.exists():
            print(f"  SKIP {per_id} @{start}: no per-speaker mp4", file=sys.stderr)
            continue

        seg_id = find_decode_segment_id(report_csv, per_id, start)
        if seg_id is None:
            print(f"  SKIP {per_id} @{start}: not found in report.csv", file=sys.stderr)
            continue

        out_mp4 = args.out / f"{per_id}__win{int(start):04d}__burned.mp4"
        cmd = [
            "python3", str(BURN_SCRIPT),
            "--face-mp4", str(face_mp4),
            "--segment-id", seg_id,
            "--start-sec", f"{start:.3f}",
            "--end-sec", f"{end:.3f}",
            "--report-csv", str(report_csv),
            "--aggregated-json", str(aggregated_json),
            "--reference-text", r.get("transcript", ""),
            "--out", str(out_mp4),
        ]
        if agreement_json:
            cmd.extend(["--agreement-json", str(agreement_json)])
        if args.show_reference:
            cmd.append("--show-reference")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            written += 1
            print(f"  ✓ {out_mp4.name}")
        except subprocess.CalledProcessError as e:
            print(f"  FAIL {out_mp4.name}:\n    stderr: {e.stderr.strip()[:300]}",
                  file=sys.stderr)

    print(f"\nwrote {written}/{len(rows)} burns to {args.out}")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
