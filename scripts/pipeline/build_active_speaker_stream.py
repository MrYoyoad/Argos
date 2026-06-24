#!/usr/bin/env python3
"""Build a single active-speaker "stacked" stream from two single-speaker crops.

No audio is available on the client-camera footage, so the active speaker is detected
*visually*: per crop, per frame, we measure mouth-region motion energy (mean absolute
inter-frame difference over the lower-center ROI), smooth it, and assign the active side
with hysteresis + a minimum dwell time. The output is one hard-cut video that always shows
whoever is currently talking, plus a turn timeline, decode-segment list, and QC metrics.

See work/eval/INTERFACES.md §3 for the exact output contract. Pure functions
(build_active_timeline, merge_turns_to_segments, seg_id) are unit-tested in
tests/egla_kafe/.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np


# ----------------------------- pure logic (unit-tested) -----------------------------

def _moving_average(x: np.ndarray, win: int) -> np.ndarray:
    if win <= 1:
        return x.astype(float)
    k = np.ones(int(win), dtype=float) / float(win)
    return np.convolve(x.astype(float), k, mode="same")


def build_active_timeline(energy_l, energy_r, fps, smooth_win=0.3, min_dwell=0.4, margin=1e-6):
    """Return (active:int array 0=left/1=right per frame, turns:list[(side,t0,t1)]).

    A hysteretic state machine: stay on the current side until the OTHER side's smoothed
    energy has continuously exceeded the current side's (by `margin`) for >= min_dwell.
    """
    energy_l = np.asarray(energy_l, dtype=float)
    energy_r = np.asarray(energy_r, dtype=float)
    n = min(len(energy_l), len(energy_r))
    energy_l, energy_r = energy_l[:n], energy_r[:n]
    sw = max(1, int(round(smooth_win * fps)))
    sl = _moving_average(energy_l, sw)
    sr = _moving_average(energy_r, sw)
    dwell_frames = max(1, int(round(min_dwell * fps)))

    active = np.zeros(n, dtype=int)
    if n == 0:
        return active, []
    # seed with whichever side has more energy in the opening window
    cur = 1 if sr[:dwell_frames].sum() > sl[:dwell_frames].sum() else 0
    other_run = 0
    for t in range(n):
        want = 1 if (sr[t] > sl[t] + margin) else 0
        if want != cur:
            other_run += 1
            if other_run >= dwell_frames:
                cur = want
                other_run = 0
        else:
            other_run = 0
        active[t] = cur

    # collapse to turns
    turns = []
    start = 0
    for t in range(1, n + 1):
        if t == n or active[t] != active[start]:
            side = "left" if active[start] == 0 else "right"
            turns.append((side, start / fps, t / fps))
            start = t
    return active, turns


def seg_id(stem: str, idx: int, t0: float, t1: float, fps_model: int = 25) -> str:
    f0 = int(round(t0 * fps_model))
    f1 = int(round(t1 * fps_model))
    return f"{stem}_{idx:02d}_{f0:06d}_{f1:06d}"


def merge_turns_to_segments(turns, stem, merge_target=6.0, min_dwell=0.4, fps_model=25):
    """Merge consecutive SAME-side turns (and absorb sub-min_dwell turns) into decode
    segments of up to ~merge_target seconds. Never merges across a side change.
    Returns list of {seg_id, side, t0, t1, turn_idxs}.
    """
    segments = []
    i = 0
    seg_idx = 0
    n = len(turns)
    while i < n:
        side, t0, t1 = turns[i]
        cur_t0, cur_t1 = t0, t1
        idxs = [i]
        j = i + 1
        while j < n:
            nside, nt0, nt1 = turns[j]
            same_side = (nside == side)
            short = (nt1 - nt0) < min_dwell
            # extend if same side (or absorbing a tiny blip) and within target length
            if (same_side or short) and (nt1 - cur_t0) <= merge_target:
                cur_t1 = nt1
                idxs.append(j)
                j += 1
            else:
                break
        segments.append({
            "seg_id": seg_id(stem, seg_idx, cur_t0, cur_t1, fps_model),
            "side": side, "t0": round(cur_t0, 3), "t1": round(cur_t1, 3),
            "turn_idxs": idxs,
        })
        seg_idx += 1
        i = j
    return segments


def mouth_roi(h, w):
    """Lower-center ROI (rows 0.55-0.92, cols 0.25-0.75) of a square face crop."""
    r0, r1 = int(0.55 * h), int(0.92 * h)
    c0, c1 = int(0.25 * w), int(0.75 * w)
    return r0, r1, c0, c1


# ----------------------------- video I/O -----------------------------

def _rolling_std(x: np.ndarray, win: int) -> np.ndarray:
    """Centered rolling standard deviation (captures oscillation = speech)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n == 0:
        return x
    w = max(1, int(win))
    out = np.zeros(n)
    half = w // 2
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        seg = x[a:b]
        out[i] = float(np.std(seg)) if len(seg) > 1 else 0.0
    return out


