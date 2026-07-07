#!/usr/bin/env python3
"""Identify which named person is on which side of each video — by face clustering.

Filenames give the speaker PAIR (e.g. 'תומר ויועד') but not who sat left vs right. We:
  1. embed each L/R crop's face (ArcFace via insightface), averaged over sampled frames;
  2. cluster embeddings into distinct identities (cosine, agglomerative);
  3. NAME each cluster with zero manual labels via the pair constraint — a person's cluster spans
     several videos, and the one name common to ALL those videos' pairs is that person.

Output: work/eval/face_id.json — per crop (video,side) -> person name, plus per-cluster summary.
This feeds per-PERSON statistics (who was where) into the evaluation.
"""
import argparse
import json
import os
from collections import Counter

import cv2
import numpy as np


def embed_crop(app, path, n_frames=6):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    idxs = np.linspace(0, max(0, total - 1), n_frames).astype(int)
    embs = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        faces = app.get(fr)
        if not faces:
            continue
        f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        embs.append(f.normed_embedding)
    cap.release()
    if not embs:
        return None
    v = np.mean(embs, axis=0)
    return v / (np.linalg.norm(v) + 1e-9)


def name_clusters(labels, crops):
    """Assign each cluster a unique person name by constraint propagation.

    A cluster is ONE person, appearing as one of the two named people in each of its videos, so its
    name must lie in EVERY one of those videos' pairs -> candidate = intersection of pairs. Assign
    clusters with a single candidate first, remove that name from others' candidates, and repeat;
    remaining ambiguous clusters (e.g. a person who ALWAYS co-appears with one partner, like Tal with
    Yoad) take the leftover name by elimination.
    """
    by_cluster = {}
    for lab, c in zip(labels, crops):
        by_cluster.setdefault(lab, []).append(c)
    # candidate names per cluster = intersection of its videos' pairs (ignoring nameless masters)
    cand = {}
    for lab, items in by_cluster.items():
        common = None
        for c in items:
            if not c["pair"]:
                continue  # master crop: no name constraint
            s = set(c["pair"])
            common = s if common is None else (common & s)
        cand[lab] = set(common) if common else set()
    names, assigned = {}, set()
    changed = True
    while changed:
        changed = False
        for lab, cs in cand.items():
            if lab in names:
                continue
            rem = cs - assigned
            if len(rem) == 1:
                names[lab] = next(iter(rem)); assigned.add(names[lab]); changed = True
    # leftover clusters (no name constraint = masters, or fully ambiguous) -> nearest named cluster
    # by embedding is resolved in main(); here mark unresolved
    for lab in by_cluster:
        names.setdefault(lab, None)
    return names, by_cluster, cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json")
    ap.add_argument("--out", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/face_id.json")
    ap.add_argument("--scenes", default="scene1,scene2,shaam,shaam_4k")
    ap.add_argument("--n-clusters", type=int, default=5, help="known distinct people")
    ap.add_argument("--cache", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/face_emb_cache.npz")
    args = ap.parse_args()

    idx = json.load(open(args.index, encoding="utf-8"))
    scenes = set(args.scenes.split(","))
    all_scenes = "all" in scenes
    # collect crop list first
    crops = []
    for e in idx["entries"]:
        if not all_scenes and e.get("scene") not in scenes:
            continue
        pair = e.get("speakers_in_name") or []
        for side in ("left", "right"):
            p = e["existing_crops"].get(side)
            if p and os.path.exists(p):
                crops.append({"stem": e["stem"], "side": side, "pair": pair,
                              "scene": e["scene"], "path": p})
    # embeddings (cached by path)
    cache = {}
    if os.path.exists(args.cache):
        z = np.load(args.cache, allow_pickle=True)
        cache = {k: z[k] for k in z.files}
    need = [c for c in crops if c["path"] not in cache]
    if need:
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        app.prepare(ctx_id=-1, det_size=(640, 640))
        for c in need:
            v = embed_crop(app, c["path"])
            if v is not None:
                cache[c["path"]] = v
        np.savez(args.cache, **cache)
    crops = [c for c in crops if c["path"] in cache]
    embs = np.array([cache[c["path"]] for c in crops])
    print(f"[face-id] embedded {len(embs)} crops ({len(need)} new)")

    from sklearn.cluster import AgglomerativeClustering
    k = min(args.n_clusters, len(embs))
    cl = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
    labels = cl.fit_predict(embs)
    names, by_cluster, cand = name_clusters(labels, crops)
    # any unresolved cluster (shouldn't happen if masters share identities) -> nearest named centroid
    centroids = {lab: np.mean([embs[i] for i in range(len(crops)) if labels[i] == lab], axis=0)
                 for lab in by_cluster}
    named_labs = [l for l, n in names.items() if n]
    for lab, nm in list(names.items()):
        if nm is None and named_labs:
            best = max(named_labs, key=lambda L: float(np.dot(centroids[lab], centroids[L])))
            names[lab] = names[best]
    n_clusters = len(set(labels))
    print(f"[face-id] {n_clusters} identity clusters; candidates={ {l: sorted(c) for l,c in cand.items()} }")
    print(f"[face-id] names: { {l: names[l] for l in sorted(by_cluster)} }")
    # verify: every named video's two sides got its two pair names
    bad = 0
    perv = {}
    for lab, c in zip(labels, crops):
        perv.setdefault(c["stem"], {})[c["side"]] = (names[lab], c["pair"])
    for stem, sides in perv.items():
        pair = next((v[1] for v in sides.values() if v[1]), None)
        if pair and len(sides) == 2:
            got = {v[0] for v in sides.values()}
            if got != set(pair):
                bad += 1
                print(f"  [verify-FAIL] {stem}: got {got} expected {set(pair)}")
    print(f"[face-id] verification: {len(perv)-bad}/{len(perv)} videos consistent")

    per_crop = {}
    for lab, c in zip(labels, crops):
        per_crop[f"{c['stem']}__{c['side']}"] = {
            "stem": c["stem"], "side": c["side"], "scene": c["scene"],
            "cluster": int(lab), "person": names[lab], "pair_in_name": c["pair"]}
    clusters_summary = []
    for lab, items in by_cluster.items():
        clusters_summary.append({"cluster": int(lab), "person": names[lab], "n_crops": len(items),
                                 "videos": sorted({i["stem"] for i in items})})
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"n_crops": len(crops), "n_clusters": n_clusters,
                   "per_crop": per_crop, "clusters": clusters_summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"[face-id] -> {args.out}")
    for cs in sorted(clusters_summary, key=lambda x: -x["n_crops"]):
        print(f"  {cs['person']:>8}: {cs['n_crops']} crops in {len(cs['videos'])} videos")


if __name__ == "__main__":
    main()
