#!/usr/bin/env python3
"""Egla-Kafe per-video PDF deliverable (TOOL C).

One card-page per video (21 videos = one per work/eval/judge/judgments/*.json),
ranked best->worst by context-aware Y+P recovery, preceded by a single
honest-positive intro card.

Each video card contains:
  - a recognizable mid-timestamp frame from the SOURCE video (orig_path),
    extracted via ffmpeg at original resolution, scaled to ~640px wide JPG.
  - header: friendly scene title (Emma & Jake (airport) / Military (planning)),
    source (iPhone-4K vs client camera), speakers (face-ID resolved persons;
    masters labelled by scene), camera angle.
  - body: "What is understood" (judgment gist), "You can take away"
    (recoverable_facts), and a small metrics line (context Y+P %, mean IS).

Self-contained ReportLab renderer (reportlab already in the system Python).
Frames cached under deliverables/frames/. Re-running is idempotent (frames
re-extracted only if missing).

Run:
  /home/ubuntu/vsp-llm-yoad-venv/bin/python \
    docs/_research-tools/generators/generate_egla_kafe_per_video_pdf.py
"""
from __future__ import annotations

import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepInFrame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EVAL = Path("/home/ubuntu/datasets/clients/egla_kafe/work/eval")
JUDGE_DIR = EVAL / "judge" / "judgments"
INDEX_JSON = EVAL / "index.json"
FACE_ID_JSON = EVAL / "face_id.json"
REPORTS = {
    "run_scene12_all": EVAL / "run_scene12_all",
    "run_shaam_all": EVAL / "run_shaam_all",
}
DELIV = Path("/home/ubuntu/datasets/clients/egla_kafe/deliverables")
FRAMES = DELIV / "frames"
OUT_PDF = DELIV / "EglaKafe_per_video.pdf"

# ---------------------------------------------------------------------------
# Palette (matches project STYLE_GUIDE navy + tier colours)
# ---------------------------------------------------------------------------
NAVY_DEEP = HexColor("#1a3a5c")
NAVY_MID = HexColor("#2a5a8c")
NAVY_TINT = HexColor("#eef3fa")
CARD_BG = HexColor("#f7f9fc")
INK = HexColor("#1a1a1a")
MUTED = HexColor("#5b6470")
RULE_GREY = HexColor("#cfd6df")
TIER_GREEN = HexColor("#2e7d32")
TIER_YELLOW = HexColor("#b8860b")
TIER_RED = HexColor("#c0392b")
CHIP_BG = HexColor("#e4ecf6")

# ---------------------------------------------------------------------------
# Friendly labels
# ---------------------------------------------------------------------------
SCENE_TITLE = {
    "scene1": "Emma & Jake (airport)",
    "scene2": "Military (planning)",
}
# Person transliterations (display). Hebrew names are acceptable in captions,
# but transliterated forms read cleaner in a client deliverable.
PERSON_DISPLAY = {
    "yoad": "Yoad",
    "tomer": "Tomer",
    "tal": "Tal",
    "ido": "Ido",
    "amosi": "Amosi",
}
ANGLE_DISPLAY = {
    "front": "Frontal (0°)",
    "30": "Angled (30°)",
    "45": "Profile (45°)",
    "master_4k": "Frontal (iPhone master)",
}


def source_label(source_type: str) -> str:
    return "iPhone 4K (high-res master)" if source_type == "master" else "Client camera (screen recording)"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_index() -> dict:
    idx = json.loads(INDEX_JSON.read_text())
    return {e["stem"]: e for e in idx["entries"]}


def load_face_persons() -> dict:
    fid = json.loads(FACE_ID_JSON.read_text())
    by_stem: dict[str, dict[str, str]] = defaultdict(dict)
    for v in fid["per_crop"].values():
        by_stem[v["stem"]][v["side"]] = v["person"]
    return by_stem


def stem_for_report(report_dir: Path) -> dict[str, str]:
    pv = json.loads((report_dir / "provenance.json").read_text())
    return {seg_id: meta["stem"] for seg_id, meta in pv.items()}


