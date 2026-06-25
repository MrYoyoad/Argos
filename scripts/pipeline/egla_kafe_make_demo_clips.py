#!/usr/bin/env python3
"""
Egla-Kafe (עגלת קפה) demo clip builder.

Produces four client-facing demo clips (each 12-20s, H.264, on-frame labels)
into datasets/clients/egla_kafe/deliverables/clips/:

  1) active_speaker_overlay.mp4 — trims the existing L|R active-speaker overlay
     to a clean L/R-alternation stretch and adds a title bar. (img_6825 variant
     too, if an overlay exists.)
  2) confidence_colored.mp4 — burns a strong video's lip-read words onto its
     stacked stream, colored by per-word confidence band (green=high,
     orange=med, red=low), timed to the stream's segments. A second clip on a
     weak take (mostly red) is also produced.
  3) best_vs_worst.mp4 — hstack of two streams with their lip-read hyps burned:
     img_6825 (iPhone 4K frontal, recovers the conversation) vs
     s1_yoad_tal_z45_1 (45-degree profile, fails).
  4) iphone_vs_camera.mp4 — the SAME Military (scene2) script captured by two
     cameras, hyps burned + labels: img_6825 (iPhone 4K) vs shaam_amosi_ido_1
     (client camera). Panels are aligned by shared reference line.

All source crop paths have Hebrew names; they are read from index.json
existing_crops rather than hardcoded. Streams/overlays are 256-px tall.

This script is self-contained (only stdlib + ffmpeg on PATH). Reuses the ASS
per-word coloring approach from VSP-LLM/scripts/make_burn.py.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path("/home/ubuntu/datasets/clients/egla_kafe")
STREAMS = ROOT / "work" / "streams"
EVAL = ROOT / "work" / "eval"
INDEX = EVAL / "index.json"
OUT = ROOT / "deliverables" / "clips"

WC_SCENE12 = Path("/home/ubuntu/flat_runs_archive/20260624_145832/client_outputs/report/word_confidence.json")
WC_SHAAM = Path("/home/ubuntu/flat_runs_archive/20260624_200135/client_outputs/report/word_confidence.json")

# Confidence palette (ASS BGR &HBBGGRR&). Matches the HTML/burn report bands but
# uses plain green/orange/red for an at-a-glance client demo.
ASS_GREEN = "&H4CAF50&"   # green  (#50AF4C BGR-ish; ASS uses BGR so this reads green)
ASS_ORANGE = "&H00A5FF&"  # orange (#FFA500 -> BGR 00A5FF)
ASS_RED = "&H4040E0&"     # red    (#E04040 -> BGR 4040E0)
ASS_WHITE = "&HFFFFFF&"

BAND_COLOR = {"conf-high": ASS_GREEN, "conf-med": ASS_ORANGE, "conf-low": ASS_RED}

FFMPEG = "ffmpeg"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def run(cmd: List[str], timeout: int = 600) -> Tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=timeout)
    if p.returncode == 0:
        return 0, ""
    return p.returncode, "\n".join((p.stderr or "").splitlines()[-40:])


def load_json(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_index() -> Dict[str, dict]:
    d = load_json(INDEX)
    return {e["stem"]: e for e in d["entries"]}


def load_align(run_name: str, stem: str) -> List[dict]:
    p = EVAL / run_name / "align" / stem / "alignment.json"
    return load_json(p)["segments"]


def load_stream_segments(stem: str) -> List[dict]:
    p = STREAMS / stem / f"{stem}__segments.json"
    return load_json(p)["segments"]


def t0_frame(seg_id: str) -> int:
    return int(seg_id.split("_")[-2])


def ass_escape(text: str) -> str:
    return (text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}"))


def _ass_time(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ffmpeg_filter_path(p: str) -> str:
    """Escape a path for use inside an ffmpeg filter (subtitles=...)."""
    return p.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


# ----------------------------------------------------------------------------
# ASS subtitle builders
# ----------------------------------------------------------------------------
def write_ass(events: str, w: int, h: int, styles: str = "") -> str:
    default_style = (
        "Style: Default,Arial,22,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
        "1,0,0,0,100,100,0,0,1,2,1,2,16,16,12,1\n"
    )
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{default_style}{styles}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{events}"""
    tf = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".ass", delete=False)
    tf.write(ass)
    tf.flush()
    tf.close()
    return tf.name


