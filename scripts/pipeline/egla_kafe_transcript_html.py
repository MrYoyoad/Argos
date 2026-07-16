#!/usr/bin/env python3
"""Per-video colored hypothesis transcript HTML for the egla_kafe guessing-game package.

One self-contained HTML file per video stem: what the model read from the lips
(the MBR display text), one line per speaker turn, each word colored by its
confidence band (same palette as the burned videos) with a small superscript
confidence percentage and a hover tooltip (prob + beam agreement).

The client reads it while (or after) watching the hypothesis-subtitled video.

Leak-proof BY CONSTRUCTION: inputs are seg_meta.json + word_confidence_mbr.json
+ face_id.json (+ optional substitutions.json). This script never opens
alignment.json, script files, or any reference text — no reference can appear.

Self-contained output: inline CSS only, no JS, no external references
(no http/https, no src=), light theme, print-friendly.

Confidence bands (conf_class comes from the sidecar's joint rule):
  high (green)  = word prob >= 0.95 AND beam agreement >= 0.80
  med  (orange) = word prob >= 0.65 AND beam agreement >= 0.50 (numerics capped here)
  low  (red)    = everything else
The legend therefore describes bands qualitatively (confident / uncertain /
guessing) — the numeric superscript is the raw word prob, which alone does NOT
determine the color.

Usage (drafts, no substitutions):
  /home/ubuntu/vsp-llm-yoad-venv/bin/python scripts/pipeline/egla_kafe_transcript_html.py \
      --stems img_6825,img_6824,img_6822,img_6821,img_6823,s2_tomer_ido_1,s1_tomer_yoad_1 \
      --out-dir /home/ubuntu/datasets/clients/egla_kafe/deliverables/guessing_game/draft

Final render adds:  --substitutions <substitutions.json> --marking subtle
"""
import argparse
import html
import json
import os
import sys
from datetime import date

# Default run mapping (mirrors egla_kafe_conversation_subtitle_video.py, but
# word confidence is the MBR-anchored sidecar — display text everywhere = hyp_mbr).
DEFAULT_RUNS = [
    {"name": "scene12",
     "seg_meta": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_scene12_all/seg_meta.json",
     "wconf": "/home/ubuntu/flat_runs_archive/20260624_145832/client_outputs/report/word_confidence_mbr.json"},
    {"name": "shaam",
     "seg_meta": "/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_shaam_all/seg_meta.json",
     "wconf": "/home/ubuntu/flat_runs_archive/20260624_200135/client_outputs/report/word_confidence_mbr.json"},
]

DEFAULT_FACE_ID = "/home/ubuntu/datasets/clients/egla_kafe/work/eval/face_id.json"
DEFAULT_OUT_DIR = "/home/ubuntu/datasets/clients/egla_kafe/deliverables/guessing_game/draft"

SIDE_LABEL = {"left": "Left speaker", "right": "Right speaker"}