def load_mean_is() -> dict[str, float]:
    """Mean IS per stem across both report runs (utt_id -> stem via provenance)."""
    agg: dict[str, list[float]] = defaultdict(list)
    for rdir in REPORTS.values():
        seg2stem = stem_for_report(rdir)
        with open(rdir / "report" / "report.csv") as f:
            for row in csv.DictReader(f):
                stem = seg2stem.get(row["utt_id"])
                if stem is None:
                    continue
                s = (row.get("is_score") or "").strip()
                if s:
                    try:
                        agg[stem].append(float(s))
                    except ValueError:
                        pass
    return {st: (sum(v) / len(v) if v else 0.0) for st, v in agg.items()}


def load_judgments() -> list[dict]:
    out = []
    for p in sorted(JUDGE_DIR.glob("*.json")):
        out.append(json.loads(p.read_text()))
    return out


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------
def video_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def extract_frame(stem: str, orig_path: Path) -> Path | None:
    """Extract a mid-timestamp frame, scaled to 640px wide, into FRAMES/."""
    out = FRAMES / f"{stem}.jpg"
    if out.exists() and out.stat().st_size > 0:
        return out
    if not orig_path.exists():
        print(f"  [WARN] source missing for {stem}: {orig_path}")
        return None
    dur = video_duration(orig_path)
    ts = max(0.5, dur / 2.0) if dur > 0 else 5.0
    FRAMES.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{ts:.2f}", "-i", str(orig_path),
        "-frames:v", "1",
        "-vf", "scale=640:-2",
        "-q:v", "3",
        str(out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"  [WARN] ffmpeg failed for {stem}: {e.stderr.decode(errors='ignore')[:200]}")
        return None
    if out.exists() and out.stat().st_size > 0:
        return out
    return None


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
SS = getSampleStyleSheet()

S_COVER_TITLE = ParagraphStyle(
    "CoverTitle", parent=SS["Title"], fontName="Helvetica-Bold",
    fontSize=30, leading=36, textColor=NAVY_DEEP, spaceAfter=6, alignment=TA_LEFT,
)
S_COVER_SUB = ParagraphStyle(
    "CoverSub", parent=SS["Normal"], fontName="Helvetica",
    fontSize=13, leading=19, textColor=MUTED, spaceAfter=14,
)
S_H_INTRO = ParagraphStyle(
    "IntroHead", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=13, leading=18, textColor=NAVY_MID, spaceBefore=10, spaceAfter=4,
)
S_BODY = ParagraphStyle(
    "Body", parent=SS["Normal"], fontName="Helvetica",
    fontSize=11, leading=16, textColor=INK, spaceAfter=6,
)
S_BULLET = ParagraphStyle(
    "Bullet", parent=S_BODY, leftIndent=14, bulletIndent=2, spaceAfter=3,
)
S_RANK = ParagraphStyle(
    "Rank", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=11, leading=14, textColor=white,
)
S_CARD_TITLE = ParagraphStyle(
    "CardTitle", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=19, leading=23, textColor=NAVY_DEEP, spaceAfter=2,
)
S_CARD_SUB = ParagraphStyle(
    "CardSub", parent=SS["Normal"], fontName="Helvetica",
    fontSize=10.5, leading=15, textColor=MUTED, spaceAfter=2,
)
S_META_LABEL = ParagraphStyle(
    "MetaLabel", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=9.5, leading=13, textColor=NAVY_MID,
)
S_META_VAL = ParagraphStyle(
    "MetaVal", parent=SS["Normal"], fontName="Helvetica",
    fontSize=9.5, leading=13, textColor=INK,
)
S_SECTION = ParagraphStyle(
    "Section", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=NAVY_MID, spaceBefore=8, spaceAfter=3,
)
S_GIST = ParagraphStyle(
    "Gist", parent=SS["Normal"], fontName="Helvetica",
    fontSize=10.5, leading=15, textColor=INK, spaceAfter=4,
)
S_TAKEAWAY = ParagraphStyle(
    "Takeaway", parent=SS["Normal"], fontName="Helvetica",
    fontSize=10.5, leading=15, textColor=INK,
)
S_METRIC = ParagraphStyle(
    "Metric", parent=SS["Normal"], fontName="Helvetica-Bold",
    fontSize=11, leading=15, textColor=INK,
)
S_FOOT = ParagraphStyle(
    "Foot", parent=SS["Normal"], fontName="Helvetica-Oblique",
    fontSize=8.5, leading=11, textColor=MUTED,
)