def colored_words_run(words: List[dict]) -> str:
    """Return an ASS dialogue text string with each word colored by conf band."""
    parts = []
    for i, wd in enumerate(words):
        cc = wd.get("conf_class", "conf-med")
        color = BAND_COLOR.get(cc, ASS_WHITE)
        word = ass_escape(str(wd.get("word", "")))
        sep = " " if i < len(words) - 1 else ""
        parts.append(f"{{\\1c{color}}}{word}{sep}")
    return "".join(parts)


# ----------------------------------------------------------------------------
# Clip 1 — active-speaker overlay with title bar
# ----------------------------------------------------------------------------
def find_alternation_window(stem: str, dur: float = 18.0) -> Tuple[float, float]:
    turns = load_json(STREAMS / stem / f"{stem}__turns.json")["turns"]
    best = None
    for t in turns:
        s = t["t0"]
        e = s + dur
        win = [x for x in turns if x["t0"] >= s - 0.01 and x["t1"] <= e + 0.5]
        if len(win) < 2:
            continue
        sides = [x["side"] for x in win]
        switches = sum(1 for i in range(1, len(sides)) if sides[i] != sides[i - 1])
        score = switches + (1 if ("left" in sides and "right" in sides) else -10)
        if best is None or score > best[0]:
            best = (score, s, e)
    if best is None:
        return 0.0, dur
    return best[1], best[2]


