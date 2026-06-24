#!/usr/bin/env python3
"""Detection-based per-speaker cropper — produce uniform single-face L/R crops for ANY source.

Completes the L/R split for videos that lack hand-made crops (the 4K masters, and any future
footage). Samples frames, detects every face (MediaPipe), clusters faces by horizontal position,
keeps the two side speakers (drops a constant center listener when present), and emits a stable
square crop per side. See work/eval/INTERFACES.md §2.

Static-per-video (one fixed box per speaker) — the fast version. Phase B upgrades to per-frame
dynamic tracking.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np


def detect_faces_all(frame, fd):
    """Return list of (x_center_norm, y_center_norm, x, y, w, h) for every face in the frame."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = fd.process(rgb)
    out = []
    if res.detections:
        for det in res.detections:
            bb = det.location_data.relative_bounding_box
            x, y = bb.xmin * w, bb.ymin * h
            bw, bh = bb.width * w, bb.height * h
            out.append((bb.xmin + bb.width / 2, bb.ymin + bb.height / 2, x, y, bw, bh))
    return out


def cluster_speakers(dets, n_speakers=2, n_people=None):
    """dets: list of (xc_norm, yc_norm, x,y,w,h). Returns (kept_clusters left..right, dropped).

    k (number of x-position clusters) is driven by the actual people count `n_people` (estimated
    by the caller from the modal faces/frame), clamped to [n_speakers, n_speakers+1]. So a
    2-person master clusters into 2 (keep both), a 3-person scene into 3 (drop the center
    listener). Falls back to n_speakers when n_people is unknown.
    """
    if not dets:
        return [], False
    xs = np.array([d[0] for d in dets])
    from sklearn.cluster import KMeans
    uniq = np.unique(np.round(xs, 2))
    base = n_people if (n_people and n_people > 0) else n_speakers
    k = int(min(max(n_speakers, base), n_speakers + 1))
    k = min(k, len(uniq))
    if k == 1:
        labels = np.zeros(len(xs), dtype=int)
        centers = [xs.mean()]
    else:
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(xs.reshape(-1, 1))
        labels = km.labels_
        centers = km.cluster_centers_.ravel().tolist()
    order = np.argsort(centers)  # left -> right
    clusters = []
    for ci in order:
        members = [dets[i] for i in range(len(dets)) if labels[i] == ci]
        if not members:
            continue
        box = np.median(np.array([[m[2], m[3], m[4], m[5]] for m in members]), axis=0)
        clusters.append({"x_center": float(centers[ci]), "box": box.tolist(),
                         "n_det": len(members)})
    # keep the two extreme-x clusters; drop the middle listener if 3
    dropped = False
    if len(clusters) > n_speakers:
        keep = [clusters[0], clusters[-1]] if n_speakers == 2 else clusters[:n_speakers]
        dropped = True
        clusters = keep
    return clusters, dropped


def square_crop_box(box, W, H, pad=1.9):
    """Expand a face bbox [x,y,w,h] to a padded square, clamped to frame."""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    side = max(w, h) * pad
    side = min(side, min(W, H))
    x0 = int(round(cx - side / 2)); y0 = int(round(cy - side / 2))
    x0 = max(0, min(x0, W - int(side))); y0 = max(0, min(y0, H - int(side)))
    return x0, y0, int(round(side)), int(round(side))


def ffmpeg_crop(video, box, out, keep_audio=True):
    x, y, w, h = box
    vf = f"crop={w}:{h}:{x}:{y}"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", vf,
           "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if keep_audio:
        cmd += ["-c:a", "aac"]
    else:
        cmd += ["-an"]
    cmd.append(out)
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def verify_single_face(path, fd, sample=15):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    idxs = np.linspace(0, max(0, total - 1), sample).astype(int)
    counts = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        counts.append(len(detect_faces_all(fr, fd)))
    cap.release()
    if not counts:
        return False, 0.0
    counts = np.array(counts)
    # "single stable face" = exactly one face in the majority of sampled frames
    return bool(np.mean(counts == 1) >= 0.6), float(np.mean(counts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--stem", default=None)
    ap.add_argument("--n-speakers", type=int, default=2)
    ap.add_argument("--sample-fps", type=float, default=3.0)
    ap.add_argument("--keep-audio", action="store_true", default=True)
    args = ap.parse_args()

    import mediapipe as mp
    os.makedirs(args.out_dir, exist_ok=True)
    stem = args.stem or os.path.splitext(os.path.basename(args.video))[0]

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"ERROR: cannot open {args.video}", file=sys.stderr); sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, int(round(fps / args.sample_fps)))

    fd = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5, model_selection=1)
    dets = []
    face_counts = []
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            fs = detect_faces_all(frame, fd)
            face_counts.append(len(fs))
            dets.extend(fs)
        i += 1
    cap.release()
    n_sampled = len(face_counts)
    modal_faces = int(np.bincount(face_counts).argmax()) if face_counts else 0

    clusters, dropped = cluster_speakers(dets, args.n_speakers, n_people=modal_faces)
    if len(clusters) < 2:
        print(f"ERROR: detected <2 speaker clusters ({len(clusters)}) in {stem}", file=sys.stderr)
        sys.exit(2)

    sides = ["left", "right"]
    speakers_meta = []
    for side, cl in zip(sides, clusters[:2]):
        box = square_crop_box(cl["box"], W, H)
        out = os.path.join(args.out_dir, f"{stem}__{side}.mp4")
        ok = ffmpeg_crop(args.video, box, out, args.keep_audio)
        sf_ok, mean_faces = (verify_single_face(out, fd) if ok else (False, 0.0))
        speakers_meta.append({"side": side, "box": list(box), "x_center": round(cl["x_center"], 4),
                              "n_det": cl["n_det"], "single_face_ok": sf_ok,
                              "verify_mean_faces": round(mean_faces, 2), "out": out, "ok": ok})
    fd.close()

    meta = {"source": os.path.abspath(args.video), "stem": stem, "fps": fps,
            "src_width": W, "src_height": H, "n_frames_sampled": n_sampled,
            "modal_faces_per_frame": modal_faces, "center_dropped": dropped,
            "speakers": speakers_meta}
    with open(os.path.join(args.out_dir, f"{stem}__crops.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[crops] {stem}: modal_faces={modal_faces} center_dropped={dropped} "
          f"single_face_ok={[s['single_face_ok'] for s in speakers_meta]}", file=sys.stderr)


if __name__ == "__main__":
    main()