# Video palette — must match the burned-subtitle colors exactly.
CSS = """
  body { margin: 0; padding: 1.5rem 1rem; background: #ffffff; color: #1a1a1a;
         font-family: Georgia, "Times New Roman", "DejaVu Serif", serif; }
  .page { max-width: 50rem; margin: 0 auto; }
  header { border-bottom: 2px solid #e8e8e8; padding-bottom: .9rem; margin-bottom: 1.2rem; }
  h1 { font-size: 1.55rem; margin: 0 0 .35rem;
       font-family: "Helvetica Neue", Helvetica, Arial, "DejaVu Sans", sans-serif; }
  .explainer { margin: 0 0 .75rem; color: #444444; font-style: italic; }
  .legend { margin: 0 0 .55rem; }
  .chip { display: inline-block; padding: .12rem .6rem; margin-right: .45rem;
          border-radius: .8rem; font-size: .82rem;
          font-family: "Helvetica Neue", Helvetica, Arial, "DejaVu Sans", sans-serif; }
  .note { margin: .2rem 0 0; color: #666666; font-size: .82rem;
          font-family: "Helvetica Neue", Helvetica, Arial, "DejaVu Sans", sans-serif; }
  .turn { margin: 0 0 .95rem; line-height: 2.1; }
  .t { font-family: "Courier New", "DejaVu Sans Mono", monospace; font-size: .8em;
       color: #888888; white-space: nowrap; }
  .lbl { font-weight: bold; color: #222222;
         font-family: "Helvetica Neue", Helvetica, Arial, "DejaVu Sans", sans-serif;
         font-size: .92em; }
  .w { padding: .04em .26em; border-radius: .28em; white-space: nowrap; }
  .w sup { font-size: .58em; opacity: .78; margin-left: .06em; }
  /* three bands — video palette as text color on very light same-hue tints;
     kept distinct in grayscale print too: high=semibold, med=regular, low=italic */
  .conf-high { color: #3CB343; background: rgba(60, 179, 67, .11); font-weight: 600; }
  .conf-med  { color: #FF9800; background: rgba(255, 152, 0, .13); }
  .conf-low  { color: #F44336; background: rgba(244, 67, 54, .10); font-style: italic; }
  /* substituted word (auto-correction): orange, dotted underline, superscript degree */
  .sub-marked { color: #FF9800; background: rgba(255, 152, 0, .13);
                text-decoration: underline dotted; text-underline-offset: .22em; }
  .none { color: #999999; font-style: italic; }
  footer { margin-top: 1.7rem; padding-top: .55rem; border-top: 1px solid #eeeeee;
           color: #999999; font-size: .78rem;
           font-family: "Helvetica Neue", Helvetica, Arial, "DejaVu Sans", sans-serif; }
  @media print { * { print-color-adjust: exact; -webkit-print-color-adjust: exact; } }
"""


def warn(msg):
    print(f"[warn] {msg}", file=sys.stderr)


def mmss(t):
    t = max(0, int(t or 0))
    return f"{t // 60:02d}:{t % 60:02d}"


def pct(x):
    try:
        return int(round(float(x) * 100))
    except (TypeError, ValueError):
        return 0


def mass_pct(x):
    """beam_mass_pct is already a percentage (0-100) per the substitutions schema."""
    try:
        return int(round(float(x)))
    except (TypeError, ValueError):
        return None


def load_pairs(args):
    """Return [(name, seg_meta_dict, wconf_dict)] from CLI pairs or the default map."""
    if args.seg_meta:
        wconf = args.wconf or []
        if len(wconf) != len(args.seg_meta):
            sys.exit("--seg-meta and --wconf must be given the same number of times (paired in order)")
        runs = [{"name": os.path.basename(os.path.dirname(sm)) or f"run{i}",
                 "seg_meta": sm, "wconf": wc}
                for i, (sm, wc) in enumerate(zip(args.seg_meta, wconf))]
    else:
        if args.wconf:
            sys.exit("--wconf without --seg-meta is ambiguous; pass them as pairs")
        runs = DEFAULT_RUNS
    pairs = []
    for r in runs:
        if not (os.path.isfile(r["seg_meta"]) and os.path.isfile(r["wconf"])):
            warn(f"run '{r['name']}': missing {r['seg_meta']} or {r['wconf']} — skipped")
            continue
        with open(r["seg_meta"], encoding="utf-8") as f:
            sm = json.load(f)
        with open(r["wconf"], encoding="utf-8") as f:
            wc = json.load(f)
        pairs.append((r["name"], sm, wc))
    if not pairs:
        sys.exit("no usable (seg-meta, wconf) pair")
    return pairs


def load_face_id(path):
    if not path or not os.path.isfile(path):
        warn(f"face_id not found at {path} — falling back to side labels")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("per_crop", {})


def load_substitutions(path):
    """{utt_id: {subs: [...], flags_kept: [...]}} — absent/broken file => render normally."""
    if not path:
        return {}
    if not os.path.isfile(path):
        warn(f"substitutions file not found: {path} — rendering without substitutions")
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        segs = data.get("segments", {})
        if not isinstance(segs, dict):
            raise ValueError("'segments' is not an object")
        return segs
    except (ValueError, OSError) as e:
        warn(f"substitutions file unreadable ({e}) — rendering without substitutions")
        return {}


