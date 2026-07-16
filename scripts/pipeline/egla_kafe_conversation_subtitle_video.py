#!/usr/bin/env python3
"""Full-length subtitle videos per conversation, on the JOINT frame.

Modes (--mode):
  said_vs_heard (default) — two lines per speaker turn:
      line 1 — what was actually SAID (the script line, white)
      line 2 — what the model HEARD (its lip-read transcription), each word colored by confidence
               (green=high / orange=med / red=low)
      Uses the per-turn (split-speaker) decode — the better arm — but displays it on the joint
      frame so the whole thing reads as one continuous captioned conversation.
  hyp_only — ONE line per turn: '<label>:  <colored model words>'. Events are built ONLY from
      seg_meta (turn timing/side) + the word-confidence sidecar (+ face_id.json for labels).
      alignment.json / references / script files are never opened on this code path, so a
      reference leak is impossible by construction. This is the guessing-game 'reveal' video.
  clean — no subtitles at all (same probe/scale plumbing); the 'watch first, guess' companion.

ALL modes strip audio (-an): the iPhone masters carry the real dialogue on their AAC track.

Word-confidence source is swappable per run (--wconf): a bare filename (e.g.
word_confidence_mbr.json) resolves inside each run's report dir next to its default sidecar;
a value containing '/' is used verbatim for every run.

Optional --substitutions substitutions.json (phonetic auto-correction, Workstream P) marks
substituted words on the hyp line; --marking subtle = orange band + trailing degree sign
(never green), debug = 'orig→new[NN%]', none = swap text only (color capped below green).
Rendered via ASS subtitles (clean per-word color + wrapping + timing).
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
FACE_ID_DEFAULT = "/home/ubuntu/datasets/clients/egla_kafe/work/eval/face_id.json"

_SEG_META_CACHE = {}


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


def load_seg_meta(path):
    if path not in _SEG_META_CACHE:
        _SEG_META_CACHE[path] = json.load(open(path))
    return _SEG_META_CACHE[path]


def find_run_by_seg_meta(stem):
    """Run resolution that never touches the eval/align tree (hyp_only / leak-safe path)."""
    for key, cfg in RUNS.items():
        try:
            sm = load_seg_meta(cfg["seg_meta"])
        except (OSError, ValueError):
            continue
        if any(v.get("stem") == stem for v in sm.values()):
            return key, cfg
    return None, None


def resolve_wconf(cfg, wconf):
    """--wconf: None -> the run's default sidecar; bare filename -> same dir as the run's
    default (per-run swap, e.g. word_confidence_mbr.json); contains '/' -> used verbatim."""
    if not wconf:
        return cfg["wconf"]
    if os.sep in wconf:
        return wconf
    return os.path.join(os.path.dirname(cfg["wconf"]), wconf)


def load_face_persons(face_id_path):
    try:
        fid = json.load(open(face_id_path))
        return {k: (v or {}).get("person") for k, v in (fid.get("per_crop") or {}).items()}
    except (OSError, ValueError, AttributeError) as e:
        print(f"[warn] face_id not readable ({e}) — falling back to side labels")
        return {}


def side_label(side):
    return f"{str(side).capitalize()} speaker" if side else "Speaker"


def label_for(stem, side, label_source, persons):
    """Speaker label for one turn. side: 'left'/'right' from seg_meta.
    person = capitalized first name from face_id per_crop['{stem}__{side}'];
    auto = person iff the stem's two sides map to DISTINCT persons, else side label."""
    sl = side_label(side)
    if label_source == "side":
        return sl
    if label_source == "auto":
        pl, pr = persons.get(f"{stem}__left"), persons.get(f"{stem}__right")
        if not (pl and pr and pl != pr):
            return sl
    p = persons.get(f"{stem}__{side}")
    if not p:
        print(f"[warn] no face-id person for {stem}__{side} — using side label")
        return sl
    return str(p).split()[0].split("_")[0].capitalize()


def load_substitutions(path):
    if not path:
        return {}
    if not os.path.exists(path):
        print(f"[note] substitutions file not found: {path} — rendering without substitution marks")
        return {}
    try:
        return json.load(open(path)).get("segments") or {}
    except (OSError, ValueError, AttributeError) as e:
        print(f"[warn] substitutions unreadable ({e}) — rendering without substitution marks")
        return {}


def subs_for(subs_segments, seg_id, words):
    """pos -> substitution dict for one utt; defensive (missing utt / bad pos / word mismatch -> no mark)."""
    e = (subs_segments or {}).get(seg_id)
    if not e:
        return {}
    out = {}
    for s in e.get("subs") or []:
        pos = s.get("pos")
        chosen = ((s.get("chosen") or {}).get("word") or "").strip()
        if not isinstance(pos, int) or not (0 <= pos < len(words)) or not chosen:
            print(f"[warn] {seg_id}: malformed substitution (pos={pos!r}) — skipped")
            continue
        orig = ((s.get("original") or {}).get("word") or "").strip()
        if orig and orig.lower() != str(words[pos].get("word", "")).strip().lower():
            print(f"[warn] {seg_id}@{pos}: substitution original {orig!r} != rendered word "
                  f"{words[pos].get('word')!r} — skipped")
            continue
        out[pos] = s
    return out