# MediaPipe FaceMesh lip landmark indices (468-pt mesh)
_LM_UP, _LM_LO = 13, 14          # inner upper / lower lip centers
_LM_CL, _LM_CR = 61, 291         # left / right mouth corners


def compute_motion_energy(path, method="lipvar", score_win=0.4):
    """Pass 1: per-frame speaking score. Returns (score, fps, n, (w,h)).

    method="lipvar" (default): MediaPipe FaceMesh mouth-openness RATIO (vertical gap / mouth
        width), then a rolling std over `score_win` s — high when the mouth oscillates open/closed
        (speech), low for a sustained smile (width up, vertical flat) or a closed mouth. Falls back
        to pixel-diff for frames with no detected face.
    method="pixeldiff": legacy mean-abs inter-frame diff over the lower-center mouth ROI.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = h = 0

    if method == "pixeldiff":
        energies, prev = [], None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            r0, r1, c0, c1 = mouth_roi(h, w)
            roi = gray[r0:r1, c0:c1].astype(np.float32)
            energies.append(0.0 if prev is None else float(np.mean(np.abs(roi - prev))))
            prev = roi
        cap.release()
        return np.asarray(energies, dtype=float), float(fps), len(energies), (w, h)

    # lipvar
    import mediapipe as mp
    fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                         refine_landmarks=False, min_detection_confidence=0.5,
                                         min_tracking_confidence=0.5)
    openness, pdiff, prev = [], [], None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = fm.process(rgb)
            # pixel-diff fallback signal (same ROI as legacy)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            r0, r1, c0, c1 = mouth_roi(h, w)
            roi = gray[r0:r1, c0:c1]
            pdiff.append(0.0 if prev is None else float(np.mean(np.abs(roi - prev))))
            prev = roi
            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                vgap = abs(lm[_LM_UP].y - lm[_LM_LO].y)
                width = abs(lm[_LM_CL].x - lm[_LM_CR].x) + 1e-6
                openness.append(vgap / width)
            else:
                openness.append(np.nan)
    finally:
        fm.close()
        cap.release()

    openness = np.asarray(openness, dtype=float)
    # interpolate missing (no-face) frames so the rolling std isn't corrupted by NaNs
    if np.isnan(openness).any():
        idx = np.arange(len(openness))
        good = ~np.isnan(openness)
        if good.sum() >= 2:
            openness = np.interp(idx, idx[good], openness[good])
        else:
            openness = np.nan_to_num(openness)
    win = max(2, int(round(score_win * fps)))
    score = _rolling_std(openness, win)
    # where FaceMesh produced (near) nothing, blend in the pixel-diff signal so a totally
    # undetected crop still yields a usable (if coarser) score
    if float(np.max(score)) < 1e-5:
        score = np.asarray(pdiff, dtype=float)
    return score, float(fps), len(score), (w, h)


def render_stream(left_path, right_path, active, out_path, out_size, fourcc="mp4v"):
    """Pass 2: read both crops in lockstep, write the active side's frame (resized)."""
    capL = cv2.VideoCapture(left_path)
    capR = cv2.VideoCapture(right_path)
    fps = capL.get(cv2.CAP_PROP_FPS) or 30.0
    W, H = out_size
    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*fourcc), fps, (W, H))
    n = len(active)
    for t in range(n):
        okL, fL = capL.read()
        okR, fR = capR.read()
        if not (okL and okR):
            break
        frame = fL if active[t] == 0 else fR
        if frame.shape[1] != W or frame.shape[0] != H:
            frame = cv2.resize(frame, (W, H))
        vw.write(frame)
    capL.release(); capR.release(); vw.release()


