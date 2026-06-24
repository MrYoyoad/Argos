#!/usr/bin/env python3
"""Build a canonical ASCII-safe index of the Egla-Kafe dataset.

The source filenames are Hebrew with spaces (e.g. ``תומר ויועד 1.mp4``), which break the
VSP pipeline's bash globbing / TSV / seg-id regex. This scans the byte-exact mirror and emits
``work/eval/index.json``: one entry per source video with a safe ASCII stem, the parsed
scene/script/speaker-pair/camera-angle, the source type, and paths to any existing L/R crops.

Filename grammar (client): ``<NameA> ו<NameB> [זוית NN] [-]<take>``  (ו = Hebrew "and", prefixed
to the 2nd name). שפם names are prefixed ``סצנה N`` (a take label, NOT the top-level scene folder).
Scene folder → script: ``סצנה 1`` → script1 (Emma/Jake), ``סצנה 2`` → script2 (Tom/Dan),
``שפם`` → script TBD (per-file 1/2 to be confirmed; left null here).
"""
import argparse
import json
import os
import re
import sys

# Hebrew speaker name -> ascii
NAME_MAP = {
    "תומר": "tomer", "יועד": "yoad", "טל": "tal", "עידו": "ido", "עמוסי": "amosi", "דן": "dan",
}
SCENE_DIR_MAP = {  # top-level folder -> (scene_id, script_id)
    "סצנה 1": ("scene1", "script1"),
    "סצנה 2": ("scene2", "script2"),
    "שפם": ("shaam", None),  # per-file script confirmed later
}
SIDE_MAP = {"שמאל": "left", "ימין": "right"}


def _strip_noise(name: str):
    """Remove angle/scene/take tokens; return (clean_name_part, angle)."""
    angle = "front"
    m = re.search(r"זוית\s*(\d+)", name)
    if m:
        angle = m.group(1)
    name = re.sub(r"זוית\s*\d+", " ", name)      # camera angle
    name = re.sub(r"סצנה\s*\d+", " ", name)        # שפם take label
    name = re.sub(r"ללא\s*שפם", " ", name)         # "without mustache" descriptor
    name = re.sub(r"[-_]\s*\d+\s*$", " ", name)    # trailing take number "-1"
    name = re.sub(r"\s+\d+\s*$", " ", name)        # trailing bare take number
    name = re.sub(r"\s+", " ", name).strip()
    return name, angle


def parse_speakers(name: str):
    """Parse 'NameA וNameB' -> ['namea','nameb'] (ascii). Unknown names kept transliterated-ish."""
    clean, _ = _strip_noise(name)
    speakers = []
    for tok in clean.split():
        t = tok
        # the conjunction ו is glued to the 2nd name
        if t.startswith("ו") and t not in NAME_MAP and t[1:] in NAME_MAP:
            t = t[1:]
        speakers.append(NAME_MAP.get(t, t))
    # drop any stray non-name tokens (digits etc.)
    speakers = [s for s in speakers if not s.isdigit()]
    return speakers


def make_stem(scene_id, name, angle, idx):
    clean, _ = _strip_noise(name)
    sp = parse_speakers(name)
    base = "_".join(sp) if sp else "spk"
    parts = [{"scene1": "s1", "scene2": "s2", "shaam": "shaam"}.get(scene_id, scene_id), base]
    if angle != "front":
        parts.append(f"z{angle}")
    parts.append(str(idx))
    stem = "_".join(parts)
    return re.sub(r"[^a-z0-9_]", "", stem.lower())


def build_index(root: str):
    dataset = os.path.join(root, "dataset")
    crops_root = os.path.join(dataset, "קטעי דוברים")
    entries = []
    seen = {}
    # scene-recording originals
    for folder, (scene_id, script_id) in SCENE_DIR_MAP.items():
        d = os.path.join(dataset, folder)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".mp4"):
                continue
            name = os.path.splitext(fn)[0].strip()
            speakers = parse_speakers(name)
            angle = _strip_noise(name)[1]
            idx = seen.get((scene_id, tuple(speakers), angle), 0) + 1
            seen[(scene_id, tuple(speakers), angle)] = idx
            stem = make_stem(scene_id, name, angle, idx)
            # existing crops (by exact stem match in crops folder, trailing-space tolerant)
            crop_dir = os.path.join(crops_root, folder)
            left = right = None
            if os.path.isdir(crop_dir):
                for cf in os.listdir(crop_dir):
                    base = os.path.splitext(cf)[0]
                    for heb, side in SIDE_MAP.items():
                        suff = f" - {heb}"
                        if base.endswith(suff) and base[: -len(suff)].strip() == name.strip():
                            p = os.path.join(crop_dir, cf)
                            if side == "left":
                                left = p
                            else:
                                right = p
            entries.append({
                "stem": stem, "scene": scene_id, "script": script_id,
                "speakers_in_name": speakers, "angle": angle,
                "source_type": "scene_recording", "orig_name": name,
                "orig_path": os.path.join(d, fn),
                "existing_crops": {"left": left, "right": right},
            })
    # 4K masters (different angle/camera; the שפם scene from the iPhone). The user supplied L/R
    # crops under "קטעי דוברים/שפם 4K/IMG_NNNN - שמאל|ימין.mp4" — attach them (reuse path).
    crop4k_dir = os.path.join(crops_root, "שפם 4K")
    for fn in sorted(os.listdir(dataset)):
        if re.match(r"IMG_\d+\.mp4$", fn):
            base = os.path.splitext(fn)[0]
            stem = base.lower()
            left = right = None
            if os.path.isdir(crop4k_dir):
                l = os.path.join(crop4k_dir, f"{base} - שמאל.mp4")
                r = os.path.join(crop4k_dir, f"{base} - ימין.mp4")
                left = l if os.path.exists(l) else None
                right = r if os.path.exists(r) else None
            entries.append({
                # masters belong to the שפם session (4K angle); per-file script (1/2) TBD
                "stem": stem, "scene": "shaam_4k", "script": None,
                "speakers_in_name": [], "angle": "master_4k",
                "source_type": "master", "orig_name": base,
                "orig_path": os.path.join(dataset, fn),
                "existing_crops": {"left": left, "right": right},
            })
    # uniqueness check
    stems = [e["stem"] for e in entries]
    dupes = {s for s in stems if stems.count(s) > 1}
    if dupes:
        print(f"[WARN] duplicate stems: {dupes}", file=sys.stderr)
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/home/ubuntu/datasets/clients/egla_kafe")
    ap.add_argument("--out", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json")
    args = ap.parse_args()
    entries = build_index(args.root)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"n": len(entries), "entries": entries}, f, ensure_ascii=False, indent=2)
    # summary
    by_scene = {}
    for e in entries:
        by_scene.setdefault(e["scene"], []).append(e)
    print(f"[index] {len(entries)} videos -> {args.out}", file=sys.stderr)
    for sc, es in by_scene.items():
        haveboth = sum(1 for e in es if e["existing_crops"]["left"] and e["existing_crops"]["right"])
        print(f"  {sc}: {len(es)} videos, {haveboth} with existing L/R crops", file=sys.stderr)


if __name__ == "__main__":
    main()