def _sub_pct(s):
    v = (s.get("chosen") or {}).get("beam_mass_pct")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "?"
    if 0 <= v <= 1.0:  # tolerate fraction-valued files; shipped subs carry >= 5% mass
        v *= 100.0
    return f"{int(round(v))}%"


def render_hyp_words(words, sub_map=None, marking="subtle"):
    """Per-word colored hyp line. Substituted words NEVER render green (handoff guardrail):
    subtle = orange band + trailing degree sign; debug = orig→new[NN%]; none = swap text only."""
    parts = []
    for i, w in enumerate(words):
        s = (sub_map or {}).get(i)
        if s is None:
            c = ass_color(CONF_RGB.get(w.get("conf_class"), WHITE_RGB))
            parts.append(f"{{\\c{c}}}{esc(w['word'])}")
            continue
        chosen = (s.get("chosen") or {}).get("word", "")
        if marking == "debug":
            c = ass_color(CONF_RGB["conf-med"])
            parts.append(f"{{\\c{c}}}{esc(w['word'])}→{esc(chosen)}[{_sub_pct(s)}]")
        elif marking == "none":
            cls = w.get("conf_class")
            cls = "conf-med" if cls == "conf-high" else cls  # cap below green
            c = ass_color(CONF_RGB.get(cls, WHITE_RGB))
            parts.append(f"{{\\c{c}}}{esc(chosen)}")
        else:  # subtle
            c = ass_color(CONF_RGB["conf-med"])
            parts.append(f"{{\\c{c}}}{esc(chosen)}°")
    return " ".join(parts) if parts else "{\\c" + ass_color((0x88, 0x88, 0x88)) + "}(no speech read)"


def write_ass(out_ass, W, H, fs, events):
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


def build_ass(stem, W, H, out_ass, wconf=None, label_source="char", subs=None, marking="subtle",
              face_id=FACE_ID_DEFAULT):
    """said_vs_heard events (reference line + colored hyp line). Needs alignment.json."""
    key, cfg = find_run(stem)
    if not cfg:
        raise SystemExit(f"no run/align found for {stem}")
    seg_meta = json.load(open(cfg["seg_meta"]))
    align = json.load(open(os.path.join(cfg["align"], stem, "alignment.json")))
    wc = json.load(open(resolve_wconf(cfg, wconf)))
    s2c = align.get("side_to_char", {})
    ref_by = {s["seg_id"]: s for s in align["segments"]}
    persons = load_face_persons(face_id) if label_source in ("person", "auto") else {}
    segs = sorted([(k, v) for k, v in seg_meta.items() if v["stem"] == stem], key=lambda kv: kv[1]["t0"])

    fs = max(20, int(H * 0.042))          # font size scales with height
    fs_lbl = int(fs * 0.75)
    events = []
    for seg_id, m in segs:
        a = ref_by.get(seg_id)
        if not a:
            continue
        if label_source == "char":
            who = (a.get("char") or s2c.get(m["side"]) or "").upper()
        else:
            who = esc(label_for(stem, m.get("side"), label_source, persons))
        ref = esc(a.get("ref", "")).strip()
        words = wc.get(seg_id, {}).get("words", [])
        hyp = render_hyp_words(words, subs_for(subs, seg_id, words), marking)
        lbl = ass_color(LABEL_RGB); wht = ass_color(WHITE_RGB)
        # one event, two lines: SAID (white) \N model heard (colored)
        text = (f"{{\\c{lbl}}}{who} said:  {{\\c{wht}}}{ref}"
                f"\\N{{\\c{lbl}}}model read:  {hyp}")
        events.append((m["t0"], m["t1"], text))
    write_ass(out_ass, W, H, fs, events)
    return key