def yp_color(yp: float) -> HexColor:
    if yp >= 45.0:
        return TIER_GREEN
    if yp >= 25.0:
        return TIER_YELLOW
    return TIER_RED


def yp_word(yp: float) -> str:
    if yp >= 45.0:
        return "strong recovery"
    if yp >= 25.0:
        return "partial recovery"
    return "limited recovery"


# ---------------------------------------------------------------------------
# Card builders
# ---------------------------------------------------------------------------
def build_intro(width: float) -> list:
    el: list = []
    el.append(Paragraph("Egla-Kafe — Lip-Reading Results, Video by Video", S_COVER_TITLE))
    el.append(Paragraph(
        "What our visual speech model understood from each of your 21 clips, "
        "ranked from clearest to hardest.", S_COVER_SUB))

    # divider
    el.append(_rule(width))
    el.append(Spacer(1, 8))

    el.append(Paragraph("What this is", S_H_INTRO))
    el.append(Paragraph(
        "We ran each video through a lip-reading model that watches the speaker's "
        "mouth (no audio is used) and writes down what it believes was said. We then "
        "asked an independent reviewer, who knows only the general topic of each scene, "
        "how much of each conversation a person could actually follow from the model's "
        "output. This document gives you one page per video so you can see exactly what "
        "came through.", S_BODY))

    el.append(Paragraph("How to read each page", S_H_INTRO))
    for txt in [
        "<b>The frame</b> is a still from your original video, so you can recognise the clip at a glance.",
        "<b>What is understood</b> is the reviewer's plain-language summary of the storyline the model recovered.",
        "<b>You can take away</b> lists the specific phrases and facts that survived lip-reading reliably.",
        "<b>Context recovery (Y+P)</b> is the share of speaking turns a viewer can grasp with topic context — "
        "our headline measure of usefulness. <b>Mean IS</b> (0–5) is the average per-segment intelligibility score.",
    ]:
        el.append(Paragraph(f"• {txt}", S_BULLET))

    el.append(Paragraph("An honest word on what to expect", S_H_INTRO))
    el.append(Paragraph(
        "Lip-reading without sound is genuinely hard, and these were real-world clips, "
        "non-native English, and varied camera setups. The model is strongest on "
        "<b>high-resolution, frontal footage</b> and on <b>distinctive content words</b> "
        "(topics, key phrases, rough numbers). It is weakest on names, places, and exact "
        "wording, and it can produce confident-sounding text that is wrong. The pages are "
        "ordered so the clearest results come first. The takeaway is positive and practical: "
        "with good capture and topic context, the model recovers the gist of a conversation "
        "far more often than the raw word-error rate alone would suggest.", S_BODY))

    el.append(Spacer(1, 8))
    el.append(_rule(width))
    el.append(Spacer(1, 6))
    el.append(Paragraph(
        "Color key for the rank badge: "
        "<font color='#2e7d32'><b>green</b></font> = strong recovery (Y+P ≥ 45%), "
        "<font color='#b8860b'><b>amber</b></font> = partial (25–45%), "
        "<font color='#c0392b'><b>red</b></font> = limited (&lt; 25%).", S_FOOT))
    return el


