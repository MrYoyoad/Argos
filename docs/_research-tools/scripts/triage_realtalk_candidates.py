#!/usr/bin/env python3
"""Triage per-speaker RealTalk segments for the demo deck.

Slides a 12 s window across each video at the pipeline's natural phase (step = 10 s,
matching fast_segment.py's seg_duration=12, overlap=2). For each (video, window,
dominant_speaker), scores the window on:
  - named-entity density in the matching Whisper text (capitalized non-initial
    words and numerals)
  - speaker dominance (one speaker is current_speaker for >= 80% of the frames)
  - duration / aliveness (Whisper text in the window covers >= 6 s of speech)
  - boilerplate penalty (Patreon, subscribe, intro phrases)
  - position (drops the first 30 s and last 15 s of each video)

Outputs `realtalk_candidates.csv` with one row per surviving (video, speaker, window)
tuple, capped at top-N per source video, ordered by score.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import Counter

REALTALK_ROOT = Path("/data/conversation_datasets/realtalk/data/english")
DEFAULT_OUT = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk_candidates.csv")

WINDOW_SEC = 12.0
STEP_SEC = 10.0  # pipeline phase: seg_duration - overlap_duration
HEAD_SKIP_SEC = 30.0
TAIL_SKIP_SEC = 15.0
SPEAKER_DOMINANCE_MIN = 0.80
MIN_SPEECH_COVERAGE_SEC = 6.0
TOP_PER_VIDEO = 3

BOILERPLATE_PATTERNS = [
    r"\bpatreon\b", r"\bsubscribe\b", r"\bsubscription\b",
    r"\bskin\s*deep\b", r"\bplease\s+(like|share|follow|comment)\b",
    r"\b(check\s+out|click)\s+(the\s+)?(link|description)\b",
    r"\bsupport\s+(the\s+)?(channel|show)\b",
]

ENTITY_REGEX = re.compile(r"\b([A-Z][A-Za-z]{2,}|\d+)\b")
SENTENCE_START_REGEX = re.compile(r"[.!?]\s+")


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def named_entities(text: str) -> list[str]:
    """Return capitalized non-sentence-initial tokens plus numerals.
    Strips the very first word of each sentence so 'Hey' / 'I' don't all count.
    """
    sentences = SENTENCE_START_REGEX.split(text)
    out = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        # skip first word; check the rest
        for w in words[1:]:
            m = ENTITY_REGEX.match(w)
            if m:
                tok = m.group(1)
                if tok.lower() not in {"i", "ive", "im", "ill"}:
                    out.append(tok)
    return out


def is_boilerplate(text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in BOILERPLATE_PATTERNS)


def whisper_text_in_window(segments: list[dict], start: float, end: float) -> tuple[str, float]:
    parts: list[str] = []
    coverage = 0.0
    for seg in segments:
        s, e = seg["start"], seg["end"]
        ov = min(end, e) - max(start, s)
        if ov <= 0:
            continue
        parts.append(seg["text"].strip())
        coverage += ov
    return " ".join(parts).strip(), coverage


def speaker_dominance(labels: dict, start: float, end: float, fps: float) -> tuple[str | None, float]:
    """Returns (dominant_speaker, fraction). Dominant speaker is whichever of p0/p1
    has the most frames where current_speaker == that speaker, within the window.
    Fraction is dominant_count / total_speaker_frames (excluding None).
    """
    start_f = int(round(start * fps))
    end_f = int(round(end * fps))
    counts: Counter[str] = Counter()
    for f in range(start_f, end_f):
        v = labels.get(str(f))
        if not v:
            continue
        sp = v.get("current_speaker")
        if sp:
            counts[sp] += 1
    total = sum(counts.values())
    if total == 0:
        return None, 0.0
    dom, n = counts.most_common(1)[0]
    return dom, n / total


def score_window(window_text: str, coverage_sec: float, dom_frac: float,
                 entity_count: int, position_sec: float, video_dur: float) -> float:
    if not window_text:
        return -1.0
    if is_boilerplate(window_text):
        return -1.0
    s = 0.0
    s += min(entity_count, 6) * 1.0           # cap to avoid runaway entity-spammy windows
    s += dom_frac * 2.0                        # cleaner speaker assignment is worth a lot
    s += min(coverage_sec / WINDOW_SEC, 1.0)   # how much of the 12s actually has speech
    # mild penalty for very early/late positions even after the hard skips
    if position_sec < 60:
        s -= 0.5
    if position_sec > video_dur - 30:
        s -= 0.5
    return s


def probe_video_meta(video_id: str) -> tuple[float, float]:
    """Return (duration_sec, fps) using the source MP4."""
    import subprocess
    src = REALTALK_ROOT / "videos" / f"{video_id}.mp4"
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate:format=duration",
        "-of", "csv=p=0",
        str(src),
    ], text=True).strip().splitlines()
    fps_str = out[0]
    dur = float(out[1])
    num, den = fps_str.split("/")
    fps = float(num) / float(den)
    return dur, fps


def pipeline_segment_filename(per_speaker_id: str, start_sec: float, fps_pipeline: float = 25.0) -> str:
    """Reproduce fast_segment.py naming for a per-speaker stream that the pipeline
    will normalize to 25 fps."""
    seg_idx = int(round(start_sec / STEP_SEC))
    start_frame = int(seg_idx * (WINDOW_SEC - 2.0) * fps_pipeline)
    end_frame = start_frame + int(WINDOW_SEC * fps_pipeline)
    return f"{per_speaker_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}.mp4"


def triage_video(video_id: str) -> list[dict]:
    transcripts = load_json(REALTALK_ROOT / "transcripts" / f"{video_id}.json")
    labels = load_json(REALTALK_ROOT / "speaker_labels" / f"{video_id}.json")
    segments = transcripts.get("segments", [])
    if not segments:
        return []

    duration, fps = probe_video_meta(video_id)
    end_limit = duration - TAIL_SKIP_SEC

    rows: list[dict] = []
    t = HEAD_SKIP_SEC
    while t + WINDOW_SEC <= end_limit:
        text, coverage = whisper_text_in_window(segments, t, t + WINDOW_SEC)
        if coverage < MIN_SPEECH_COVERAGE_SEC:
            t += STEP_SEC
            continue
        dom_speaker, dom_frac = speaker_dominance(labels, t, t + WINDOW_SEC, fps)
        if dom_speaker is None or dom_frac < SPEAKER_DOMINANCE_MIN:
            t += STEP_SEC
            continue
        entities = named_entities(text)
        s = score_window(text, coverage, dom_frac, len(entities), t, duration)
        if s <= 0:
            t += STEP_SEC
            continue
        per_speaker_id = f"{video_id}__{dom_speaker}"
        rows.append({
            "source_id": video_id,
            "speaker": dom_speaker,
            "per_speaker_id": per_speaker_id,
            "start_sec": round(t, 2),
            "end_sec": round(t + WINDOW_SEC, 2),
            "score": round(s, 3),
            "dominant_speaker_frac": round(dom_frac, 3),
            "speech_coverage_sec": round(coverage, 2),
            "named_entities": ";".join(sorted(set(entities))),
            "named_entity_count": len(entities),
            "transcript": text,
            "pipeline_segment_filename": pipeline_segment_filename(per_speaker_id, t),
        })
        t += STEP_SEC

    # Per-video diversity: cap at TOP_PER_VIDEO, prefer different speakers
    rows.sort(key=lambda r: r["score"], reverse=True)
    by_speaker: dict[str, list[dict]] = {"p0": [], "p1": []}
    for r in rows:
        by_speaker[r["speaker"]].append(r)
    picks: list[dict] = []
    # Round-robin between speakers up to TOP_PER_VIDEO
    while len(picks) < TOP_PER_VIDEO and (by_speaker["p0"] or by_speaker["p1"]):
        for sp in ("p0", "p1"):
            if by_speaker[sp]:
                picks.append(by_speaker[sp].pop(0))
                if len(picks) >= TOP_PER_VIDEO:
                    break
    return picks


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", nargs="+", help="restrict to these video ids")
    ap.add_argument("--total-cap", type=int, default=25,
                    help="hard ceiling on total candidates emitted")
    args = ap.parse_args()

    vids = sorted(p.stem for p in (REALTALK_ROOT / "videos").glob("*.mp4"))
    if args.only:
        vids = [v for v in vids if v in args.only]

    all_rows: list[dict] = []
    for v in vids:
        try:
            rows = triage_video(v)
            print(f"[{v}] {len(rows)} candidates", file=sys.stderr)
            all_rows.extend(rows)
        except FileNotFoundError as e:
            print(f"[{v}] missing input: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[{v}] FAIL: {e}", file=sys.stderr)

    # Global re-rank, take top-cap
    all_rows.sort(key=lambda r: r["score"], reverse=True)
    all_rows = all_rows[: args.total_cap]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id", "speaker", "per_speaker_id",
        "start_sec", "end_sec", "score",
        "dominant_speaker_frac", "speech_coverage_sec",
        "named_entity_count", "named_entities",
        "pipeline_segment_filename", "transcript",
    ]
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)
    print(f"wrote {len(all_rows)} candidates → {args.out}")


if __name__ == "__main__":
    main()