def build_ass_hyp_only(stem, W, H, out_ass, wconf=None, label_source="auto", subs=None,
                       marking="subtle", face_id=FACE_ID_DEFAULT):
    """Guessing-game events: ONE line per turn, '<label>:  <colored hyp>'.
    Inputs: seg_meta (timing/side) + word-confidence sidecar + face_id (labels) ONLY —
    alignment.json / hypo-corrected.json / script files are never opened here."""
    key, cfg = find_run_by_seg_meta(stem)
    if not cfg:
        raise SystemExit(f"no run seg_meta contains stem {stem}")
    seg_meta = load_seg_meta(cfg["seg_meta"])
    wc = json.load(open(resolve_wconf(cfg, wconf)))
    persons = load_face_persons(face_id) if label_source in ("person", "auto") else {}
    segs = sorted([(k, v) for k, v in seg_meta.items() if v["stem"] == stem], key=lambda kv: kv[1]["t0"])
    if not segs:
        raise SystemExit(f"stem {stem} has no turns in {cfg['seg_meta']}")

    fs = max(20, int(H * 0.042))          # font size scales with height
    lbl = ass_color(LABEL_RGB)
    events = []
    for seg_id, m in segs:
        words = wc.get(seg_id, {}).get("words", [])
        hyp = render_hyp_words(words, subs_for(subs, seg_id, words), marking)
        who = esc(label_for(stem, m.get("side"), label_source, persons))
        events.append((m["t0"], m["t1"], f"{{\\c{lbl}}}{who}:  {hyp}"))
    write_ass(out_ass, W, H, fs, events)
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
    ap.add_argument("--stems", required=True, help="comma list or a RUNS key ('scene12'/'shaam'/'all')")
    ap.add_argument("--mode", choices=("said_vs_heard", "hyp_only", "clean"), default="said_vs_heard",
                    help="said_vs_heard=reference+hyp (default); hyp_only=model line only "
                         "(guessing game, never opens alignment/refs); clean=no subtitles")
    ap.add_argument("--label-source", choices=("char", "person", "side", "auto"), default=None,
                    help="speaker label: char=script character (said_vs_heard only), person=face-id "
                         "first name, side='Left/Right speaker', auto=person iff the stem's two sides "
                         "are distinct persons else side. Default: char for said_vs_heard, auto for hyp_only")
    ap.add_argument("--wconf", default=None,
                    help="word-confidence sidecar: bare filename (e.g. word_confidence_mbr.json) swaps "
                         "the basename inside each run's report dir; a path containing '/' is used verbatim")
    ap.add_argument("--substitutions", default=None,
                    help="optional substitutions.json (phonetic auto-correction); missing file => render normally")
    ap.add_argument("--marking", choices=("subtle", "none", "debug"), default="subtle",
                    help="how substituted words are marked (subtle=orange+degree sign, never green)")
    ap.add_argument("--out-dir", default="/home/ubuntu/datasets/clients/egla_kafe/deliverables/conversation_videos")
    ap.add_argument("--max-h", type=int, default=900, help="scale output down if taller")
    ap.add_argument("--runs-json", default=None,
                    help="JSON overriding the run map {key:{seg_meta,align,wconf}} for a generic dataset")
    ap.add_argument("--index", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/index.json")
    ap.add_argument("--face-id", default=FACE_ID_DEFAULT,
                    help="face_id.json for person/auto labels (per_crop['{stem}__{side}']['person'])")
    args = ap.parse_args()
    label_source = args.label_source or ("auto" if args.mode == "hyp_only" else "char")
    if args.mode == "hyp_only" and label_source == "char":
        raise SystemExit("--mode hyp_only cannot use --label-source char: character names live in "
                         "alignment.json, which the hyp_only path never opens (reference-leak guard)")
    if args.runs_json and os.path.exists(args.runs_json):
        RUNS.clear(); RUNS.update(json.load(open(args.runs_json)))
    os.makedirs(args.out_dir, exist_ok=True)
    idx = {e["stem"]: e for e in json.load(open(args.index))["entries"]}
    subs = load_substitutions(args.substitutions) if args.mode != "clean" else {}

    if args.stems in ("scene12", "shaam", "all"):
        keys = list(RUNS) if args.stems == "all" else [args.stems]
        if args.mode == "said_vs_heard":
            stems = [s for s in sorted(os.listdir(RUNS[args.stems]["align"]))] if args.stems != "all" else \
                    sorted(set(list(os.listdir(RUNS["scene12"]["align"])) + list(os.listdir(RUNS["shaam"]["align"]))))
        else:  # leak-safe modes list stems from seg_meta, not the eval/align tree
            stems = sorted({v["stem"] for k in keys for v in load_seg_meta(RUNS[k]["seg_meta"]).values()})
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
        if args.mode == "clean":
            out = os.path.join(args.out_dir, f"{stem}__clean.mp4")
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"scale={ow}:{oh}", "-map", "0:v",
                   "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-an", out]
        else:
            if args.mode == "hyp_only":
                ass_path = os.path.join(args.out_dir, f"{stem}__model_read.ass")
                out = os.path.join(args.out_dir, f"{stem}__model_read.mp4")
                build_ass_hyp_only(stem, ow, oh, ass_path, wconf=args.wconf, label_source=label_source,
                                   subs=subs, marking=args.marking, face_id=args.face_id)
            else:
                ass_path = os.path.join(args.out_dir, f"{stem}.ass")
                out = os.path.join(args.out_dir, f"{stem}__said_vs_heard.mp4")
                build_ass(stem, ow, oh, ass_path, wconf=args.wconf, label_source=label_source,
                          subs=subs, marking=args.marking, face_id=args.face_id)
            vf = f"scale={ow}:{oh},ass={ass_path}" if (ow, oh) != (W, H) else f"ass={ass_path}"
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf,
                   "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-an", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(out)
        print(f"[{'ok' if ok else 'FAIL'}] {stem} -> {out} ({ow}x{oh})" + ("" if ok else f"  {r.stderr[-200:]}"))


if __name__ == "__main__":
    main()
