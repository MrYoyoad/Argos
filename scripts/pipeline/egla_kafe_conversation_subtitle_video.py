#!/usr/bin/env python3
"""Full-length 'said vs heard' subtitle video per conversation, on the JOINT frame.

Plays the original scene video (both speakers visible) and burns, timed to each speaker turn:
  line 1 — what was actually SAID (the script line, white)
  line 2 — what the model HEARD (its lip-read transcription), each word colored by confidence
           (green=high / orange=med / red=low)
Uses the per-turn (split-speaker) decode — the better arm — but displays it on the joint frame so
the whole thing reads as one continuous captioned conversation. Rendered via ASS subtitles (clean
per-word color + wrapping + timing).
"""
import argparse, glob, json, os, subprocess

RUNS = {
    "scene12": {"seg_meta": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_scene12_all/seg_meta.json",
                "align": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_scene12_all/align",
                "wconf": "/home/ubuntu/flat_runs_archive/20260624_145832/client_outputs/report/word_confidence.json"},
    "shaam":   {"seg_meta": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_shaam_all/seg_meta.json",
                "align": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_shaam_all/align",
                "wconf": "/home/ubuntu/flat_runs_archive/20260624_200135/client_outputs/report/word_confidence.json"},
}
# conf_class -> RGB
CONF_RGB = {"conf-high": (0x3C, 0xB3, 0x43), "conf-med": (0xFF, 0x98, 0x00), "conf-low": (0xF4, 0x43, 0x36)}
WHITE_RGB = (0xFF, 0xFF, 0xFF)
LABEL_RGB = (0x9A, 0xD8, 0xF0)  # light cyan for the "said/heard" labels


def ass_color(rgb):  # ASS is &HBBGGRR&
    r, g, b = rgb
    return f"&H{b:02X}{g:02X}{r:02X}&"


def t_fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{int(s):02d}.{int(round((s - int(s)) * 100)):02d}"


def esc(s):
    return (s or "").replace("{", "(").replace("}", ")").replace("\n", " ")


def find_run(stem, align_root_key=None):
    for key, cfg in RUNS.items():
        if os.path.isdir(os.path.join(cfg["align"], stem)):
            return key, cfg
    return None, None


def build_ass(stem, W, H, out_ass):
    key, cfg = find_run(stem)
    if not cfg:
        raise SystemExit(f"no run/align found for {stem}")
    seg_meta = json.load(open(cfg["seg_meta"]))
    align = json.load(open(os.path.join(cfg["align"], stem, "alignment.json")))
    wconf = json.load(open(cfg["wconf"]))
    s2c = align.get("side_to_char", {})
    ref_by = {s["seg_id"]: s for s in align["segments"]}
    segs = sorted([(k, v) for k, v in seg_meta.items() if v["stem"] == stem], key=lambda kv: kv[1]["t0"])

    fs = max(20, int(H * 0.042))          # font size scales with height
    fs_lbl = int(fs * 0.75)
    events = []
    for seg_id, m in segs:
        a = ref_by.get(seg_id)
        if not a:
            continue
        char = (a.get("char") or s2c.get(m["side"]) or "").upper()
        ref = esc(a.get("ref", "")).strip()
        words = wconf.get(seg_id, {}).get("words", [])
        # colored hyp
        parts = []
        for w in words:
            c = ass_color(CONF_RGB.get(w.get("conf_class"), WHITE_RGB))
            parts.append(f"{{\\c{c}}}{esc(w['word'])}")
        hyp = " ".join(parts) if parts else "{\\c" + ass_color((0x88, 0x88, 0x88)) + "}(no speech read)"
        lbl = ass_color(LABEL_RGB); wht = ass_color(WHITE_RGB)
        # one event, two lines: SAID (white) \N model heard (colored)
        text = (f"{{\\c{lbl}}}{char} said:  {{\\c{wht}}}{ref}"
                f"\\N{{\\c{lbl}}}model read:  {hyp}")
        events.append((m["t0"], m["t1"], text))

    box = "&H64000000"  # semi-transparent black box (AABBGGRR, AA=0x64)
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Cap,DejaVu Sans,{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,{box},"
        f"-1,0,0,0,100,100,0,0,3,2,0,2,40,40,28,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for t0, t1, text in events:
        ass.append(f"Dialogue: 0,{t_fmt(t0)},{t_fmt(t1)},Cap,,0,0,0,,{text}")
    open(out_ass, "w", encoding="utf-8").write("\n".join(ass) + "\n")
    return key


def probe_wh(path):
    """Return the DISPLAY dimensions (post-rotation) by extracting one auto-rotated frame —
    robust to rotation metadata on the 4K iPhone masters (ffmpeg auto-rotates before filters)."""
    from PIL import Image
    tmp = "/tmp/_ek_probe.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", path,
                    "-frames:v", "1", tmp], capture_output=True, text=True)
    if os.path.exists(tmp):
        with Image.open(tmp) as im:
            return im.width, im.height
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                          "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip().split(",")
    return int(out[0]), int(out[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", required=True, help="comma list or 'scene12'/'shaam'/'all'")
    ap.add_argument("--out-dir", default="/home/ubuntu/datasets/clients/egla_kafe/deliverables/conversation_videos")
    ap.add_argument("--max-h", type=int, default=900, help="scale output down if taller")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    idx = {e["stem"]: e for e in json.load(open("/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json"))["entries"]}

    if args.stems in ("scene12", "shaam", "all"):
        stems = [s for s in sorted(os.listdir(RUNS[args.stems]["align"]))] if args.stems != "all" else \
                sorted(set(list(os.listdir(RUNS["scene12"]["align"])) + list(os.listdir(RUNS["shaam"]["align"]))))
    else:
        stems = args.stems.split(",")

    for stem in stems:
        e = idx.get(stem)
        if not e:
            print(f"[skip] {stem}: not in index"); continue
        src = e["orig_path"]
        W, H = probe_wh(src)
        # scale target (keep aspect); ass PlayRes must match final dims
        if H > args.max_h:
            oh = args.max_h; ow = int(round(W * oh / H / 2) * 2)
        else:
            ow, oh = W, H
        ass_path = os.path.join(args.out_dir, f"{stem}.ass")
        build_ass(stem, ow, oh, ass_path)
        out = os.path.join(args.out_dir, f"{stem}__said_vs_heard.mp4")
        vf = f"scale={ow}:{oh},ass={ass_path}" if (ow, oh) != (W, H) else f"ass={ass_path}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf,
               "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", "-an", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(out)
        print(f"[{'ok' if ok else 'FAIL'}] {stem} -> {out} ({ow}x{oh})" + ("" if ok else f"  {r.stderr[-200:]}"))


if __name__ == "__main__":
    main()