def _rule(width: float, color=RULE_GREY, thickness=0.8):
    t = Table([[""]], colWidths=[width], rowHeights=[thickness])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), thickness, color),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _chip(text: str) -> Table:
    p = Paragraph(text, ParagraphStyle(
        "Chip", parent=SS["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=NAVY_DEEP))
    t = Table([[p]], colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CHIP_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return t


def build_card(rank: int, total: int, j: dict, idx_entry: dict,
               persons: dict, mean_is: float, frame: Path | None,
               width: float) -> list:
    el: list = []
    stem = j["stem"]
    scene = j.get("scene", idx_entry.get("scene", ""))
    yp = float(j["overall"].get("yp_pct", 0.0))
    y = float(j["overall"].get("y_pct", 0.0))

    title = SCENE_TITLE.get(scene, scene.title())
    src = source_label(idx_entry.get("source_type", ""))
    angle = ANGLE_DISPLAY.get(idx_entry.get("angle", ""), idx_entry.get("angle", "—"))
    is_master = idx_entry.get("source_type") == "master"

    # Speakers line. Masters: label by scene; still list resolved persons.
    if is_master:
        ppl = sorted({persons.get(stem, {}).get(s) for s in ("left", "right")} - {None})
        ppl_disp = ", ".join(PERSON_DISPLAY.get(p, p.title()) for p in ppl) if ppl else "—"
        speakers = f"{ppl_disp} (single-frame master)"
    else:
        L = persons.get(stem, {}).get("left")
        R = persons.get(stem, {}).get("right")
        parts = []
        if L:
            parts.append(f"{PERSON_DISPLAY.get(L, L.title())} (left)")
        if R:
            parts.append(f"{PERSON_DISPLAY.get(R, R.title())} (right)")
        speakers = " · ".join(parts) if parts else "—"

    # ---- rank badge + title block (left) ----
    badge = Table([[Paragraph(f"#{rank}", S_RANK)]], colWidths=[1.05 * cm], rowHeights=[1.05 * cm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), yp_color(yp)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    titleblock = [
        Paragraph(title, S_CARD_TITLE),
        Paragraph(f"{src}", S_CARD_SUB),
    ]
    head = Table([[badge, titleblock]], colWidths=[1.35 * cm, width - 1.35 * cm])
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    el.append(head)
    el.append(Spacer(1, 8))

    # ---- frame image ----
    if frame is not None:
        img_w = min(width, 13.0 * cm)
        try:
            from PIL import Image as PILImage
            with PILImage.open(frame) as im:
                iw, ih = im.size
            ratio = ih / iw if iw else 0.5625
        except Exception:
            ratio = 0.5625
        img = Image(str(frame), width=img_w, height=img_w * ratio)
        wrap = Table([[img]], colWidths=[width])
        wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        el.append(wrap)
    else:
        el.append(Paragraph("(source frame unavailable)", S_FOOT))
    el.append(Spacer(1, 8))

    # ---- meta grid ----
    meta_rows = [
        [Paragraph("Scene", S_META_LABEL), Paragraph(title, S_META_VAL),
         Paragraph("Camera angle", S_META_LABEL), Paragraph(angle, S_META_VAL)],
        [Paragraph("Source", S_META_LABEL), Paragraph(src, S_META_VAL),
         Paragraph("Speakers", S_META_LABEL), Paragraph(speakers, S_META_VAL)],
    ]
    meta = Table(meta_rows, colWidths=[2.0 * cm, width / 2 - 2.0 * cm, 2.4 * cm, width / 2 - 2.4 * cm])
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_TINT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, white),
    ]))
    el.append(meta)
    el.append(Spacer(1, 6))

    # ---- What is understood ----
    el.append(Paragraph("What is understood", S_SECTION))
    el.append(Paragraph(j.get("gist", "").strip() or "—", S_GIST))

    # ---- You can take away ----
    facts = j.get("recoverable_facts") or []
    el.append(Paragraph("You can take away", S_SECTION))
    if facts:
        chips = [_chip(str(f)) for f in facts]
        # arrange chips in rows of up to 4
        rows = [chips[i:i + 4] for i in range(0, len(chips), 4)]
        for r in rows:
            while len(r) < 4:
                r.append("")
        chip_tbl = Table(rows, colWidths=[width / 4] * 4)
        chip_tbl.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        el.append(chip_tbl)
    else:
        el.append(Paragraph("Nothing reliably recovered from this clip.", S_TAKEAWAY))
    el.append(Spacer(1, 8))

    # ---- metrics line ----
    el.append(_rule(width))
    el.append(Spacer(1, 5))
    yc = yp_color(yp)
    metric_para = Paragraph(
        f"Context recovery (Y+P): <font color='#{_hex(yc)}'><b>{yp:.0f}%</b></font> "
        f"({yp_word(yp)})&nbsp;&nbsp;•&nbsp;&nbsp;"
        f"Clearly conveyed (Y): <b>{y:.0f}%</b>&nbsp;&nbsp;•&nbsp;&nbsp;"
        f"Mean intelligibility (IS): <b>{mean_is:.2f}</b> / 5.0",
        S_METRIC)
    el.append(metric_para)
    el.append(Spacer(1, 3))
    el.append(Paragraph(
        f"Video {rank} of {total} · ranked by context recovery · "
        f"clip id: {stem}", S_FOOT))
    return el


def _hex(c: HexColor) -> str:
    return c.hexval()[2:]  # strip the "0x" prefix -> 6 hex digits


# ---------------------------------------------------------------------------
# Page frame: a rounded card background
# ---------------------------------------------------------------------------
PAGE = A4
MARGIN = 1.5 * cm
FRAME_W = PAGE[0] - 2 * MARGIN
FRAME_H = PAGE[1] - 2 * MARGIN


def draw_card_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CARD_BG)
    canvas.setStrokeColor(RULE_GREY)
    canvas.setLineWidth(0.8)
    canvas.roundRect(MARGIN - 4 * mm, MARGIN - 4 * mm,
                     FRAME_W + 8 * mm, FRAME_H + 8 * mm, 6 * mm, stroke=1, fill=1)
    # top accent bar
    canvas.setFillColor(NAVY_DEEP)
    canvas.roundRect(MARGIN - 4 * mm, PAGE[1] - MARGIN - 4 * mm + 2 * mm,
                     FRAME_W + 8 * mm, 3 * mm, 1.5 * mm, stroke=0, fill=1)
    canvas.restoreState()