def render_overlay(left_path, right_path, active, out_path, tile=256):
    """QC: side-by-side L|R with the active side boxed green."""
    capL = cv2.VideoCapture(left_path)
    capR = cv2.VideoCapture(right_path)
    fps = capL.get(cv2.CAP_PROP_FPS) or 30.0
    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (tile * 2, tile))
    n = len(active)
    for t in range(n):
        okL, fL = capL.read(); okR, fR = capR.read()
        if not (okL and okR):
            break
        fL = cv2.resize(fL, (tile, tile)); fR = cv2.resize(fR, (tile, tile))
        if active[t] == 0:
            cv2.rectangle(fL, (2, 2), (tile - 3, tile - 3), (0, 255, 0), 4)
            cv2.putText(fL, "ACTIVE", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.rectangle(fR, (2, 2), (tile - 3, tile - 3), (0, 255, 0), 4)
            cv2.putText(fR, "ACTIVE", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(fL, "LEFT", (8, tile - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(fR, "RIGHT", (8, tile - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        vw.write(np.hstack([fL, fR]))
    capL.release(); capR.release(); vw.release()


def qc_metrics(energy_l, energy_r, active, fps, turns, smooth_win):
    sw = max(1, int(round(smooth_win * fps)))
    sl = _moving_average(np.asarray(energy_l, float), sw)
    sr = _moving_average(np.asarray(energy_r, float), sw)
    n = min(len(sl), len(sr), len(active))
    sl, sr, active = sl[:n], sr[:n], active[:n]
    shown = np.where(active == 0, sl, sr)
    hidden = np.where(active == 0, sr, sl)
    consistent = float(np.mean(shown >= hidden)) if n else 0.0
    # voiced-frame consistency: among frames where SOMEONE is clearly talking (max score above a
    # noise floor), is the shown side the louder one? Excludes mutual-pause frames where the
    # comparison is just noise — a fairer measure of whether the stream tracks the real speaker.
    peak = np.maximum(sl, sr)
    floor = 0.25 * float(np.median(peak[peak > 0])) if np.any(peak > 0) else 0.0
    voiced = peak > floor
    voiced_consistent = float(np.mean(shown[voiced] >= hidden[voiced])) if voiced.any() else 0.0
    durs = [t1 - t0 for _, t0, t1 in turns]
    sides = [s for s, _, _ in turns]
    alternations = sum(1 for k in range(1, len(sides)) if sides[k] != sides[k - 1])
    return {
        "lip_activity_consistency": round(consistent, 4),
        "voiced_consistency": round(voiced_consistent, 4),
        "voiced_frac": round(float(np.mean(voiced)), 4) if n else 0.0,
        "n_turns": len(turns),
        "alternation_rate": round(alternations / max(1, len(sides) - 1), 4),
        "mean_turn_sec": round(float(np.mean(durs)), 3) if durs else 0.0,
        "median_turn_sec": round(float(np.median(durs)), 3) if durs else 0.0,
        "shown_motion_mean": round(float(np.mean(shown)), 4) if n else 0.0,
        "hidden_motion_mean": round(float(np.mean(hidden)), 4) if n else 0.0,
        "left_motion_mean": round(float(np.mean(sl)), 4) if n else 0.0,
        "right_motion_mean": round(float(np.mean(sr)), 4) if n else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stem", default=None, help="default: left filename minus __left/ - שמאל")
    ap.add_argument("--method", choices=["lipvar", "pixeldiff"], default="lipvar",
                    help="speaking signal: lipvar=FaceMesh mouth-openness variance (default), "
                         "pixeldiff=legacy mouth-ROI frame diff")
    ap.add_argument("--score-win", type=float, default=0.4, help="rolling-std window (s) for lipvar")
    ap.add_argument("--min-dwell", type=float, default=0.4)
    ap.add_argument("--smooth-win", type=float, default=0.3)
    ap.add_argument("--merge-target", type=float, default=6.0)
    ap.add_argument("--out-size", type=int, default=256)
    ap.add_argument("--overlay", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    stem = args.stem
    if stem is None:
        b = os.path.splitext(os.path.basename(args.left))[0]
        for suf in ("__left", " - שמאל", "_left"):
            if b.endswith(suf):
                b = b[: -len(suf)]
        stem = b.strip().replace(" ", "_")

    eL, fpsL, nL, dimL = compute_motion_energy(args.left, args.method, args.score_win)
    eR, fpsR, nR, dimR = compute_motion_energy(args.right, args.method, args.score_win)
    fps = fpsL or fpsR or 30.0
    active, turns = build_active_timeline(eL, eR, fps, args.smooth_win, args.min_dwell)
    segments = merge_turns_to_segments(turns, stem, args.merge_target, args.min_dwell)
    duration = round(len(active) / fps, 3)

    out_size = (args.out_size, args.out_size)
    stream_path = os.path.join(args.out_dir, f"{stem}__stream.mp4")
    render_stream(args.left, args.right, active, stream_path, out_size)

    turns_obj = {"stem": stem, "fps": fps, "duration": duration,
                 "turns": [{"idx": i, "side": s, "t0": round(t0, 3), "t1": round(t1, 3)}
                           for i, (s, t0, t1) in enumerate(turns)]}
    seg_obj = {"stem": stem, "fps_model": 25, "segments": segments}
    qc = qc_metrics(eL, eR, active, fps, turns, args.smooth_win)
    qc["n_segments"] = len(segments)
    qc["duration_sec"] = duration

    for name, obj in [("__turns.json", turns_obj), ("__segments.json", seg_obj),
                      ("__qc_metrics.json", qc)]:
        with open(os.path.join(args.out_dir, stem + name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    if args.overlay:
        render_overlay(args.left, args.right, active,
                       os.path.join(args.out_dir, f"{stem}__qc_overlay.mp4"))

    print(f"[stream] {stem}: {len(turns)} turns, {len(segments)} segments, "
          f"lip_consistency={qc['lip_activity_consistency']:.3f}, dur={duration}s -> {stream_path}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