def make_active_speaker_overlay(stem: str, out_path: Path, dur: float = 18.0) -> Optional[Path]:
    overlay = STREAMS / stem / f"{stem}__qc_overlay.mp4"
    if not overlay.exists():
        print(f"[SKIP] no overlay for {stem}")
        return None
    s0, _ = find_alternation_window(stem, dur)
    # Overlay is 512x256. Add a 40px title bar on top -> 512x296.
    title = "Active-speaker detection: the box follows whoever is talking"
    # drawtext title bar: black strip + centered text, sized to fit 512px width.
    title_esc = title.replace(":", r"\:").replace("'", r"’")
    vf = (
        "pad=iw:ih+44:0:44:color=black,"
        f"drawtext=text='{title_esc}':fontcolor=white:fontsize=15:"
        "x=(w-text_w)/2:y=14:box=0"
    )
    cmd = [
        FFMPEG, "-y", "-nostdin",
        "-ss", f"{s0:.3f}", "-i", str(overlay),
        "-t", f"{dur:.3f}",
        "-vf", vf,
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    rc, tail = run(cmd)
    if rc != 0:
        print(f"[FAIL] active_speaker {stem}: {tail}")
        return None
    print(f"[OK] {out_path}  (window {s0:.1f}-{s0+dur:.1f}s)")
    return out_path


# ----------------------------------------------------------------------------
# Clip 2 — confidence-colored stream
# ----------------------------------------------------------------------------
def make_confidence_colored(stem: str, wc: Dict[str, dict], out_path: Path,
                            title: str, t_start: float = 0.0, dur: float = 18.0) -> Optional[Path]:
    stream = STREAMS / stem / f"{stem}__stream.mp4"
    if not stream.exists():
        print(f"[SKIP] no stream for {stem}")
        return None
    segs = load_stream_segments(stem)
    t_end = t_start + dur
    # Build ASS events for each segment overlapping the window, with timing
    # shifted so the clip starts at 0.
    events = []
    for s in segs:
        sid = s["seg_id"]
        rec = wc.get(sid)
        if not rec or not rec.get("words"):
            continue
        st, en = s["t0"], s["t1"]
        if en <= t_start or st >= t_end:
            continue
        cst = max(0.0, st - t_start)
        cen = min(dur, en - t_start)
        if cen - cst < 0.15:
            continue
        text = colored_words_run(rec["words"])
        events.append(
            f"Dialogue: 0,{_ass_time(cst)},{_ass_time(cen)},Default,,0,0,0,,{text}"
        )
    if not events:
        print(f"[SKIP] no confidence segments in window for {stem}")
        return None
    # Title bar style (top) + legend.
    title_style = (
        "Style: Title,Arial,15,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,"
        "1,0,0,0,100,100,0,0,1,2,0,8,10,10,6,1\n"
    )
    legend_style = (
        "Style: Legend,Arial,13,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,"
        "1,0,0,0,100,100,0,0,1,2,0,8,10,10,28,1\n"
    )
    legend = (f"{{\\1c{ASS_GREEN}}}green=sure  "
              f"{{\\1c{ASS_ORANGE}}}orange=maybe  "
              f"{{\\1c{ASS_RED}}}red=guessing")
    events.append(f"Dialogue: 0,{_ass_time(0)},{_ass_time(dur)},Title,,0,0,0,,{ass_escape(title)}")
    events.append(f"Dialogue: 0,{_ass_time(0)},{_ass_time(dur)},Legend,,0,0,0,,{legend}")
    # Stream is 256x256; pad top by 56px for the title+legend so they don't
    # cover the faces. New canvas 256x312.
    pad_top = 56
    w, h = 256, 256 + pad_top
    ass = write_ass("\n".join(events), w, h, styles=title_style + legend_style)
    vf = (
        f"pad=iw:ih+{pad_top}:0:{pad_top}:color=black,"
        f"subtitles='{ffmpeg_filter_path(ass)}'"
    )
    cmd = [
        FFMPEG, "-y", "-nostdin",
        "-ss", f"{t_start:.3f}", "-i", str(stream),
        "-t", f"{dur:.3f}",
        "-vf", vf, "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    rc, tail = run(cmd)
    Path(ass).unlink(missing_ok=True)
    if rc != 0:
        print(f"[FAIL] confidence {stem}: {tail}")
        return None
    print(f"[OK] {out_path}")
    return out_path


def window_band_stats(stem: str, wc: Dict[str, dict], t_start: float, dur: float) -> Tuple[int, int, int]:
    segs = load_stream_segments(stem)
    g = y = r = 0
    for s in segs:
        if s["t1"] <= t_start or s["t0"] >= t_start + dur:
            continue
        rec = wc.get(s["seg_id"])
        if not rec:
            continue
        for wd in rec["words"]:
            cc = wd.get("conf_class")
            if cc == "conf-high":
                g += 1
            elif cc == "conf-med":
                y += 1
            elif cc == "conf-low":
                r += 1
    return g, y, r


# ----------------------------------------------------------------------------
# Clip 3 / 4 — side-by-side hstack with burned hyps
# ----------------------------------------------------------------------------
def burn_caption_stream(stream: Path, label: str, caption: str,
                        out_path: Path, t_start: float, dur: float,
                        label_color: str = "&H00FFFFFF") -> bool:
    """Burn a static label (top) + caption (bottom) onto a 256x256 stream,
    padded to 256x312 (top 28 for label, bottom 28 for caption box)."""
    pad_top, pad_bot = 30, 36
    w = 256
    h = 256 + pad_top + pad_bot
    label_style = (
        f"Style: Label,Arial,14,{label_color},&H00FFFFFF,&H00000000,&HC8000000,"
        "1,0,0,0,100,100,0,0,1,2,0,8,8,8,6,1\n"
    )
    cap_style = (
        "Style: Cap,Arial,15,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC8000000,"
        "1,0,0,0,100,100,0,0,1,2,0,2,10,10,8,1\n"
    )
    cap = caption.strip() or "(no words recovered)"
    events = (
        f"Dialogue: 0,{_ass_time(0)},{_ass_time(dur)},Label,,0,0,0,,{ass_escape(label)}\n"
        f"Dialogue: 0,{_ass_time(0)},{_ass_time(dur)},Cap,,0,0,0,,{ass_escape(cap)}"
    )
    ass = write_ass(events, w, h, styles=label_style + cap_style)
    vf = (
        f"pad=iw:ih+{pad_top+pad_bot}:0:{pad_top}:color=black,"
        f"subtitles='{ffmpeg_filter_path(ass)}'"
    )
    cmd = [
        FFMPEG, "-y", "-nostdin",
        "-ss", f"{t_start:.3f}", "-i", str(stream),
        "-t", f"{dur:.3f}",
        "-vf", vf, "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    rc, tail = run(cmd)
    Path(ass).unlink(missing_ok=True)
    if rc != 0:
        print(f"[FAIL] burn {out_path.name}: {tail}")
        return False
    return True


def hstack(left: Path, right: Path, out_path: Path,
           header_left: str, header_right: str) -> Optional[Path]:
    """hstack two equal-height panels and add a header band over each half."""
    hl = header_left.replace(":", r"\:").replace("'", r"’")
    hr = header_right.replace(":", r"\:").replace("'", r"’")
    # After hstack width is 512. Add a 30px header band, write two centered labels.
    vf = (
        "[0:v][1:v]hstack=inputs=2[s];"
        "[s]pad=iw:ih+34:0:34:color=black[p];"
        f"[p]drawtext=text='{hl}':fontcolor=white:fontsize=15:x=(256-text_w)/2:y=9:box=0,"
        f"drawtext=text='{hr}':fontcolor=white:fontsize=15:x=256+(256-text_w)/2:y=9:box=0[v]"
    )
    cmd = [
        FFMPEG, "-y", "-nostdin",
        "-i", str(left), "-i", str(right),
        "-filter_complex", vf, "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    rc, tail = run(cmd)
    if rc != 0:
        print(f"[FAIL] hstack {out_path.name}: {tail}")
        return None
    print(f"[OK] {out_path}")
    return out_path


def make_best_vs_worst(out_path: Path, tmp: Path) -> Optional[Path]:
    """img_6825 (iPhone, recovers) vs s1_yoad_tal_z45_1 (45 profile, fails).

    Picks an 18s window from each stream and burns the concatenation of the
    hyps that fall in that window as a running caption.
    """
    dur = 18.0
    # LEFT: img_6825 — strong window with recognizable content (How bad / that's a
    # good point...). Use a window around the strongest matched segments.
    left_stem, left_run = "img_6825", "run_shaam_all"
    right_stem, right_run = "s1_yoad_tal_z45_1", "run_scene12_all"

    def window_caption(stem: str, run_name: str, t_start: float, dur: float) -> str:
        segs = load_stream_segments(stem)
        al = {s["seg_id"]: s for s in load_align(run_name, stem)}
        words = []
        for s in sorted(segs, key=lambda x: x["t0"]):
            if s["t1"] <= t_start or s["t0"] >= t_start + dur:
                continue
            a = al.get(s["seg_id"])
            if a and a.get("hyp", "").strip():
                words.append(a["hyp"].strip())
        cap = " ".join(words)
        return cap[:160]

    # LEFT window: from 4.6s captures "how bad", "you're showing it", "it did not
    # improve that so why are we changing everything", "that's a good point".
    lt0 = 4.6
    left_cap = window_caption(left_stem, left_run, lt0, dur)
    # RIGHT window: from 0s — profile failures.
    rt0 = 0.0
    right_cap = window_caption(right_stem, right_run, rt0, dur)

    lp = tmp / "bw_left.mp4"
    rp = tmp / "bw_right.mp4"
    ok1 = burn_caption_stream(STREAMS / left_stem / f"{left_stem}__stream.mp4",
                              "READS the conversation", left_cap, lp, lt0, dur,
                              label_color="&H0050AF4C")  # green-ish
    ok2 = burn_caption_stream(STREAMS / right_stem / f"{right_stem}__stream.mp4",
                              "Mostly fails", right_cap, rp, rt0, dur,
                              label_color="&H004040E0")  # red-ish
    if not (ok1 and ok2):
        return None
    return hstack(lp, rp, out_path,
                  "iPhone 4K, frontal", "45° profile")


def make_iphone_vs_camera(out_path: Path, tmp: Path) -> Optional[Path]:
    """Same Military (scene2) script, two cameras, aligned by shared ref line.

    img_6825 (iPhone 4K) vs shaam_amosi_ido_1 (client camera). We build a
    sequence of ref-aligned panels: for each shared reference line we show the
    matching iPhone clip (left) and camera clip (right) with their hyps burned,
    then concatenate the panels.
    """
    dur_per = 3.2  # seconds per ref-line panel
    iphone_stem = "img_6825"
    cam_stem = "shaam_amosi_ido_1"
    iphone = {s["seg_id"]: s for s in load_align("run_shaam_all", iphone_stem)}
    cam = {s["seg_id"]: s for s in load_align("run_shaam_all", cam_stem)}
    iphone_segs = {s["seg_id"]: s for s in load_stream_segments(iphone_stem)}
    cam_segs = {s["seg_id"]: s for s in load_stream_segments(cam_stem)}

    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()

    cam_by_ref = {}
    for sid, a in cam.items():
        r = norm(a.get("ref", ""))
        if r and r not in cam_by_ref and sid in cam_segs:
            cam_by_ref[r] = (sid, a)

    # Hand-picked strong refs where the iPhone clearly recovers the line.
    wanted = [
        "how bad",
        "thats a good point",
        "how many do we have",
        "what are our options",
        "you know most people think military life is action movies",
    ]
    panels = []
    for w in wanted:
        # find iPhone seg with this normalized ref
        ip = None
        for sid, a in iphone.items():
            if norm(a.get("ref", "")) == w and sid in iphone_segs:
                ip = (sid, a)
                break
        cm = cam_by_ref.get(w)
        if not ip or not cm:
            continue
        panels.append((ip, cm, a.get("ref", "")))

    if not panels:
        print("[SKIP] iphone_vs_camera: no shared-ref panels")
        return None

    panel_files = []
    for i, (ip, cm, ref) in enumerate(panels):
        ip_sid, ip_a = ip
        cm_sid, cm_a = cm
        ip_seg = iphone_segs[ip_sid]
        cm_seg = cam_segs[cm_sid]
        # center the panel on each segment, clamp to dur_per
        def clip_window(seg):
            length = seg["t1"] - seg["t0"]
            if length >= dur_per:
                return seg["t0"], dur_per
            pad = (dur_per - length) / 2.0
            return max(0.0, seg["t0"] - pad), dur_per
        ip_t, ip_d = clip_window(ip_seg)
        cm_t, cm_d = clip_window(cm_seg)
        lp = tmp / f"ivc_l_{i}.mp4"
        rp = tmp / f"ivc_r_{i}.mp4"
        ok1 = burn_caption_stream(STREAMS / iphone_stem / f"{iphone_stem}__stream.mp4",
                                  f"said: “{ref.strip()}”", ip_a.get("hyp", ""),
                                  lp, ip_t, ip_d, label_color="&H0050AF4C")
        ok2 = burn_caption_stream(STREAMS / cam_stem / f"{cam_stem}__stream.mp4",
                                  f"said: “{ref.strip()}”", cm_a.get("hyp", ""),
                                  rp, cm_t, cm_d, label_color="&H004040E0")
        if not (ok1 and ok2):
            continue
        pf = tmp / f"ivc_panel_{i}.mp4"
        if hstack(lp, rp, pf, "iPhone 4K (~1200px)", "client camera (380px)"):
            panel_files.append(pf)

    if not panel_files:
        return None
    # concat the panels
    listfile = tmp / "ivc_concat.txt"
    listfile.write_text("".join(f"file '{p}'\n" for p in panel_files))
    cmd = [
        FFMPEG, "-y", "-nostdin", "-f", "concat", "-safe", "0",
        "-i", str(listfile), "-c", "copy", str(out_path),
    ]
    rc, tail = run(cmd)
    if rc != 0:
        # fallback: re-encode concat
        cmd = [FFMPEG, "-y", "-nostdin", "-f", "concat", "-safe", "0",
               "-i", str(listfile), "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "20", "-pix_fmt", "yuv420p", str(out_path)]
        rc, tail = run(cmd)
        if rc != 0:
            print(f"[FAIL] iphone_vs_camera concat: {tail}")
            return None
    print(f"[OK] {out_path}  ({len(panel_files)} ref-aligned panels)")
    return out_path


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_tmp"
    tmp.mkdir(exist_ok=True)

    wc_scene12 = load_json(WC_SCENE12)
    wc_shaam = load_json(WC_SHAAM)

    results: Dict[str, str] = {}

    # --- Clip 1: active-speaker overlay ---
    p = make_active_speaker_overlay("s1_tomer_yoad_1", OUT / "active_speaker_overlay.mp4")
    if p:
        results[str(p)] = "Active-speaker overlay (s1_tomer_yoad_1): green box tracks the talking speaker across 12 L/R turns; titled."
    p2 = make_active_speaker_overlay("img_6825", OUT / "active_speaker_overlay_img6825.mp4")
    if p2:
        results[str(p2)] = "Active-speaker overlay (img_6825 iPhone 4K): green box tracks the talker; titled."

    # --- Clip 2: confidence-colored (strong + weak) ---
    # Strong: img_6825 window 4.6-22.6s (How bad / why are we changing everything / good point).
    p = make_confidence_colored(
        "img_6825", wc_shaam, OUT / "confidence_colored.mp4",
        "What the model is confident about (green) vs guessing (red)",
        t_start=4.6, dur=18.0)
    if p:
        g, y, r = window_band_stats("img_6825", wc_shaam, 4.6, 18.0)
        results[str(p)] = (f"Confidence-colored lip-read (img_6825 strong take): per-word green/orange/red bands, "
                           f"timed to segments. {g} green / {y} orange / {r} red words in window.")
    # Weak take: a 45-degree profile run, mostly red.
    p = make_confidence_colored(
        "s1_yoad_tal_z45_1", wc_scene12, OUT / "confidence_colored_weak.mp4",
        "A weak take: the model is mostly guessing (red)",
        t_start=0.0, dur=18.0)
    if p:
        g, y, r = window_band_stats("s1_yoad_tal_z45_1", wc_scene12, 0.0, 18.0)
        results[str(p)] = (f"Confidence-colored lip-read (s1_yoad_tal_z45_1 weak 45-degree take): mostly red. "
                           f"{g} green / {y} orange / {r} red words in window.")

    # --- Clip 3: best vs worst ---
    p = make_best_vs_worst(OUT / "best_vs_worst.mp4", tmp)
    if p:
        results[str(p)] = ("Best vs worst side-by-side: LEFT img_6825 (iPhone 4K frontal) reads the conversation; "
                           "RIGHT s1_yoad_tal_z45_1 (45-degree profile) fails. Hyps burned as captions.")

    # --- Clip 4: iphone vs camera ---
    p = make_iphone_vs_camera(OUT / "iphone_vs_camera.mp4", tmp)
    if p:
        results[str(p)] = ("Same Military (scene2) script, two cameras: LEFT iPhone 4K (~1200px) recovers each line, "
                           "RIGHT client camera (380px) hallucinates. Ref-aligned panels, hyps burned.")

    print("\n=== RESULTS ===")
    for k, v in results.items():
        print(f"{k}\n  {v}")

    # Write a small manifest for downstream consumers.
    manifest = OUT / "clips_manifest.json"
    manifest.write_text(json.dumps(
        [{"path": k, "description": v} for k, v in results.items()],
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