def draw_intro_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(white)
    canvas.rect(0, 0, PAGE[0], PAGE[1], stroke=0, fill=1)
    canvas.setFillColor(NAVY_DEEP)
    canvas.rect(0, PAGE[1] - 1.0 * cm, PAGE[0], 1.0 * cm, stroke=0, fill=1)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    DELIV.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)

    index = load_index()
    persons = load_face_persons()
    mean_is = load_mean_is()
    judgments = load_judgments()

    # rank best->worst by context Y+P
    judgments.sort(key=lambda j: float(j["overall"].get("yp_pct", 0.0)), reverse=True)
    total = len(judgments)

    print(f"Extracting {total} source frames...")
    frames: dict[str, Path | None] = {}
    for j in judgments:
        stem = j["stem"]
        entry = index.get(stem, {})
        orig = Path(entry.get("orig_path", ""))
        frames[stem] = extract_frame(stem, orig)
        status = "ok" if frames[stem] else "MISSING"
        print(f"  {stem:24s} {status}")

    # build document
    doc = BaseDocTemplate(
        str(OUT_PDF), pagesize=PAGE,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Egla-Kafe — Per-Video Lip-Reading Results",
        author="Argos VSP",
    )
    frame = Frame(MARGIN, MARGIN, FRAME_W, FRAME_H, id="body",
                  leftPadding=6, rightPadding=6, topPadding=6, bottomPadding=6)
    doc.addPageTemplates([
        PageTemplate(id="intro", frames=[frame], onPage=draw_intro_bg),
        PageTemplate(id="card", frames=[frame], onPage=draw_card_bg),
    ])

    story: list = []
    # intro
    story.append(_NextTemplate("intro"))
    story.extend(build_intro(FRAME_W - 12))
    # cards
    for rank, j in enumerate(judgments, start=1):
        story.append(PageBreak())
        story.append(_NextTemplate("card"))
        stem = j["stem"]
        entry = index.get(stem, {})
        card = build_card(rank, total, j, entry, persons,
                          mean_is.get(stem, 0.0), frames.get(stem), FRAME_W - 12)
        # keep the whole card together on the page
        story.append(KeepInFrame(FRAME_W - 12, FRAME_H - 12, card, mode="shrink"))

    doc.build(story)
    print(f"\nWrote {OUT_PDF}  ({total + 1} pages: 1 intro + {total} videos)")


from reportlab.platypus.doctemplate import NextPageTemplate as _NextTemplate  # noqa: E402

if __name__ == "__main__":
    main()