def resolve_labeler(stem, mode, per_crop):
    """Return (label_fn(side) -> str, effective_mode).

    auto: person labels iff BOTH sides of this stem map to distinct persons in
    face_id (img_6823 / img_6825 have the same person on both sides -> side labels).
    """
    def side_lab(side):
        return SIDE_LABEL.get(side, f"{str(side or 'Unknown').capitalize()} speaker")

    def person_lab(side):
        p = (per_crop.get(f"{stem}__{side}") or {}).get("person")
        return str(p).capitalize() if p else side_lab(side)

    if mode == "side":
        return side_lab, "side"
    pl = (per_crop.get(f"{stem}__left") or {}).get("person")
    pr = (per_crop.get(f"{stem}__right") or {}).get("person")
    distinct = bool(pl) and bool(pr) and pl != pr
    if mode == "person":
        return person_lab, "person"
    return (person_lab, "person") if distinct else (side_lab, "side")


def word_entries(utt_id, wconf_utt):
    """Base render entries for one utterance: [{text, cls, sup, title}]."""
    entries = []
    for w in (wconf_utt or {}).get("words", []):
        text = str(w.get("word", "")).strip()
        if not text:
            continue
        p, a = pct(w.get("prob")), pct(w.get("agreement"))
        cls = w.get("conf_class")
        if cls not in ("conf-high", "conf-med", "conf-low"):
            cls = "conf-low"
        entries.append({"text": text, "cls": cls, "sup": str(p),
                        "title": f"prob {p}% · agreement {a}%"})
    return entries


def apply_substitutions(utt_id, entries, sub_seg, marking):
    """Mutate entries per substitutions.json (defensive: skip anything malformed).

    subtle: substituted word -> .sub-marked (orange, dotted underline, sup °) with an
            'auto-correction: ...' tooltip; flags_kept words get their top-2
            alternatives appended to the tooltip.
    none:   text swapped silently (orange band, no marker, no tooltip).
    Returns number of substitutions applied.
    """
    n_applied = 0
    for sub in (sub_seg.get("subs") or []):
        if not isinstance(sub, dict):
            warn(f"{utt_id}: non-dict sub entry — skipped")
            continue
        pos = sub.get("pos")
        orig = str((sub.get("original") or {}).get("word") or "")
        chosen = sub.get("chosen") or {}
        new = str(chosen.get("word") or "")
        if not isinstance(pos, int) or not (0 <= pos < len(entries)):
            warn(f"{utt_id}: sub pos {pos!r} out of range — skipped")
            continue
        if not new:
            warn(f"{utt_id}: sub at pos {pos} has no chosen word — skipped")
            continue
        if orig and entries[pos]["text"].lower() != orig.lower():
            warn(f"{utt_id}: sub pos {pos} original mismatch "
                 f"({orig!r} vs displayed {entries[pos]['text']!r}) — skipped")
            continue
        if marking == "subtle":
            mp = mass_pct(chosen.get("beam_mass_pct"))
            tip = (f"auto-correction: was '{orig}' ({mp}% beam support for '{new}')"
                   if mp is not None else f"auto-correction: was '{orig}'")
            entries[pos] = {"text": new, "cls": "sub-marked", "sup": "°", "title": tip}
        else:  # marking == none: silent text swap, never green
            entries[pos] = {"text": new, "cls": "conf-med", "sup": "", "title": ""}
        n_applied += 1

    if marking == "subtle":
        for fl in (sub_seg.get("flags_kept") or []):
            if not isinstance(fl, dict):
                continue
            pos = fl.get("pos")
            if not isinstance(pos, int) or not (0 <= pos < len(entries)):
                warn(f"{utt_id}: flag pos {pos!r} out of range — skipped")
                continue
            if entries[pos]["cls"] == "sub-marked":
                continue  # already rewritten by a sub
            wd = str(fl.get("word") or "")
            if wd and entries[pos]["text"].lower() != wd.lower():
                warn(f"{utt_id}: flag pos {pos} word mismatch ({wd!r}) — skipped")
                continue
            alts = []
            for c in (fl.get("candidates") or [])[:2]:
                if isinstance(c, dict) and c.get("word"):
                    mp = mass_pct(c.get("beam_mass_pct"))
                    alts.append(f"{c['word']} {mp}%" if mp is not None else str(c["word"]))
            if alts:
                base = entries[pos]["title"]
                entries[pos]["title"] = (base + " · " if base else "") + \
                    "alternatives: " + ", ".join(alts)
    return n_applied


def span_html(e):
    sup = f"<sup>{html.escape(e['sup'])}</sup>" if e["sup"] else ""
    title = f' title="{html.escape(e["title"], quote=True)}"' if e["title"] else ""
    return f'<span class="w {e["cls"]}"{title}>{html.escape(e["text"])}{sup}</span>'


def build_html(stem, turns, wconf, label_fn, subs, marking):
    """turns: [(seg_id, meta)] sorted by t0. Returns (html_text, stats)."""
    body, n_words, n_subs = [], 0, 0
    for seg_id, m in turns:
        entries = word_entries(seg_id, wconf.get(seg_id))
        if seg_id not in wconf:
            warn(f"{seg_id}: missing from word-confidence sidecar — rendered as no-speech")
        sub_seg = subs.get(seg_id)
        if sub_seg:
            n_subs += apply_substitutions(seg_id, entries, sub_seg, marking)
        n_words += len(entries)
        words = " ".join(span_html(e) for e in entries) if entries else \
            '<span class="none">(no speech read)</span>'
        body.append(
            f'      <p class="turn"><span class="t">[{mmss(m.get("t0"))}–{mmss(m.get("t1"))}]</span> '
            f'<span class="lbl">{html.escape(label_fn(m.get("side")))}:</span> {words}</p>')

    sub_note = ""
    if n_subs and marking == "subtle":
        sub_note = ('\n      <p class="note">° = auto-correction chosen from the '
                    "recognizer's own alternative readings.</p>")

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(stem)} — model lip-reading transcript</title>
<style>{CSS}</style>
</head>
<body>
  <div class="page">
    <header>
      <h1>{html.escape(stem)}</h1>
      <p class="explainer">What the model read from the lips alone — no audio was used.</p>
      <div class="legend"><span class="chip conf-high">confident</span><span
        class="chip conf-med">uncertain</span><span class="chip conf-low">guessing</span></div>
      <p class="note">Colors combine the model's confidence in each word with the agreement
      between its alternative readings. The small number beside each word = the model's
      confidence in that word (%).</p>{sub_note}
    </header>
    <main>
{os.linesep.join(body)}
    </main>
    <footer>Generated {date.today().isoformat()} · Argos VSP</footer>
  </div>
</body>
</html>
"""
    return doc, {"turns": len(turns), "words": n_words, "subs": n_subs}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stems", required=True, help="comma list of video stems")
    ap.add_argument("--seg-meta", action="append", default=None,
                    help="per-run seg_meta.json (repeatable, paired in order with --wconf); "
                         "default: built-in scene12 + shaam map")
    ap.add_argument("--wconf", action="append", default=None,
                    help="per-run word-confidence sidecar (repeatable; default: the "
                         "MBR-anchored word_confidence_mbr.json of each run)")
    ap.add_argument("--face-id", default=DEFAULT_FACE_ID)
    ap.add_argument("--label-source", choices=("person", "side", "auto"), default="auto",
                    help="auto = person names iff the stem's two sides map to distinct "
                         "persons in face_id, else 'Left/Right speaker'")
    ap.add_argument("--substitutions", default=None,
                    help="optional substitutions.json (P2 output); absent file = render normally")
    ap.add_argument("--marking", choices=("subtle", "none"), default="subtle",
                    help="subtle = mark substituted words (° + dotted underline + tooltip); "
                         "none = swap text silently")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    pairs = load_pairs(args)
    per_crop = load_face_id(args.face_id)
    subs = load_substitutions(args.substitutions)
    os.makedirs(args.out_dir, exist_ok=True)

    n_fail = 0
    for stem in [s.strip() for s in args.stems.split(",") if s.strip()]:
        hit = None
        for name, sm, wc in pairs:
            turns = sorted(((sid, m) for sid, m in sm.items() if m.get("stem") == stem),
                           key=lambda kv: (kv[1].get("t0", 0), kv[0]))
            if turns:
                hit = (name, turns, wc)
                break
        if not hit:
            warn(f"{stem}: no segments in any seg-meta — skipped")
            n_fail += 1
            continue
        name, turns, wc = hit
        label_fn, eff = resolve_labeler(stem, args.label_source, per_crop)
        doc, st = build_html(stem, turns, wc, label_fn, subs, args.marking)
        out = os.path.join(args.out_dir, f"{stem}__transcript.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"[ok] {stem} -> {out}  ({st['turns']} turns, {st['words']} words, "
              f"labels={eff}, subs={st['subs']}, run={name}, {os.path.getsize(out)} B)")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
