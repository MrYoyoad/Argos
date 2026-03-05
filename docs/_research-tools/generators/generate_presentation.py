#!/usr/bin/env python3
"""
Argos VSP — PPTX Presentation Generator

Creates the complete 31-slide "Argos VSP: Research Findings and Production
Roadmap" presentation with professional styling, real images, entrance
animations, fade transitions, and speaker notes.

Usage:
    python3 docs/_research-tools/generators/generate_presentation.py

Output:
    presentation_materials_20260224/Argos_VSP_Project_Review.pptx
"""

import os
import subprocess
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

# ═══════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent
MATERIALS = Path("/home/ubuntu/presentation_materials_20260224")
PLOTS = MATERIALS / "01_plots_for_slides"
BRANDING = MATERIALS / "08_branding"
VIDEOS = MATERIALS / "06_demo_videos"
OUTPUT = MATERIALS / "Argos_VSP_Project_Review.pptx"

# Image map
IMG = {
    "logo": BRANDING / "BlackLogo300x300-W-BG.png",
    "pipeline": PLOTS / "pipeline_architecture.png",
    "model_arch": PLOTS / "model_architecture.png",
    "P1_quality": PLOTS / "P1_quality_tiers.png",
    "P2_paper": PLOTS / "P2_paper_vs_reality.png",
    "P3_trajectory": PLOTS / "P3_wer_trajectory.png",
    "P3b_is_trajectory": PLOTS / "P3b_is_trajectory.png",
    "P4_lenpen": PLOTS / "P4_lenpen_sensitivity.png",
    "boxplot": PLOTS / "09_boxplot_wwer_all_experiments.png",
    "wer_duration": PLOTS / "01_wer_vs_duration.png",
    "nea_scatter": PLOTS / "14_nea_vs_wwer_scatter.png",
    "empty_halluc": PLOTS / "10_empty_and_hallucination_rates.png",
    "cdf_wwer": PLOTS / "15_cdf_wwer_curated.png",
    "ft_dashboard": PLOTS / "finetune" / "FT_10_summary_dashboard.png",
    "ft_clean": PLOTS / "finetune" / "FT_11_clean_summary.png",
    "tuning_ba": PLOTS / "P5_tuning_before_after.png",
    "improve_ja": PLOTS / "16_improvement_J_vs_A.png",
    "P6_is_radar": PLOTS / "P6_is_radar.png",
    "P6b_radar_dual": PLOTS / "P6b_radar_dual.png",
    "P7_is_wer_scatter": PLOTS / "P7_is_wer_scatter.png",
}

VID = {
    # Curated examples (Slide 14)
    "perfect":        VIDEOS / "IEa7qEkMvfQ_3__c5447488_with_hyp.mp4",
    "bogo":           VIDEOS / "d8BR6hsvzoY_31__2e9546df_with_hyp.mp4",
    "nearmiss":       VIDEOS / "-WQZsfHcPDM_7__5210cac1_with_hyp.mp4",
    "halluc":         VIDEOS / "00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4",
    "tuning_fix":     VIDEOS / "DBhaa45mAro_2__07d05c7a_Part1_with_hyp.mp4",
    "topic_drift":    VIDEOS / "vBCnI4kf3-E_0__d2216cbf_Part1_with_hyp.mp4",
    "salvage":        VIDEOS / "Q8aPjew1aUU_5__621126f2_with_hyp.mp4",
    # Failure modes / salvage (A11b, A13)
    "extreme_halluc": VIDEOS / "BmmJujNQvXw_0__5d6e5798_with_hyp.mp4",
    "phonetic_bridge":VIDEOS / "cT6aHJmM4cA_2__a0c6120f_with_hyp.mp4",
    "wer_broken":     VIDEOS / "0FUlRjBcGGE_21__8fc418e2_with_hyp.mp4",
    "entity_success": VIDEOS / "BS4kTgaiydQ_0__10c532bb_with_hyp.mp4",
    "entity_destroy": VIDEOS / "EMfcKvHA5Uc_0__b74dba61_with_hyp.mp4",
    "ok_demo":        VIDEOS / "8SMYkCQkT4Q_0__fdf516a0_with_hyp.mp4",
}

POSTER_DIR = MATERIALS / ".poster_frames"

# ═══════════════════════════════════════════════════════════════════════
# DESIGN CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

# Slide size (16:9 widescreen)
SL_W = Emu(12192000)   # 13.333 in
SL_H = Emu(6858000)    # 7.5 in

# Colors
BG      = RGBColor(0x0D, 0x1B, 0x2A)  # deep navy
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
TEAL    = RGBColor(0x00, 0xB4, 0xD8)
CORAL   = RGBColor(0xE0, 0x6C, 0x75)
LGRAY   = RGBColor(0xAA, 0xAA, 0xAA)
MGRAY   = RGBColor(0x66, 0x66, 0x66)
DGRAY   = RGBColor(0x33, 0x33, 0x33)
GREEN   = RGBColor(0x4C, 0xAF, 0x50)
YELLOW  = RGBColor(0xFF, 0xC1, 0x07)
GOLD    = RGBColor(0xFF, 0xD5, 0x4F)
ORANGE  = RGBColor(0xFF, 0x98, 0x00)
RED     = RGBColor(0xF4, 0x43, 0x36)
DRED    = RGBColor(0xB7, 0x1C, 0x1C)
NAVY2   = RGBColor(0x15, 0x2A, 0x40)  # slightly lighter navy for cards
NAVY3   = RGBColor(0x1A, 0x35, 0x50)  # lighter still for hover cards

FONT = "Calibri"

# Auto-numbering: incremented by _finish() for each main slide
_auto_num = [0]

# Layout (inches)
MX   = Inches(0.6)      # horizontal margin
MY   = Inches(0.4)      # top margin
CT   = Inches(1.45)     # content top (below title + accent)
CW   = Inches(12.13)    # content width (SL_W - 2*MX)
CH   = Inches(5.55)     # content height
SLW  = Inches(5.6)      # split left width
SRG  = Inches(0.3)      # split gap
SRL  = Inches(6.5)      # split right left
SRW  = Inches(5.93)     # split right width

# ═══════════════════════════════════════════════════════════════════════
# HELPERS — SLIDE SETUP
# ═══════════════════════════════════════════════════════════════════════

def new_slide(prs):
    """Create blank slide with navy background."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_fill = slide.background.fill
    bg_fill.solid()
    bg_fill.fore_color.rgb = BG
    return slide


def set_notes(slide, text):
    """Set speaker notes."""
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


def add_logo(slide, size=Inches(0.35)):
    """Small logo in bottom-right."""
    p = IMG["logo"]
    if p.exists():
        return slide.shapes.add_picture(
            str(p), SL_W - MX - size, SL_H - Inches(0.12) - size, height=size)
    return None


def add_slide_num(slide, num):
    """Slide number in bottom-left."""
    tb = slide.shapes.add_textbox(MX, SL_H - Inches(0.38), Inches(0.5), Inches(0.25))
    p = tb.text_frame.paragraphs[0]
    p.text = str(num)
    _fmt(p, size=Pt(9), color=MGRAY)
    return tb


def add_accent_line(slide, top=Inches(1.2)):
    """Thin teal accent line below title area."""
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MX, top, CW, Pt(1.5))
    shp.fill.solid()
    shp.fill.fore_color.rgb = TEAL
    shp.line.fill.background()
    return shp

# ═══════════════════════════════════════════════════════════════════════
# HELPERS — TEXT
# ═══════════════════════════════════════════════════════════════════════

def _fmt(para, size=Pt(16), color=WHITE, bold=False, italic=False, font=FONT):
    """Format all runs in a paragraph, or create default run formatting."""
    for run in para.runs:
        run.font.size = size
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
    if not para.runs:
        para.font.size = size
        para.font.color.rgb = color
        para.font.bold = bold
        para.font.italic = italic
        para.font.name = font


def add_title(slide, text, top=MY, left=MX, width=None, size=Pt(32)):
    """Add title text box."""
    if width is None:
        width = CW
    tb = slide.shapes.add_textbox(left, top, width, Inches(0.75))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    _fmt(p, size=size, color=WHITE, bold=True)
    return tb


def add_text(slide, text, left, top, width, height, size=Pt(16),
             color=WHITE, bold=False, italic=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP):
    """Add a simple text box."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        body_props = tf._txBody.bodyPr
        body_props.set('anchor', {
            MSO_ANCHOR.TOP: 't', MSO_ANCHOR.MIDDLE: 'ctr',
            MSO_ANCHOR.BOTTOM: 'b'
        }.get(anchor, 't'))
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    _fmt(p, size=size, color=color, bold=bold, italic=italic)
    return tb


def add_rich_text(slide, runs_list, left, top, width, height,
                  align=PP_ALIGN.LEFT, space_after=Pt(6)):
    """
    Add text box with mixed formatting.
    runs_list: list of lists of (text, {props}) tuples — one inner list per paragraph.
    """
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for pi, para_runs in enumerate(runs_list):
        p = tf.paragraphs[0] if pi == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = space_after
        for text, props in para_runs:
            run = p.add_run()
            run.text = text
            run.font.name = props.get("font", FONT)
            run.font.size = props.get("size", Pt(16))
            run.font.color.rgb = props.get("color", WHITE)
            run.font.bold = props.get("bold", False)
            run.font.italic = props.get("italic", False)
    return tb


def add_bullets(slide, items, left, top, width, height, size=Pt(15),
                color=WHITE, bullet_color=TEAL, spacing=Pt(6)):
    """
    Add bullet list. items can be str or (str, {props}) for custom bullets.
    Returns the text box shape.
    """
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, props = item
        else:
            text, props = item, {}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = spacing
        p.alignment = PP_ALIGN.LEFT
        # Bullet character
        brun = p.add_run()
        bc = props.get("bullet", "•")
        brun.text = f"{bc} "
        brun.font.size = size
        brun.font.color.rgb = props.get("bullet_color", bullet_color)
        brun.font.name = FONT
        brun.font.bold = True
        # Text
        trun = p.add_run()
        trun.text = text
        trun.font.size = size
        trun.font.color.rgb = props.get("color", color)
        trun.font.name = FONT
        trun.font.bold = props.get("bold", False)
    return tb

# ═══════════════════════════════════════════════════════════════════════
# HELPERS — SHAPES & IMAGES
# ═══════════════════════════════════════════════════════════════════════

def add_rect(slide, left, top, width, height, fill_color=NAVY2,
             border_color=None, border_width=Pt(1), corner_radius=None):
    """Add a filled rectangle (optionally rounded)."""
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if corner_radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    if border_color:
        shp.line.color.rgb = border_color
        shp.line.width = border_width
    else:
        shp.line.fill.background()
    return shp


def add_image(slide, key_or_path, left, top, width=None, height=None):
    """Add an image by key name or path. Returns shape or None."""
    path = key_or_path if isinstance(key_or_path, Path) else IMG.get(key_or_path)
    if path and path.exists():
        kwargs = {}
        if width:
            kwargs["width"] = width
        if height:
            kwargs["height"] = height
        if not kwargs:
            kwargs["width"] = Inches(4)
        return slide.shapes.add_picture(str(path), left, top, **kwargs)
    # Placeholder rectangle if image missing
    w = width or Inches(4)
    h = height or Inches(3)
    shp = add_rect(slide, left, top, w, h, fill_color=DGRAY, border_color=MGRAY)
    tf = shp.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    name = path.name if path else str(key_or_path)
    p.text = f"[{name}]"
    p.alignment = PP_ALIGN.CENTER
    _fmt(p, size=Pt(11), color=LGRAY)
    try:
        tf._txBody.bodyPr.set('anchor', 'ctr')
    except Exception:
        pass
    return shp


def add_play_button(slide, left, top, size=Inches(1.8)):
    """Create a play button icon (circle + triangle)."""
    # Outer circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, size, size)
    circle.fill.solid()
    circle.fill.fore_color.rgb = NAVY2
    circle.line.color.rgb = WHITE
    circle.line.width = Pt(2.5)
    # Play triangle text
    inset = Inches(0.15)
    tb = slide.shapes.add_textbox(
        left + inset, top + inset, size - 2 * inset, size - 2 * inset)
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "▶"
    run.font.size = Pt(int(size / Inches(1) * 36))
    run.font.color.rgb = WHITE
    run.font.name = FONT
    try:
        tf._txBody.bodyPr.set('anchor', 'ctr')
    except Exception:
        pass
    return circle


def _extract_poster(vid_path, poster_path):
    """Extract first frame from video as a poster image for embedding."""
    poster_path.parent.mkdir(parents=True, exist_ok=True)
    if poster_path.exists():
        return poster_path
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(vid_path), "-vframes", "1",
             "-q:v", "2", str(poster_path)],
            capture_output=True, timeout=10, check=True)
        if poster_path.exists() and poster_path.stat().st_size > 0:
            return poster_path
    except Exception:
        pass
    return None


def add_video_poster(slide, vid_key, left, top, width, height):
    """Show a video poster frame (static thumbnail) with play button overlay.

    This avoids PowerPoint repair issues caused by python-pptx video embeds.
    Falls back to a dark placeholder with play icon if poster not available.
    """
    vid_path = VID.get(vid_key)
    poster = None
    if vid_path and vid_path.exists():
        poster = _extract_poster(vid_path, POSTER_DIR / f"{vid_key}.jpg")
    if poster and poster.exists():
        shape = slide.shapes.add_picture(str(poster), left, top, width, height)
    else:
        # Dark placeholder
        shape = add_rect(slide, left, top, width, height,
                         fill_color=NAVY2, border_color=MGRAY, border_width=Pt(1))
    # Play button overlay (centered, small)
    btn_size = min(width, height) * 0.3
    btn_x = left + (width - btn_size) // 2
    btn_y = top + (height - btn_size) // 2
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, btn_x, btn_y, btn_size, btn_size)
    circle.fill.solid()
    circle.fill.fore_color.rgb = RGBColor(0, 0, 0)
    # Semi-transparent effect via alpha on the XML element
    try:
        spPr = circle._element.find(qn('a:spPr'))
        if spPr is not None:
            sf = spPr.find(qn('a:solidFill'))
            if sf is not None:
                srgb = sf.find(qn('a:srgbClr'))
                if srgb is not None:
                    alpha = etree.SubElement(srgb, qn('a:alpha'))
                    alpha.set('val', '50000')  # 50% opacity
    except Exception:
        pass
    circle.line.fill.background()
    tb = slide.shapes.add_textbox(btn_x, btn_y, btn_size, btn_size)
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "\u25b6"
    run.font.size = Pt(int(btn_size / Inches(1) * 28))
    run.font.color.rgb = WHITE
    run.font.name = FONT
    try:
        tf._txBody.bodyPr.set('anchor', 'ctr')
    except Exception:
        pass
    return shape


def add_video(slide, vid_key, left, top, width, height):
    """Embed an MP4 video with poster frame. Click to play in PowerPoint."""
    vid_path = VID.get(vid_key)
    if not vid_path or not vid_path.exists():
        return add_play_button(slide, left, top, size=min(width, height))
    poster = _extract_poster(vid_path, POSTER_DIR / f"{vid_key}.jpg")
    poster_arg = str(poster) if poster else None
    shape = slide.shapes.add_movie(
        str(vid_path), left, top, width, height,
        poster_frame_image=poster_arg, mime_type="video/mp4")
    # Fix python-pptx bug: add_movie creates <a:hlinkClick r:id="" action="ppaction://media"/>
    # with empty r:id, which triggers PowerPoint repair warning.  Remove empty hlinkClick.
    cNvPr = shape._element.find('.//' + qn('p:cNvPr'))
    if cNvPr is not None:
        for hlink in list(cNvPr):
            if hlink.tag.endswith('hlinkClick'):
                rid = hlink.get(qn('r:id'), '')
                if rid == '':
                    cNvPr.remove(hlink)
    return shape


# ═══════════════════════════════════════════════════════════════════════
# HELPERS — TABLES
# ═══════════════════════════════════════════════════════════════════════

def add_table(slide, headers, rows, left, top, width, row_height=Inches(0.38),
              header_color=TEAL, text_size=Pt(11), col_widths=None,
              row_colors=None):
    """
    Add a styled table. row_colors: dict mapping row_index -> dict mapping
    col_index -> RGBColor for cell text coloring.
    """
    n_rows = 1 + len(rows)
    n_cols = len(headers)
    tbl_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width,
                                        row_height * n_rows)
    tbl = tbl_shape.table
    # Column widths
    if col_widths:
        for i, w in enumerate(col_widths):
            tbl.columns[i].width = w
    # Header row
    for ci, h in enumerate(headers):
        cell = tbl.cell(0, ci)
        cell.text = h
        _shade_cell(cell, _rgb_hex(header_color))
        for p in cell.text_frame.paragraphs:
            _fmt(p, size=text_size, color=WHITE, bold=True)
            p.alignment = PP_ALIGN.CENTER
    # Data rows
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            cell.text = str(val)
            # Alternating row shading
            if ri % 2 == 1:
                _shade_cell(cell, "152a40")
            else:
                _shade_cell(cell, "0d1b2a")
            txt_color = WHITE
            if row_colors and ri in row_colors and ci in row_colors[ri]:
                txt_color = row_colors[ri][ci]
            for p in cell.text_frame.paragraphs:
                _fmt(p, size=text_size, color=txt_color)
                p.alignment = PP_ALIGN.LEFT
    # Remove table borders for dark theme
    _style_table_borders(tbl, "1a3550")
    return tbl_shape


def _shade_cell(cell, hex_color):
    """Set cell background color."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    # Remove existing shading
    for child in list(tcPr):
        if child.tag.endswith('solidFill') or child.tag.endswith('shd'):
            tcPr.remove(child)
    solidFill = etree.SubElement(tcPr, qn('a:solidFill'))
    srgb = etree.SubElement(solidFill, qn('a:srgbClr'))
    srgb.set('val', hex_color)


def _style_table_borders(tbl, hex_color):
    """Set subtle table borders."""
    tbl_xml = tbl._tbl
    tblPr = tbl_xml.tblPr
    if tblPr is None:
        tblPr = etree.SubElement(tbl_xml, qn('a:tblPr'))
    # Remove default style
    for attr in ['bandRow', 'firstRow', 'lastRow', 'bandCol']:
        tblPr.set(attr, '0')


def _rgb_hex(color):
    """Convert RGBColor to hex string."""
    return f"{color[0]:02x}{color[1]:02x}{color[2]:02x}"

# ═══════════════════════════════════════════════════════════════════════
# HELPERS — ANIMATIONS & TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════

def add_fade_transition(slide, speed='med'):
    """Add fade transition to slide.

    ECMA-376 requires p:sld children in order:
        cSld, clrMapOvr, transition, timing, extLst
    So we must insert transition *before* any existing timing element,
    not just append it (python-pptx add_movie creates timing early).
    """
    sld = slide._element
    # Remove existing transition
    for child in list(sld):
        if child.tag.endswith('transition'):
            sld.remove(child)
    transition = etree.Element(qn('p:transition'))
    transition.set('spd', speed)
    transition.set('advClick', '1')
    etree.SubElement(transition, qn('p:fade'))
    # Insert before timing/extLst to maintain ECMA-376 order
    timing_el = sld.find(qn('p:timing'))
    if timing_el is not None:
        sld.insert(list(sld).index(timing_el), transition)
    else:
        sld.append(transition)


def _fix_pptx_video_compat(pptx_path):
    """Post-process saved PPTX to wrap video p:pic in mc:AlternateContent.

    python-pptx embeds videos as bare p:pic elements with p14:media extensions.
    PowerPoint expects these wrapped in mc:AlternateContent (Choice/Fallback)
    per ISO/IEC 29500.  Without the wrapper, PowerPoint shows a repair dialog.

    This function opens the saved PPTX zip, fixes affected slide XMLs, and
    writes the corrected file back.
    """
    import zipfile, io, re as _re, copy, shutil, tempfile

    MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
    P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.pptx')
    os.close(tmp_fd)
    changed = False

    with zipfile.ZipFile(pptx_path, 'r') as zin, \
         zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)

            # Only process slide XMLs that contain videoFile
            if (item.filename.startswith('ppt/slides/slide') and
                    item.filename.endswith('.xml') and
                    b'videoFile' in raw):
                text = raw.decode('utf-8')

                # Ensure mc namespace is declared on root element
                if 'xmlns:mc=' not in text:
                    text = text.replace(
                        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"',
                        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                        f'xmlns:mc="{MC_NS}" mc:Ignorable="p14"',
                        1)
                elif 'mc:Ignorable' not in text:
                    # mc namespace declared but no Ignorable — add it
                    text = _re.sub(
                        r'(xmlns:mc="[^"]*")',
                        r'\1 mc:Ignorable="p14"', text, count=1)

                # Ensure p14 namespace is declared on root element
                if 'xmlns:p14=' not in text:
                    text = text.replace(
                        f'xmlns:mc="{MC_NS}"',
                        f'xmlns:mc="{MC_NS}" xmlns:p14="{P14_NS}"',
                        1)

                # Wrap each video p:pic in mc:AlternateContent
                # Match <p:pic>...</p:pic> blocks containing videoFile
                def _wrap_video_pic(m):
                    pic_xml = m.group(0)
                    if 'videoFile' not in pic_xml:
                        return pic_xml
                    # Build fallback: same pic but without videoFile and p14:media
                    fallback = _re.sub(
                        r'<a:videoFile[^/]*/>', '', pic_xml)
                    fallback = _re.sub(
                        r'<p:extLst>.*?</p:extLst>', '', fallback,
                        flags=_re.DOTALL)
                    # Keep inline p14 namespace decls in Choice version
                    # (removing them can break namespace resolution)
                    choice_xml = pic_xml
                    return (f'<mc:AlternateContent>'
                            f'<mc:Choice Requires="p14">{choice_xml}</mc:Choice>'
                            f'<mc:Fallback>{fallback}</mc:Fallback>'
                            f'</mc:AlternateContent>')

                new_text = _re.sub(
                    r'<p:pic>.*?</p:pic>', _wrap_video_pic, text,
                    flags=_re.DOTALL)

                if new_text != text:
                    changed = True
                raw = new_text.encode('utf-8')

            zout.writestr(item, raw)

    if changed:
        shutil.move(tmp_path, pptx_path)
    else:
        os.remove(tmp_path)


def _para_indices(shape):
    """Return indices of non-empty paragraphs in shape's text frame."""
    try:
        return [i for i, p in enumerate(shape.text_frame.paragraphs)
                if p.text.strip()]
    except (AttributeError, TypeError):
        return []


def add_animations(slide, groups, click_reveal=False, para_build=False):
    """
    Add click-to-advance entrance animations (Appear) with valid OOXML.

    Produces the three-level par nesting that PowerPoint 365 expects:
      timing > tnLst > par(tmRoot) > seq(mainSeq)
        per click:  par(indefinite) > par(delay=0) > par(presetID=1) > set

    groups       – list of lists of shape objects; each inner list is one
                   animation group (one "click step").
    click_reveal – True  → first group visible on slide entry;
                   False → all groups hidden until clicked.
    para_build   – True  → multi-paragraph text shapes (bullet lists)
                   reveal one paragraph per click instead of all at once.
    """
    if not groups:
        return
    groups = [g for g in groups if g]
    if not groups:
        return

    # ── Collect all animatable shapes ──────────────────────────────────
    all_anim_shapes = []
    for gi, group in enumerate(groups):
        for shape in group:
            if shape is None:
                continue
            try:
                _ = shape.shape_id
                all_anim_shapes.append((gi, shape))
            except AttributeError:
                continue
    if not all_anim_shapes:
        return

    # ── Expand groups into click steps ─────────────────────────────────
    # Each step is a list of (shape, para_idx | None) tuples.
    click_steps = []
    para_build_spids = set()   # shape IDs needing build="p"
    hidden_spids = set()       # shape IDs that go in bldLst

    for gi, group in enumerate(groups):
        is_entry = click_reveal and gi == 0
        step_items = []

        for shape in group:
            if shape is None:
                continue
            try:
                spid = shape.shape_id
            except AttributeError:
                continue

            pindices = _para_indices(shape) if para_build else []

            if len(pindices) > 1:
                # Multi-paragraph → per-paragraph click steps
                para_build_spids.add(spid)
                hidden_spids.add(spid)
                for pi in pindices:
                    click_steps.append([(shape, pi)])
            elif is_entry:
                pass   # visible on entry — no animation needed
            else:
                hidden_spids.add(spid)
                step_items.append((shape, None))

        if step_items:
            click_steps.append(step_items)

    if not click_steps:
        return

    # ── Remove existing timing ─────────────────────────────────────────
    sld = slide._element
    for child in list(sld):
        if child.tag.endswith('timing'):
            sld.remove(child)

    _id = [1]
    def nid():
        v = _id[0]; _id[0] += 1; return str(v)

    SE = etree.SubElement

    # ── Timing tree ────────────────────────────────────────────────────
    timing  = SE(sld, qn('p:timing'))
    tnLst   = SE(timing, qn('p:tnLst'))
    par0    = SE(tnLst, qn('p:par'))
    cTn0    = SE(par0, qn('p:cTn'))
    cTn0.set('id', nid()); cTn0.set('dur', 'indefinite')
    cTn0.set('restart', 'never'); cTn0.set('nodeType', 'tmRoot')
    root_cl = SE(cTn0, qn('p:childTnLst'))

    # Main click sequence
    seq     = SE(root_cl, qn('p:seq'))
    seq.set('concurrent', '1'); seq.set('nextAc', 'seek')
    cTn_seq = SE(seq, qn('p:cTn'))
    cTn_seq.set('id', nid()); cTn_seq.set('dur', 'indefinite')
    cTn_seq.set('nodeType', 'mainSeq')
    seq_cl  = SE(cTn_seq, qn('p:childTnLst'))

    for step in click_steps:
        # Level 1 – click step container (delay=indefinite → waits for click)
        p1 = SE(seq_cl, qn('p:par'))
        c1 = SE(p1, qn('p:cTn'))
        c1.set('id', nid()); c1.set('fill', 'hold')
        s1 = SE(c1, qn('p:stCondLst'))
        SE(s1, qn('p:cond')).set('delay', 'indefinite')
        ch1 = SE(c1, qn('p:childTnLst'))

        # Level 2 – group container (delay=0)
        p2 = SE(ch1, qn('p:par'))
        c2 = SE(p2, qn('p:cTn'))
        c2.set('id', nid()); c2.set('fill', 'hold')
        s2 = SE(c2, qn('p:stCondLst'))
        SE(s2, qn('p:cond')).set('delay', '0')
        ch2 = SE(c2, qn('p:childTnLst'))

        for si, (shape, para_idx) in enumerate(step):
            spid = str(shape.shape_id)
            delay_ms = si * 120    # subtle stagger within group

            # Level 3 – Appear effect (presetID=1)
            p3 = SE(ch2, qn('p:par'))
            c3 = SE(p3, qn('p:cTn'))
            c3.set('id', nid())
            c3.set('presetID', '1')         # Appear
            c3.set('presetClass', 'entr')
            c3.set('presetSubtype', '0')
            c3.set('fill', 'hold')
            c3.set('grpId', '0')
            c3.set('nodeType', 'clickEffect' if si == 0 else 'withEffect')
            s3 = SE(c3, qn('p:stCondLst'))
            SE(s3, qn('p:cond')).set('delay', str(delay_ms))
            ch3 = SE(c3, qn('p:childTnLst'))

            # <p:set> visibility → visible
            p_set = SE(ch3, qn('p:set'))
            cb = SE(p_set, qn('p:cBhvr'))
            ct = SE(cb, qn('p:cTn'))
            ct.set('id', nid()); ct.set('dur', '1'); ct.set('fill', 'hold')
            sc = SE(ct, qn('p:stCondLst'))
            SE(sc, qn('p:cond')).set('delay', '0')
            tgt = SE(cb, qn('p:tgtEl'))
            sp = SE(tgt, qn('p:spTgt'))
            sp.set('spid', spid)
            if para_idx is not None:
                tx = SE(sp, qn('p:txEl'))
                pr = SE(tx, qn('p:pRg'))
                pr.set('st', str(para_idx)); pr.set('end', str(para_idx))
            al = SE(cb, qn('p:attrNameLst'))
            SE(al, qn('p:attrName')).text = 'style.visibility'
            to = SE(p_set, qn('p:to'))
            SE(to, qn('p:strVal')).set('val', 'visible')

    # Prev / Next navigation
    for evt, tag in [('onPrev', 'p:prevCondLst'),
                     ('onNext', 'p:nextCondLst')]:
        cl = SE(seq, qn(tag))
        c  = SE(cl, qn('p:cond'))
        c.set('evt', evt); c.set('delay', '0')
        t  = SE(c, qn('p:tgtEl'))
        SE(t, qn('p:sldTgt'))

    # ── Build list — shapes that start HIDDEN ──────────────────────────
    if hidden_spids:
        bldLst = SE(timing, qn('p:bldLst'))
        seen = set()
        for _gi, shape in all_anim_shapes:
            spid = shape.shape_id
            if spid not in hidden_spids or spid in seen:
                continue
            seen.add(spid)
            bp = SE(bldLst, qn('p:bldP'))
            bp.set('spid', str(spid))
            bp.set('grpId', '0')
            bp.set('animBg', '1')
            if spid in para_build_spids:
                bp.set('build', 'p')

# ═══════════════════════════════════════════════════════════════════════
# REUSABLE SLIDE BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def _finish(slide, num, notes, anim_groups=None, click_reveal=True,
            para_build=True):
    """Add logo, slide number, transition, animations, and notes.

    num: ignored for int values (auto-numbered); string values (e.g. "A1")
         are used directly for appendix slides.  Use None to skip numbering
         entirely (section dividers).
    click_reveal: if True, first animation group visible on entry, rest
        appear one-by-one on click.  Default True.
    para_build: if True, multi-paragraph text shapes (bullet lists) reveal
        one paragraph per click.  Default True.
    """
    if num is None:
        display_num = ""  # Section dividers — no number
    elif isinstance(num, int):
        _auto_num[0] += 1
        display_num = _auto_num[0]
    else:
        display_num = num  # Appendix labels like "A1"
    add_logo(slide)
    add_slide_num(slide, display_num)
    add_fade_transition(slide)
    if anim_groups:
        try:
            add_animations(slide, anim_groups, click_reveal=click_reveal,
                           para_build=para_build)
        except Exception:
            pass  # Graceful fallback — slides still render
    set_notes(slide, notes)
    return slide


def build_split(prs, num, title, image_key, notes, big_num=None,
                num_color=TEAL, num_label=None, bullets=None,
                bottom_text=None):
    """Split layout: text/numbers left, image right."""
    slide = new_slide(prs)
    t = add_title(slide, title)
    add_accent_line(slide)

    left_shapes = []
    top = CT

    if big_num:
        s = add_text(slide, big_num, MX, top, SLW, Inches(1.1),
                     size=Pt(72), color=num_color, bold=True)
        left_shapes.append(s)
        top += Inches(1.1)
        if num_label:
            s2 = add_text(slide, num_label, MX, top, SLW, Inches(0.5),
                          size=Pt(15), color=LGRAY)
            left_shapes.append(s2)
            top += Inches(0.55)

    if bullets:
        # Cap bullet height so it doesn't overlap bottom_text at y=6.4
        max_h = Inches(6.1) - top if bottom_text else CH - (top - CT) - Inches(0.3)
        s = add_bullets(slide, bullets, MX, top, SLW, max_h)
        left_shapes.append(s)

    if bottom_text:
        s = add_text(slide, bottom_text, MX, Inches(6.45), CW, Inches(0.5),
                     size=Pt(13), color=LGRAY, italic=True)
        left_shapes.append(s)

    img = add_image(slide, image_key, SRL, CT, width=SRW)
    _finish(slide, num, notes, [left_shapes, [img]], click_reveal=True)
    return slide


def build_bullets(prs, num, title, items, notes, subtitle=None):
    """Full-width bullet list slide."""
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    top = CT
    if subtitle:
        s = add_text(slide, subtitle, MX, top, CW, Inches(0.4),
                     size=Pt(16), color=LGRAY, italic=True)
        top += Inches(0.5)

    bul = add_bullets(slide, items, MX, top, CW, CH - (top - CT))
    _finish(slide, num, notes, [[bul]], click_reveal=True)
    return slide


def build_two_col(prs, num, title, left_title, left_items, right_title,
                  right_items, notes, left_color=TEAL, right_color=CORAL):
    """Two-column text layout."""
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column
    lt = add_text(slide, left_title, MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=left_color, bold=True)
    lb = add_bullets(slide, left_items, MX, CT + Inches(0.5), col_w,
                     CH - Inches(0.5))

    # Right column
    rx = MX + col_w + gap
    rt = add_text(slide, right_title, rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=right_color, bold=True)
    rb = add_bullets(slide, right_items, rx, CT + Inches(0.5), col_w,
                     CH - Inches(0.5))

    _finish(slide, num, notes, [[lt, lb], [rt], [rb]], click_reveal=True)
    return slide


def build_full_image(prs, num, title, image_key, notes, subtitle=None,
                     bottom_text=None):
    """Full-width image with optional text."""
    slide = new_slide(prs)
    add_title(slide, title)
    add_accent_line(slide)

    top = CT
    if subtitle:
        add_text(slide, subtitle, MX, top, CW, Inches(0.35),
                 size=Pt(16), color=LGRAY, italic=True)
        top += Inches(0.4)

    # Cap image height to avoid overlapping bottom text or going off-screen
    if bottom_text:
        img_h = Inches(4.5)
    else:
        img_h = SL_H - top - Inches(0.2)  # stay within slide bounds
    img = add_image(slide, image_key, MX, top, width=CW, height=img_h)

    if bottom_text:
        add_text(slide, bottom_text, MX, Inches(6.3), CW, Inches(0.5),
                 size=Pt(13), color=LGRAY, italic=True)

    _finish(slide, num, notes, [[img]])
    return slide

# ═══════════════════════════════════════════════════════════════════════
# NEW SLIDES — EXECUTIVE SUMMARY, TOC, IS BUILD-UP
# ═══════════════════════════════════════════════════════════════════════

def slide_exec_summary(prs):
    """Executive summary — bottom-line-up-front overview."""
    slide = new_slide(prs)
    add_title(slide, "Executive Summary")
    add_accent_line(slide)

    add_text(slide, "Three months of research and engineering on visual speech processing:",
             MX, CT, CW, Inches(0.4), size=Pt(16), color=LGRAY, italic=True)

    items = [
        ("Evaluated a lip-reading AI on 1,497 real-world YouTube segments",
         {"bold": True}),
        "Standard metric (WER) reports 64.1% error — 2.5\u00d7 worse than benchmark",
        ("Our new Intelligibility Score (IS) reveals 40% is actually useful — "
         "3.5\u00d7 more than WER admits", {"color": TEAL, "bold": True}),
        "Built a complete production system: 8-stage pipeline, standalone container",
        ("Clear roadmap to IS 3.5\u20134.0 (from 2.52) through data scaling + LLM upgrade",
         {"color": TEAL}),
        ("Arabic pipeline: replication roadmap established for Arabic lip-reading", {}),
        "Produced 8 comprehensive research reports",
    ]
    bul = add_bullets(slide, items, MX, CT + Inches(0.6), CW, Inches(4.0),
                      size=Pt(17), spacing=Pt(14))

    _finish(slide, 2,
        "Executive summary. Three months of work on visual speech processing. "
        "Key finding: WER dramatically overstates failure. Our Intelligibility "
        "Score shows 40% of output is properly captured, not the 11% WER suggests. "
        "Complete production system delivered. Clear roadmap to improve further.",
        [[bul]], click_reveal=True)



def slide_wer_lies(prs):
    """Side-by-side truth: WER says failure, IS says excellent."""
    slide = new_slide(prs)
    add_title(slide, "WER: The Metric That Lies")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)
    card_h = Inches(2.8)

    # Left card: WER verdict (CORAL)
    wer_shapes = []
    wer_shapes.append(add_rect(slide, MX, CT, col_w, card_h,
                       fill_color=NAVY2, border_color=CORAL, border_width=Pt(3),
                       corner_radius=True))
    wer_shapes.append(add_text(slide, "46.2%", MX + Inches(0.3), CT + Inches(0.2),
                                col_w - Inches(0.6), Inches(1.0),
                                size=Pt(64), color=CORAL, bold=True,
                                align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide, "Word Error Rate",
                                MX + Inches(0.3), CT + Inches(1.2),
                                col_w - Inches(0.6), Inches(0.3),
                                size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide, 'Verdict: "FAILING"',
                                MX + Inches(0.3), CT + Inches(1.6),
                                col_w - Inches(0.6), Inches(0.35),
                                size=Pt(18), color=CORAL, bold=True,
                                align=PP_ALIGN.CENTER))
    wer_shapes.append(add_text(slide,
        "6 insertions, 1 deletion\n= nearly half the words are \"wrong\"",
        MX + Inches(0.3), CT + Inches(2.1), col_w - Inches(0.6), Inches(0.6),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER))

    # Right card: IS verdict (GREEN)
    rx = MX + col_w + gap
    is_shapes = []
    is_shapes.append(add_rect(slide, rx, CT, col_w, card_h,
                      fill_color=NAVY2, border_color=GREEN, border_width=Pt(3),
                      corner_radius=True))
    is_shapes.append(add_text(slide, "4.03", rx + Inches(0.3), CT + Inches(0.2),
                               col_w - Inches(0.6), Inches(1.0),
                               size=Pt(64), color=GREEN, bold=True,
                               align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide, "Intelligibility Score (Excellent)",
                               rx + Inches(0.3), CT + Inches(1.2),
                               col_w - Inches(0.6), Inches(0.3),
                               size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide, 'Verdict: "EXCELLENT"',
                               rx + Inches(0.3), CT + Inches(1.6),
                               col_w - Inches(0.6), Inches(0.35),
                               size=Pt(18), color=GREEN, bold=True,
                               align=PP_ALIGN.CENTER))
    is_shapes.append(add_text(slide,
        "Semantic similarity: 0.90\nMeaning fully preserved",
        rx + Inches(0.3), CT + Inches(2.1), col_w - Inches(0.6), Inches(0.6),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER))

    # Bottom: ref/hyp comparison + callout
    bottom_shapes = []
    by = CT + card_h + Inches(0.3)
    bottom_shapes.append(add_rich_text(slide, [
        [("\u25b6 Reference:  ", {"size": Pt(12), "color": LGRAY, "bold": True}),
         ("i want you to remember all these i want you to memorize them",
          {"size": Pt(12), "color": WHITE})],
        [("\u25b6 Prediction: ", {"size": Pt(12), "color": LGRAY, "bold": True}),
         ("i want you to remember all the things that i wanted you to memorize in my",
          {"size": Pt(12), "color": TEAL})],
    ], MX, by, CW, Inches(0.7), space_after=Pt(4)))
    cb_y = by + Inches(0.8)
    bottom_shapes.append(add_rect(slide, MX + Inches(1.5), cb_y,
                                   CW - Inches(3.0), Inches(0.6),
                                   fill_color=NAVY2, border_color=TEAL,
                                   border_width=Pt(2), corner_radius=True))
    bottom_shapes.append(add_text(slide,
        "WER counts word edits.  IS asks: did the viewer get the message?  Here \u2014 yes, completely.",
        MX + Inches(1.7), cb_y + Inches(0.1), CW - Inches(3.4), Inches(0.4),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER))

    _finish(slide, 0,
        "Side-by-side: same segment scores 46.2% WER (failure) but IS 4.03 "
        "(excellent). The prediction preserves the complete meaning.",
        [wer_shapes, is_shapes, bottom_shapes], click_reveal=True)


def slide_toc(prs):
    """Table of contents — 4-section overview."""
    slide = new_slide(prs)
    add_title(slide, "Presentation Overview")
    add_accent_line(slide)

    sections = [
        ("1. Context",
         "What is lip reading? \u2022 How does the system work? \u2022 What's the benchmark?",
         TEAL),
        ("2. Research Findings",
         "Real-world evaluation \u2022 Intelligibility Score metric \u2022 Failure analysis "
         "\u2022 Tuning experiments",
         TEAL),
        ("3. Engineering",
         "8-stage pipeline \u2022 Modular refactoring \u2022 Standalone container "
         "\u2022 Evaluation infrastructure",
         TEAL),
        ("4. Future Directions",
         "Improvement roadmap \u2022 Data scaling \u2022 LLM upgrade \u2022 "
         "Arabic pipeline \u2022 Target: IS 3.5\u20134.0",
         TEAL),
    ]
    shapes = []
    y = CT + Inches(0.1)
    for sec_title, desc, color in sections:
        r = add_rect(slide, MX, y, CW, Inches(1.05), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        add_text(slide, sec_title, MX + Inches(0.3), y + Inches(0.1),
                 CW - Inches(0.6), Inches(0.4),
                 size=Pt(22), color=WHITE, bold=True)
        add_text(slide, desc, MX + Inches(0.3), y + Inches(0.55),
                 CW - Inches(0.6), Inches(0.4),
                 size=Pt(13), color=LGRAY)
        shapes.append(r)
        y += Inches(1.25)

    _finish(slide, 3,
        "Four sections. Context sets the stage — what is lip reading, "
        "how the system works. Research findings are the core: our novel "
        "evaluation framework and what we learned. Engineering covers the "
        "production system. Future directions lays out the improvement roadmap.",
        [[s] for s in shapes], click_reveal=True)


def slide_is_foreshadow(prs):
    """Brief IS introduction — bridge from WER limitations."""
    slide = new_slide(prs)
    add_title(slide, "We Need a Better Metric")
    add_accent_line(slide)

    bul = add_bullets(slide, [
        "WER counts word errors — but ignores whether the viewer understood",
        ("We created the Intelligibility Score (IS): a composite 0\u20135 metric",
         {"bold": True, "color": TEAL}),
        "Combines 6 quality signals: meaning, phonetics, word accuracy, entities, length",
        ("IS \u2265 3.0 = \u201cProperly Captured\u201d — the viewer gets the right message",
         {"color": GREEN, "bold": True}),
    ], MX, CT + Inches(0.2), CW, Inches(3.5), size=Pt(17))

    add_text(slide,
        "Designed at development time, runs as pure "
        "deterministic Python — $0 per evaluation, 100% reproducible.",
        MX, Inches(5.0), CW, Inches(0.5),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Bridge slide: WER is blind to meaning. We created IS — a composite "
        "0-5 metric combining 6 quality signals. IS >= 3.0 means the viewer "
        "gets the right message. Designed at development time, "
        "runs as deterministic Python at evaluation time.",
        [[bul]], click_reveal=True)


def slide_is_intro(prs):
    """Introduce IS concept before showing results."""
    slide = new_slide(prs)
    add_title(slide, "Introducing the Intelligibility Score")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — motivation
    lt = add_text(slide, "Why a new metric?", MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        "WER counts word errors but ignores meaning",
        '"admiral" \u2192 "animal" gets same WER as "the" \u2192 "a"',
        "WER treats all errors equally \u2014 but not all errors matter equally",
        "We need: does a viewer get the right message?",
    ], MX, CT + Inches(0.55), col_w, Inches(3.0), size=Pt(15))

    # Right column — what IS is
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "What is IS?", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)
    rb = add_bullets(slide, [
        ("Composite score from 0 to 5", {"bold": True}),
        "Combines 6 complementary quality signals",
        "Designed at development time, not per-sample",
        "Fully deterministic at runtime \u2014 no LLM per sample",
        "Free, reproducible, decomposable",
        ('IS \u2265 3.0 = "Properly Captured"', {"color": TEAL, "bold": True}),
    ], rx, CT + Inches(0.55), rw, Inches(3.5), size=Pt(15))

    # Calculation method details — positioned below right column bullets
    # Order: WWER first (builds on WER motivation), NEA second (binary metric),
    # then remaining signals briefly. Phonetic/Semantic detail deferred to slide 16.
    calc = add_rich_text(slide, [
        [("How each signal is calculated:", {"size": Pt(13), "color": WHITE, "bold": True})],
        [("WWER (15%): ", {"size": Pt(11), "color": CORAL, "bold": True}),
         ("WER weights all words equally \u2014 WWER fixes this. Content words (nouns, verbs, names) "
          "penalized 2\u00d7, function words ('the', 'a') only 0.5\u00d7. "
          "Losing 'Admiral McRae' matters more than losing 'the'.",
          {"size": Pt(11), "color": LGRAY})],
        [("NEA (15%): ", {"size": Pt(11), "color": CORAL, "bold": True}),
         ("Named Entity F1 \u2014 are names, numbers, proper nouns preserved? "
          "Extracted via spaCy NER, scored as precision/recall. "
          "Binary: entities are either correct or destroyed, no partial credit.",
          {"size": Pt(11), "color": LGRAY})],
        [("Semantic (25%): ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("Sentence-level meaning similarity via embeddings (see next slide for details).",
          {"size": Pt(11), "color": LGRAY})],
        [("Phonetic (15%): ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("Pronunciation-based similarity \u2014 catches words that sound right but spell differently (details next slide).",
          {"size": Pt(11), "color": LGRAY})],
        [("Length (15%): ", {"size": Pt(11), "color": TEAL, "bold": True}),
         ("Output length vs reference length ratio. Catches truncation (too short) and hallucination (too long).",
          {"size": Pt(11), "color": LGRAY})],
    ], MX, CT + Inches(3.8), CW, Inches(2.0))

    _finish(slide, 0,
        "IS introduction. WER can't distinguish meaning preservation from "
        "destruction. First, we introduce WWER: WER treats all words equally, "
        "but WWER penalizes content words 2x and discounts function words 0.5x, "
        "so losing a name hurts more than losing 'the'. Second, NEA: Named "
        "Entity F1 checks whether names, numbers, and proper nouns survive "
        "the lip-reading process -- binary pass/fail per entity. Third, IS "
        "itself: a composite 0-5 metric combining 6 signals (WWER, NEA, WER, "
        "Semantic, Phonetic, Length Ratio) that together capture whether a "
        "viewer would understand the output. Designed at development time, "
        "runs as pure deterministic Python at evaluation time. "
        "IS >= 3.0 means properly captured. Phonetic and Semantic calculation "
        "details are covered on the next slide.",
        [[lt, lb], [rt, rb], [calc]], click_reveal=True)


def slide_tuning_intro(prs):
    """Motivation slide: why we ran 13 tuning experiments."""
    slide = new_slide(prs)
    add_title(slide, "Can We Tune Our Way Out?")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: The question
    lt = add_text(slide, "The Question", MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "The visual encoder is the primary bottleneck",
        "But decode parameters control HOW the LLM generates text",
        "Can beam search, length penalty, or temperature improve output?",
        ("We ran 13 systematic experiments to find out", {"bold": True}),
    ], MX, CT + Inches(0.55), col_w, Inches(3.0), size=Pt(15))

    # Right: What we varied
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Parameters Tested", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)

    params = [
        ("Beam size", "5 \u2192 50 candidates"),
        ("Length penalty", "\u22120.5 \u2192 2.0"),
        ("Temperature", "0.3 \u2192 1.5"),
        ("Sampling strategy", "greedy vs nucleus"),
        ("Repetition penalty", "on / off"),
    ]
    py = CT + Inches(0.55)
    for name, desc in params:
        add_text(slide, f"{name}: {desc}",
                 rx + Inches(0.2), py, rw - Inches(0.4), Inches(0.35),
                 size=Pt(14), color=WHITE)
        py += Inches(0.45)

    # Bottom
    add_text(slide,
        "107-segment test set \u2022 Best config validated on all 1,497 segments",
        MX, Inches(6.4), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Motivation for tuning. The visual encoder determines which segments "
        "succeed or fail, but decode parameters affect output quality. We ran "
        "13 experiments varying beam size, length penalty, temperature, sampling, "
        "and repetition penalty. Tested on 107 segments, best config validated "
        "on the full 1,497-segment dataset.",
        [[lt, lb], [rt]], click_reveal=True)


def slide_is_signals(prs):
    """Step-by-step breakdown of the 6 IS signals with weight rationale."""
    slide = new_slide(prs)
    add_title(slide, "IS: Six Signals of Quality")
    add_accent_line(slide)

    # Each signal: name, weight, question, how it works, why this weight, color
    signals = [
        ("Semantic Similarity", "(25%)",
         "Does the output preserve the intended meaning?",
         "Sentence embeddings (SBERT) \u2014 cosine distance in 384-dim meaning space",
         'Standard WER treats "admiral" \u2192 "animal" the same as "the" \u2192 "a". '
         "Semantic similarity captures that these are fundamentally different errors "
         "\u2014 one destroys meaning, the other doesn't.",
         TEAL),
        ("Phonetic Similarity", "(15%)",
         "Do the words sound like what was actually said?",
         "Double Metaphone encoding \u2014 maps words to pronunciation codes",
         "Lip-reading outputs are phonetically constrained \u2014 the model sees mouth "
         "shapes, not text. Phonetic similarity measures how well it decoded what "
         "the lips actually produced.",
         TEAL),
        ("Inverse WER", "(15%)",
         "How many words are correct at the surface level?",
         "Standard 1 \u2212 WER (edit distance: substitutions + insertions + deletions)",
         "The universal baseline in speech recognition. Necessary but insufficient "
         "\u2014 a WER of 60% tells you nothing about whether the meaning survived.",
         TEAL),
        ("Inverse WWER", "(15%)",
         "Are the important words correct?",
         'Entities weighted 2\u00d7, content words 1\u00d7, function words 0.5\u00d7',
         'Not all words carry equal information. Losing "the" barely matters; '
         'losing "Admiral McRae" is catastrophic. WWER weights errors by '
         "information content.",
         TEAL),
        ("Named Entity F1", "(15%)",
         "Are names, numbers, and places preserved?",
         "spaCy NER extraction \u2192 precision/recall on proper nouns",
         "Entities are irreplaceable \u2014 a viewer can infer a missing 'the' from "
         "context, but cannot recover a lost name or number. Binary pass/fail "
         "nature makes it the swing factor.",
         CORAL),
        ("Length Ratio", "(15%)",
         "Is the output the right length?",
         "len(hypothesis) / len(reference) \u2014 ideal = 1.0",
         "Safety net for extreme failures: ratio > 2.0 = hallucination (model "
         "rambling), ratio < 0.3 = truncation (model gave up). Lowest real impact "
         "\u2014 most outputs are roughly correct length.",
         LGRAY),
    ]

    bw = Inches(5.76)
    bh = Inches(1.65)
    gap_x = Inches(0.6)
    gap_y = Inches(0.05)

    anim_groups = []
    for i, (name, weight, question, how, why_weight, color) in enumerate(signals):
        col = i % 2
        row = i // 2
        x = MX + col * (bw + gap_x)
        y = CT + row * (bh + gap_y)

        r = add_rect(slide, x, y, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, f"{name} {weight}", x + Inches(0.15), y + Inches(0.06),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(14), color=color, bold=True)
        add_text(slide, question, x + Inches(0.15), y + Inches(0.34),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(12), color=WHITE)
        add_text(slide, how, x + Inches(0.15), y + Inches(0.62),
                 bw - Inches(0.3), Inches(0.28),
                 size=Pt(10), color=LGRAY, italic=True)
        add_text(slide, f"\u25b8 {why_weight}",
                 x + Inches(0.15), y + Inches(0.92),
                 bw - Inches(0.3), Inches(0.68),
                 size=Pt(11), color=GOLD)
        anim_groups.append([r])

    # Formula at bottom
    add_text(slide,
        "IS = 0.25\u00d7Semantic + 0.15\u00d7(Phonetic + InvWER + InvWWER + NEA + Length)"
        "   \u2022   Score: 0\u20135   \u2022   Threshold: IS \u2265 3.0",
        MX, Inches(6.55), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Six signals with weight rationale. Semantic (25%) gets the highest "
        "weight because meaning preservation is the ultimate goal \u2014 it drives "
        "28.5% of IS variance. The other 5 signals each get 15%. Phonetic, WER, "
        "WWER, and NEA form a 'word accuracy' cluster (60% total weight) that "
        "measures whether the encoder decoded the right words. Length ratio is "
        "a safety check for hallucination and truncation. The 3 independent "
        "dimensions: word accuracy (~60%), meaning preservation (~28%), "
        "output sanity (~9%).",
        anim_groups)


def slide_is_weight_rationale(prs):
    """Explain why IS uses 25%/15% weighting and the 3-dimension design."""
    slide = new_slide(prs)
    add_title(slide, "Why These Weights? Three Dimensions of Quality")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — the 3 dimensions
    lt = add_text(slide, "Three Independent Dimensions",
                  MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)

    dims = [
        ("Word Accuracy", "60%", TEAL,
         "Phonetic + WER + WWER + NEA (4 \u00d7 15%)",
         "All 4 correlate tightly (r > 0.79). Did the model get the right words?"),
        ("Meaning Preservation", "28%", GREEN,
         "Semantic Similarity (1 \u00d7 25%)",
         "Highest single weight \u2014 meaning is the ultimate deliverable."),
        ("Output Sanity", "9%", LGRAY,
         "Length Ratio (1 \u00d7 15%)",
         "Safety net: catches hallucination (too long) and truncation (too short)."),
    ]

    py = CT + Inches(0.55)
    dim_shapes = []
    for name, pct, color, signals, desc in dims:
        r = add_rect(slide, MX, py, col_w, Inches(1.35), fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, name, MX + Inches(0.2), py + Inches(0.08),
                 Inches(3.5), Inches(0.35), size=Pt(16), color=color, bold=True)
        add_text(slide, pct, MX + col_w - Inches(1.0), py + Inches(0.08),
                 Inches(0.8), Inches(0.35), size=Pt(16), color=color,
                 bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, signals, MX + Inches(0.2), py + Inches(0.45),
                 col_w - Inches(0.4), Inches(0.35), size=Pt(13), color=WHITE)
        add_text(slide, desc, MX + Inches(0.2), py + Inches(0.85),
                 col_w - Inches(0.4), Inches(0.4), size=Pt(12), color=LGRAY)
        dim_shapes.append(r)
        py += Inches(1.5)

    # Right column — design rationale
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Why 25% / 15%?", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Semantic gets 25%: meaning is the ultimate deliverable",
         {"bold": True, "color": GREEN}),
        "If a viewer understands the message, the transcription succeeded \u2014 "
        "even if exact wording differs. This is the goal of lip reading.",
        ("4 word-accuracy signals share 60%: diminishing returns",
         {"bold": True, "color": TEAL}),
        "WER, WWER, Phonetic, and NEA all measure overlapping aspects of "
        "'did the model get the right words?' Equal 15% weights prevent "
        "any single word-level metric from dominating.",
        ("Length ratio at 15%: a safety net, not a quality signal",
         {"bold": True}),
        "Catches hallucination and truncation \u2014 the two catastrophic "
        "failure modes that other signals can miss.",
        ("Validated: r=0.93 with expert judgment, \u03ba=0.77",
         {"color": GOLD}),
    ], rx, CT + Inches(0.55), rw, Inches(4.5), size=Pt(13))

    add_text(slide,
        "Validated against 1,497 segments: the resulting IS correlates at "
        "r=0.93 with an independent expert heuristic and \u03ba=0.77 with "
        "human-like judgment.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Weight rationale. The 6 IS signals collapse into 3 independent "
        "dimensions: word accuracy (60%, 4 signals at 15% each), meaning "
        "preservation (28%, semantic at 25%), and output sanity (9%, length "
        "at 15%). Semantic gets double weight because meaning is the ultimate "
        "goal. The 4 word-accuracy signals overlap heavily (r>0.79), so equal "
        "15% weights avoid over-counting. Validated: r=0.93 with expert "
        "heuristic, kappa=0.77.",
        [[lt] + dim_shapes, [rt], [rb]], click_reveal=True)


def slide_is_calc_examples(prs):
    """Two concrete IS calculation examples — side-by-side cards."""
    slide = new_slide(prs)
    add_title(slide, "IS in Action: Two Real Segments")
    add_accent_line(slide)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    card_h = Inches(4.6)

    def _draw_calc_card(slide, x, label, is_val, color, ref, hyp, lines, summary):
        """Draw one calculation card at position x. Returns list of all shapes."""
        shapes = []
        r = add_rect(slide, x, CT, col_w, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(3), corner_radius=True)
        shapes.append(r)

        # Header bar with colored background (reduced height)
        shapes.append(add_rect(slide, x + Inches(0.1), CT + Inches(0.1),
                 col_w - Inches(0.2), Inches(0.4), fill_color=color,
                 corner_radius=True))
        shapes.append(add_text(slide, f"{label} \u2014 IS = {is_val}",
                 x + Inches(0.1), CT + Inches(0.1),
                 col_w - Inches(0.2), Inches(0.4),
                 size=Pt(16), color=BG, bold=True, align=PP_ALIGN.CENTER))

        # Ref / Hyp (increased font size)
        shapes.append(add_rich_text(slide, [
            [("Ref: ", {"size": Pt(14), "color": LGRAY, "bold": True}),
             (f"\u201c{ref}\u201d", {"size": Pt(14), "color": WHITE})],
            [("Hyp: ", {"size": Pt(14), "color": LGRAY, "bold": True}),
             (f"\u201c{hyp}\u201d", {"size": Pt(14), "color": WHITE})],
        ], x + Inches(0.25), CT + Inches(0.55), col_w - Inches(0.5), Inches(0.65)))

        # Calculation rows (increased font size)
        cy = CT + Inches(1.35)
        for name, val, mult, result, clr in lines:
            shapes.append(add_text(slide, name, x + Inches(0.3), cy, Inches(1.8), Inches(0.32),
                     size=Pt(14), color=LGRAY))
            shapes.append(add_text(slide, val, x + Inches(2.2), cy, Inches(0.7), Inches(0.32),
                     size=Pt(14), color=clr, bold=True))
            shapes.append(add_text(slide, mult, x + Inches(2.9), cy, Inches(0.8), Inches(0.32),
                     size=Pt(14), color=LGRAY))
            shapes.append(add_text(slide, result, x + Inches(3.7), cy, Inches(0.9), Inches(0.32),
                     size=Pt(14), color=WHITE, bold=True))
            cy += Inches(0.35)

        # Summary
        shapes.append(add_text(slide, summary,
                 x + Inches(0.3), cy + Inches(0.2), col_w - Inches(0.6), Inches(0.4),
                 size=Pt(15), color=color, bold=True))
        return shapes

    # --- Left: Good segment ---
    good_lines = [
        ("Semantic Sim", "0.82", "\u00d7 0.25", "= 0.205", GREEN),
        ("Phonetic Sim", "0.89", "\u00d7 0.15", "= 0.134", GREEN),
        ("Inverse WER", "0.71", "\u00d7 0.15", "= 0.107", TEAL),
        ("Inverse WWER", "0.76", "\u00d7 0.15", "= 0.114", TEAL),
        ("NEA F1", "1.00", "\u00d7 0.15", "= 0.150", TEAL),
        ("Length Ratio", "0.89", "\u00d7 0.15", "= 0.134", TEAL),
    ]
    r1 = _draw_calc_card(slide, MX,
        "Good Segment", "4.2", GREEN,
        "allow you to work with the team in a more",
        "allow you to work with a team and more",
        good_lines, "Sum \u00d7 5 = 4.22 \u2192 IS 4.2 (Good)")

    # --- Right: Bad segment ---
    bad_lines = [
        ("Semantic Sim", "0.04", "\u00d7 0.25", "= 0.010", CORAL),
        ("Phonetic Sim", "0.12", "\u00d7 0.15", "= 0.018", CORAL),
        ("Inverse WER", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Inverse WWER", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("NEA F1", "0.00", "\u00d7 0.15", "= 0.000", CORAL),
        ("Length Ratio", "1.00", "\u00d7 0.15", "= 0.150", LGRAY),
    ]
    r2 = _draw_calc_card(slide, MX + col_w + gap,
        "Bad Segment", "0.9", CORAL,
        "carry strap",
        "holocaust denier explanation of the final act",
        bad_lines, "Sum \u00d7 5 = 0.89 \u2192 IS 0.9 (Failed)")

    _finish(slide, 0,
        "Two IS calculation examples. Left: good segment (IS 4.2) with high "
        "scores across all signals. Right: hallucination (IS 0.9) where only "
        "length ratio is non-zero — the output is a completely different topic. "
        "The formula is IS = (sum of weighted scores) x 5, mapping to 0-5 scale.",
        [r1, r2], click_reveal=True)


def slide_is_radar(prs):
    """Radar chart showing captured vs failed IS profiles -- large centered."""
    slide = new_slide(prs)
    add_title(slide, "IS Radar: Success vs Failure Profile")
    add_accent_line(slide)
    sub = add_text(slide,
        "Captured segments (green) are strong across all 6 signals. "
        "Failed segments (red) collapse on meaning and entities.",
        MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)
    img_top = CT + Inches(0.45)
    img_h = SL_H - img_top - Inches(0.55)
    img_w = Inches(8.5)
    img_l = (SL_W - img_w) / 2
    # Prefer dual radar (LRS3 vs YouTube) if available
    radar_key = "P6b_radar_dual" if IMG.get("P6b_radar_dual", Path("x")).exists() \
                else "P6_is_radar"
    img = add_image(slide, radar_key, img_l, img_top,
                    width=img_w, height=img_h)
    ann_w = Inches(2.5)
    if radar_key == "P6b_radar_dual":
        add_text(slide, "\u25cf LRS3 Benchmark (WER 25.4%)", MX, SL_H - Inches(0.55),
                 Inches(3.5), Inches(0.3), size=Pt(12), color=GREEN, bold=True)
        add_text(slide, "\u25cf Real-World YouTube (WER 64.1%)",
                 MX + CW - Inches(3.5), SL_H - Inches(0.55),
                 Inches(3.5), Inches(0.3), size=Pt(12), color=CORAL, bold=True,
                 align=PP_ALIGN.RIGHT)
    else:
        add_text(slide, "\u25cf Captured (IS \u2265 3.0)", MX, SL_H - Inches(0.55),
                 ann_w, Inches(0.3), size=Pt(12), color=GREEN, bold=True)
        add_text(slide, "\u25cf Failed (IS < 3.0)",
                 MX + CW - ann_w, SL_H - Inches(0.55),
                 ann_w, Inches(0.3), size=Pt(12), color=CORAL, bold=True,
                 align=PP_ALIGN.RIGHT)
    _finish(slide, 0,
        "Radar chart comparing mean component values for IS >= 3.0 "
        "(green) vs IS < 3.0 (red). Captured segments are strong across "
        "all 6 signals. Failed segments collapse on meaning and entity "
        "preservation while maintaining only partial length ratio. "
        "The biggest gaps between green and red are on Semantic and NEA "
        "axes, confirming these as the primary differentiators.",
        [[img]])


def slide_is_wer_scatter(prs):
    """IS vs WER scatter showing 'the gap'."""
    build_split(prs, 0,
        "The Gap: Where WER Lies Most",
        "P7_is_wer_scatter",
        notes="Scatter plot of WER vs IS for all 1,497 segments. The green "
              "highlighted region shows 147 segments where WER > 40% but IS >= 3.0.",
        big_num="147",
        num_color=GREEN,
        num_label="segments in the gap: high WER, useful IS",
        bullets=[
            ("WER > 40% but IS \u2265 3.0 \u2014 useful output that WER discards", {"bold": True}),
            "Synonyms, tense changes, and filler words inflate WER",
            "Semantic meaning is preserved despite word-level errors",
            ("Validates IS as a more honest metric for VSP", {"color": TEAL}),
        ])


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ═══════════════════════════════════════════════════════════════════════

def slide_01(prs):
    slide = new_slide(prs)

    # Logo top-right
    logo = add_image(slide, "logo", SL_W - MX - Inches(0.9),
                     Inches(0.3), height=Inches(0.9))

    # Title
    t1 = add_text(slide, "Argos VSP", MX, Inches(2.0), CW, Inches(1.0),
                  size=Pt(48), color=WHITE, bold=True, align=PP_ALIGN.LEFT)
    t2 = add_text(slide, "Research Findings and Production Roadmap",
                  MX, Inches(3.0), CW, Inches(0.7),
                  size=Pt(28), color=TEAL, bold=False, align=PP_ALIGN.LEFT)
    t3 = add_text(slide, "Visual Speech Processing — Project Review",
                  MX, Inches(3.8), CW, Inches(0.5),
                  size=Pt(18), color=LGRAY, italic=True, align=PP_ALIGN.LEFT)

    # Accent line
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  MX, Inches(4.5), Inches(3), Pt(2))
    shp.fill.solid()
    shp.fill.fore_color.rgb = TEAL
    shp.line.fill.background()

    # Date & author
    add_text(slide, "February 2026", MX, Inches(5.2), Inches(4), Inches(0.4),
             size=Pt(16), color=LGRAY)
    add_text(slide, "Yoad Oxman  •  The Orchard", MX, Inches(5.6),
             Inches(5), Inches(0.4), size=Pt(14), color=MGRAY)

    add_slide_num(slide, 1)
    add_fade_transition(slide)
    add_animations(slide, [[t1], [t2, t3]])
    set_notes(slide,
        "Welcome. This presentation covers 3 months of research and engineering "
        "on a visual speech processing system — reading lips from video, no audio. "
        "We'll cover what we found, what we built, and where we go next.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 2 — WHAT IS VSP? (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_02(prs):
    slide = new_slide(prs)
    add_title(slide, "What is Visual Speech Processing?")
    add_accent_line(slide)

    add_text(slide, "A system that reads lips from video — no audio needed.",
             MX, Inches(1.55), CW, Inches(0.4),
             size=Pt(20), color=LGRAY, align=PP_ALIGN.CENTER)

    # Embedded video — click to play directly in PowerPoint
    vid_w = Inches(8.5)
    vid_h = Inches(4.3)
    vid_x = (SL_W - vid_w) // 2
    add_video(slide, "perfect", vid_x, Inches(2.1), vid_w, vid_h)

    add_text(slide, "33 words about health insurance — WER 0%, IS 5.0. "
             "Click the video to play.",
             MX, Inches(6.6), CW, Inches(0.4),
             size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 2,
        "PLAY VIDEO: IEa7qEkMvfQ_3__c5447488_with_hyp.mp4 — 33 words about "
        "health insurance, WER 0%. Play the video first, then explain: this is "
        "the best case. The system perfectly reads 33 consecutive words from lip "
        "movement alone. Now let's see how it works.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 3 — MODEL ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_03(prs):
    slide = new_slide(prs)
    add_title(slide, "How It Works: Three Components")
    add_accent_line(slide)

    # Model architecture diagram (AV-HuBERT → Projection → LLaMA-2-7B flow)
    img = add_image(slide, "model_arch", MX, CT, width=CW, height=Inches(3.6))

    # Three component blocks
    bw = Inches(3.5)
    bh = Inches(0.7)
    by = Inches(5.4)
    gap = Inches(0.4)
    total = 3 * bw + 2 * gap
    bx = (SL_W - total) / 2

    labels = [
        ("AV-HuBERT", "Visual Encoder, frozen, 1024-dim", TEAL),
        ("Linear Projection", "1024 → 4096", LGRAY),
        ("LLaMA-2-7B", "4-bit QLoRA, r=16", CORAL),
    ]
    blocks = []
    for i, (name, desc, border) in enumerate(labels):
        x = bx + i * (bw + gap)
        r = add_rect(slide, x, by, bw, bh, fill_color=NAVY2, border_color=border,
                     border_width=Pt(2), corner_radius=True)
        tb = add_text(slide, f"{name}\n{desc}", x + Inches(0.1), by + Inches(0.05),
                      bw - Inches(0.2), bh - Inches(0.1),
                      size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)
        blocks.append(r)

    # Arrow indicators between blocks
    for i in range(2):
        ax = bx + (i + 1) * bw + i * gap + Inches(0.05)
        add_text(slide, "→", ax, by + Inches(0.1), gap - Inches(0.1), Inches(0.5),
                 size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER)

    # Bottom note
    add_text(slide,
             "Only 12.6M trainable params (0.19%). LLM is swappable — "
             "Llama 3.1 8B is a drop-in replacement (same 4096 hidden size).",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True)

    _finish(slide, 3,
        "Three components. Visual encoder (AV-HuBERT) is frozen — pre-trained "
        "on LRS3 lip-reading data. It outputs 1024-dim features per frame. A "
        "linear projection maps to 4096-dim (LLM input space). Then LLaMA-2-7B "
        "generates text. Key: only the LoRA adapters and projection layer are "
        "trained — 12.6M of 7B parameters. And the LLM is swappable: Llama 3.1 "
        "8B has the same hidden dimension, making it a trivial 1-2 hour swap.",
        [[img], blocks], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════

def slide_04(prs):
    build_split(prs, 4, "The Benchmark: Paper vs Reality", "P2_paper",
        big_num="25.4%", num_color=TEAL,
        num_label="WER on LRS3 (TED Talks)",
        bullets=[
            ("LRS3: 1,000+ hours of TED talks", {"bold": True}),
            "Controlled studio lighting, frontal face, professional speakers",
            "High-quality audio alignment, clean transcripts",
            ("Our dataset: 1,497 YouTube segments", {"color": CORAL}),
            "Uncontrolled conditions, diverse topics, multiple accents",
            ("Real-world YouTube: 64.1% WER \u2014 2.5\u00d7 worse",
             {"color": CORAL, "bold": True}),
        ],
        bottom_text="Two questions: How does this hold on real-world video? "
                    "And is WER even the right metric?",
        notes="The paper claims 25.4% Word Error Rate on LRS3 — a curated dataset "
              "of 1,000+ hours of TED talks with controlled studio lighting, "
              "frontal faces, professional speakers, and high-quality audio "
              "alignment. Our dataset: 1,497 segments from diverse YouTube "
              "videos — uncontrolled conditions, multiple accents, varied topics. "
              "Result: 64.1% WER, 2.5x worse. And more importantly — is WER "
              "even the right way to measure this?")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 5 — THE REALITY GAP
# ═══════════════════════════════════════════════════════════════════════

def slide_05(prs):
    build_split(prs, 5, "The Reality Gap", "P1_quality",
        big_num="64.1%", num_color=CORAL,
        num_label="Mean WER across 1,497 real-world segments",
        bullets=[
            ("11.4% Usable (<30%)", {"bullet": "●", "bullet_color": GREEN}),
            ("17.4% Marginal (30-50%)", {"bullet": "●", "bullet_color": YELLOW}),
            ("17.8% Poor (50-75%)", {"bullet": "●", "bullet_color": ORANGE}),
            ("32.8% Unusable (75-100%)", {"bullet": "●", "bullet_color": RED}),
            ("20.6% Hallucinated (>100%)", {"bullet": "●", "bullet_color": DRED}),
        ],
        bottom_text="But WER overstates failure — see next slide.",
        notes="1,497 diverse YouTube segments. 64.1% mean WER — 2.5x worse than "
              "the paper's 25.4%. Only 11.4% usable by WER standards. And 20.6% "
              "are hallucinations — fluent text that's completely fabricated. This "
              "is the most dangerous failure mode. But WER is misleading — it "
              "treats all errors equally.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 6 — WER IS BLIND
# ═══════════════════════════════════════════════════════════════════════

def slide_06(prs):
    slide = new_slide(prs)
    add_title(slide, 'WER Is Blind to Meaning')
    add_accent_line(slide)

    bw = Inches(5.5)
    bh = Inches(3.8)
    by = CT + Inches(0.1)
    gap = Inches(1.13)

    # Left box — good
    r1 = add_rect(slide, MX, by, bw, bh, fill_color=NAVY2,
                  border_color=GREEN, border_width=Pt(2.5), corner_radius=True)
    add_text(slide, "WER 29%  •  IS 4.3 — Fully Intelligible",
             MX + Inches(0.3), by + Inches(0.2), bw - Inches(0.6), Inches(0.4),
             size=Pt(14), color=GREEN, bold=True)
    add_text(slide, 'Ref: "allow you to work with the team in a more"\n'
                    'Hyp: "allow you to work with a team and more"',
             MX + Inches(0.3), by + Inches(0.8), bw - Inches(0.6), Inches(2.5),
             size=Pt(15), color=WHITE)

    # Right box — bad
    rx = MX + bw + gap
    r2 = add_rect(slide, rx, by, bw, bh, fill_color=NAVY2,
                  border_color=RED, border_width=Pt(2.5), corner_radius=True)
    add_text(slide, "WER 58%  •  IS 2.7 — Near-Miss",
             rx + Inches(0.3), by + Inches(0.2), bw - Inches(0.6), Inches(0.4),
             size=Pt(14), color=RED, bold=True)
    add_text(slide, 'Ref: "1 billion cfus of probiotics"\n'
                    'Hyp: "1 million cfus of permafrost"',
             rx + Inches(0.3), by + Inches(0.8), bw - Inches(0.6), Inches(2.5),
             size=Pt(15), color=WHITE)

    # Bottom
    add_text(slide,
             "WER says equal. Meaning says opposite. So we built a metric to "
             "capture this.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 6,
        "Same low WER on the left, high WER on the right — but the real "
        "difference is meaning. Left: minor grammatical change, meaning "
        "fully preserved at WER 29%. Right: 'probiotics' becomes 'permafrost' — "
        "phonetically similar but completely wrong product. Structure intact, "
        "key terms destroyed. This motivated our Intelligibility Score.",
        None)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 7 — THE INTELLIGIBILITY SCORE
# ═══════════════════════════════════════════════════════════════════════

def slide_07(prs):
    slide = new_slide(prs)
    add_title(slide, "Intelligibility Score: 39.9% Properly Captured")
    add_accent_line(slide)

    # 6 signal blocks
    signals = [
        ("Semantic\nSim", "25%", TEAL),
        ("Phonetic\nSim", "15%", TEAL),
        ("Inv.\nWER", "15%", TEAL),
        ("Inv.\nWWER", "15%", TEAL),
        ("NEA\nF1", "15%", CORAL),
        ("Length\nRatio", "15%", LGRAY),
    ]
    bw = Inches(1.7)
    bh = Inches(1.1)
    gap = Inches(0.22)
    total = 6 * bw + 5 * gap
    bx = (SL_W - total) / 2
    by = CT

    signal_shapes = []
    for i, (label, weight, color) in enumerate(signals):
        x = bx + i * (bw + gap)
        r = add_rect(slide, x, by, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, f"{label}\n({weight})", x + Inches(0.1), by + Inches(0.1),
                 bw - Inches(0.2), bh - Inches(0.2),
                 size=Pt(11), color=WHITE, align=PP_ALIGN.CENTER)
        signal_shapes.append(r)

    # Key callout
    callout = add_text(slide,
        "IS ≥ 3.0 = Properly Captured: 39.9% — 3.5× more than WER's 11.4%\n"
        "Phonetic similarity: 41.5% mean, r=0.943 with IS (strongest single signal)",
        MX, by + bh + Inches(0.2), CW, Inches(0.55),
        size=Pt(14), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # 5 tier bars
    tiers = [
        ("18.4% Excellent", 18.4, GREEN),
        ("21.4% Good", 21.4, TEAL),
        ("21.7% Fair", 21.7, YELLOW),
        ("22.4% Poor", 22.4, ORANGE),
        ("16.0% Failed", 16.0, RED),
    ]
    bar_y = by + bh + Inches(1.05)
    bar_h = Inches(0.38)
    bar_gap = Inches(0.12)
    max_w = Inches(8.0)
    label_w = Inches(3.0)
    bar_x = MX + label_w + Inches(0.2)

    tier_shapes = []
    for i, (label, val, color) in enumerate(tiers):
        y = bar_y + i * (bar_h + bar_gap)
        add_text(slide, label, MX, y, label_w, bar_h,
                 size=Pt(13), color=WHITE, align=PP_ALIGN.RIGHT)
        w = int(max_w * val / 25.0)  # scale to max
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color)
        tier_shapes.append(bar)

    _finish(slide, 7,
        "The Intelligibility Score combines 6 signals into a 0-5 composite. "
        "Key insight: 39.9% of segments are properly captured (IS >= 3.0) — "
        "3.5x more than WER's 11.4% 'usable.' WER dramatically overstates "
        "failure. Methodology: LLM-distilled evaluation — the "
        "rubric, selected signals and weights, defined tier boundaries. "
        "Validated across 16 decode configs: LLM heuristic judge r=0.925 "
        "with IS, 88.6% agreement.",
        None)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 8 — FAILURE MODE TAXONOMY (BAR CHART)
# ═══════════════════════════════════════════════════════════════════════

def slide_08(prs):
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy")
    add_accent_line(slide)

    add_text(slide,
        "900 segments failed (IS < 3.0) \u2014 how often does each mode occur?",
        MX, CT, CW, Inches(0.35), size=Pt(14), color=LGRAY, italic=True)

    modes = [
        ("Wrong Topic", 31.6, 284, GOLD),
        ("Accumulated Errors", 24.4, 220, LGRAY),
        ("Right Topic, Wrong Details", 22.7, 204, TEAL),
        ("Hallucination", 12.3, 111, CORAL),
        ("Signal Loss", 9.0, 81, MGRAY),
    ]

    bar_h = Inches(0.65)
    bar_gap = Inches(0.2)
    label_w = Inches(3.5)
    max_bar_w = Inches(6.0)
    bar_x = MX + label_w + Inches(0.2)
    start_y = CT + Inches(0.55)

    bar_shapes = []
    for i, (name, pct, count, color) in enumerate(modes):
        y = start_y + i * (bar_h + bar_gap)
        # Label
        add_text(slide, name, MX, y, label_w, bar_h,
                 size=Pt(16), color=WHITE, bold=True, align=PP_ALIGN.RIGHT)
        # Bar
        w = max(Inches(0.2), int(max_bar_w * pct / 32.0))
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color,
                       corner_radius=True)
        bar_shapes.append(bar)
        # Value label
        add_text(slide, f"{pct}% ({count})",
                 bar_x + w + Inches(0.15), y, Inches(1.8), bar_h,
                 size=Pt(14), color=LGRAY)

    add_text(slide,
             "Failures are diverse — no single fix. Each roadmap phase "
             "targets specific modes.",
             MX, Inches(6.4), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    _finish(slide, 8,
        "900 failed segments classified into 5 failure categories. Wrong Topic "
        "is the largest (31.6%), combining topic drift and phonetic confusion. "
        "Hallucination (12.3%) is the most dangerous: fluent, confident, "
        "completely fabricated. Right Topic Wrong Details (22.7%) loses names and "
        "numbers. This taxonomy maps directly to our roadmap.",
        None)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — DEFINITIONS & CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_1a(prs):
    """Failure mode taxonomy: 5 academically-grounded categories as animated cards."""
    slide = new_slide(prs)
    add_title(slide, "Failure Mode Taxonomy: 5 Categories")
    add_accent_line(slide)

    add_text(slide,
        "900 failed segments (IS < 3.0) classified into 5 mutually exclusive "
        "categories \u2014 each segment gets exactly one label, checked 1\u21925.",
        MX, CT, CW, Inches(0.28), size=Pt(13), color=LGRAY, italic=True)

    add_text(slide,
        "Grounded in ASR error taxonomy (Fosler-Lussier 2004) and "
        "LLM hallucination analysis (ACL 2025)",
        MX, CT + Inches(0.28), CW, Inches(0.22),
        size=Pt(10), color=MGRAY, italic=True)

    modes = [
        ("1. Signal Loss", "9.0%", "81 segments", LGRAY,
         "Nothing came out",
         "Empty output OR length ratio < 0.3",
         "Ref: \u201cthe thirteenth amendment\u201d \u2192 Hyp: \u201c\u201d"),
        ("2. Hallucination", "12.3%", "111 segments", CORAL,
         "Model invented fake text",
         "WER \u2265 100% (output longer than reference)",
         "Ref: \u201ccarry strap\u201d \u2192 Hyp: \u201cholocaust denier explanation of the final act\u201d"),
        ("3. Wrong Topic", "31.6%", "284 segments", GOLD,
         "Mouth shapes decoded to wrong domain",
         "Semantic < 0.2 (phonetic-matched or not)",
         "Ref: \u201cweight loss and diet\u201d \u2192 Hyp: \u201cwanted to be a princess\u201d"),
        ("4. Right Topic, Wrong Details", "22.7%", "204 segments", TEAL,
         "Roughly right but names/content words lost",
         "NEA F1 < 20% OR key content words substituted (Semantic \u2265 0.2)",
         "Ref: \u201c13th amendment is going\u201d \u2192 Hyp: \u201c13th may mean something to him\u201d"),
        ("5. Accumulated Errors", "24.4%", "220 segments", LGRAY,
         "Many small errors compound",
         "IS < 3.0 and doesn\u2019t match categories 1\u20134",
         "Many words slightly wrong throughout, meaning erodes"),
    ]

    card_h = Inches(0.88)
    gap = Inches(0.08)
    y0 = CT + Inches(0.55)
    name_w = Inches(3.5)
    rule_w = CW - name_w - Inches(0.1)

    anim_groups = []
    for i, (name, pct, count, color, desc, rule, example) in enumerate(modes):
        y = y0 + i * (card_h + gap)

        # Card background
        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)

        # Left: category name + percentage
        add_text(slide, f"{name}  ({pct})",
                 MX + Inches(0.2), y + Inches(0.05),
                 name_w - Inches(0.3), Inches(0.3),
                 size=Pt(15), color=color, bold=True)

        # Left: one-line description + count
        add_text(slide, f"{desc}  \u2014  {count}",
                 MX + Inches(0.2), y + Inches(0.38),
                 name_w - Inches(0.3), Inches(0.45),
                 size=Pt(11), color=LGRAY)

        # Right: detection rule
        add_text(slide, f"Rule: {rule}",
                 MX + name_w, y + Inches(0.06),
                 rule_w - Inches(0.15), Inches(0.35),
                 size=Pt(12), color=WHITE)

        # Right: example
        add_text(slide, f"\u25b8 {example}",
                 MX + name_w, y + Inches(0.45),
                 rule_w - Inches(0.15), Inches(0.35),
                 size=Pt(11), color=LGRAY, italic=True)

        anim_groups.append([r])

    # Priority order footer
    add_text(slide,
        "Priority: Signal Loss \u2192 Hallucination \u2192 Wrong Topic \u2192 "
        "Right Topic Wrong Details \u2192 Accumulated Errors",
        MX, Inches(6.55), CW, Inches(0.35),
        size=Pt(11), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Five-category failure taxonomy grounded in ASR error research "
        "(Fosler-Lussier 2004) and LLM hallucination analysis (ACL 2025). "
        "Key insight: Wrong Topic is the LARGEST category at 31.6% — it merges "
        "the old Topic Drift and Phonetic Wrong Topic categories because the fix "
        "is the same (stronger LLM, more training data). Signal Loss and "
        "Accumulated Errors are the bookends: one produces nothing, the other "
        "produces something but death-by-a-thousand-cuts erodes meaning. "
        "Each segment gets exactly one label, checked in priority order 1 through 5.",
        anim_groups, click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — REAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_2(prs):
    """Three concrete failure mode examples for the hardest-to-distinguish categories."""
    slide = new_slide(prs)
    add_title(slide, "Failure Modes: Real Examples")
    add_accent_line(slide)

    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(4.9)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.05)

    examples = [
        {
            "title": "Hallucination",
            "pct": "12.3%",
            "color": CORAL,
            "ref": "carry strap",
            "hyp": "holocaust denier explanation\nof the final act",
            "wer": "100%", "is_score": "0.1",
            "why_label": "Why this category?",
            "why": "The model generated 8 words from\n"
                   "a 2-word input. The LLM\u2019s language\n"
                   "model \u2018ran away\u2019 \u2014 output is fluent\n"
                   "English but completely fabricated.\n"
                   "Distinguishing feature: output is\n"
                   "LONGER than reference (WER \u2265 100%).",
        },
        {
            "title": "Wrong Topic",
            "pct": "31.6%",
            "color": GOLD,
            "ref": "i\u2019ve made lots of videos\nabout weight loss and diet",
            "hyp": "when i was a little girl i\nalways wanted to be a princess",
            "wer": "97%", "is_score": "0.38",
            "why_label": "Why this category?",
            "why": "Output is similar LENGTH to\n"
                   "reference (not hallucination) but\n"
                   "about a completely different subject.\n"
                   "The visual encoder extracted mouth\n"
                   "shapes that the LLM mapped to a\n"
                   "wrong but coherent domain.",
        },
        {
            "title": "Right Topic, Wrong Details",
            "pct": "22.7%",
            "color": TEAL,
            "ref": "about the 13th amendment\nthe 13th amendment is going",
            "hyp": "13th may mean something to\nhim because it can help him",
            "wer": "81%", "is_score": "2.14",
            "why_label": "Why this category?",
            "why": "The word \u201c13th\u201d survived but\n"
                   "\u201camendment\u201d was lost. A viewer\n"
                   "might guess the topic (law) but\n"
                   "critical entity information is\n"
                   "irrecoverable. Key distinction:\n"
                   "Semantic \u2265 0.2 (topic is correct).",
        },
    ]

    anim_groups = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)

        # Title + percentage
        add_text(slide, f'{ex["title"]}  ({ex["pct"]})',
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.35),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.5),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.7), cw_card - Inches(0.3), Inches(0.6),
                 size=Pt(10), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.35),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.55), cw_card - Inches(0.3), Inches(0.6),
                 size=Pt(10), color=ex["color"], italic=True)

        # Metrics badge
        add_text(slide, f'WER {ex["wer"]}  |  IS {ex["is_score"]}',
                 x + Inches(0.15), cy + Inches(2.25), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(11), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        # Why explanation
        add_text(slide, ex["why_label"],
                 x + Inches(0.15), cy + Inches(2.7),
                 cw_card - Inches(0.3), Inches(0.22), size=Pt(9), color=TEAL, bold=True)
        add_text(slide, ex["why"],
                 x + Inches(0.15), cy + Inches(2.9), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(10), color=LGRAY)

        anim_groups.append([r])

    _finish(slide, 0,
        "Three real examples for the three most confusing categories. "
        "Hallucination vs Wrong Topic: hallucination generates MORE words than "
        "the reference (WER >= 100%), while Wrong Topic substitutes at similar "
        "length. Wrong Topic vs Right Topic Wrong Details: semantic similarity "
        "threshold of 0.2 separates them — below 0.2 means completely different "
        "subject, above 0.2 means topic preserved but details lost. "
        "Right Topic Wrong Details is the 'frustrating near-miss' — you can tell "
        "what the speaker was ABOUT but not what they SAID.",
        anim_groups, click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# FAILURE MODE DEEP-DIVE — IMPACT & ROADMAP MAPPING
# ═══════════════════════════════════════════════════════════════════════

def slide_failure_deep_3(prs):
    """Failure mode impact and what fixes each of the 5 categories."""
    slide = new_slide(prs)
    add_title(slide, "Failure Modes: Impact & What Fixes Them")
    add_accent_line(slide)

    add_text(slide,
        "Each category maps to a specific remedy \u2014 "
        "no single fix addresses all failure types.",
        MX, CT, CW, Inches(0.3),
        size=Pt(13), color=LGRAY, italic=True)

    headers = ["Category", "%", "Severity", "What Fixes It"]
    rows = [
        ["Signal Loss", "9.0%", "Low \u2014 obvious",
         "Quality filtering, longer segments"],
        ["Hallucination", "12.3%", "Moderate \u2014 easy to\nidentify and ignore",
         "Anti-hallucination prompts,\nconfidence gating, GER*"],
        ["Wrong Topic", "31.6%", "High \u2014 wrong\ndomain entirely",
         "Stronger LLM, topic-aware\nprompting, more training data"],
        ["Right Topic,\nWrong Details", "22.7%", "Very High \u2014 clients\nwill distrust model",
         "Entity injection, domain\nadaptation, fine-tuning"],
        ["Accumulated\nErrors", "24.4%", "Medium \u2014 gradual\nmeaning erosion",
         "General model improvement,\nN-best aggregation"],
    ]

    row_colors = {
        0: {0: LGRAY, 2: MGRAY},
        1: {0: CORAL, 2: ORANGE},
        2: {0: GOLD, 2: RED},
        3: {0: TEAL, 2: DRED},
        4: {0: LGRAY, 2: YELLOW},
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT + Inches(0.45), CW,
                    row_height=Inches(0.7),
                    col_widths=[Inches(2.0), Inches(1.0), Inches(3.5), Inches(5.63)],
                    text_size=Pt(12),
                    row_colors=row_colors)

    # GER footnote
    ger_note = add_text(slide,
        "*GER = Gross Error Rate \u2014 the fraction of outputs with catastrophic "
        "errors (WER > 100%). Filters out the worst hallucinations before "
        "they reach users.",
        MX, Inches(5.1), CW, Inches(0.35),
        size=Pt(11), color=MGRAY, italic=True)

    # Key insight callout
    callout_r = add_rect(slide, MX, Inches(5.5), CW, Inches(0.65), fill_color=NAVY2,
             border_color=TEAL, border_width=Pt(1), corner_radius=True)

    callout_t = add_text(slide,
        "Key insight: Wrong Topic (31.6%) is the largest failure mode and "
        "most likely to improve with a stronger LLM (Llama 3.1 8B). "
        "Right Topic Wrong Details (22.7%) is the most dangerous \u2014 clients "
        "will distrust the model, and confidence values for those words "
        "are likely always low. Over half of failures need better language modeling.",
        MX + Inches(0.2), Inches(5.55), CW - Inches(0.4), Inches(0.55),
        size=Pt(13), color=WHITE)

    severity_t = add_text(slide,
        "Hallucination: not that bad \u2014 relatively easy to identify and ignore "
        "but still painful. Right Topic Wrong Details: very high impact.",
        MX, Inches(6.25), CW, Inches(0.5),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Impact and fixes table for the 5-category taxonomy. Right Topic Wrong "
        "Details is the most dangerous because clients cannot trust the output \u2014 "
        "confidence values for those words are likely always low. Hallucination is "
        "relatively easy to identify and ignore but still painful. Wrong Topic is "
        "the LARGEST at 31.6% and the most amenable to improvement through LLM "
        "upgrade. GER = Gross Error Rate, the fraction of outputs with catastrophic "
        "errors. 54.3% of failures trace to the LLM backbone being too weak.",
        [[tbl], [ger_note, callout_r, callout_t, severity_t]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 9 — PERFORMANCE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════

def slide_09(prs):
    build_full_image(prs, 9, "How Results Vary Across Configurations", "boxplot",
        subtitle="Each box shows the WWER distribution for one of 13 decode configs. "
                 "Lower is better.",
        bottom_text="Most segments: 50\u201380% WER. ~11% always good, ~16% always bad "
                    "\u2014 regardless of parameters.",
        notes="This boxplot shows WWER distribution across all 13 decode "
              "experiments. The box is consistently in the 50-80% range. "
              "About 11% of segments are always good regardless of parameters, "
              "and about 16% are always bad. The bottleneck is the visual "
              "encoder, not decode strategy.")


def slide_metric_transition(prs):
    """The three numbers: 64.1% -> 39.9% -> 50.9%."""
    slide = new_slide(prs)
    add_title(slide, "Three Numbers That Tell the Real Story")
    add_accent_line(slide)

    card_w = CW - Inches(2.0)
    card_h = Inches(1.25)
    card_x = MX + Inches(1.0)
    arrow_h = Inches(0.4)

    c1_y = CT + Inches(0.2)
    g1 = []
    g1.append(add_rect(slide, card_x, c1_y, card_w, card_h,
                        fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                        corner_radius=True))
    g1.append(add_text(slide, "64.1%", card_x + Inches(0.3), c1_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=CORAL, bold=True))
    g1.append(add_text(slide, "What WER reports\n\"Two-thirds of words are wrong\"",
                        card_x + Inches(3.0), c1_y + Inches(0.15),
                        card_w - Inches(3.3), card_h - Inches(0.3),
                        size=Pt(15), color=LGRAY))
    # Strikethrough line
    g1.append(add_rect(slide, card_x + Inches(0.4), c1_y + card_h / 2 - Pt(1.5),
                        Inches(2.3), Pt(3), fill_color=CORAL))

    a1_y = c1_y + card_h + Inches(0.05)
    g1_arrow = []
    g1_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a1_y, Inches(0.6), arrow_h,
                              size=Pt(20), color=TEAL, align=PP_ALIGN.CENTER))

    c2_y = a1_y + arrow_h
    g2 = []
    g2.append(add_rect(slide, card_x, c2_y, card_w, card_h,
                        fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                        corner_radius=True))
    g2.append(add_text(slide, "39.9%", card_x + Inches(0.3), c2_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=TEAL, bold=True))
    g2.append(add_text(slide,
        "What IS reveals: 597 of 1,497 segments\ndeliver genuinely useful output",
        card_x + Inches(3.0), c2_y + Inches(0.15),
        card_w - Inches(3.3), card_h - Inches(0.3),
        size=Pt(15), color=WHITE))

    a2_y = c2_y + card_h + Inches(0.05)
    g2_arrow = []
    g2_arrow.append(add_text(slide, "\u25bc", card_x + card_w / 2 - Inches(0.3),
                              a2_y, Inches(0.6), arrow_h,
                              size=Pt(20), color=GREEN, align=PP_ALIGN.CENTER))

    c3_y = a2_y + arrow_h
    g3 = []
    g3.append(add_rect(slide, card_x, c3_y, card_w, card_h,
                        fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                        corner_radius=True))
    g3.append(add_text(slide, "50.9%", card_x + Inches(0.3), c3_y + Inches(0.1),
                        Inches(2.5), card_h - Inches(0.2),
                        size=Pt(48), color=GREEN, bold=True))
    g3.append(add_text(slide,
        "+ Salvage recovery: 165 additional segments\n1 in 2 segments delivers useful output",
        card_x + Inches(3.0), c3_y + Inches(0.15),
        card_w - Inches(3.3), card_h - Inches(0.3),
        size=Pt(15), color=WHITE))

    _finish(slide, 0,
        "The three numbers: WER 64.1% (misleading), IS captured 39.9% (real), "
        "with salvage 50.9% (the full picture).",
        [g1, g1_arrow + g2, g2_arrow + g3], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

def slide_10(prs):
    build_two_col(prs, 10, "Three Root Causes \u2014 Why 64.1% WER?",
        "Root Causes", [
            ("1. Domain Mismatch", {"bold": True, "color": TEAL}),
            "Model trained on TED talks (LRS3); real-world: DIY, cooking, sports",
            ("2. Short Segments Fail", {"bold": True, "color": TEAL}),
            "Under 10 words: only 32% captured vs 49% for 20+ words",
            ("3. Hallucination (20.5%)", {"bold": True, "color": TEAL}),
            "LLM prior overwhelms weak visual signal \u2014 fluent but fabricated",
        ],
        "By the Numbers", [
            ("Business/Finance: IS 3.08, 57% captured", {"color": GREEN}),
            ("DIY/Home: IS 2.13, 30% captured \u2014 27pp gap", {"color": CORAL}),
            "Short (5\u201310 words): 74% WER, 32% captured",
            "Long (20+ words): 55% WER, 49% captured \u2014 17pp gap",
            ("28.2% of failures = drift + hallucination", {"color": CORAL, "bold": True}),
        ],
        "Three root causes explain most failures: domain mismatch (model trained "
        "on TED, tested on YouTube), short segments lacking context, and "
        "hallucination where the LLM generates fluent but fabricated text.",
        left_color=CORAL, right_color=TEAL)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 11 — NAMED ENTITY ACCURACY
# ═══════════════════════════════════════════════════════════════════════

def slide_11(prs):
    slide = new_slide(prs)
    add_title(slide, "Named Entity Accuracy: The Largest Differentiator")
    add_accent_line(slide)

    # Left column with bullets, right column with scatter plot
    col_w = Inches(4.8)
    lt = add_text(slide, "What are named entities?", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Names (Admiral McRae), numbers (13th), places, "
        "organizations",
        "Either correct or destroyed \u2014 no partial credit",
        ("Captured: 74% NEA F1 vs Failed: 16%",
         {"bold": True, "color": CORAL}),
        "58pp gap \u2014 largest differentiator of any signal",
        "17.3% of IS variance (highest for 15%-weight signal)",
        'A viewer can guess a missing "the" but not a missing name',
    ], MX, CT + Inches(0.5), col_w, Inches(3.8), size=Pt(13))

    # Large image on right -- increased gap to prevent occlusion with point 4
    img_l = MX + col_w + Inches(0.5)
    img_w = CW - col_w - Inches(0.5)
    img = add_image(slide, "nea_scatter", img_l, CT, width=img_w)

    _finish(slide, 11,
        "PLOT EXPLANATION (NEA Recall vs WWER Per Segment):\n\n"
        "This scatter plot shows every segment as a dot, with WWER (Weighted "
        "Word Error Rate) on the x-axis and Named Entity Recall on the y-axis. "
        "Each dot color represents a different decode configuration (A: Baseline, "
        "C: LenPen=1, E: Sampling t=0.5, G: Greedy, J: LP1+t=0.5).\n\n"
        "KEY PATTERNS TO NOTE:\n"
        "1. Top-left cluster (low WWER, high NEA): These are the success cases \u2014 "
        "segments where both word accuracy and entity preservation are high. "
        "Most captured segments live here.\n\n"
        "2. Bottom row at NEA=0: A large cluster of segments with ZERO entity "
        "recall across ALL WWER values. This means many segments lose ALL named "
        "entities regardless of how many other words they get right. This is why "
        "NEA is the swing factor \u2014 entity destruction is binary.\n\n"
        "3. Right side (WWER > 100%): These are hallucinated segments where the "
        "model generates more wrong words than the reference contains. Even some "
        "of these have high NEA (top-right dots) \u2014 meaning the model hallucinated "
        "but still preserved some entity names.\n\n"
        "4. All configurations cluster together: different decode parameters "
        "don't change the fundamental NEA vs WWER relationship. The visual "
        "encoder determines entity preservation, not the decoder.\n\n"
        "TAKEAWAY: Named entities are binary \u2014 either preserved or destroyed. "
        "The dense cluster at NEA=0 across all WWER levels shows that entity "
        "loss is catastrophic and independent of general word accuracy. This is "
        "why NEA accounts for 17.3% of IS variance despite only 15% weight \u2014 "
        "it's the single most discriminating signal between captured and failed.",
        [[lt, lb], [img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 12 — 13 TUNING EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_12(prs):
    slide = new_slide(prs)
    add_title(slide, "Best Config vs Baseline: The Trade-off")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — What we found
    lt = add_text(slide, "What We Found", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Config J (lenpen=1.0, temp=0.5) was best overall", {"bold": True}),
        "Most configs cluster in a narrow IS range (2.45\u20132.60)",
        "Extreme parameters cause catastrophic failures",
        ("Lenpen=\u22120.5: 45% empty outputs", {"color": CORAL}),
        ("Lenpen=2.0: mean WER 540% (massive hallucination)", {"color": CORAL}),
    ], MX, CT + Inches(0.45), col_w, Inches(3.0))

    # Right column — Best Config (J)
    rx = MX + col_w + gap
    rt = add_text(slide, "Best Config (J) — 1,497 segments",
                  rx, CT, col_w, Inches(0.35),
                  size=Pt(17), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "IS: 2.60 vs 2.52 baseline (+0.08)",
        ("Captured: 622 vs 597 (+25 segments)", {"color": GREEN}),
        ("Empties: 0 vs 70 (eliminated)", {"color": GREEN}),
        ("Hallucinations: 348 vs 307 (+41 more)", {"color": CORAL}),
    ], rx, CT + Inches(0.45), col_w, Inches(2.0))

    # Right image — before/after tuning comparison
    img = add_image(slide, "tuning_ba", rx, CT + Inches(2.6), width=col_w,
                    height=Inches(3.0))

    _finish(slide, 12,
        "13 systematic experiments across beam size, length penalty, "
        "temperature, and sampling. Config J achieved the best IS. Key "
        "trade-off: eliminated all 70 empty outputs but added 41 "
        "hallucinations. Net IS gain: only +0.08.",
        [[lt, lb], [rt, rb, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

def slide_13(prs):
    build_split(prs, 13, "Tuning Is Mitigation, Not a Cure", "P4_lenpen",
        bullets=[
            ("Config J: eliminates empties but increases hallucinations by 13%",
             {"color": CORAL}),
            "Net IS gain: only +0.08 across 1,497 segments",
            "Cross-config proof: per-segment rankings identical (r > 0.92)",
            ('"Hard" and "easy" segments stay the same — '
             "bottleneck is the visual encoder", {"bold": True}),
            ("Data is the real constraint: 1,273 training segments is "
             "below the ~1K LoRA minimum", {"color": CORAL}),
            ("Three levers remain: scale data (20K+), swap LLM "
             "(Llama 3.1 8B), smart prompts", {"color": TEAL}),
        ],
        notes="Tuning is mitigation, not a cure. Config J's fundamental "
              "trade-off: silent failures (empties) vs noisy failures "
              "(hallucinations). Cross-config analysis proves: per-segment "
              "IS rankings are nearly identical across all 16 configs "
              "(r > 0.92). The bottleneck is the visual encoder AND data "
              "scarcity — 1,273 training segments is below the ~1K minimum "
              "for LoRA generalization. Three levers: (1) scale data to "
              "20K-50K, (2) swap LLM to Llama 3.1 8B, (3) smart prompts.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE — TUNING SUMMARY (condensed)
# ═══════════════════════════════════════════════════════════════════════

def slide_tuning_summary(prs):
    """Condensed tuning section: 5 slides into 1."""
    slide = new_slide(prs)
    add_title(slide, "Decode Tuning: 13 Experiments, Minimal Gain")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — What we tested
    lt = add_text(slide, "What We Tested", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "4 decode parameters: beam size, length penalty, temperature, sampling",
        "13 systematic experiments (A\u2013M) on 107 segments",
        "Best config (J) validated on full 1,497 segments",
        "Parameters explored: beam 5\u201350, lenpen \u22120.5 to 2.0, temp 0.3\u20131.5",
    ], MX, CT + Inches(0.45), col_w, Inches(2.5), size=Pt(14))

    # Callout box
    r1 = add_rect(slide, MX, CT + Inches(3.1), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    kf_title = add_text(slide, "Key Finding",
             MX + Inches(0.2), CT + Inches(3.2), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=CORAL, bold=True)
    kf_bullets = add_bullets(slide, [
        "Per-segment quality rankings identical across configs (r > 0.92)",
        "A \u201cgood\u201d segment is good in ALL configs; a \u201cbad\u201d one is always bad",
        ("The bottleneck is the visual encoder, not decode parameters",
         {"bold": True, "color": CORAL}),
    ], MX + Inches(0.2), CT + Inches(3.55), col_w - Inches(0.4), Inches(1.2),
       size=Pt(13))

    # Right — What we found
    rx = MX + col_w + gap  # slide_tuning_summary right col
    rt = add_text(slide, "What We Found", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=CORAL, bold=True)

    # Config J definition note
    j_note = add_text(slide,
        "Config J = lenpen=1.0, temp=0.5 (length penalty forces output, "
        "low temperature reduces randomness)",
        rx, CT + Inches(0.35), col_w, Inches(0.3),
        size=Pt(11), color=MGRAY, italic=True)

    headers = ["Metric", "Baseline", "Best (J)", "\u0394"]
    rows = [
        ["Mean IS", "2.52", "2.60", "+0.08"],
        ["Captured (IS\u22653)", "39.9%", "41.2%", "+1.3pp"],
        ["Empty outputs", "70 (4.7%)", "0 (0%)", "\u221270"],
        ["Hallucinations", "307 (20.5%)", "348 (23.2%)", "+41"],
        ["Mean WWER", "61.9%", "59.8%", "\u22122.1pp"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.75), col_w,
                    row_height=Inches(0.4),
                    col_widths=[Inches(1.7), Inches(1.2), Inches(1.2), Inches(1.4)],
                    text_size=Pt(11))

    # Bottom verdict
    verdict = add_text(slide,
        "Config J eliminates empties but adds hallucinations. "
        "Net IS gain: +0.08. Tuning is mitigation, not a cure.",
        rx, CT + Inches(3.3), col_w, Inches(0.7),
        size=Pt(14), color=LGRAY, italic=True)

    _finish(slide, 0,
        "Condensed tuning results. 13 experiments across 4 decode parameters "
        "showed minimal improvement. Best config (J = lenpen=1.0, temp=0.5) eliminates empty outputs "
        "but increases hallucinations by 13%. Net IS gain only +0.08. "
        "Per-segment rankings are identical across configs (r > 0.92), proving "
        "the bottleneck is the visual encoder, not decode parameters.\n\n"
        "The original slide included a length penalty sensitivity chart showing "
        "the empty-vs-hallucination trade-off: lenpen=-0.5 causes 44.9% empty "
        "outputs; baseline (lenpen=0) has 4.7% empties; lenpen=1.0 (Config J) "
        "eliminates all empties but hallucinations rise from 20.5% to 23.2%; "
        "lenpen=2.0 pushes hallucinations to 52.9%. This demonstrates the "
        "fundamental trade-off: length penalty controls whether the model stays "
        "silent (empty) or fabricates (hallucination). Config J chose the sweet "
        "spot — zero empties at the cost of +41 hallucinations.",
        [[lt, lb], [rt, j_note, tbl], [r1, kf_title, kf_bullets, verdict]],
        click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14 — CURATED EXAMPLES (TABLE)
# ═══════════════════════════════════════════════════════════════════════

def slide_14(prs):
    slide = new_slide(prs)
    add_title(slide, "Representative Examples")
    add_accent_line(slide)

    headers = ["Category", "Reference", "Hypothesis", "WER", "IS"]
    rows = [
        ["Perfect", "health insurance company they pay...", "[exact match]", "0%", "5.0"],
        ["WER Misleads", "work with the team in a more", "work with a team and more", "29%", "4.3"],
        ["Near-Miss", "1 billion cfus of probiotics", "1 million cfus of permafrost", "58%", "2.7"],
        ["Hallucinated", "carry strap", "holocaust denier", "100%", "0.7"],
    ]
    # Color IS column by value
    row_colors = {
        0: {4: GREEN},
        1: {4: GREEN},
        2: {4: YELLOW},
        3: {4: RED},
    }

    tbl = add_table(slide, headers, rows,
                    MX, CT, CW, row_height=Inches(0.55),
                    col_widths=[Inches(1.5), Inches(3.8), Inches(3.8),
                                Inches(1.0), Inches(1.0)],
                    row_colors=row_colors)

    _finish(slide, 14,
        "Four examples spanning the quality range. Row 1: perfect lip-reading. "
        "Row 2: WER says 29% error but the meaning is fully preserved — IS 4.3. "
        "Row 3: near-miss — structure intact but key terms phonetically garbled "
        "(probiotics→permafrost). Row 4: complete hallucination — 'carry strap' "
        "becomes 'holocaust denier.' This is why WER alone is insufficient.",
        [[tbl]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_15(prs):
    slide = new_slide(prs)
    add_title(slide, "Demo: OK → Near-miss → Hallucination")
    add_accent_line(slide)

    # Three embedded videos side by side — click each to play
    # VID dict mapping (confirmed correct):
    #   "ok_demo"   -> 8SMYkCQkT4Q_0  (sheetaro -> just hara, gist right)
    #   "nearmiss"  -> -WQZsfHcPDM_7  (probiotics -> permafrost)
    #   "halluc"    -> 00MUdHQ7GGY_8  (carry strap -> holocaust denier)
    vid_w = Inches(3.6)
    vid_h = Inches(2.7)
    gap = Inches(0.4)
    total = 3 * vid_w + 2 * gap
    start_x = (SL_W - total) / 2
    vid_y = CT + Inches(0.1)

    vids = [
        ("ok_demo", '"sheetaro" \u2192 "just hara"\nGist right, names garbled', "WER 33%  IS 3.8", TEAL),
        ("nearmiss", '"probiotics" \u2192 "permafrost"\nStructure right, key terms garbled', "WER 58%  IS 2.7", YELLOW),
        ("halluc", '"carry strap" \u2192 "holocaust denier"', "WER 100%  IS 0.1", RED),
    ]

    for i, (key, desc, wer, color) in enumerate(vids):
        x = start_x + i * (vid_w + gap)
        add_video(slide, key, x, vid_y, vid_w, vid_h)
        add_text(slide, wer, x, vid_y + vid_h + Inches(0.05), vid_w,
                 Inches(0.3), size=Pt(14), color=color, bold=True,
                 align=PP_ALIGN.CENTER)
        add_text(slide, desc, x, vid_y + vid_h + Inches(0.35), vid_w,
                 Inches(0.6), size=Pt(11), color=LGRAY,
                 align=PP_ALIGN.CENTER)

    add_text(slide, "Click each video to play.",
             MX, Inches(6.6), CW, Inches(0.3),
             size=Pt(11), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 15,
        "Three demos side by side. Left: 'sheetaro' becomes 'just hara' "
        "(IS 3.8 — gist right but names garbled, OK quality). Center: "
        "'probiotics' becomes 'permafrost' (near-miss, IS 2.7 — sentence "
        "structure preserved but key terms phonetically garbled). "
        "Right: 'carry strap' becomes 'holocaust denier' (hallucination, "
        "IS 0.1). Click each video to play.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — IS VALIDATION: CLAUDE-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════════

def slide_16(prs):
    slide = new_slide(prs)
    add_title(slide, "IS Validation: Design-Time Distilled Evaluation")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left: How IS works
    lt = add_text(slide, "How the IS Was Built", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Full evaluation framework designed at development time",
        "Selected 6 signals: Semantic (25%), Phonetic (15%), "
        "inv. WER (15%), inv. WWER (15%), NEA F1 (15%), Length (15%)",
        "Defined 5 tiers, 5 failure categories, 7 success patterns",
        ("Distilled into deterministic formulas — no LLM per sample",
         {"bold": True}),
        "Result: reproducible, free, decomposable scoring",
    ], MX, CT + Inches(0.45), col_w, Inches(3.0), size=Pt(13))

    # Right: Correlation analysis + validation
    rx = MX + col_w + gap
    rt = add_text(slide, "Correlation Analysis (PCA)", rx, CT, col_w,
                  Inches(0.35), size=Pt(17), color=CORAL, bold=True)

    # Three dimensions
    dims = [
        ("Word Accuracy", "WER + WWER + Phonetic (r > 0.79)", "~60% of IS", TEAL),
        ("Meaning Preservation", "Semantic similarity", "28.5%", GREEN),
        ("Output Sanity", "Length ratio", "9.1%", LGRAY),
    ]
    dim_y = CT + Inches(0.5)
    for i, (name, signals, pct, color) in enumerate(dims):
        y = dim_y + i * Inches(0.75)
        add_text(slide, name, rx, y, col_w, Inches(0.3),
                 size=Pt(14), color=color, bold=True)
        add_text(slide, f"{signals} — {pct} of variance",
                 rx + Inches(0.15), y + Inches(0.3), col_w - Inches(0.15),
                 Inches(0.3), size=Pt(11), color=LGRAY)

    # Cross-config validation stats
    add_text(slide, "Cross-Config Validation (16 configs)",
             rx, CT + Inches(2.9), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["LLM heuristic vs IS", "r = 0.925"],
        ["Agreement (IS ≥ 3.0)", "88.6%"],
        ["Recall (IS ≥ 3.0)", "97.6–100%"],
        ["Cohen's κ", "0.773"],
        ["Segment ranking stability", "r > 0.92"],
    ]
    add_table(slide, headers, rows, rx, CT + Inches(3.3), col_w,
              row_height=Inches(0.32),
              col_widths=[Inches(3.0), Inches(2.5)],
              text_size=Pt(11))

    _finish(slide, 16,
        "How the IS was built: the entire framework was designed at development "
        "time — rubric, 6 signals with weights, tier boundaries, failure mode "
        "taxonomy, success patterns. These were then encoded into deterministic "
        "formulas. No LLM is called per sample at runtime.\n\n"
        "KEY CORRELATION FINDINGS:\n"
        "1. Phonetic Sim is the strongest single predictor (r=0.943) despite "
        "15% weight — it's the most direct measure of visual encoder quality.\n"
        "2. The 6 signals collapse into 3 dimensions: word accuracy "
        "(WER/WWER/Phonetic, ~60%), meaning (Semantic, 28.5%), output sanity "
        "(Length, 9.1%). Four of six signals measure the same thing.\n"
        "3. Semantic Sim (25% weight) drives the most IS variance (28.5%) — "
        "it's the tiebreaker that separates segments with similar word accuracy.\n"
        "4. NEA F1 punches above its weight: 17.3% variance from 15% weight. "
        "Names/numbers are binary — either preserved or not.\n"
        "5. WER is UNRELIABLE across configs — correlation with IS swings from "
        "-0.95 to -0.45 depending on length penalty. This is why IS was created.\n"
        "6. Length Ratio is nearly useless (9.1%, sign flips). Future versions "
        "could reduce its weight.\n\n"
        "Cross-config validation: r=0.925, 88.6% agreement, κ=0.773, "
        "recall 97.6-100% across 16 decode configs.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_17(prs):
    """8-Stage Pipeline — per-stage wipe reveal with connector arrows."""
    slide = new_slide(prs)
    add_title(slide, "8-Stage Automated Pipeline")
    add_accent_line(slide)

    add_text(slide, "3 research repos \u2192 single orchestrated system",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    BLUE   = RGBColor(0x4D, 0xD0, 0xE1)
    SGREEN = RGBColor(0x66, 0xBB, 0x6A)
    SGOLD  = RGBColor(0xFF, 0xCA, 0x28)
    SPINK  = RGBColor(0xEF, 0x9A, 0x9A)
    DARK   = RGBColor(0x0D, 0x1B, 0x2A)
    DARK2  = RGBColor(0x1A, 0x2A, 0x3A)

    row1_stages = [
        ("1", "Normalize", "HDR/10-bit\nconversion", BLUE, ".mp4"),
        ("2", "ASR", "Whisper\ntranscription", BLUE, ".wrd"),
        ("3", "Mouth Crop", "Face detection\n& ROI extract", BLUE, ".mp4 (crop)"),
        ("4", "LRS3 Convert", "Flat \u2192 LRS3\nformat", BLUE, "LRS3/"),
    ]
    row2_stages = [
        ("5", "Manifests", "TSV + splits\ngeneration", SGREEN, ".tsv"),
        ("6", "K-means", "Feature\nextraction", SGREEN, ".npy"),
        ("7", "LLM Decode", "AV-HuBERT +\nLLaMA-2", SGOLD, "text"),
        ("8", "Outputs", "Reports &\nburned video", SPINK, ".json"),
    ]

    box_w = Inches(2.65)
    box_h = Inches(1.6)
    gap = Inches(0.35)
    arrow_w = Inches(0.25)
    total_w = 4 * box_w + 3 * gap
    start_x = (SL_W - total_w) / 2
    row1_y = CT + Inches(0.7)
    row2_y = row1_y + box_h + Inches(0.9)

    def _draw_one_stage(num, name, sub, color, fmt_label, x, y_top):
        """Draw one stage box. Returns list of shapes for this stage."""
        shapes = []
        shapes.append(add_text(slide, fmt_label,
                 x, y_top - Inches(0.25), box_w, Inches(0.22),
                 size=Pt(10), color=LGRAY, align=PP_ALIGN.CENTER))
        shapes.append(add_rect(slide, x, y_top, box_w, box_h,
                     fill_color=color, border_color=None))
        shapes.append(add_text(slide, f"{num}. {name}",
                 x + Inches(0.1), y_top + Inches(0.15),
                 box_w - Inches(0.2), Inches(0.45),
                 size=Pt(18), color=DARK, bold=True,
                 align=PP_ALIGN.CENTER))
        shapes.append(add_text(slide, sub,
                 x + Inches(0.1), y_top + Inches(0.65),
                 box_w - Inches(0.2), Inches(0.7),
                 size=Pt(13), color=DARK2, align=PP_ALIGN.CENTER))
        return shapes

    def _add_arrow(x, y, direction="right"):
        """Add connector arrow. Returns list with one shape."""
        if direction == "right":
            return [add_text(slide, "\u2192", x, y + box_h / 2 - Inches(0.15),
                             arrow_w, Inches(0.3), size=Pt(18), color=TEAL,
                             bold=True, align=PP_ALIGN.CENTER)]
        else:  # down
            return [add_text(slide, "\u2193", x, y, Inches(0.3), Inches(0.4),
                             size=Pt(18), color=TEAL, bold=True,
                             align=PP_ALIGN.CENTER)]

    # Build per-stage animation groups
    anim_groups = []

    # Group 0: Input label (visible on entry)
    input_label = [add_text(slide, ".mp4\n\nVideo\nInput",
                   MX, row1_y + Inches(0.15),
                   Inches(0.8), box_h - Inches(0.3),
                   size=Pt(11), color=LGRAY, bold=True, align=PP_ALIGN.CENTER)]
    anim_groups.append(input_label)

    # Groups 1-4: Row 1 stages with arrows
    for i, (num, name, sub, color, fmt) in enumerate(row1_stages):
        x = start_x + i * (box_w + gap)
        stage_shapes = _draw_one_stage(num, name, sub, color, fmt, x, row1_y)
        if i > 0:
            ax = start_x + (i - 1) * (box_w + gap) + box_w
            stage_shapes = _add_arrow(ax, row1_y, "right") + stage_shapes
        anim_groups.append(stage_shapes)

    # Group 5: Down arrow + repo labels for row 1
    down_x = start_x + 3 * (box_w + gap) + box_w / 2 - Inches(0.15)
    down_y = row1_y + box_h + Inches(0.15)
    down_group = _add_arrow(down_x, down_y, "down")
    down_group.append(add_text(slide, "auto_avsr",
             start_x + 2 * (box_w + gap), row1_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))
    anim_groups.append(down_group)

    # Groups 6-9: Row 2 stages with arrows
    for i, (num, name, sub, color, fmt) in enumerate(row2_stages):
        x = start_x + i * (box_w + gap)
        stage_shapes = _draw_one_stage(num, name, sub, color, fmt, x, row2_y)
        if i > 0:
            ax = start_x + (i - 1) * (box_w + gap) + box_w
            stage_shapes = _add_arrow(ax, row2_y, "right") + stage_shapes
        anim_groups.append(stage_shapes)

    # Group 10: Output label + repo labels + legend
    final_group = []
    final_group.append(add_text(slide, ".json\n\nReports\n& Videos",
                    SL_W - MX - Inches(0.8), row2_y + Inches(0.15),
                    Inches(0.8), box_h - Inches(0.3),
                    size=Pt(11), color=LGRAY, bold=True, align=PP_ALIGN.CENTER))
    final_group.append(add_text(slide, "av_hubert",
             start_x, row2_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))
    final_group.append(add_text(slide, "VSP-LLM",
             start_x + 2 * (box_w + gap), row2_y + box_h + Inches(0.08),
             2 * box_w + gap, Inches(0.25),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER))

    legend_y = Inches(6.8)
    legend_items = [
        ("Preprocessing", BLUE), ("Feature Processing", SGREEN),
        ("LLM Inference", SGOLD), ("Output Generation", SPINK),
    ]
    leg_w = Inches(0.25)
    leg_h = Inches(0.25)
    leg_gap = Inches(2.8)
    leg_start = (SL_W - 4 * leg_gap) / 2 + Inches(0.3)
    for i, (lbl, clr) in enumerate(legend_items):
        lx = leg_start + i * leg_gap
        final_group.append(add_rect(slide, lx, legend_y, leg_w, leg_h,
                                 fill_color=clr))
        final_group.append(add_text(slide, lbl,
                 lx + Inches(0.35), legend_y - Inches(0.02),
                 Inches(2.0), Inches(0.3), size=Pt(12), color=WHITE))
    anim_groups.append(final_group)

    # Use wipe animation for per-stage sequential reveal
    _auto_num[0] += 1
    add_logo(slide)
    add_slide_num(slide, _auto_num[0])
    add_fade_transition(slide)
    try:
        add_wipe_animation(slide, anim_groups, click_reveal=True, dur_ms=400)
    except Exception:
        add_animations(slide, anim_groups, click_reveal=True)
    set_notes(slide,
        "8-stage automated pipeline built from 3 research repos. "
        "Each stage reveals sequentially with a wipe animation. "
        "Row 1: Normalize, ASR, Mouth Crop, LRS3 Convert (preprocessing). "
        "Row 2: Manifests, K-means, LLM Decode, Outputs (processing). "
        "Click through to reveal each stage one by one.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 18 — ENGINEERING JOURNEY
# ═══════════════════════════════════════════════════════════════════════

def slide_18(prs):
    """Engineering journey: integration, migration, bug fixing."""
    slide = new_slide(prs)
    add_title(slide, "Building the Pipeline: The Engineering Journey")
    add_accent_line(slide)

    # Three phase cards
    cw_card = Inches(3.6)
    ch_card = Inches(4.5)
    gap_card = Inches(0.5)
    total = 3 * cw_card + 2 * gap_card
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.1)

    phases = [
        {
            "title": "Pipeline Build",
            "subtitle": "~2\u20133 weeks",
            "color": TEAL,
            "items": [
                "3 independent repos with no docs",
                "Hardcoded paths everywhere",
                "No error handling or logging",
                "Built 8-stage orchestration\npipeline from scratch",
                "Added venv management,\nGPU detection, logging",
            ],
        },
        {
            "title": "Migration",
            "subtitle": "~4\u20135 weeks",
            "color": CORAL,
            "items": [
                "EC2 \u2192 Docker container",
                "Missing NVIDIA GPU drivers",
                "Python version conflicts",
                "Offline dependency packaging\n(no internet in container)",
                "spaCy wheels, fairseq patches,\nCython compilation",
                "Web UI migration (1\u20132 weeks\nwithin this phase)",
            ],
        },
        {
            "title": "Bug Fixing &\nRefactoring",
            "subtitle": "Ongoing",
            "color": GREEN,
            "items": [
                "37+ bugs found and fixed",
                "NVENC silent corruption\n(destroyed 43% of videos)",
                "HDR/10-bit tone mapping",
                "823-line monolith \u2192 11 modules\n(52% reduction)",
                "37 automated tests added",
            ],
        },
    ]

    card_groups = []  # list of lists — each inner list = all shapes for one card
    for i, phase in enumerate(phases):
        x = cx + i * (cw_card + gap_card)
        card = []
        card.append(add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=phase["color"], border_width=Pt(2.5),
                     corner_radius=True))
        card.append(add_text(slide, phase["title"],
                 x + Inches(0.2), cy + Inches(0.15),
                 cw_card - Inches(0.4), Inches(0.55),
                 size=Pt(18), color=phase["color"], bold=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_text(slide, phase["subtitle"],
                 x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.3),
                 size=Pt(12), color=LGRAY, italic=True,
                 align=PP_ALIGN.CENTER))
        card.append(add_bullets(slide, phase["items"],
                    x + Inches(0.15), cy + Inches(1.1),
                    cw_card - Inches(0.3), Inches(3.2),
                    size=Pt(11)))
        card_groups.append(card)

    bottom = add_text(slide,
        "Every bug documented with root cause. Every change synced between "
        "EC2 and production container.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=WHITE, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 18,
        "The full engineering journey: 2-3 weeks of pipeline build, 4-5 weeks of "
        "migration to Docker (including 1-2 weeks for Web UI migration), and "
        "ongoing bug fixing. 37+ bugs including NVENC silent corruption. "
        "Refactored from 823-line monolith to 11 reusable modules.",
        card_groups + [[bottom]], click_reveal=True, para_build=False)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 19 — MODULAR REFACTORING (BEFORE/AFTER)
# ═══════════════════════════════════════════════════════════════════════

def slide_19(prs):
    slide = new_slide(prs)
    add_title(slide, "52% Code Reduction: 823 → 393 Lines")
    add_accent_line(slide)

    bw = Inches(5.5)
    bh = Inches(4.5)
    by = CT
    gap = Inches(1.13)

    # BEFORE box (coral)
    r1 = add_rect(slide, MX, by, bw, bh, fill_color=NAVY2,
                  border_color=CORAL, border_width=Pt(3), corner_radius=True)
    add_text(slide, "BEFORE", MX + Inches(0.3), by + Inches(0.2),
             bw - Inches(0.6), Inches(0.4),
             size=Pt(22), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "Monolithic 823-line script",
        "Fragile, untestable",
        "No environment detection",
        "Hardcoded paths everywhere",
    ], MX + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(15), bullet_color=CORAL)

    # AFTER box (teal)
    rx = MX + bw + gap
    r2 = add_rect(slide, rx, by, bw, bh, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(3), corner_radius=True)
    add_text(slide, "AFTER", rx + Inches(0.3), by + Inches(0.2),
             bw - Inches(0.6), Inches(0.4),
             size=Pt(22), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        "393-line orchestrator + 11 modules in lib/",
        ("37 automated tests", {"color": TEAL}),
        "Each stage independently testable",
        "Auto-detects EC2 vs container",
    ], rx + Inches(0.3), by + Inches(0.9), bw - Inches(0.6), Inches(3.0),
       size=Pt(15), bullet_color=TEAL)

    _finish(slide, 19,
        "The original pipeline was a single 823-line bash script. Refactored "
        "into a 393-line orchestrator calling 11 reusable modules. 37 "
        "automated tests validate every module. Environment-aware: "
        "automatically detects EC2 development vs Docker container.",
        [[r1], [r2]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 20 — DEPLOYED PRODUCT
# ═══════════════════════════════════════════════════════════════════════

def slide_20(prs):
    build_bullets(prs, 20,
        "Standalone Container — No Cloud Required",
        [
            "Docker container with web UI on Linux machine",
            "Drag-and-drop video upload",
            "Automatic end-to-end processing",
            "INSTALL.sh overlay with backup and verification",
            ("Currently deployed at client site", {"color": TEAL, "bold": True}),
        ],
        "The system runs as a standalone Docker container — no cloud, no "
        "internet required. Web UI for drag-and-drop video upload. "
        "INSTALL.sh handles deployment with automatic backup and 13-point "
        "verification. Currently deployed and running at the client site.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 21 — INTELLIGENT FEATURES (3 CARDS)
# ═══════════════════════════════════════════════════════════════════════

def slide_21(prs):
    slide = new_slide(prs)
    add_title(slide, "Pipeline Intelligence")
    add_accent_line(slide)

    cards = [
        ("Transcription Reuse",
         "Manual corrections persist across runs. Whisper skips matched "
         "segments, saving hours.", TEAL),
        ("Golden K-means",
         "1,396-video baseline clustering model for consistent feature "
         "extraction.", CORAL),
        ("Smart Segmentation",
         "Configurable overlap for context preservation across segment "
         "boundaries.", LGRAY),
        ("Intelligibility Score (IS)",
         "IS = 0-5 composite of 6 signals (semantic, phonetic, WER, WWER, "
         "NEA, length ratio). Rubric, weights, tiers, "
         "and failure taxonomy designed at development time — distilled into "
         "deterministic code (no LLM API calls at runtime). "
         "Validated: r=0.925 across 16 configs, 88.6% agreement. "
         "6 signals collapse into 3 independent dimensions (PCA).", GREEN),
    ]

    cw = Inches(2.7)
    ch = Inches(4.0)
    gap = Inches(0.35)
    total = 4 * cw + 3 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.2)

    card_shapes = []
    for i, (title, desc, color) in enumerate(cards):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, cy, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, title, x + Inches(0.15), cy + Inches(0.3),
                 cw - Inches(0.3), Inches(0.5),
                 size=Pt(16), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, desc, x + Inches(0.15), cy + Inches(0.95),
                 cw - Inches(0.3), Inches(2.7),
                 size=Pt(12), color=WHITE)
        card_shapes.append(r)

    _finish(slide, 21,
        "Four intelligent features. Transcription reuse: manual corrections "
        "persist across runs. Golden k-means: consistent clustering baseline. "
        "Smart segmentation: configurable overlap. Intelligibility Score: the IS is "
        "a 0-5 composite score combining 6 signals — semantic similarity (25%), "
        "phonetic similarity (15%), inverse WER (15%), inverse WWER (15%), "
        "Named Entity Accuracy F1 (15%), and length ratio (15%). The entire "
        "framework was designed at development time: the rubric, signal selection "
        "and weights, tier boundaries (Excellent/Good/Fair/Poor/Failed), 10 "
        "failure modes, and 7 success patterns. These were then distilled into "
        "deterministic formulas — no LLM is called per sample at runtime. "
        "Correlation analysis shows the 6 signals collapse into 3 independent "
        "dimensions: word accuracy (WER/WWER/Phonetic, r>0.79, ~60% of IS), "
        "meaning preservation (Semantic, 28.5%), and output sanity (Length, "
        "9.1%). Cross-config validation across 16 decode configs: r=0.925, "
        "88.6% agreement, Cohen's kappa 0.773.",
        [[c] for c in card_shapes], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 22 — EVALUATION INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_22(prs):
    build_split(prs, 22, "Evaluation: Beyond Standard WER", "cdf_wwer",
        bullets=[
            "16 analytical plots per experiment (auto-generated)",
            "Per-segment HTML reports (13 interactive)",
            "Custom NEA metric for entity accuracy",
            "Intelligibility Score pipeline (LLM-distilled, 6 signals)",
            "IS correlation analysis (16 configs, r=0.925)",
            "Failure mode classification (5 categories)",
            "Topic/length analysis (11 categories)",
            ("Fine-tuning diagnostics (10 training plots)", {"color": TEAL}),
        ],
        notes="Evaluation infrastructure goes far beyond standard WER. "
              "16 plots auto-generated per experiment. Interactive HTML "
              "reports. Custom Named Entity Accuracy metric. Full IS "
              "pipeline validated across 16 decode configs.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 23 — PROCESS & DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════

def slide_23(prs):
    build_bullets(prs, 23,
        "Engineering Process",
        [
            "40+ git versions with semantic tags",
            "EC2/container sync protocol (26 tracked items)",
            "8 formal research reports + methodology docs",
            "Complete architecture, development, and bug documentation",
            "Automated test suite and verification",
        ],
        "Rigorous engineering process. Over 40 git versions with semantic "
        "tagging. EC2-to-container sync protocol tracking 26 items. "
        "Eight formal research reports. Full architecture and development "
        "documentation.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 24 — REFRAMING THE STARTING POINT
# ═══════════════════════════════════════════════════════════════════════

def slide_24(prs):
    slide = new_slide(prs)
    add_title(slide, "Starting from 40%, Not 11%")
    add_accent_line(slide)

    col_w = Inches(3.8)
    img_w = Inches(4.2)
    gap = Inches(0.3)

    # Left column — WER Says (coral)
    r1 = add_rect(slide, MX, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=CORAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "WER Says", MX + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=CORAL, bold=True)
    add_bullets(slide, [
        "11.4% usable",
        "9 out of 10 segments fail",
        "Ignores phonetic preservation (41.5%)",
    ], MX + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=CORAL)

    # Middle column — IS Says (teal)
    mx2 = MX + col_w + gap
    r2 = add_rect(slide, mx2, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "IS Says", mx2 + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=TEAL, bold=True)
    add_bullets(slide, [
        ("39.9% properly captured (IS ≥ 3.0)", {"bold": True}),
        ("50.9% with LLM salvage (165 recoverable segments)",
         {"color": GREEN}),
        "Validated across 16 decode configs",
        "Expert heuristic: 88.6% agreement, r=0.925 (no runtime LLM)",
    ], mx2 + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=TEAL)

    # Right — image
    img = add_image(slide, "P1_quality", MX + 2 * col_w + 2 * gap, CT,
                    width=img_w)

    # Bottom
    add_text(slide,
             "The gap is real — but WER dramatically overstates failure. "
             "40% works, 51% with LLM salvage.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 24,
        "This is the turning point. WER says 11.4% usable. Our "
        "Intelligibility Score says 39.9% properly captured — 3.5x more. "
        "LLM salvage analysis identified 165 additional recoverable segments, "
        "raising effective capture to 50.9%. Validated across 16 configs.",
        [[r1], [r2, img]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — LLM SALVAGE: RECOVERABLE SEGMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_25(prs):
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: 1 in 2 Segments Delivers Value")
    add_accent_line(slide)

    # Big number card — centered, full width
    r1 = add_rect(slide, MX, CT, CW, Inches(4.6), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)

    # Big number
    add_text(slide, "50.9%", MX + Inches(0.3), CT + Inches(0.2),
             CW - Inches(0.6), Inches(0.9),
             size=Pt(64), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "effective capture rate",
             MX + Inches(0.3), CT + Inches(1.1),
             CW - Inches(0.6), Inches(0.4),
             size=Pt(18), color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, "vs 39.9% from metrics alone (+11pp)",
             MX + Inches(0.3), CT + Inches(1.55),
             CW - Inches(0.6), Inches(0.35),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Key bullets below the big number
    bul = add_bullets(slide, [
        "165 recoverable from 900 metric-failures (18.3% recovery rate)",
        "58% of salvageable segments have moderate WER (50\u201370%)",
        ("Deterministic 15-rule decision tree \u2014 no LLM calls at runtime (r=0.934 with IS)",
         {"color": TEAL}),
        ("LLM Judge confirms: Y+P = 64.9% (5.7\u00d7 WER's 11.4%)",
         {"color": GREEN, "bold": True}),
    ], MX + Inches(0.3), CT + Inches(2.2), CW - Inches(0.6),
       Inches(2.0), size=Pt(14))

    # Bottom text
    add_text(slide,
             "System delivers useful output for 1 in 2 segments \u2014 "
             "not 2 in 5 as raw metrics suggest.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "LLM Salvage Analysis: 165 of 900 metric-failed segments (IS < 3.0) "
        "are recoverable \u2014 meaning a domain-aware viewer would understand them. "
        "This raises effective capture from 39.9% to 50.9% (+11pp). The recovery "
        "is identified by a deterministic 15-rule decision tree that correlates "
        "at r=0.934 with IS.\n\n"
        "Four levels of measurement: WER says 11.4% usable. IS says 39.9%. "
        "LLM salvage says 50.9%. And the LLM Judge gold standard confirms: "
        "Y+P = 64.9% \u2014 5.7x WER's assessment.",
        [[r1], [bul]], click_reveal=True)


def slide_25b(prs):
    """LLM Salvage: 6 recovery categories explained."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: 6 Recovery Categories")
    add_accent_line(slide)

    add_text(slide,
        "165 segments that metrics call \u201cfailed\u201d (IS < 3.0) actually deliver "
        "useful meaning. They fall into 6 overlapping categories:",
        MX, CT, CW, Inches(0.45), size=Pt(14), color=LGRAY, italic=True)

    categories = [
        ("Phonetic Bridge", "93", TEAL,
         "Words sound right but are spelled differently \u2014 a viewer who knows "
         "the topic fills in the gaps (phonetic sim \u2265 0.6)"),
        ("Structure Match", "74", TEAL,
         "Same grammatical structure as reference \u2014 word order intact, "
         "subject-verb-object pattern preserved"),
        ("Semantic Preservation", "57", GREEN,
         "Core meaning conveyed despite high WER \u2014 like a paraphrase "
         "(semantic sim \u2265 0.5)"),
        ("Hidden Gems", "54", GREEN,
         "Decision tree assigns \u2265 80% recovery probability despite metrics "
         "all flagging failure"),
        ("Entity-Preserved", "44", YELLOW,
         "Critical names and numbers correct even though surrounding words "
         "are wrong (NEA F1 \u2265 50%)"),
        ("WER Over-Punishment", "27", YELLOW,
         "WER inflated by function word errors (\u2018the\u2019 \u2192 \u2018a\u2019) "
         "that don\u2019t affect meaning (WER\u2212WWER \u2265 10pp)"),
    ]

    py = CT + Inches(0.55)
    cat_shapes = []
    for name, count, color, desc in categories:
        r = add_rect(slide, MX, py, CW, Inches(0.7), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        cat_shapes.append(r)
        add_text(slide, f"{name} ({count})",
                 MX + Inches(0.2), py + Inches(0.05), Inches(3.0), Inches(0.3),
                 size=Pt(13), color=color, bold=True)
        add_text(slide, desc,
                 MX + Inches(3.3), py + Inches(0.08), Inches(8.5), Inches(0.55),
                 size=Pt(11), color=LGRAY)
        py += Inches(0.78)

    add_text(slide,
        "Categories overlap \u2014 a segment can exhibit multiple recovery signals.",
        MX, Inches(6.45), CW, Inches(0.35),
        size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "25b",
        "6 salvage categories explained in plain English. Phonetic Bridge is "
        "the largest (93 segments). Categories overlap. Each represents a "
        "different mechanism by which meaning survives despite high WER.",
        [cat_shapes])


def slide_25c(prs):
    """How the salvage detection decision tree works."""
    slide = new_slide(prs)
    add_title(slide, "How Salvage Detection Works")
    add_accent_line(slide)

    # Flow: Input -> 6 checks -> Score -> Threshold -> Result
    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — the process
    lt = add_text(slide, "Deterministic Decision Tree", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)

    steps = [
        ("1. Input", "Reference + hypothesis text pair", TEAL),
        ("2. Compute 6 signals", "Word overlap, sequence order, phonetic similarity,\n"
         "semantic embedding, entity preservation, length ratio", WHITE),
        ("3. Apply 15 rules", "Decision tree checks signals in priority order,\n"
         "assigns one of 15 probability leaf nodes (0.0 \u2013 1.0)", WHITE),
        ("4. Threshold at 0.5", "Probability \u2265 0.5 = recoverable\n"
         "Probability < 0.5 = likely unrecoverable", WHITE),
        ("5. Classify", "Map to 6 recovery categories based on\n"
         "which signals triggered the high probability", GREEN),
    ]

    py = CT + Inches(0.45)
    step_shapes = []
    for title, desc, color in steps:
        t = add_text(slide, title, MX + Inches(0.1), py, Inches(1.8), Inches(0.3),
                     size=Pt(13), color=color, bold=True)
        add_text(slide, desc, MX + Inches(2.0), py, Inches(3.4), Inches(0.5),
                 size=Pt(11), color=LGRAY)
        step_shapes.append(t)
        py += Inches(0.65)

    # Right — validation stats
    rx = MX + col_w + gap
    rt = add_text(slide, "Validation", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    headers = ["Metric", "Value"]
    rows = [
        ["Correlation with IS", "r = 0.934"],
        ["Agreement (IS \u2265 3.0)", "88.6%"],
        ["Cohen\u2019s \u03ba", "0.773 (substantial)"],
        ["Recall", "99.2%"],
        ["Cross-config stability", "r = 0.925 \u00b1 0.015"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.5), col_w,
                    row_height=Inches(0.4),
                    col_widths=[Inches(2.8), Inches(2.7)],
                    text_size=Pt(12))

    rb = add_bullets(slide, [
        "Stable across all 16 decode configurations",
        "Catches 99.2% of IS \u2265 3.0 segments",
        ("Zero cost: pure Python, no LLM calls at runtime", {"bold": True}),
    ], rx, CT + Inches(3.1), col_w, Inches(1.5), size=Pt(13))

    # Bottom
    add_text(slide,
        "The decision tree was designed at development time, then distilled "
        "into deterministic Python. No LLM is called during evaluation.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "25c",
        "How the salvage detection works: a 15-rule deterministic decision tree "
        "that checks 6 linguistic signals and outputs a recovery probability. "
        "Validated at r=0.934 with IS, 88.6% agreement, stable across 16 configs.",
        [[lt] + step_shapes, [rt, tbl, rb]])

def slide_25d(prs):
    """Three real salvage examples showing HOW recovery works."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Three Real Recoveries")
    add_accent_line(slide)

    add_text(slide,
        "These segments failed IS (< 3.0) but a viewer with context would understand them:",
        MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY, italic=True)

    # Three cards side by side
    cw_card = Inches(3.8)
    ch_card = Inches(4.6)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    examples = [
        {
            "title": "Phonetic Bridge",
            "color": TEAL,
            "is_score": "1.29", "wer": "150%", "prob": "0.55",
            "ref": "when jesus rose again",
            "hyp": "in one sense it\u2019s rose\nand kennedy",
            "how": "A wise viewer watching a religious program "
                   "sees \u201cin one sense it\u2019s rose\u201d and thinks: "
                   "\u201cthis is about Jesus rising \u2014 \u2018sense it\u2019s\u2019 "
                   "sounds like \u2018Jesus,\u2019 and \u2018rose\u2019 = "
                   "resurrection.\u201d The mouth shapes for "
                   "\u201cjesus\u201d/\u201csense it\u2019s\u201d are nearly "
                   "identical. The overall message is "
                   "preserved even though exact words differ.",
        },
        {
            "title": "Semantic Preservation",
            "color": GREEN,
            "is_score": "2.18", "wer": "75%", "prob": "0.90",
            "ref": "moving conceptual surface data\nover to engineering solutions\nand tools",
            "hyp": "moved the conceptual rules\nover to engineering tools",
            "how": "Core meaning intact: \u201cmoving concepts \u2192 "
                   "engineering tools.\u201d WER is 75% because function "
                   "words changed, but a tech viewer follows the "
                   "intent perfectly. WER over-punishes this by "
                   "counting every small word change.",
        },
        {
            "title": "Structure Match",
            "color": GOLD,
            "is_score": "2.55", "wer": "40%", "prob": "0.95",
            "ref": "over the last 10 years we have\nhad 8,616 students",
            "hyp": "over the last 10 years we have\nhad 1,600 students",
            "how": "Grammar and word order are perfect. Only the "
                   "number changed (8,616 \u2192 1,600). A viewer "
                   "understands \u201cmany students over 10 years\u201d \u2014 the "
                   "structure carries the message even when the "
                   "exact figure is wrong.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # Title + badge
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  WER {ex["wer"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.4), cw_card - Inches(0.3), Inches(0.25),
                 size=Pt(9), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.7),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.88), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.5),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.68), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.35),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(2.55), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(9.5), color=WHITE)

    _finish(slide, "25d",
        "Three real salvage examples from different recovery categories. "
        "Phonetic Bridge (IS 1.29): lip-reading confusions that are linguistically "
        "plausible, not hallucinations. Semantic Preservation (IS 2.18): WER 75% "
        "but core meaning intact. Structure Match (IS 2.55): perfect grammar, "
        "only a number changed. Each shows WHY the heuristic says recoverable.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25e — SALVAGE: 3 MORE REAL EXAMPLES (DOMAIN CONTEXT RECOVERY)
# ═══════════════════════════════════════════════════════════════════════

def slide_25e(prs):
    """Three more salvage examples emphasising domain-context recovery."""
    slide = new_slide(prs)
    add_title(slide, "LLM Salvage: Domain Context Fills the Gaps")
    add_accent_line(slide)

    add_text(slide,
        "A viewer who knows the topic recovers meaning that metrics miss entirely:",
        MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY, italic=True)

    # Three cards side by side (same layout as slide_25d)
    cw_card = Inches(3.8)
    ch_card = Inches(4.6)
    gap = Inches(0.27)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.45)

    examples = [
        {
            "title": "Religious Context",
            "color": CORAL,
            "is_score": "2.75", "wer": "43%", "prob": "0.90",
            "ref": "the fear of allah is completely\ngone \u2026 no more fear of the\nunseen what a horrible spiritual",
            "hyp": "the fear of the loss complete\n\u2026 no more fear of loss\nwhat a horrible spiritual",
            "how": "A viewer watching a religious sermon "
                   "recognizes \u201cfear of the loss\u201d = \u201cfear of "
                   "Allah.\u201d The structure (\u201cno more fear \u2026 "
                   "horrible spiritual\u201d) is intact. \u201cAllah\u201d \u2192 "
                   "\u201closs\u201d and \u201cunseen\u201d \u2192 \u201cdeath\u201d are "
                   "phonetic confusions, but the sermon\u2019s "
                   "theme of spiritual fear carries through.",
        },
        {
            "title": "Geopolitical Context",
            "color": TEAL,
            "is_score": "2.86", "wer": "72%", "prob": "0.90",
            "ref": "india china afghanistan all\nthese different places \u2026 so\nboth sides would benefit",
            "hyp": "middle east and afghanistan\nall these different warring\nplaces \u2026 both sides will benefit",
            "how": "WER is 72% because country names "
                   "changed, but the argument is identical: "
                   "\u201cdistant foreign regions \u2192 both sides "
                   "benefit.\u201d A news viewer grasps the "
                   "geopolitical point instantly. \u201cIndia "
                   "China\u201d \u2192 \u201cMiddle East\u201d is a domain "
                   "swap, not a meaning loss.",
        },
        {
            "title": "Cooking Context",
            "color": GREEN,
            "is_score": "2.07", "wer": "89%", "prob": "0.80",
            "ref": "i have a tablespoon of\njalapeno fresh jalapeno",
            "hyp": "i have a dietary smoothie\ni\u2019ve got the banana called\nfresh banana",
            "how": "IS rates this a near-total failure (2.07). "
                   "But a viewer watching a cooking video "
                   "sees the presenter holding a pepper and "
                   "saying \u201cfresh banana.\u201d The visual context "
                   "instantly overrides the garbled audio \u2014 "
                   "the viewer knows it\u2019s a jalapeno. "
                   "WER is blind to multimodal cues.",
        },
    ]

    card_shapes = []
    for i, ex in enumerate(examples):
        x = cx + i * (cw_card + gap)

        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=ex["color"], border_width=Pt(2), corner_radius=True)
        card_shapes.append(r)

        # Title + badge
        add_text(slide, ex["title"],
                 x + Inches(0.15), cy + Inches(0.1), cw_card - Inches(0.3), Inches(0.3),
                 size=Pt(14), color=ex["color"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, f'IS {ex["is_score"]}  |  WER {ex["wer"]}  |  Prob {ex["prob"]}',
                 x + Inches(0.15), cy + Inches(0.4), cw_card - Inches(0.3), Inches(0.25),
                 size=Pt(9), color=LGRAY, align=PP_ALIGN.CENTER)

        # Reference
        add_text(slide, "Reference:", x + Inches(0.15), cy + Inches(0.7),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["ref"]}\u201d',
                 x + Inches(0.15), cy + Inches(0.88), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=WHITE, italic=True)

        # Hypothesis
        add_text(slide, "Prediction:", x + Inches(0.15), cy + Inches(1.5),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=LGRAY, bold=True)
        add_text(slide, f'\u201c{ex["hyp"]}\u201d',
                 x + Inches(0.15), cy + Inches(1.68), cw_card - Inches(0.3), Inches(0.55),
                 size=Pt(10), color=ex["color"], italic=True)

        # How it's recovered
        add_text(slide, "How a wise viewer recovers this:",
                 x + Inches(0.15), cy + Inches(2.35),
                 cw_card - Inches(0.3), Inches(0.2), size=Pt(9), color=TEAL, bold=True)
        add_text(slide, ex["how"],
                 x + Inches(0.15), cy + Inches(2.55), cw_card - Inches(0.3), Inches(1.8),
                 size=Pt(9.5), color=WHITE)

    _finish(slide, "25e",
        "Three more salvage examples emphasising domain-context recovery. "
        "Religious Context (IS 2.75): 'fear of allah' becomes 'fear of the loss' "
        "-- a sermon viewer recognizes the spiritual theme despite name garbling. "
        "Geopolitical Context (IS 2.86): country names swap but the argument "
        "(foreign places, both sides benefit) is intact. Cooking Context (IS 2.07): "
        "'jalapeno' becomes 'banana' -- absurd in text, but a viewer SEES the "
        "pepper on screen and corrects automatically. This is the strongest argument "
        "for multimodal context: the visual channel fills gaps that audio-only metrics "
        "cannot measure.",
        [[c] for c in card_shapes], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

def slide_26(prs):
    slide = new_slide(prs)
    add_title(slide, "Five Phases — From IS 2.5 to Target IS 3.5–4.0")
    add_accent_line(slide)

    phases = [
        ("Phase 1", "Surface the good 40%", "Confidence scoring — attach beam probabilities to outputs (2–4 hrs)",
         "IS: identify segments already ≥ 3.0", TEAL),
        ("Phase 2", "Improve the fair 22%", "N-best aggregation — vote across all 20 beam hypotheses (ROVER/MBR)",
         "IS: +0.3–0.5 from better hypothesis selection", TEAL),
        ("Phase 3", "LLM swap + smart prompts", "Llama 3.1 8B + context prompts",
         "IS: +0.5–0.8 from stronger language model", GREEN),
        ("Phase 4", "Scale data 20K–50K", "Fine-tune with more data",
         "IS: +0.5–1.0 — biggest single gain", GREEN),
        ("Phase 5", "Error Correction (GER)", "Second LLM catches hallucinations",
         "IS: +0.3–0.5 from post-processing cleanup", LGRAY),
    ]

    # Staircase on left side
    step_w = Inches(5.8)
    step_h = Inches(0.85)
    step_indent = Inches(0.35)
    start_y = CT
    start_x = MX

    step_shapes = []
    for i, (phase, desc, detail, is_note, color) in enumerate(phases):
        x = start_x + i * step_indent
        y = start_y + i * (step_h + Inches(0.08))
        w = step_w - i * step_indent
        r = add_rect(slide, x, y, w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        step_shapes.append(r)
        step_shapes.append(add_rich_text(slide, [
            [(phase, {"size": Pt(13), "color": color, "bold": True}),
             (f"  {desc}", {"size": Pt(13), "color": WHITE})],
            [(detail, {"size": Pt(11), "color": LGRAY, "italic": True}),
             (f"   {is_note}", {"size": Pt(11), "color": GOLD})],
        ], x + Inches(0.2), y + Inches(0.05), w - Inches(0.4), step_h - Inches(0.1)))

    # WER trajectory image on right
    img = add_image(slide, "P3_trajectory",
                    SRL - Inches(0.2), CT, width=SRW + Inches(0.2))

    bottom = add_text(slide,
             "Combined target: IS 3.5–4.0 (55–65% captured). "
             "Gains are multiplicative (ICLR 2024 scaling law).",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 26,
        "Five phases, each targeting different bottlenecks. Phase 1 is "
        "immediate: confidence scoring to surface the 40% that's already "
        "good (2-4 hours). Phase 2: N-best aggregation (ROVER/MBR). Phase 3: swap LLM "
        "to Llama 3.1 8B plus smart prompts. Phase 4: the biggest gain — "
        "scale training data. Phase 5: Error Correction (GER) post-processing. "
        "Key: ICLR 2024 shows these gains are multiplicative.\n\n"
        "HOW THIS TRANSLATES TO IS:\n"
        "Current: WER 64.1% -> IS 2.52 (39.9% captured).\n"
        "Each ~10pp WER reduction typically improves IS by ~0.3-0.5 points "
        "and captured rate by ~8-12pp.\n"
        "Phase 3 target (42% WER) would project to roughly IS 3.5-4.0 and "
        "55-65% captured rate.\n"
        "The relationship is non-linear — improvements accelerate as more "
        "segments cross the IS >= 3.0 threshold.",
        [step_shapes, [img, bottom]], click_reveal=True)


def slide_26b(prs):
    """26b: IS trajectory roadmap — parallel to WER trajectory on slide_26."""
    slide = new_slide(prs)
    add_title(slide, "IS Improvement Roadmap — From 2.5 to 3.8")
    add_accent_line(slide)

    add_text(slide, "Projected Intelligibility Score improvement per phase",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=LGRAY, italic=True)

    # IS trajectory plot (right side, large)
    img = add_image(slide, "P3b_is_trajectory",
                    MX + Inches(0.5), CT + Inches(0.45),
                    width=Inches(7.0))

    # Key milestones callout (right side)
    rx = MX + Inches(7.8)
    rw = Inches(4.0)
    milestones = [
        ("Current", "IS 2.52", "39.9% captured", CORAL),
        ("Phase 1", "IS ~2.85", "~48% captured", TEAL),
        ("Phase 2", "IS ~3.40", "~58% captured", GREEN),
        ("Phase 3", "IS ~3.80", "~65% captured", GREEN),
    ]
    ms_shapes = []
    for i, (phase, is_val, cap_val, color) in enumerate(milestones):
        y = CT + Inches(0.55) + i * Inches(1.15)
        ms_shapes.append(add_rect(slide, rx, y, rw, Inches(0.95), fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True))
        ms_shapes.append(add_text(slide, phase, rx + Inches(0.15), y + Inches(0.05),
                 rw - Inches(0.3), Inches(0.3),
                 size=Pt(13), color=color, bold=True))
        ms_shapes.append(add_text(slide, f"{is_val}  \u2022  {cap_val}",
                 rx + Inches(0.15), y + Inches(0.35),
                 rw - Inches(0.3), Inches(0.3),
                 size=Pt(16), color=WHITE, bold=True))
        if i > 0:
            delta = float(is_val.replace("IS ~", "")) - 2.52
            ms_shapes.append(add_text(slide, f"+{delta:.2f} from baseline",
                     rx + Inches(0.15), y + Inches(0.63),
                     rw - Inches(0.3), Inches(0.25),
                     size=Pt(10), color=LGRAY, italic=True))

    bottom = add_text(slide,
             "Each ~10pp WER reduction \u2192 ~0.3\u20130.5 IS improvement + ~8\u201312pp captured rate.",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, "26b",
        "IS improvement trajectory paralleling the WER reduction roadmap. "
        "Current IS 2.52 (39.9% captured) \u2192 Phase 3 target IS 3.80 (65% captured). "
        "The IS \u2265 3.0 threshold marks 'captured' segments. "
        "Key insight: relationship is non-linear \u2014 improvements accelerate as more "
        "segments cross the IS \u2265 3.0 threshold.",
        [[img], ms_shapes + [bottom]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

def slide_27(prs):
    slide = new_slide(prs)
    add_title(slide, "Phase 1: Confidence Scoring \u2014 Surface the Good 40%")
    add_accent_line(slide)

    col_w = Inches(5.8)
    gap = Inches(0.53)

    # Left — The Idea
    lt = add_text(slide, "The Idea", MX, CT, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Beam search already computes probability scores "
         "for every hypothesis", {"bold": True}),
        "We just don\u2019t expose them yet",
        "Confidence = attaching these scores to outputs",
        ("No extra model inference \u2014 scores are a "
         "free byproduct of decode", {"color": TEAL}),
    ], MX, CT + Inches(0.5), col_w, Inches(2.5), size=Pt(16))

    # Effort callout
    r1 = add_rect(slide, MX, CT + Inches(3.2), col_w, Inches(0.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Effort: 2\u20134 hours implementation",
             MX + Inches(0.3), CT + Inches(3.25), col_w - Inches(0.6), Inches(0.5),
             size=Pt(18), color=GREEN, bold=True)

    # Right — What It Enables
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "What It Enables", rx, CT, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        "Users see only high-confidence segments by default",
        "Low-confidence segments flagged for human review",
        ("Reduces perceived error rate from 60% to ~20%",
         {"bold": True, "color": GREEN}),
        "Business/Finance segments (57% captured) get highest confidence",
        "Short segments (<10 words, 32%) need lower thresholds",
        ("Entity-level: names, numbers, and places missed in 85% of "
         "segments — confidence scoring can flag these specifically",
         {"color": CORAL}),
    ], rx, CT + Inches(0.5), rw, Inches(3.5), size=Pt(14))

    _finish(slide, 27,
        "Phase 1 is the quick win. Beam search already computes probability "
        "scores for every hypothesis — we just don't surface them. Confidence "
        "scoring means attaching these scores to outputs so users can trust "
        "high-confidence results and flag low-confidence for review. No extra "
        "model inference needed — the scores are a free byproduct of decode. "
        "2-4 hours of implementation. Entity-level analysis shows names, "
        "numbers, and places are missed in 85% of segments.",
        [[lt, lb], [r1], [rt, rb]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

def slide_28(prs):
    """Phase 2: N-best aggregation with ROVER/MBR explanation."""
    slide = new_slide(prs)
    add_title(slide, "Phase 2: Exploit All 20 Hypotheses")
    add_accent_line(slide)

    # Main point
    add_text(slide, "Currently discarding 19 of 20 beam candidates",
             MX, CT, CW, Inches(0.35), size=Pt(16), color=WHITE, bold=True)

    # Two technique cards side by side
    cw = Inches(5.5)
    gap = Inches(1.13)
    cy = CT + Inches(0.55)
    ch = Inches(2.2)

    r1 = add_rect(slide, MX, cy, cw, ch, fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "ROVER", MX + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=TEAL, bold=True)
    add_text(slide, "Recognizer Output Voting Error Reduction",
             MX + Inches(0.2), cy + Inches(0.4), cw - Inches(0.4), Inches(0.25),
             size=Pt(11), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Align all 20 hypotheses word-by-word",
        "Vote at each position \u2014 most common word wins",
        "Reduces random substitution errors",
    ], MX + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    rx = MX + cw + gap
    r2 = add_rect(slide, rx, cy, cw, ch, fill_color=NAVY2,
                  border_color=GREEN, border_width=Pt(2), corner_radius=True)
    add_text(slide, "MBR", rx + Inches(0.2), cy + Inches(0.1),
             cw - Inches(0.4), Inches(0.3), size=Pt(16), color=GREEN, bold=True)
    add_text(slide, "Minimum Bayes Risk Decoding",
             rx + Inches(0.2), cy + Inches(0.4), cw - Inches(0.4), Inches(0.25),
             size=Pt(11), color=LGRAY, italic=True)
    add_bullets(slide, [
        "Score each hypothesis against ALL others",
        "Pick the one most similar to the consensus",
        "Best single hypothesis, no alignment needed",
    ], rx + Inches(0.2), cy + Inches(0.7), cw - Inches(0.4), Inches(1.3),
       size=Pt(13))

    # Impact summary
    iy = cy + ch + Inches(0.3)
    impact = add_bullets(slide, [
        ("Expected: 5\u201315% relative IS improvement", {"color": TEAL, "bold": True}),
        "Targets: Accumulated Errors (24.4%) \u2014 the \"death by a thousand cuts\" category",
        "Moves IS 2.0\u20132.9 segments above the 3.0 threshold",
    ], MX, iy, CW, Inches(1.5), size=Pt(14))

    _finish(slide, 28,
        "Phase 2 exploits beam search output. Currently we keep only the top "
        "hypothesis and throw away 19 alternatives. ROVER aligns all 20 and "
        "votes word-by-word. MBR picks the hypothesis closest to the consensus. "
        "Both are established ASR techniques with consistent 5-15% gains. "
        "Targets the Accumulated Errors category (24.4% of failures).",
        [[r1], [r2], [impact]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

def slide_29(prs):
    slide = new_slide(prs)
    add_title(slide, "Fine-Tuning Experiments: Limited Data, Limited Gains")
    add_accent_line(slide)

    # Dashboard image — top half
    img = add_image(slide, "ft_clean", MX, CT, width=CW,
                    height=Inches(2.8))

    # Two columns below
    col_w = Inches(5.5)
    gap = Inches(1.13)
    col_y = CT + Inches(3.0)

    # Left — Exp A/B Results
    lt = add_text(slide, "What We Tried", MX, col_y, col_w, Inches(0.3),
                  size=Pt(15), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("Small-scale LoRA fine-tune with only 1,273 segments",
         {"bold": True}),
        "Exp A (rank 16): best val accuracy 62.94% at epoch 2",
        ("Exp B (rank 64): 3.1pp WORSE — more params = faster overfitting",
         {"color": CORAL}),
        ("Result: data too limited for LoRA to generalize",
         {"bold": True, "color": GOLD}),
    ], MX, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    # Right — IS Impact
    rx = MX + col_w + gap
    rt = add_text(slide, "Impact on Intelligibility", rx, col_y, col_w,
                  Inches(0.3), size=Pt(15), color=TEAL, bold=True)
    rb = add_bullets(slide, [
        "Baseline IS: 2.49 — Exp A IS: 2.31 — Exp B IS: 2.02",
        ("Fine-tuning made IS WORSE, not better", {"color": CORAL}),
        "Empty outputs: 7% → 13% → 27% (identifiable and filterable)",
        ("Key insight: need 20K+ segments, not parameter tuning",
         {"bold": True, "color": GREEN}),
    ], rx, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    _finish(slide, 29,
        "Fine-tuning experiments with LoRA on 1,273 segments. Exp A (rank 16): "
        "62.94% val accuracy, severe overfitting. Exp B (rank 64): 3.1pp worse. "
        "IS scores actually decreased: baseline 2.49, Exp A 2.31, Exp B 2.02. "
        "Empty outputs increased dramatically. The bottleneck is data quantity "
        "(need 20K+), not model capacity or parameter tuning.",
        [[img], [lt, lb], [rt, rb]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30 — LLM UPGRADE + ADVANCED CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════

def slide_30(prs):
    slide = new_slide(prs)
    add_title(slide, "Stronger LLM + Smart Prompts = Force Multiplier")
    add_accent_line(slide)

    cols = [
        ("LLM Swap (immediate)", [
            "Llama 3.1 8B: drop-in (same hidden_size 4096)",
            "Quality ≈ Llama-2 70B, 128K vocab, 128K context",
            ("Setup: 1-2 hours", {"bold": True}),
            "Alone: -3 to -8pp WER",
        ], TEAL),
        ("Smart Prompts (force multiplier)", [
            "7 strategies: topic context, word count, anti-hallucination, GER",
            "Llama-2: +5-10pp | Llama 3.1: +12-20pp",
            ("GER post-processing: +8-15pp, no retraining", {"color": GREEN}),
        ], CORAL),
        ("Future", [
            "Arabic (K-means model exists)",
            "VALLR: 18.7% WER with 3B model",
            "Multi-speaker, streaming",
        ], LGRAY),
    ]

    cw = Inches(3.6)
    gap = Inches(0.5)
    total = 3 * cw + 2 * gap
    cx = (SL_W - total) / 2

    col_shapes = []
    for i, (title, items, color) in enumerate(cols):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, CT, cw, Inches(4.8), fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, title, x + Inches(0.2), CT + Inches(0.15),
                 cw - Inches(0.4), Inches(0.45),
                 size=Pt(15), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_bullets(slide, items, x + Inches(0.2), CT + Inches(0.7),
                    cw - Inches(0.4), Inches(3.5), size=Pt(13))
        col_shapes.append(r)

    _finish(slide, 30,
        "Three columns of future capability. Left: LLM swap to Llama 3.1 "
        "8B is trivial — same hidden dimension, 1-2 hours. Center: 7 prompt "
        "strategies are a force multiplier — more effective on stronger "
        "models. GER uses N-best hypotheses + correction LLM for +8-15pp "
        "with no retraining. Right: Arabic support exists, VALLR achieves "
        "18.7% WER with a 3B model.",
        [col_shapes])

# ═══════════════════════════════════════════════════════════════════════
# ARABIC PIPELINE ROADMAP
# ═══════════════════════════════════════════════════════════════════════

def slide_arabic_roadmap(prs):
    """Arabic pipeline replication roadmap."""
    slide = new_slide(prs)
    add_title(slide, "Arabic Pipeline: Replication Roadmap")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what's needed + how we solve it
    lt = add_text(slide, "What\u2019s Needed & How We\u2019ll Do It",
                  MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Arabic AV-HuBERT encoder", {"bold": True, "color": TEAL}),
        "Fine-tune English AV-HuBERT on Arabic visual speech data \u2014 "
        "AVSpeech dataset has Arabic videos available for training",
        ("Arabic LLM backend", {"bold": True, "color": TEAL}),
        "Swap Llama-2 for Arabic-capable LLM (e.g. Jais, AceGPT, "
        "or Arabic-tuned Llama 3) with Arabic tokenizer",
        ("Training infrastructure", {"bold": True, "color": GREEN}),
        "AWS GPU instance (existing) for AV-HuBERT fine-tuning "
        "and K-means reclustering on Arabic mouth shapes",
        ("Arabic evaluation dataset", {"bold": True, "color": CORAL}),
        "Manual transcriptions needed for MSA + dialect coverage \u2014 "
        "the main bottleneck (requires native speakers)",
        ("Text normalization", {"bold": True, "color": TEAL}),
        "spaCy Arabic, diacritic handling, Arabic NER",
    ], MX, CT + Inches(0.4), col_w, Inches(4.5), size=Pt(13))

    # Right — timeline with practical details
    rx = MX + col_w + gap
    rt = add_text(slide, "Practical Timeline", rx, CT, col_w, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    headers = ["Step", "Effort", "How"]
    rows = [
        ["AV-HuBERT\nfine-tune", "1\u20132 weeks", "AVSpeech Arabic\nvids + AWS GPU"],
        ["Arabic K-means", "2\u20133 days", "Recluster on\nArabic features"],
        ["Arabic LLM\nswap", "1\u20132 days", "Config change +\ntokenizer"],
        ["Eval dataset", "1\u20132 weeks", "Native speaker\ntranscription"],
        ["Pipeline config\n& testing", "3\u20135 days", "End-to-end\nvalidation"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(0.45), col_w,
                    row_height=Inches(0.6),
                    col_widths=[Inches(1.6), Inches(1.3), Inches(2.6)],
                    text_size=Pt(12))

    # Total callout — positioned below table with clearance
    add_rect(slide, rx, CT + Inches(4.05), col_w, Inches(0.55),
             fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
             corner_radius=True)
    add_text(slide, "Total: ~3\u20135 weeks",
             rx + Inches(0.2), CT + Inches(4.1), col_w - Inches(0.4), Inches(0.4),
             size=Pt(18), color=GREEN, bold=True, align=PP_ALIGN.CENTER)

    # Bottom
    add_text(slide,
        "Pipeline code is language-agnostic \u2014 no code changes needed. "
        "AVSpeech Arabic videos + existing AWS GPU cover training. "
        "Main bottleneck: manual Arabic evaluation transcriptions.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    # Timeline summary callout
    timeline_box = add_rect(slide, MX, Inches(5.8), CW, Inches(0.55),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    timeline_txt = add_text(slide, "Total estimated timeline: 3–5 weeks",
             MX + Inches(0.3), Inches(5.85), CW - Inches(0.6), Inches(0.4),
             size=Pt(22), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Arabic replication roadmap with practical details. We have AVSpeech "
        "Arabic videos for training data and an AWS GPU instance for fine-tuning. "
        "Steps: fine-tune AV-HuBERT on Arabic (1-2 weeks), recluster K-means "
        "(2-3 days), swap to Arabic LLM (1-2 days), build eval dataset with "
        "native speakers (1-2 weeks), end-to-end testing (3-5 days). "
        "Total 3-5 weeks. Pipeline code is language-agnostic.",
        [[lt, lb], [rt, tbl], [timeline_box, timeline_txt]], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 31 — SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def slide_31(prs):
    slide = new_slide(prs)
    add_title(slide, "Key Takeaways")
    add_accent_line(slide)

    takeaways = [
        ("1", "Rigorous assessment: 2.5\u00d7 WER gap on 1,497 segments. "
              "Novel IS metric reveals 40% properly captured, 51% with "
              "LLM salvage. 5 classified failure categories."),
        ("2", "Production system delivered: standalone container, 37 bugs "
              "fixed, 8-stage pipeline, 37 tests, 8 research reports."),
        ("3", "Data is the bottleneck: fine-tuning experiments (Exp A/B) "
              "proved 1,273 segments too small. Multiplicative scaling law: "
              "stronger LLM + more data compounds."),
        ("4", "Actionable roadmap to IS 3.5\u20134.0 (from 2.52): "
              "confidence scoring + N-best aggregation + LLM upgrade + "
              "data scaling + GER. Each phase targets a different failure "
              "category."),
    ]

    card_h = Inches(1.05)
    gap = Inches(0.12)
    circle_d = Inches(0.55)

    point_shapes = []
    for i, (num, text) in enumerate(takeaways):
        y = CT + i * (card_h + gap)

        # Card background
        r = add_rect(slide, MX, y, CW, card_h, fill_color=NAVY2,
                     border_color=TEAL, border_width=Pt(1), corner_radius=True)

        # Number circle — vertically centered in card
        cy = y + (card_h - circle_d) / 2
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX + Inches(0.2), cy, circle_d, circle_d)
        circle.fill.solid()
        circle.fill.fore_color.rgb = TEAL
        circle.line.fill.background()
        add_text(slide, num, MX + Inches(0.2), cy,
                 circle_d, circle_d,
                 size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        # Text — left-aligned next to circle
        tb = add_text(slide, text,
                      MX + Inches(1.0), y + Inches(0.12),
                      CW - Inches(1.2), card_h - Inches(0.24),
                      size=Pt(15), color=WHITE)
        point_shapes.append(r)

    _finish(slide, 31,
        "Four takeaways. One: rigorous assessment with novel IS metric. "
        "Two: production system delivered. Three: data is the bottleneck "
        "(fine-tuning proved it). Four: clear roadmap from IS 2.52 to "
        "3.5-4.0, each phase targeting a different failure category.",
        [point_shapes], click_reveal=True)

# ═══════════════════════════════════════════════════════════════════════
# APPENDIX SLIDES (A1–A13)
# ═══════════════════════════════════════════════════════════════════════

def slide_a1(prs):
    """A1: Homophenes — The Lip-Reading Problem."""
    slide = new_slide(prs)
    add_title(slide, "A1: Homophenes — The Lip-Reading Problem")
    add_accent_line(slide)

    # Left: viseme table
    add_text(slide, "50–70% of English sounds are invisible on lips.\n"
             "Multiple sounds produce identical mouth shapes:",
             MX, CT, SLW, Inches(0.7), size=Pt(14), color=LGRAY)

    tbl1 = add_table(slide,
        ["Viseme Group", "Sounds"],
        [["Bilabial", "p, b, m"],
         ["Alveolar", "t, d, n, s, z, l"],
         ["Velar", "k, g, ng"],
         ["Labiodental", "f, v"]],
        MX, CT + Inches(0.9), SLW, text_size=Pt(12))

    # Right: confusable pairs
    add_text(slide, "Confusable word pairs (identical on lips):",
             SRL, CT, SRW, Inches(0.5), size=Pt(14), color=LGRAY)

    tbl2 = add_table(slide,
        ["Word A", "Word B"],
        [["mom", "bomb"], ["pat", "bat"], ["collar", "color"],
         ["pads", "pants"], ["admiral", "animal"],
         ["probiotics", "permafrost"]],
        SRL, CT + Inches(0.6), SRW, text_size=Pt(12))

    add_text(slide, 'Context is the ONLY disambiguation signal.\n'
             'This is why the LLM component matters.',
             SRL, CT + Inches(3.6), SRW, Inches(0.5),
             size=Pt(12), color=TEAL, italic=True)

    _finish(slide, "A1",
        "Homophenes: visually identical mouth shapes for different sounds. "
        "50-70% of sounds invisible on lips. Admiral/animal, mom/bomb — "
        "context is the only way to disambiguate. This is why the LLM matters.",
        [[tbl1], [tbl2]], click_reveal=True)


def slide_a3(prs):
    """A2: Catastrophic lenpen=2.0."""
    slide = new_slide(prs)
    add_title(slide, "A2: Catastrophic lenpen=2.0 (Config H)")
    add_accent_line(slide)

    add_text(slide, "Config H forces the model to generate longer text. "
             "Mean WER: 539.6%\nThe model generates paragraphs of "
             "hallucinated text:",
             MX, CT, CW, Inches(0.6), size=Pt(14), color=CORAL)

    tbl = add_table(slide,
        ["Segment", "Reference", "Config H Output", "WER"],
        [["pOeJSxbFyto", '"get the idea"',
          '"that\'s why I\'m here thank you so much for having me '
          'it\'s been an honor and a privilege..."', "6,833%"],
         ["9KACXV-cW-4", '"now those predictions I think"',
          '"of first believers the same path I\'d like to take a moment '
          'to thank all of you..."', "4,640%"],
         ["loebelfG9T4", '"so repeat make yourself at home"',
          '"don\'t forget to make yourself at home thank you very much '
          'that was a lot of fun..."', "4,183%"]],
        MX, CT + Inches(0.8), CW, text_size=Pt(10),
        row_colors={0: {3: CORAL}, 1: {3: CORAL}, 2: {3: CORAL}})

    add_text(slide, "lenpen=2.0 removes the generation length brake, "
             "letting the LLM prior run unchecked.",
             MX, CT + Inches(3.4), CW, Inches(0.4),
             size=Pt(11), color=LGRAY, italic=True)

    _finish(slide, "A2",
        "Config H (lenpen=2.0) produces catastrophic hallucinations. "
        "Mean WER 539.6%. The model generates entire paragraphs of fluent "
        "but completely fabricated text. This dramatically illustrates the "
        "LLM prior overwhelming the visual signal.")


def slide_a8(prs):
    """A3: IS Component Correlation."""
    slide = new_slide(prs)
    add_title(slide, "A3: IS Component Correlation")
    add_accent_line(slide)

    # Dimension table
    add_text(slide, "The 6 IS signals collapse into 3 independent dimensions:",
             MX, CT, CW, Inches(0.4), size=Pt(14), color=WHITE)

    tbl1 = add_table(slide,
        ["Dimension", "Signals", "Variance", "Inter-signal r"],
        [["Word Accuracy", "WER, WWER, Phonetic", "60.0%", "> 0.79"],
         ["Meaning Preservation", "Semantic", "28.5%", "independent"],
         ["Output Sanity", "Length Ratio", "9.1%", "independent"]],
        MX, CT + Inches(0.5), CW * 0.55, text_size=Pt(11))

    # Cross-config stability
    add_text(slide, "Cross-Config Stability (16 configs)",
             SRL, CT, SRW, Inches(0.4), size=Pt(14), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["Signal", "Stability", "Std"],
        [["Semantic", "Stable", "0.017"],
         ["Phonetic", "Stable", "0.059"],
         ["NEA", "Stable", "0.023"],
         ["WER", "Volatile", "0.165"],
         ["Length", "Volatile", "0.142"]],
        SRL, CT + Inches(0.5), SRW, text_size=Pt(11),
        row_colors={3: {1: CORAL}, 4: {1: CORAL},
                    0: {1: GREEN}, 1: {1: GREEN}, 2: {1: GREEN}})

    # Heuristic validation
    add_text(slide, "Heuristic Validation (no runtime LLM)",
             SRL, CT + Inches(3.2), SRW, Inches(0.3),
             size=Pt(13), color=TEAL, bold=True)

    tbl3 = add_table(slide,
        ["Metric", "Value"],
        [["Mean r", "0.925 (std 0.015)"],
         ["Agreement", "88.6%"],
         ["Cohen's κ", "0.773"],
         ["Recall (IS≥3)", "97.6–100%"],
         ["Config range", "κ 0.62–0.86"]],
        SRL, CT + Inches(3.6), SRW * 0.7, text_size=Pt(10))

    _finish(slide, "A3",
        "IS components collapse into 3 dimensions: word accuracy (60%), "
        "meaning (28%), output sanity (9%). Cross-config: Semantic, Phonetic, "
        "NEA are stable; WER and Length Ratio are volatile. Heuristic: "
        "r=0.925, agreement 88.6%, kappa 0.773.")


def slide_a11(prs):
    """A4: LLM Salvage — Recoverable Segments."""
    slide = new_slide(prs)
    add_title(slide, "A4: LLM Salvage — Recoverable Segments")
    add_accent_line(slide)

    # Key numbers
    add_text(slide, "Key Numbers", MX, CT, SLW, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    tbl1 = add_table(slide,
        ["Metric", "Value"],
        [["Metric-failed segments", "900"],
         ["LLM-recoverable", "165 (18.3%)"],
         ["Metric capture (IS ≥ 3.0)", "39.9%"],
         ["Effective capture", "50.9%"],
         ["Uplift", "+11.0pp (+27.6% rel.)"]],
        MX, CT + Inches(0.4), SLW, text_size=Pt(11),
        row_colors={1: {1: TEAL}, 3: {1: TEAL}})

    add_text(slide, "58% of salvageable have moderate WER (50–70%).\n"
             "Decision tree: 15 rules, r=0.934 with IS.",
             MX, CT + Inches(2.8), SLW, Inches(0.6),
             size=Pt(11), color=LGRAY)

    # Recovery categories
    add_text(slide, "6 Recovery Categories", SRL, CT, SRW, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["Category", "N", "Key Signal"],
        [["Hidden Gems", "54", "LLM prob ≥ 0.8"],
         ["Semantic Pres.", "57", "Semantic ≥ 0.5"],
         ["Phonetic Bridge", "93", "Phonetic ≥ 0.6"],
         ["Entity-Preserved", "44", "NEA F1 ≥ 50%"],
         ["Structure Match", "74", "Word order intact"],
         ["WER Over-Punish.", "27", "WER−WWER ≥ 10pp"]],
        SRL, CT + Inches(0.4), SRW, text_size=Pt(11))

    add_text(slide, "Categories overlap — segments can exhibit multiple "
             "recovery signals. System delivers useful output for 1 in 2 segments.",
             SRL, CT + Inches(3.2), SRW, Inches(0.5),
             size=Pt(11), color=LGRAY, italic=True)

    _finish(slide, "A4",
        "165 of 900 metric-failed segments are recoverable by the LLM "
        "heuristic. Effective capture rises from 39.9% to 50.9%. "
        "6 recovery categories (overlap, not disjoint). "
        "58% have moderate WER (50-70%).")


def slide_a11b(prs):
    """A5: LLM Salvage — Curated Examples."""
    slide = new_slide(prs)
    add_title(slide, "A5: LLM Salvage — Curated Examples")
    add_accent_line(slide)

    add_text(slide, "One real example per recovery category — all IS < 3.0 "
             '(metrics say "failed") but heuristic says recoverable:',
             MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY)

    tbl = add_table(slide,
        ["Category", "Reference (excerpt)", "Hypothesis (excerpt)",
         "WER", "IS", "LLM"],
        [["Hidden Gem",
          "...opinions about reason and logic and all these other concepts...",
          "...our opinion is about reasoning and logic and all these...",
          "74%", "2.92", "0.90"],
         ["Semantic Pres.",
          "india china afghanistan...both sides would benefit",
          "middle east and afghanistan...both sides will benefit",
          "72%", "2.86", "0.90"],
         ["Phonetic Bridge",
          "expresses in concrete and symbolic and beautifully real deep",
          "suppresses the concrete and the symbolic and the beautiful...",
          "89%", "2.75", "0.90"],
         ["Entity-Preserved",
          "how facebook is a media company...what's about twitter",
          "how facebook is a media company on switzerland",
          "57%", "2.86", "0.90"],
         ["Structure Match",
          "neptune gives us a long time to learn...energies and wisdom...",
          "you give it a long time to learn...energies and wisdom...",
          "39%", "2.94", "0.95"],
         ["WER Over-Punish.",
          "so um",
          "so i kind of",
          "150%", "2.06", "0.65"]],
        MX, CT + Inches(0.6), CW, text_size=Pt(9),
        row_height=Inches(0.45))

    _finish(slide, "A5",
        "Curated examples showing each of the 6 recovery categories. "
        "All have IS < 3.0 but the heuristic identifies recoverable meaning. "
        "Categories overlap: a segment can exhibit multiple recovery signals.")


def slide_a13(prs):
    """A6: Failure Mode Examples."""
    slide = new_slide(prs)
    add_title(slide, "A6: Failure Mode Examples")
    add_accent_line(slide)

    add_text(slide, "One real example per failure category (5 categories):",
             MX, CT, CW, Inches(0.3), size=Pt(13), color=LGRAY)

    tbl = add_table(slide,
        ["Mode", "Reference", "Hypothesis", "WER", "IS"],
        [["Empty Output",
          '"do you say i wonder what..."',
          "(empty)", "100%", "0.00"],
         ["Hallucination",
          '"and body parts"',
          '"20 years ago when i was"', "200%", "0.00"],
         ["Truncation",
          '"i don\'t want to say mistakes but i will say..."',
          '"i don\'t want to seem disrespectful"', "69%", "1.26"],
         ["Topic Drift",
          '"i\'ve made lots of videos..."',
          '"when i was a little girl..."', "97%", "0.38"],
         ["Entity Destruction",
          '"china to take off to cross the pacific ocean..."',
          '"i don\'t think that\'s a good idea"', "100%", "0.72"],
         ["Phonetic Wrong Topic",
          '"they have something like..."',
          '"some english for you all..."', "100%", "0.94"],
         ["High Error Rate",
          '"today here the three in one..."',
          '"i\'m so happy to be here..."', "100%", "1.13"],
         ["Accum. Small Errors",
          '"you\'re rich no no no..."',
          '"your ring that\'s not what..."', "67%", "1.64"],
         ["Content Word Errors",
          '"even after the insurance..."',
          '"after the initial contamination"', "60%", "1.86"],
         ["Over-generation",
          '"to the next level"',
          '"to the next level and they..."', "100%", "2.32"]],
        MX, CT + Inches(0.4), CW, text_size=Pt(9),
        row_height=Inches(0.42),
        row_colors={0: {4: CORAL}, 1: {4: CORAL}, 3: {4: CORAL},
                    4: {4: CORAL}, 5: {4: CORAL}})

    _finish(slide, "A6",
        "5 failure categories with real examples from the 1,497-segment "
        "baseline. Wrong Topic is the largest (31.6%). Hallucination is the "
        "most dangerous — fluent but completely fabricated text.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE 14b — CURATED EXAMPLES VIDEO GALLERY
# ═══════════════════════════════════════════════════════════════════════

def slide_14b(prs):
    """14b: 2×4 clickable video grid matching Slide 14 curated examples."""
    slide = new_slide(prs)
    add_title(slide, "Curated Examples — Video Gallery")
    add_accent_line(slide)

    add_text(slide, "Click any thumbnail to play (PowerPoint / compatible viewer):",
             MX, CT, CW, Inches(0.35), size=Pt(13), color=LGRAY)

    # Grid layout: 4 cols × 2 rows
    vid_w  = Inches(2.82)
    vid_h  = Inches(1.58)   # 16:9
    gap_x  = Inches(0.23)
    gap_y  = Inches(0.55)   # space for label below each video
    row_y  = [CT + Inches(0.45), CT + Inches(0.45) + vid_h + gap_y]
    start_x = MX

    rows = [
        [("perfect",      "Perfect",     "0%",   GREEN),
         ("nearmiss",     "Near-Miss",   "58%",  YELLOW),
         ("halluc",       "Hallucin.",   "100%", RED),
         ("tuning_fix",   "Tuning Fix\n(baseline: empty)",  "73%",  ORANGE)],
        [("topic_drift",  "Topic Drift", "97%",  RED),
         ("salvage",      "Salvage",     "74%",  YELLOW),
         ("entity_success","Entity OK",  "31%",  GREEN),
         ("entity_destroy","Entity Lost","100%", RED)],
    ]

    for r, row in enumerate(rows):
        for c, (key, label, wer, color) in enumerate(row):
            x = start_x + c * (vid_w + gap_x)
            y = row_y[r]
            add_video(slide, key, x, y, vid_w, vid_h)
            # WER badge
            add_text(slide, f"{label}  WER {wer}",
                     x, y + vid_h + Inches(0.04), vid_w, Inches(0.32),
                     size=Pt(9), color=color, bold=False,
                     align=PP_ALIGN.CENTER)

    _finish(slide, "14b",
        "8 videos matching the curated examples on Slide 14. "
        "Row 1: Perfect transcription, near-miss (probiotics→permafrost), "
        "full hallucination, Config J tuning fix (empty→output). "
        "Row 2: Topic drift (#1 failure), salvage hidden gem, entity preserved "
        "despite wrong numbers, entity completely destroyed. Click each to play.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE A15 — VIDEO GALLERY MAP
# ═══════════════════════════════════════════════════════════════════════

def slide_a15(prs):
    """A7: Reference table of all 34 example segments across the presentation."""
    slide = new_slide(prs)
    add_title(slide, "A7: Video Gallery — All Example Segments")
    add_accent_line(slide)

    add_text(slide, "★ = video embedded on a slide   ─ = available in burned_videos/ only",
             MX, CT, CW, Inches(0.32), size=Pt(11), color=LGRAY, italic=True)

    col_w = [Inches(2.1), Inches(1.7), Inches(0.8), Inches(0.7), Inches(0.5)]
    headers = ["Segment ID", "Category", "Slide", "WER", ""]

    left_rows = [
        # Curated Examples
        ["IEa7qEkMvfQ_3",  "Perfect",         "14",    "0%",   "★"],
        ["-WQZsfHcPDM_7",  "Near-Miss",       "14",    "58%",  "★"],
        ["00MUdHQ7GGY_8",  "Hallucination",   "14",    "100%", "★"],
        ["DBhaa45mAro_2",  "Tuning Fix",      "14",    "73%",  "★"],
        ["vBCnI4kf3-E_0",  "Topic Drift",     "14/A6", "97%",  "★"],
        ["Q8aPjew1aUU_5",  "Salvage",         "14/A5", "74%",  "★"],
        ["d8BR6hsvzoY_31", "Perfect Short",   "15",    "0%",   "★"],
        # LLM Salvage
        ["WTSIAfzvYUU_0",  "Semantic Pres.",  "A5",    "72%",  "─"],
        ["cT6aHJmM4cA_2",  "Phonetic Bridge", "A5",    "89%",  "★"],
        ["cECxDMkqVcs_0",  "Entity-Pres.",    "A5",    "57%",  "─"],
        ["IZcKDz911X8_0",  "Structure Match", "A5",    "39%",  "─"],
        ["0FUlRjBcGGE_21", "WER Over-Pun.",   "A5",    "150%", "★"],
        # Success Patterns
        ["FLRU5qzb6hc_9",  "Near-Perfect",    "A12",   "0%",   "─"],
        ["BVynmQr3cf8_0",  "Minor Errors",    "A12",   "11%",  "─"],
        ["LiYzBldkxMc_2",  "Phonetic Pres.",  "A12",   "27%",  "─"],
        ["epuNSCr7qpA_16", "Good Sem+Len",    "A12",   "15%",  "─"],
        ["BS4kTgaiydQ_0",  "Entity Preserved","A12",   "31%",  "★"],
    ]

    right_rows = [
        ["HecEY5bF-xs_5",  "Low-Mod WER",     "A12",   "15%",  "─"],
        ["c6eBrYor21I_10",  "Sem+Phonetic",    "A12",   "52%",  "─"],
        # Failure Modes
        ["1RkFwRhhcWQ_0",  "Empty Output",    "A6",    "100%", "─"],
        ["BmmJujNQvXw_0",  "Extreme Halluc.", "A6",    "200%", "★"],
        ["0fmc81KXbB0_0",  "Truncation",      "A6",    "69%",  "─"],
        ["EMfcKvHA5Uc_0",  "Entity Destruct.","A6",    "100%", "★"],
        ["2JuBrr6TW8o_14", "Phonetic Wrong",  "A6",    "100%", "─"],
        ["ZnoJxsXKULY_0",  "High Error Rate", "A6",    "100%", "─"],
        ["49qxSMt4Xe0_0",  "Accum. Errors",   "A6",    "68%",  "─"],
        ["xITCbZxwLn4_0",  "Content Errors",  "A6",    "60%",  "─"],
        ["KcDqXon7I3c_0",  "Over-generation", "A6",    "100%", "─"],
        # Metric Mismatch
        ["10xhJGx6-kc_0",  "WER>>WWER",       "A14b",  "71%",  "─"],
        ["-WqvFSuRYo0_12", "WWER>>WER",       "A14b",  "27%",  "─"],
        ["1whXJLCrTjY_0",  "Hi Sem+Hi WER",   "A14b",  "67%",  "─"],
        ["ZB21bsGO0KA_7",  "Lo Sem+Lo WER",   "A14b",  "40%",  "─"],
        ["2T-C7vQJBis_0",  "Hi NEA+WWER",     "A14b",  "42%",  "─"],
        ["0PQonSiGkVE_0",  "LR>1.5+WER",      "A14b",  "140%", "─"],
    ]

    half = Inches(5.9)
    gap  = Inches(0.33)

    tbl_l = add_table(slide, headers, left_rows,
                      MX, CT + Inches(0.38), half,
                      row_height=Inches(0.28), text_size=Pt(8),
                      col_widths=[Inches(1.85), Inches(1.5), Inches(0.7),
                                  Inches(0.6), Inches(0.45)])

    tbl_r = add_table(slide, headers, right_rows,
                      MX + half + gap, CT + Inches(0.38), half,
                      row_height=Inches(0.28), text_size=Pt(8),
                      col_widths=[Inches(1.85), Inches(1.5), Inches(0.7),
                                  Inches(0.6), Inches(0.45)])

    _finish(slide, "A7",
        "Reference map of all 34 unique example segments used across the "
        "presentation. 12 are embedded as clickable videos on Slides 14b and A11b. "
        "All 1,497 burned videos are available at "
        "english_full_results/client_outputs/burned_videos/. "
        "Segment IDs map directly to filenames: {id}_with_hyp.mp4.")


# ═══════════════════════════════════════════════════════════════════════
# NEW SLIDES — DEEP DIVES, CONTEXT, ENGINEERING, APPENDIX
# ═══════════════════════════════════════════════════════════════════════

def slide_visemes(prs):
    """Fundamental viseme challenge — why lip reading is hard."""
    slide = new_slide(prs)
    add_title(slide, "The Invisible Problem: Visemes")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — The problem
    lt = add_text(slide, "The Invisible Problem", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("50\u201370% of English sounds are invisible on lips", {"bold": True}),
        "Multiple sounds produce identical mouth shapes (visemes)",
        "Context is the ONLY disambiguation signal",
    ], MX, CT + Inches(0.5), col_w, Inches(1.5), size=Pt(15))

    # Viseme table
    tbl1 = add_table(slide,
        ["Viseme Group", "Sounds"],
        [["Bilabial", "p, b, m"],
         ["Alveolar", "t, d, n, s, z, l"],
         ["Velar", "k, g, ng"],
         ["Labiodental", "f, v"]],
        MX, CT + Inches(2.3), col_w, text_size=Pt(12))

    # Right column — Visual proof + confusable pairs
    rx = MX + col_w + gap
    rt = add_text(slide, "Same Mouth Shape, Different Words", rx, CT, col_w,
                  Inches(0.4), size=Pt(18), color=TEAL, bold=True)

    # Poster frames side by side — two speakers saying different words
    poster_shapes = []
    poster_w = Inches(2.5)
    poster_h = Inches(1.6)
    p1_path = POSTER_DIR / "ok_demo.jpg"
    p2_path = POSTER_DIR / "salvage.jpg"
    if p1_path.exists():
        poster_shapes.append(slide.shapes.add_picture(
            str(p1_path), rx, CT + Inches(0.5), width=poster_w, height=poster_h))
    if p2_path.exists():
        poster_shapes.append(slide.shapes.add_picture(
            str(p2_path), rx + poster_w + Inches(0.3), CT + Inches(0.5),
            width=poster_w, height=poster_h))
    poster_shapes.append(add_text(slide,
        "Different words \u2014 nearly identical mouth shape to the camera",
        rx, CT + Inches(2.2), col_w, Inches(0.3),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER))

    tbl2 = add_table(slide,
        ["Word A", "Word B", "Viseme"],
        [["pat", "bat", "Bilabial"],
         ["mom", "bomb", "Bilabial"],
         ["admiral", "animal", "Alveolar"],
         ["collar", "color", "Velar"]],
        rx, CT + Inches(2.7), col_w, text_size=Pt(12))

    # Bottom
    add_text(slide,
        "Context is the ONLY disambiguation signal \u2014 this is why the LLM matters.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(14), color=TEAL, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "50-70% of English sounds are invisible on lips. Multiple sounds produce "
        "identical mouth shapes called visemes. The poster frames show two "
        "different speakers — their mouth shapes look nearly identical despite "
        "saying completely different words. Context is the only disambiguation "
        "signal, which is why the LLM component is critical.",
        [[lt, lb, tbl1], poster_shapes + [rt, tbl2]], click_reveal=True)


def slide_data_flow(prs):
    """5-step pipeline data flow."""
    slide = new_slide(prs)
    add_title(slide, "How It Works: Data Flow")
    add_accent_line(slide)

    steps = [
        ("1", "Video Frames", "25 fps raw video input", TEAL),
        ("2", "Mouth Crop", "96\u00d796 pixel region around lips", TEAL),
        ("3", "Visual Features", "AV-HuBERT encoder \u2192 1024-dim vectors", TEAL),
        ("4", "Projection", "Linear layer: 1024 \u2192 4096-dim (LLM input space)", CORAL),
        ("5", "LLM Generates Text", "LLaMA-2-7B decodes features into words", CORAL),
    ]

    step_w = Inches(10.5)
    step_h = Inches(0.75)
    start_y = CT + Inches(0.1)
    start_x = MX + Inches(0.8)

    step_shapes = []
    for i, (num, name, desc, color) in enumerate(steps):
        y = start_y + i * (step_h + Inches(0.15))
        r = add_rect(slide, start_x, y, step_w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)

        # Step number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, start_x - Inches(0.7), y + Inches(0.1),
            Inches(0.55), Inches(0.55))
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()
        add_text(slide, num, start_x - Inches(0.7), y + Inches(0.1),
                 Inches(0.55), Inches(0.55),
                 size=Pt(20), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        add_rich_text(slide, [
            [(name, {"size": Pt(16), "color": WHITE, "bold": True}),
             (f"  \u2014  {desc}", {"size": Pt(13), "color": LGRAY})],
        ], start_x + Inches(0.2), y + Inches(0.1),
           step_w - Inches(0.4), step_h - Inches(0.2))

        # Arrow between steps
        if i < len(steps) - 1:
            add_text(slide, "\u2193", start_x + step_w / 2 - Inches(0.2),
                     y + step_h - Inches(0.05), Inches(0.4), Inches(0.3),
                     size=Pt(16), color=TEAL, align=PP_ALIGN.CENTER)

        step_shapes.append(r)

    add_text(slide,
        "Visual encoder is frozen (pre-trained on LRS3). Only projection + LoRA adapters are trained.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Five-step data flow. Raw video at 25fps is cropped to 96x96 mouth "
        "region. AV-HuBERT extracts 1024-dim visual features. Linear projection "
        "maps to 4096-dim LLM input space. LLaMA-2-7B generates text. The visual "
        "encoder is frozen — only the projection layer and LoRA adapters are trained.",
        [step_shapes])


def slide_eval_dataset(prs):
    """Our 1,497-segment evaluation dataset."""
    slide = new_slide(prs)
    add_title(slide, "Our Evaluation: 1,497 Real-World Segments")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — big number + bullets
    s1 = add_text(slide, "1,497", MX, CT, col_w, Inches(1.0),
                  size=Pt(64), color=TEAL, bold=True)
    s2 = add_text(slide, "segments from diverse YouTube videos",
                  MX, CT + Inches(1.0), col_w, Inches(0.4),
                  size=Pt(16), color=WHITE)
    s3 = add_bullets(slide, [
        "Uncontrolled lighting, angles, occlusions",
        "Multiple speakers and accents",
        "Diverse topics: business to DIY to gaming",
        ("Not a curated benchmark \u2014 real-world difficulty", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.5), size=Pt(14))

    # Right — topic categories table
    rx = MX + col_w + gap
    add_text(slide, "Topic Distribution", rx, CT, col_w, Inches(0.4),
             size=Pt(17), color=CORAL, bold=True)

    tbl = add_table(slide,
        ["Topic", "Segments", "Quality*"],
        [["Business/Finance", "214", "3.08"],
         ["Education/Lecture", "312", "2.63"],
         ["Entertainment", "198", "2.51"],
         ["News/Politics", "267", "2.48"],
         ["Tech/Science", "186", "2.43"],
         ["Sports/Health", "153", "2.38"],
         ["DIY/Home", "167", "2.13"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {2: GREEN}, 6: {2: CORAL}})

    # Footnote explaining Quality* column
    add_text(slide,
        "*Quality = our composite metric (0\u20135 scale), introduced in the next section.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(11), color=MGRAY, italic=True)

    _finish(slide, 0,
        "1,497 segments from diverse YouTube videos. Not a curated benchmark. "
        "Multiple topics, speakers, accents, lighting conditions. Business and "
        "Finance has the highest quality score (3.08) because it's closest to the "
        "TED talk training data. DIY/Home is worst (2.13) due to inherently visual "
        "content. The Quality column is our Intelligibility Score, introduced later.",
        [[s1, s2, s3], [tbl]], click_reveal=True)


def slide_wer_explained(prs):
    """WER formula and its limitations."""
    slide = new_slide(prs)
    add_title(slide, "Word Error Rate: What It Measures (and Misses)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — formula + example
    lt = add_text(slide, "The Formula", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    add_text(slide, "WER = (S + D + I) / N",
             MX + Inches(0.3), CT + Inches(0.55), col_w - Inches(0.6), Inches(0.5),
             size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "S = substitutions (wrong word)",
        "D = deletions (missing word)",
        "I = insertions (extra word)",
        "N = total words in reference",
    ], MX, CT + Inches(1.2), col_w, Inches(1.5), size=Pt(14))

    add_text(slide, "Example:", MX, CT + Inches(2.8), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_text(slide, 'Ref: "the admiral gave orders"\n'
                    'Hyp: "the animal gave water"\n'
                    'WER = 2/4 = 50% (2 substitutions)',
             MX + Inches(0.2), CT + Inches(3.2), col_w - Inches(0.4), Inches(1.2),
             size=Pt(13), color=WHITE)

    # Right — what it captures vs misses
    rx = MX + col_w + gap
    rt = add_text(slide, "What WER Captures", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=GREEN, bold=True)
    rb1 = add_bullets(slide, [
        "Exact word-level accuracy",
        "Simple, widely understood",
        "Standard in ASR research",
    ], rx, CT + Inches(0.5), col_w, Inches(1.2), size=Pt(14), bullet_color=GREEN)

    rm = add_text(slide, "What WER Misses", rx, CT + Inches(2.0), col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    rb2 = add_bullets(slide, [
        ("All errors weighted equally", {"color": CORAL}),
        ('"admiral"\u2192"animal" = "the"\u2192"a"', {"color": CORAL}),
        "No meaning preservation signal",
        "No phonetic similarity credit",
        ("Can exceed 100% (insertions)", {"color": CORAL}),
    ], rx, CT + Inches(2.5), col_w, Inches(2.5), size=Pt(14), bullet_color=CORAL)

    _finish(slide, 0,
        "WER formula: substitutions plus deletions plus insertions divided by "
        "reference word count. Simple and standard, but treats all errors equally. "
        "Admiral-to-animal gets the same penalty as the-to-a. No credit for "
        "meaning preservation or phonetic similarity. Can exceed 100% when the "
        "model generates extra words (insertions).",
        [[lt], [rt], [rb1], [rm], [rb2]], click_reveal=True)


def slide_design_philosophy(prs):
    """Deterministic evaluation — not runtime AI."""
    slide = new_slide(prs)
    add_title(slide, "Design Philosophy: Deterministic, Not AI")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — Option A
    lt = add_text(slide, "Option A: LLM per Sample", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(3.5),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_bullets(slide, [
        "Call Claude/GPT for every ref+hyp pair",
        "$$$ per evaluation run",
        "Non-deterministic (varies between runs)",
        "Can't reproduce results",
        "Slow: minutes per 1,497 pairs",
    ], MX + Inches(0.2), CT + Inches(0.7), col_w - Inches(0.4), Inches(2.5),
       size=Pt(14), bullet_color=CORAL)

    # Right — Option B (ours)
    rx = MX + col_w + gap
    rt = add_text(slide, "Option B: Design-Time LLM (Ours)", rx, CT, col_w,
                  Inches(0.4), size=Pt(18), color=GREEN, bold=True)
    r2 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(3.5),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_bullets(slide, [
        ("Rubric, signals, weights designed at development time",
         {"bold": True}),
        "Distilled into deterministic Python formulas",
        ("$0 per evaluation run", {"color": GREEN}),
        ("100% reproducible", {"color": GREEN}),
        "Instant: seconds for 1,497 pairs",
        ("Same framework, unlimited runs", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(0.7), col_w - Inches(0.4), Inches(2.5),
       size=Pt(14), bullet_color=GREEN)

    # Bottom
    add_text(slide,
        "Validated: 88.6% agreement with IS \u2265 3.0 threshold, r = 0.85 "
        "Pearson correlation with LLM judge gold standard.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Two approaches: Option A calls an LLM for every pair — expensive, "
        "non-deterministic, slow. Option B (ours): the entire "
        "evaluation framework was designed at development time, then distilled into "
        "deterministic formulas. Zero cost per run, 100% reproducible. "
        "Validated at 88.6% agreement, r=0.85.",
        [[r1], [r2]], click_reveal=True)


def slide_is_dimensions(prs):
    """Three quality dimensions from PCA analysis."""
    slide = new_slide(prs)
    add_title(slide, "Three Dimensions of Quality")
    add_accent_line(slide)

    add_text(slide, "PCA reveals the 6 IS signals collapse into 3 independent dimensions:",
             MX, CT, CW, Inches(0.4), size=Pt(15), color=LGRAY)

    # Three cards
    dims = [
        ("Word Accuracy", "60%", "of IS variance",
         "WER + WWER + Phonetic\n(r > 0.79 between them)",
         "The visual encoder\u2019s core capability", TEAL),
        ("Meaning Preservation", "29%", "of IS variance",
         "Semantic similarity\n(sentence embeddings)",
         "Tiebreaker between\nsimilar-accuracy segments", GREEN),
        ("Output Sanity", "9%", "of IS variance",
         "Length ratio\n(hyp vs ref word count)",
         "Catches hallucination\nand truncation", LGRAY),
    ]

    cw_card = Inches(3.6)
    ch_card = Inches(4.0)
    gap = Inches(0.5)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.55)

    card_shapes = []
    for i, (name, pct, label, signals, insight, color) in enumerate(dims):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5), corner_radius=True)

        # Big percentage
        add_text(slide, pct, x + Inches(0.2), cy + Inches(0.2),
                 cw_card - Inches(0.4), Inches(0.6),
                 size=Pt(36), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, label, x + Inches(0.2), cy + Inches(0.8),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

        # Name
        add_text(slide, name, x + Inches(0.2), cy + Inches(1.3),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(16), color=color, bold=True, align=PP_ALIGN.CENTER)

        # Signals
        add_text(slide, signals, x + Inches(0.2), cy + Inches(1.8),
                 cw_card - Inches(0.4), Inches(0.8),
                 size=Pt(13), color=WHITE, align=PP_ALIGN.CENTER)

        # Insight
        add_text(slide, insight, x + Inches(0.2), cy + Inches(2.8),
                 cw_card - Inches(0.4), Inches(0.8),
                 size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

        card_shapes.append(r)

    _finish(slide, 0,
        "PCA analysis reveals three independent dimensions. Word Accuracy "
        "(60% of variance) combines WER, WWER, and Phonetic \u2014 they all measure "
        "the same thing: visual encoder quality. Meaning Preservation (29%) is "
        "the semantic similarity tiebreaker. Output Sanity (9%) is mostly length "
        "ratio. Four of six signals are redundant \u2014 but deliberate: cross-"
        "validation makes the metric robust.\n\n"
        "CORRELATION BETWEEN DIMENSIONS: Word accuracy signals (WER, WWER, "
        "Phonetic) are highly correlated with each other (r > 0.79). Semantic "
        "is moderately correlated with word accuracy. Length ratio is the most "
        "independent dimension (9.1% of total variance). This confirms these "
        "are genuinely 3 independent dimensions, not redundant signals.",
        [[c] for c in card_shapes], click_reveal=True)


def slide_domain_mismatch(prs):
    """Full topic analysis — domain mismatch detail."""
    slide = new_slide(prs)
    add_title(slide, "Domain Mismatch: Training vs Reality")
    add_accent_line(slide)

    col_w = Inches(6.5)
    gap = Inches(0.6)

    # Left — topic table
    lt = add_text(slide, "Performance by Topic", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Topic", "IS", "Captured", "Judge N%"],
        [["Business/Finance", "3.08", "57%", "25%"],
         ["Education/Lecture", "2.63", "42%", "33%"],
         ["Entertainment", "2.51", "39%", "36%"],
         ["News/Politics", "2.48", "38%", "37%"],
         ["Tech/Science", "2.43", "36%", "39%"],
         ["Sports/Health", "2.38", "34%", "41%"],
         ["DIY/Home", "2.13", "30%", "52%"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {1: GREEN, 2: GREEN}, 6: {1: CORAL, 2: CORAL, 3: CORAL}})

    # Right — big number + insight
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    add_text(slide, "19%", rx, CT + Inches(0.3), rw, Inches(0.9),
             size=Pt(64), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "of segments show\ndomain vocabulary\nconfusion",
             rx, CT + Inches(1.2), rw, Inches(1.0),
             size=Pt(16), color=WHITE, align=PP_ALIGN.CENTER)

    add_bullets(slide, [
        "Model trained on TED talks (formal, educational)",
        ("Business content closest to training \u2192 best results",
         {"color": GREEN}),
        ("DIY content most visual, least verbal \u2192 worst results",
         {"color": CORAL}),
        "A topic label at decode time would help ~284 segments",
    ], rx, CT + Inches(2.5), rw, Inches(2.5), size=Pt(13))

    _finish(slide, 0,
        "Domain mismatch is a major factor. Business and Finance has IS 3.08 "
        "(57% captured) because it's closest to the TED talk training data. "
        "DIY/Home is worst at IS 2.13 (30% captured) — inherently visual content "
        "that doesn't translate to speech patterns. 19% of segments (~284) show "
        "domain vocabulary confusion where a topic label would help.\n\n"
        "WHY DOES A TOPIC LABEL HELP? The model was trained on general "
        "lip-reading data (TED talks) without topic context. When it encounters "
        "domain-specific vocabulary (medical, legal, technical), it hallucinates "
        "common words instead. A topic label (e.g., 'cooking', 'medicine') at "
        "decode time would constrain the vocabulary space, helping the LLM "
        "generate domain-appropriate words. The ~284 segments (19%) are those "
        "where the LLM judge identified domain vocabulary confusion as the "
        "primary error source.",
        [[lt, tbl], []], click_reveal=True)


def slide_decode_params(prs):
    """Decode parameter explanations — what the dials do."""
    slide = new_slide(prs)
    add_title(slide, "Decode Parameters: The Four Dials")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Four parameter blocks in two columns
    params = [
        ("Beam Size", "How many candidates to consider simultaneously",
         "Like checking multiple routes on a map",
         "5 \u2192 50 candidates", TEAL),
        ("Length Penalty", "Encourages longer or shorter outputs",
         "Positive = longer, negative = shorter, 0 = neutral",
         "\u22120.5 \u2192 2.0", CORAL),
        ("Temperature", "Controls randomness of word selection",
         "Low = conservative, high = creative",
         "0.3 \u2192 1.5", TEAL),
        ("Sampling", "Whether to pick the best or roll the dice",
         "Greedy (always best) vs nucleus (weighted random)",
         "greedy / nucleus p=0.9", CORAL),
    ]

    bw = Inches(5.5)
    bh = Inches(1.1)
    shapes = []
    for i, (name, desc, analogy, range_str, color) in enumerate(params):
        col = i % 2
        row = i // 2
        x = MX + col * (bw + gap)
        y = CT + row * (bh + Inches(0.25))

        r = add_rect(slide, x, y, bw, bh, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, name, x + Inches(0.2), y + Inches(0.08),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(15), color=color, bold=True)
        add_text(slide, desc, x + Inches(0.2), y + Inches(0.4),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(12), color=WHITE)
        add_text(slide, f"{analogy}  \u2022  Range: {range_str}",
                 x + Inches(0.2), y + Inches(0.72),
                 bw - Inches(0.4), Inches(0.3),
                 size=Pt(11), color=LGRAY, italic=True)
        shapes.append(r)

    # Bottom quote
    add_text(slide,
        '"Think of it like a stereo equalizer \u2014 you can adjust the dials, '
        'but the speakers determine the sound quality."',
        MX, Inches(5.8), CW, Inches(0.7),
        size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    add_text(slide,
        "13 experiments tested combinations across these 4 dimensions.",
        MX, Inches(6.5), CW, Inches(0.3),
        size=Pt(13), color=TEAL, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four decode parameters. Beam size: how many candidates. Length penalty: "
        "bias toward longer or shorter. Temperature: randomness. Sampling: greedy "
        "vs stochastic. Like a stereo equalizer — you can adjust the dials but "
        "the speakers (visual encoder) determine the sound quality.",
        [shapes])


def slide_is_deep_dive(prs):
    """IS correlation deep dive — signal relationships."""
    slide = new_slide(prs)
    add_title(slide, "Why These 6 Signals? A Validation")
    add_accent_line(slide)

    add_text(slide,
        "Three independent quality dimensions confirm IS captures distinct, "
        "complementary aspects of transcription quality \u2014 not arbitrary signals.",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    col_w = Inches(5.8)
    gap = Inches(0.53)
    offset = Inches(0.45)

    # Left — correlation table (larger)
    lt = add_text(slide, "Signal \u2192 IS Correlation", MX, CT + offset, col_w, Inches(0.4),
                  size=Pt(20), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Signal", "r with IS", "Weight", "Variance %"],
        [["Phonetic Sim", "0.943", "15%", "~18%"],
         ["Semantic Sim", "0.856", "25%", "28.5%"],
         ["Inv. WER", "0.834", "15%", "~16%"],
         ["Inv. WWER", "0.823", "15%", "~15%"],
         ["NEA F1", "0.748", "15%", "17.3%"],
         ["Length Ratio", "0.521", "15%", "9.1%"]],
        MX, CT + offset + Inches(0.5), col_w, text_size=Pt(14),
        row_height=Inches(0.5),
        row_colors={0: {1: GREEN}, 5: {1: CORAL, 3: CORAL}})

    # Right — key insights (larger text)
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Key Insights", rx, CT + offset, rw, Inches(0.4),
                  size=Pt(20), color=CORAL, bold=True)
    rb = add_bullets(slide, [
        ("Phonetic Sim is strongest predictor (r=0.943) "
         "despite only 15% weight", {"bold": True}),
        "WER/WWER/Phonetic are NOT independent \u2014 "
         "all measure visual encoder quality",
        "Semantic Sim (25%) drives 28.5% variance \u2014 "
         "the tiebreaker for similar-accuracy segments",
        ("NEA punches above weight: 17.3% variance "
         "\u2014 names are binary (right or wrong)",
         {"color": TEAL}),
        ("Length Ratio weakest (9.1%) \u2014 could "
         "reduce its weight in future", {"color": CORAL}),
        ("Expert heuristic: r=0.934 with IS", {"bold": True}),
    ], rx, CT + offset + Inches(0.5), rw, Inches(4.5), size=Pt(15))

    _finish(slide, 0,
        "Signal correlation analysis. Phonetic similarity is the strongest "
        "single predictor at r=0.943, despite only 15% weight. This makes "
        "sense: it's the most direct measure of visual encoder quality. "
        "Semantic similarity (25% weight) captures 28.5% of IS variance. "
        "Length ratio is weakest at 9.1%. The expert heuristic (15-rule "
        "decision tree) achieves r=0.934.",
        [[rt, rb], [lt, tbl]], click_reveal=True)


def slide_metric_disagreement(prs):
    """What metric disagreements reveal about transcription quality."""
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: What It Tells Us")
    add_accent_line(slide)

    add_text(slide,
        "IS uses 6 signals because no single metric tells the full story. "
        "Disagreements between metrics reveal specific quality patterns:",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    # Four disagreement pattern cards (2x2 grid)
    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("WWER \u226a WER", TEAL,
         "Function words wrong, content words right",
         "\"the team discussed a quarterly\" \u2192 \"team discuss quarterly\"\n"
         "WER 43% but WWER 15% — viewer gets the message.\n"
         "IS captures this: meaning preserved despite surface errors."),
        ("NEA high, WER high", GREEN,
         "Names preserved despite overall poor accuracy",
         "\"Dr. Chen presented the Q3 results\" \u2192 \"Dr. Chen present Q3 result\"\n"
         "WER 57% but NEA F1 = 100% — critical info intact.\n"
         "IS rewards: the most important facts came through."),
        ("Semantic high, WER high", GOLD,
         "Meaning preserved through paraphrasing",
         "\"we need to reduce spending\" \u2192 \"must cut the budget\"\n"
         "WER 100% but Semantic 0.87 — same meaning, different words.\n"
         "IS captures: WER says total failure, IS says useful output."),
        ("Phonetic high, Semantic low", CORAL,
         "Sounds right, wrong meaning (deceptive)",
         "\"the alliance was formed\" \u2192 \"the lions were found\"\n"
         "Phonetic 0.71 but Semantic 0.12 — sounds similar, wrong topic.\n"
         "IS catches: phonetic alone would miss this dangerous error."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        cards.append(r)
        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35))
        add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY)

    add_text(slide,
        "This is why IS uses 6 signals, not just WER — each disagreement pattern "
        "reveals a different type of quality that a single metric would miss.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four key metric disagreement patterns. WWER<<WER means function words "
        "are wrong but content preserved. High NEA + high WER means names survived. "
        "High semantic + high WER means paraphrasing. High phonetic + low semantic "
        "is the dangerous case — sounds right but wrong meaning.",
        [[c] for c in cards], click_reveal=True)

    # Hide slide
    slide._element.set('show', '0')


def slide_metric_disagreement_2(prs):
    """More metric disagreement patterns — part 2."""
    slide = new_slide(prs)
    add_title(slide, "When Metrics Disagree: More Patterns")
    add_accent_line(slide)

    add_text(slide,
        "Additional diagnostic patterns that reveal specific transcription behaviors:",
        MX, CT, CW, Inches(0.4), size=Pt(13), color=LGRAY, italic=True)

    cw = Inches(5.8)
    ch = Inches(2.0)
    gap_x = Inches(0.53)
    gap_y = Inches(0.2)
    cy = CT + Inches(0.55)

    patterns = [
        ("Length \u226a 1.0, all metrics low", CORAL,
         "Signal loss — model gave up or truncated",
         "Ref: \"the thirteenth amendment abolished slavery\"\n"
         "Hyp: \"the\" (length ratio 0.06)\n"
         "All signals collapse — nothing to evaluate."),
        ("Length \u226b 1.0, Semantic low", CORAL,
         "Hallucination — fluent fabrication",
         "Ref: \"carry strap\" → Hyp: 3 paragraphs about history\n"
         "WER 6,833%, length ratio 45\u00d7 — LLM ran unchecked.\n"
         "IS catches via length + semantic: fluent but fabricated."),
        ("NEA low, Semantic moderate", GOLD,
         "Topic right, entities destroyed",
         "\"the 13th amendment\" → \"the important decision\"\n"
         "Semantic 0.52 but NEA F1 = 0% — gist right, facts lost.\n"
         "IS penalizes: critical info (names, numbers) irrecoverable."),
        ("All metrics moderate (~0.5)", TEAL,
         "Accumulated small errors — death by a thousand cuts",
         "Every signal is mediocre, none catastrophic.\n"
         "WER 55%, Semantic 0.48, Phonetic 0.51, NEA 40%.\n"
         "IS: ~2.5 (borderline) — individually OK, collectively degraded."),
    ]

    cards = []
    for i, (title, color, subtitle, body) in enumerate(patterns):
        col = i % 2
        row = i // 2
        x = MX + col * (cw + gap_x)
        y = cy + row * (ch + gap_y)
        r = add_rect(slide, x, y, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        cards.append(r)
        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": color, "bold": True}),
             (f"  —  {subtitle}", {"size": Pt(12), "color": WHITE})],
        ], x + Inches(0.2), y + Inches(0.1), cw - Inches(0.4), Inches(0.35))
        add_text(slide, body, x + Inches(0.2), y + Inches(0.5),
                 cw - Inches(0.4), ch - Inches(0.6),
                 size=Pt(11), color=LGRAY)

    add_text(slide,
        "8 total diagnostic patterns — IS decomposes quality into actionable signals "
        "that each point to a different engineering fix.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(12), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Four more metric disagreement patterns. Length collapse = signal loss. "
        "Length explosion + low semantic = hallucination. Low NEA + moderate semantic = "
        "entity destruction. All-moderate = accumulated errors.",
        [[c] for c in cards], click_reveal=True)

    # Hide slide
    slide._element.set('show', '0')


def slide_two_eval_systems(prs):
    """Two evaluation systems — IS and expert heuristic."""
    slide = new_slide(prs)
    add_title(slide, "Two Evaluation Systems, One Framework")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — IS (strict) + Expert Heuristic (generous)
    lt = add_text(slide, "The Two Systems", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    # IS card
    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Intelligibility Score (IS)", MX + Inches(0.2),
             CT + Inches(0.6), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    add_bullets(slide, [
        "Strict metric: composite 0\u20135 score",
        ("IS \u2265 3.0 = Captured: 39.9% (597/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(13))

    # Expert heuristic card
    r2 = add_rect(slide, MX, CT + Inches(2.3), col_w, Inches(1.6),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Expert Heuristic (LLM Salvage)", MX + Inches(0.2),
             CT + Inches(2.4), col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=GREEN, bold=True)
    add_bullets(slide, [
        "Generous: identifies recoverable segments",
        ("IS < 3.0 but salvageable: 50.9% (762/1,497)", {"bold": True}),
    ], MX + Inches(0.2), CT + Inches(2.8), col_w - Inches(0.4), Inches(0.8),
       size=Pt(13))

    # Right — agreement + worked example
    rx = MX + col_w + gap
    rt = add_text(slide, "Agreement Between Systems", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    tbl = add_table(slide,
        ["Metric", "Value"],
        [["Pearson r", "0.934"],
         ["Agreement at IS \u2265 3.0", "88.6%"],
         ["Cohen's \u03ba", "0.773"],
         ["Recall (Heuristic)", "99.2%"],
         ["Cross-config mean r", "0.925"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12))

    # Worked example
    add_text(slide, "Worked Example:", rx, CT + Inches(2.8), col_w, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)
    add_text(slide,
        'Ref: "opinions about reason and logic"\n'
        'Hyp: "our opinion is about reasoning and logic"\n'
        'WER: 74% \u2022 IS: 2.92 (failed) \u2022 LLM prob: 0.90 (salvaged)\n'
        'Meaning preserved despite word differences.',
        rx, CT + Inches(3.2), col_w, Inches(1.5),
        size=Pt(12), color=WHITE)

    _finish(slide, 0,
        "Two evaluation systems. IS is strict: 39.9% pass at IS >= 3.0. "
        "The expert heuristic is generous: identifies 165 additional segments, "
        "raising effective capture to 50.9%. They agree 88.6% of the time "
        "(r=0.934, kappa=0.773). The heuristic catches meaning preservation "
        "that strict metrics miss.",
        [[r1, r2], [rt, tbl]], click_reveal=True)


def slide_llm_judge(prs):
    """LLM-as-a-Judge gold standard evaluation."""
    slide = new_slide(prs)
    add_title(slide, "LLM-as-a-Judge: Gold Standard (1,497 Pairs)")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — protocol + results
    lt = add_text(slide, "Protocol", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Claude Opus evaluated all 1,497 ref+hyp pairs",
        "Blind (no topic context), 3-level: Y / P / N",
        "30 duplicate pairs for intra-rater reliability",
        ("Intra-rater: 86.7% exact agreement", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(1.8), size=Pt(13))

    # Results table
    res_t = add_text(slide, "Results (Blind)", MX, CT + Inches(2.4), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Count", "%"],
        [["Y (fully preserved)", "345", "23.0%"],
         ["P (partially)", "626", "41.8%"],
         ["N (not preserved)", "526", "35.1%"],
         ["Y+P (any useful)", "971", "64.9%"]],
        MX, CT + Inches(2.8), col_w, text_size=Pt(12),
        row_colors={0: {2: GREEN}, 2: {2: CORAL}, 3: {2: TEAL}})

    # Right — IS correlation
    rx = MX + col_w + gap
    rt = add_text(slide, "Correlation with IS", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    add_text(slide, "r = 0.85", rx, CT + Inches(0.6), col_w, Inches(0.7),
             size=Pt(36), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Pearson correlation (IS \u2194 LLM Judge)",
             rx, CT + Inches(1.2), col_w, Inches(0.3),
             size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)

    # Tier summary
    add_text(slide, "LLM Judge \u00d7 IS Tier", rx, CT + Inches(1.8), col_w,
             Inches(0.3), size=Pt(15), color=TEAL, bold=True)

    tbl2 = add_table(slide,
        ["IS Tier", "Y%", "P%", "N%"],
        [["5 (Excellent)", "57%", "38%", "5%"],
         ["4 (Good)", "21%", "59%", "20%"],
         ["3 (Fair)", "8%", "51%", "41%"],
         ["2 (Poor)", "4%", "34%", "62%"],
         ["1 (Failed)", "2%", "17%", "81%"]],
        rx, CT + Inches(2.2), col_w, text_size=Pt(11),
        row_colors={0: {1: GREEN}, 4: {3: CORAL}})

    # Key takeaway
    add_text(slide,
        "LLM judge is more conservative for full success (23% vs IS 40%) "
        "but more generous for any useful output (Y+P=65%).",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "LLM-as-a-Judge gold standard. Claude Opus evaluated all 1,497 pairs "
        "blind. Y=23.0% (345), P=41.8% (626), N=35.1% (526). Y+P=64.9% — "
        "the LLM says nearly 2 in 3 segments have useful output. Intra-rater "
        "reliability 86.7%. Correlation with IS: r=0.85 (Pearson 0.8495).",
        [[lt, lb, res_t, tbl], [rt, tbl2]], click_reveal=True)


def slide_context_eval(prs):
    """Context-aware re-evaluation results."""
    slide = new_slide(prs)
    add_title(slide, "Context Makes the Judge Stricter, Not Lenient")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — comparison table
    lt = add_text(slide, "Blind vs Context-Aware", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Verdict", "Blind", "Context", "\u0394"],
        [["Y (fully preserved)", "23.0% (345)", "15.0% (225)", "\u22128.0pp"],
         ["P (partially)", "41.8% (626)", "47.1% (705)", "+5.3pp"],
         ["N (not preserved)", "35.1% (526)", "37.9% (567)", "+2.8pp"],
         ["Y+P (useful)", "64.9% (971)", "62.1% (930)", "\u22122.7pp"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(11),
        col_widths=[Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.0)],
        row_colors={0: {3: CORAL}, 3: {3: CORAL}})

    add_text(slide,
        "Context reveals vocabulary failures that blind evaluation misses.",
        MX, CT + Inches(2.4), col_w, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True)

    # Key finding
    kf_t = add_text(slide, "Key Finding:", MX, CT + Inches(3.0), col_w, Inches(0.3),
             size=Pt(15), color=CORAL, bold=True)
    kf_b = add_bullets(slide, [
        ("Y drops 8pp: context reveals missed domain vocabulary",
         {"color": CORAL}),
        "Y\u2192P dominant transition (138 of 230 downgrades)",
        ("Only 1 N\u2192Y rescue across all 1,497 pairs", {"bold": True}),
    ], MX, CT + Inches(3.4), col_w, Inches(1.5), size=Pt(13))

    # Right — transition matrix
    rx = MX + col_w + gap
    rt = add_text(slide, "Transition Matrix", rx, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)

    tbl2 = add_table(slide,
        ["", "Ctx Y", "Ctx P", "Ctx N"],
        [["Blind Y", "207", "138", "0"],
         ["Blind P", "17", "519", "90"],
         ["Blind N", "1", "48", "477"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(12),
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    # Summary stats
    add_text(slide, "Summary", rx, CT + Inches(2.3), col_w, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)

    tbl3 = add_table(slide,
        ["Direction", "Count"],
        [["Downgrades (stricter)", "230"],
         ["Upgrades (lenient)", "68"],
         ["Unchanged", "1,199"],
         ["Cross-condition agreement", "80.0%"]],
        rx, CT + Inches(2.7), col_w, text_size=Pt(11),
        row_colors={0: {1: CORAL}, 1: {1: GREEN}})

    # Bottom
    add_text(slide,
        "Context is STRICTER not lenient \u2014 230 downgrades vs 68 upgrades. "
        "Domain knowledge reveals vocabulary failures.",
        MX, Inches(6.3), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Context-aware re-evaluation. When the judge knows the topic, Y drops "
        "from 23% to 15% (-8pp). Y+P drops from 64.9% to 62.1%. Context is "
        "STRICTER, not lenient. 230 downgrades vs 68 upgrades. Dominant "
        "transition: Y to P (138 cases) — the judge realizes domain vocabulary "
        "was wrong. Only 1 N-to-Y rescue across all 1,497 pairs.",
        [[lt, tbl], [rt, tbl2, tbl3], [kf_t, kf_b]], click_reveal=True)


def slide_what_good_looks_like(prs):
    """IS Tier 5 examples — what good looks like."""
    slide = new_slide(prs)
    add_title(slide, "What Good Looks Like: IS Tier 5")
    add_accent_line(slide)

    add_text(slide,
        "276 segments (18.4%) score IS \u2265 4.0 \u2014 Excellent quality:",
        MX, CT, CW, Inches(0.35), size=Pt(15), color=LGRAY)

    tbl = add_table(slide,
        ["Reference", "Hypothesis", "WER", "IS"],
        [["health insurance company they pay for all "
          "the medications they pay for all your visits",
          "[exact match]", "0%", "5.0"],
         ["so here we have a different example and in "
          "this case the buyer wants to buy one and get "
          "one free",
          "so here we have a different example and in "
          "this case the buyer wants to buy one and get "
          "one free", "0%", "5.0"],
         ["allow you to work with the team in a more "
          "productive efficient and effective manner",
          "allow you to work with a team and more "
          "productive efficient and effective manner", "14%", "4.6"]],
        MX, CT + Inches(0.5), CW, text_size=Pt(11),
        row_height=Inches(0.65),
        col_widths=[Inches(4.5), Inches(4.5), Inches(0.8), Inches(0.8)],
        row_colors={0: {3: GREEN}, 1: {3: GREEN}, 2: {3: GREEN}})

    # Key callout
    add_text(slide,
        "The system reads lips with high fidelity when visual signal is strong.",
        MX, CT + Inches(3.1), CW, Inches(0.4),
        size=Pt(15), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Stats
    add_bullets(slide, [
        "276 segments (18.4%) \u2014 the architecture works",
        "57% LLM Judge Y among Tier 5 \u2014 even the strictest evaluator agrees",
        "Business/Finance topics dominate Tier 5 (closest to training data)",
        ("Perfect transcription across 20\u201340 consecutive words \u2014 not luck",
         {"bold": True}),
    ], MX, CT + Inches(3.7), CW, Inches(2.0), size=Pt(14))

    _finish(slide, 0,
        "What good looks like: 276 segments (18.4%) achieve IS 4.0-5.0. "
        "Perfect word-for-word transcription over 20-40 consecutive words. "
        "The architecture works — the challenge is getting it to work "
        "consistently across all domains.",
        [[tbl]], click_reveal=True)


def slide_research_transition(prs):
    """Section divider: entering research findings portion."""
    slide = new_slide(prs)

    add_text(slide, "RESEARCH FINDINGS",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(48), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Understanding What Works, What Fails, and Why",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=CORAL)

    add_text(slide, "1,497 segments  \u2022  6 quality signals  \u2022  5 failure categories  "
             "\u2022  13 tuning experiments",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, None,
        "Section transition: we now present the research findings — our novel "
        "Intelligibility Score metric, root cause analysis, failure mode taxonomy, "
        "and decode tuning experiments.")


def slide_eng_transition(prs):
    """Section divider: entering engineering portion."""
    slide = new_slide(prs)

    # Large centered section title
    add_text(slide, "ENGINEERING",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(52), color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "From Research Code to Production System",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    # Subtle accent line
    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=TEAL)

    add_text(slide, "3 research repositories  \u2192  1 automated pipeline  \u2192  deployed container",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, None,
        "Section transition: we now move from research analysis to the "
        "engineering work that turned three research codebases into a "
        "production-ready system.")


def slide_three_repos(prs):
    """Starting point: three research codebases."""
    slide = new_slide(prs)
    add_title(slide, "Starting Point: Three Research Codebases")
    add_accent_line(slide)

    repos = [
        ("auto_avsr", "Preprocessing",
         "Face detection, mouth cropping,\nvideo normalization",
         TEAL),
        ("av_hubert", "Feature Extraction",
         "AV-HuBERT encoder,\nK-means clustering",
         CORAL),
        ("VSP-LLM", "Inference",
         "LLaMA-2 integration,\ndecode & generation",
         GREEN),
    ]

    cw_card = Inches(3.6)
    ch_card = Inches(2.8)
    gap = Inches(0.5)
    total = 3 * cw_card + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.2)

    card_shapes = []
    for i, (name, role, desc, color) in enumerate(repos):
        x = cx + i * (cw_card + gap)
        r = add_rect(slide, x, cy, cw_card, ch_card, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2.5), corner_radius=True)
        add_text(slide, name, x + Inches(0.2), cy + Inches(0.2),
                 cw_card - Inches(0.4), Inches(0.45),
                 size=Pt(20), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, role, x + Inches(0.2), cy + Inches(0.7),
                 cw_card - Inches(0.4), Inches(0.35),
                 size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, desc, x + Inches(0.2), cy + Inches(1.3),
                 cw_card - Inches(0.4), Inches(1.2),
                 size=Pt(12), color=LGRAY, align=PP_ALIGN.CENTER)
        card_shapes.append(r)

    # Bottom bullets
    bul = add_bullets(slide, [
        "No documentation, no tests, no integration",
        "Research-grade code: hardcoded paths, no error handling",
        ("Each runs independently \u2014 no orchestration between them",
         {"bold": True}),
        "Required 37 bug fixes to reach production quality",
    ], MX, cy + ch_card + Inches(0.3), CW, Inches(2.0), size=Pt(14))

    _finish(slide, 0,
        "We started with three independent research codebases: auto_avsr for "
        "preprocessing, av_hubert for feature extraction, and VSP-LLM for "
        "inference. No documentation, no tests, no integration between them. "
        "Research-grade code with hardcoded paths and no error handling. "
        "Required 37 bug fixes to reach production quality.",
        [card_shapes, [bul]])


def slide_web_ui(prs):
    """User experience — web UI and pipeline stages."""
    slide = new_slide(prs)
    add_title(slide, "User Experience: Web Interface")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — web UI features
    lt = add_text(slide, "Web UI Features", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Drag-and-drop video upload",
        "Real-time pipeline progress display",
        "Side-by-side burned video comparison",
        "Per-segment JSON reports with all metrics",
        "Single-click processing start",
        ("No command line needed", {"bold": True}),
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(14))

    # Right — UI screenshot placeholder
    rx = MX + col_w + gap
    ph = add_rect(slide, rx, CT, col_w, Inches(4.0),
                  fill_color=NAVY2, border_color=LGRAY, border_width=Pt(1),
                  corner_radius=True)
    add_text(slide, "UI Screenshot",
             rx, CT + Inches(1.5), col_w, Inches(0.5),
             size=Pt(20), color=MGRAY, align=PP_ALIGN.CENTER)
    add_text(slide, "(will be added from running server)",
             rx, CT + Inches(2.1), col_w, Inches(0.4),
             size=Pt(12), color=MGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "The web UI provides a simple drag-and-drop interface for non-technical "
        "users. Under the hood, 8 pipeline stages run automatically. Each stage "
        "is a modular component that can be tested independently.",
        [[lt, lb], [ph]], click_reveal=True)


def slide_dual_env(prs):
    """Two environments — EC2 and container."""
    slide = new_slide(prs)
    add_title(slide, "Two Environments: Development and Production")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — EC2 vs Container comparison
    lt = add_text(slide, "EC2 (Development)", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    r1 = add_rect(slide, MX, CT + Inches(0.5), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    b1 = add_bullets(slide, [
        "Full research environment",
        "GPU: Tesla T4 (16GB)",
        "Path: /home/ubuntu/",
        "All datasets and evaluation tools",
    ], MX + Inches(0.2), CT + Inches(0.6), col_w - Inches(0.4), Inches(1.2),
       size=Pt(13))

    ct_label = add_text(slide, "Container (Production)", MX, CT + Inches(2.3), col_w,
             Inches(0.4), size=Pt(18), color=CORAL, bold=True)

    r2 = add_rect(slide, MX, CT + Inches(2.8), col_w, Inches(1.5),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    b2 = add_bullets(slide, [
        "Docker container, no internet",
        "GPU: client hardware",
        "Path: /workspace/",
        "Pipeline + web UI only",
    ], MX + Inches(0.2), CT + Inches(2.9), col_w - Inches(0.4), Inches(1.2),
       size=Pt(13))

    # Right — sync challenges
    rx = MX + col_w + gap
    rt = add_text(slide, "Synchronization Challenge", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)

    big_num = add_text(slide, "26", rx, CT + Inches(0.6), col_w, Inches(0.7),
             size=Pt(48), color=CORAL, bold=True, align=PP_ALIGN.CENTER)
    num_label = add_text(slide, "tracked sync items",
             rx, CT + Inches(1.2), col_w, Inches(0.3),
             size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)

    rb = add_bullets(slide, [
        "Every EC2 change must be replicated to container",
        "Path translations (/home/ubuntu/ \u2192 /workspace/)",
        "Different Python environments and dependencies",
        ("Detailed sync changelog with exact code diffs", {"color": TEAL}),
        "INSTALL.sh overlay with 13-point verification",
    ], rx, CT + Inches(1.8), col_w, Inches(3.0), size=Pt(13))

    _finish(slide, 0,
        "Two environments: EC2 for development and research, Docker container "
        "for production deployment. 26 tracked sync items ensure changes are "
        "replicated correctly. Path translations, different Python environments, "
        "different hardware. INSTALL.sh handles deployment with automatic backup "
        "and 13-point verification.",
        [[lt, r1, b1, ct_label, r2, b2],
         [rt, big_num, num_label, rb]],
        click_reveal=True, para_build=False)


def slide_future_transition(prs):
    """Section divider: entering future directions portion."""
    slide = new_slide(prs)

    add_text(slide, "FUTURE DIRECTIONS",
             MX, Inches(2.2), CW, Inches(1.2),
             size=Pt(48), color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "From Analysis to Action",
             MX, Inches(3.5), CW, Inches(0.6),
             size=Pt(22), color=LGRAY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(4.3), Inches(4.33), Inches(0.04),
             fill_color=GREEN)

    add_text(slide, "5 research insights  \u2192  5-phase improvement roadmap",
             MX, Inches(4.8), CW, Inches(0.5),
             size=Pt(16), color=MGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, None,
        "Section transition: we now move from what we found to what we "
        "recommend doing about it. Five key insights lead to a five-phase "
        "improvement roadmap.")


def slide_insights(prs):
    """Key research insights that inform the roadmap."""
    slide = new_slide(prs)
    add_title(slide, "Five Insights That Inform the Roadmap")
    add_accent_line(slide)

    insights = [
        ("1", "The visual encoder is the bottleneck, not the LLM",
         "Per-segment IS rankings are identical across 16 configs (r > 0.92). "
         "Tuning the LLM's decode parameters changes almost nothing.",
         TEAL),
        ("2", "WER dramatically overstates failure",
         "40% properly captured vs WER's 11% \u2014 3.5\u00d7 more. Even 51% "
         "with LLM salvage. Most useful output has moderate WER (50\u201370%).",
         GREEN),
        ("3", "Domain mismatch is the primary quality driver",
         "IS ranges from 3.08 (Business) to 2.13 (DIY). Training data is TED "
         "talks \u2014 formal, educational, frontal face.",
         CORAL),
        ("4", "Data scarcity, not model capacity, limits fine-tuning",
         "1,273 segments is below the ~1K LoRA minimum. r=64 was 3.1pp "
         "WORSE than r=16 \u2014 faster overfitting, not better learning.",
         CORAL),
        ("5", "Gains are multiplicative, not additive",
         "ICLR 2024 scaling law: stronger LLM \u00d7 more data \u00d7 smart "
         "prompts compound. Each lever alone is modest; together they're "
         "transformative.",
         TEAL),
    ]

    step_h = Inches(0.85)
    start_y = CT

    shapes = []
    for i, (num, title, detail, color) in enumerate(insights):
        y = start_y + i * (step_h + Inches(0.1))

        # Number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX, y + Inches(0.1), Inches(0.5), Inches(0.5))
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()
        add_text(slide, num, MX, y + Inches(0.1),
                 Inches(0.5), Inches(0.5),
                 size=Pt(18), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        add_rich_text(slide, [
            [(title, {"size": Pt(14), "color": WHITE, "bold": True})],
            [(detail, {"size": Pt(11), "color": LGRAY})],
        ], MX + Inches(0.7), y + Inches(0.02),
           CW - Inches(0.8), step_h - Inches(0.04))
        shapes.append(circle)

    _finish(slide, 0,
        "Five key research insights. The visual encoder is the bottleneck. "
        "WER dramatically overstates failure. Domain mismatch is the primary "
        "quality driver. Data scarcity limits fine-tuning. And gains are "
        "multiplicative — stronger LLM times more data times smart prompts.",
        [shapes])


def slide_llm_context_engine(prs):
    """LLM as context engine — what it does and where to go."""
    slide = new_slide(prs)
    add_title(slide, "The LLM Is a Context Engine")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what the LLM does
    lt = add_text(slide, "What the LLM Does", MX, CT, col_w, Inches(0.4),
                  size=Pt(18), color=TEAL, bold=True)

    add_text(slide, "The visual encoder sees mouth shapes.",
             MX, CT + Inches(0.6), col_w, Inches(0.3),
             size=Pt(14), color=WHITE)
    add_text(slide, "The LLM resolves ambiguity using language context.",
             MX, CT + Inches(1.0), col_w, Inches(0.3),
             size=Pt(14), color=TEAL, bold=True)

    lb = add_bullets(slide, [
        '"p/b/m" \u2192 Is it "pat," "bat," or "mat"?',
        "LLM uses surrounding words to disambiguate",
        "Stronger LLM = better disambiguation",
        ("This is why LLM quality matters more than size", {"bold": True}),
    ], MX, CT + Inches(1.6), col_w, Inches(2.0), size=Pt(14))

    # Right — current vs upgrade
    rx = MX + col_w + gap
    rt = add_text(slide, "Current vs Upgrade", rx, CT, col_w, Inches(0.4),
                  size=Pt(18), color=CORAL, bold=True)

    # Current
    r1 = add_rect(slide, rx, CT + Inches(0.5), col_w, Inches(1.8),
                  fill_color=NAVY2, border_color=CORAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Current: LLaMA-2 7B", rx + Inches(0.2), CT + Inches(0.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=CORAL, bold=True)
    add_bullets(slide, [
        "32K vocab, 4K context",
        "2023 model, limited reasoning",
    ], rx + Inches(0.2), CT + Inches(1.0), col_w - Inches(0.4), Inches(0.8),
       size=Pt(12), bullet_color=CORAL)

    # Upgrade
    r2 = add_rect(slide, rx, CT + Inches(2.5), col_w, Inches(2.0),
                  fill_color=NAVY2, border_color=GREEN, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "Upgrade: Llama 3.1 8B", rx + Inches(0.2), CT + Inches(2.6),
             col_w - Inches(0.4), Inches(0.3),
             size=Pt(14), color=GREEN, bold=True)
    add_bullets(slide, [
        "128K vocab, 128K context",
        "Quality \u2248 LLaMA-2 70B",
        ("Same hidden_size (4096) = drop-in swap", {"color": GREEN}),
        ("Setup: 1\u20132 hours", {"bold": True}),
    ], rx + Inches(0.2), CT + Inches(3.0), col_w - Inches(0.4), Inches(1.2),
       size=Pt(12), bullet_color=GREEN)

    _finish(slide, 0,
        "The LLM is a context engine. The visual encoder sees mouth shapes but "
        "can't distinguish visemes. The LLM resolves ambiguity using language "
        "context. A stronger LLM means better disambiguation. Llama 3.1 8B "
        "has quality equivalent to LLaMA-2 70B with the same hidden dimension "
        "(4096), making it a trivial 1-2 hour swap.",
        [[lt, lb], [rt, r1, r2]], click_reveal=True)


def slide_data_scaling(prs):
    """Data scaling evidence and projections."""
    slide = new_slide(prs)
    add_title(slide, "Data Scaling: The Path to IS 3.5–4.0")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — fine-tuning results + scaling law
    lt = add_text(slide, "Why More Data Is the Answer", MX, CT, col_w, Inches(0.4),
                  size=Pt(17), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        ("Current: 1,273 English segments \u2014 far below LoRA minimum", {"bold": True}),
        "Fine-tune experiments confirmed: small data = overfitting",
        "Scaling law (ICLR 2024): data × LLM quality = multiplicative gains",
        ("AVSpeech: 290K English videos available for curation", {"color": TEAL}),
        ("Data scarcity is a curation bottleneck, not a hard blocker",
         {"color": LGRAY, "italic": True}),
        ("Next step: curate 20K\u201350K diverse English segments", {"bold": True, "color": GREEN}),
    ], MX, CT + Inches(0.5), col_w, Inches(3.5), size=Pt(13))

    # Right — projection table with IS
    rx = MX + col_w + gap
    rt = add_text(slide, "Projected Impact on IS", rx, CT, col_w,
                  Inches(0.4), size=Pt(17), color=TEAL, bold=True)

    tbl = add_table(slide,
        ["Phase", "Data", "WER", "IS Target", "Timeline"],
        [["Current", "1.3K segs", "64.1%", "2.52", "\u2014"],
         ["Phase 1", "5K hrs", "55\u201358%", "~2.9", "2\u20134 wks"],
         ["Phase 2", "10K hrs", "48\u201352%", "~3.3", "4\u20136 wks"],
         ["Phase 3", "20K hrs", "42\u201346%", "~3.7", "6\u20138 wks"],
         ["Phase 4", "50K+ hrs", "38\u201342%", "~4.0+", "3\u20134 mo"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(11),
        col_widths=[Inches(0.9), Inches(1.0), Inches(1.0), Inches(0.9), Inches(1.0)],
        row_colors={0: {2: CORAL}, 3: {3: GREEN}, 4: {3: GREEN}})

    # AVSpeech callout
    r1 = add_rect(slide, rx, CT + Inches(3.0), col_w, Inches(1.0),
                  fill_color=NAVY2, border_color=TEAL, border_width=Pt(2),
                  corner_radius=True)
    add_text(slide, "290K", rx + Inches(0.2), CT + Inches(3.1),
             Inches(1.2), Inches(0.4),
             size=Pt(28), color=TEAL, bold=True)
    add_text(slide, "AVSpeech English videos available\nfor training data curation",
             rx + Inches(1.5), CT + Inches(3.1), col_w - Inches(1.7),
             Inches(0.7), size=Pt(13), color=WHITE)

    _finish(slide, 0,
        "Data scaling projections based on ICLR 2024 multiplicative scaling "
        "law. Current 1,273 segments is far below minimum. 20K segments with "
        "Llama 3.1 8B projects to IS 3.5-4.0 (55-65% captured). AVSpeech has "
        "290K videos available for training data curation.",
        [[lt, lb], [rt, tbl, r1]], click_reveal=True)


def slide_price_tag(prs):
    """Cost projections: GPU, data, timeline to reach IS targets."""
    slide = new_slide(prs)
    add_title(slide, "The Price Tag: Cost to Reach IS 3.5\u20134.0")
    add_accent_line(slide)

    add_text(slide,
        "AWS eu-west-1 (Ireland)  \u2022  p4d.24xlarge (8\u00d7A100) spot  \u2022  "
        "Paper\u2019s two-phase training curriculum",
        MX, CT, CW, Inches(0.35), size=Pt(12), color=LGRAY, italic=True)

    tbl_w = Inches(7.8)
    tbl = add_table(slide,
        ["Phase", "Data", "Train Cost", "Total Cost", "Timeline", "IS Target"],
        [["Current", "1.3K segs", "\u2014", "\u2014", "\u2014", "2.52"],
         ["Phase 1", "5K hrs", "~$3K", "~$8\u201312K", "2\u20134 wks", "~2.9\u20133.1"],
         ["Phase 2", "10K hrs", "~$6K", "~$15\u201320K", "4\u20136 wks", "~3.2\u20133.5"],
         ["Phase 3", "20K hrs", "~$13K", "~$30\u201340K", "6\u20138 wks", "~3.5\u20133.8"],
         ["Phase 4", "50K hrs", "~$32K", "~$70\u2013100K", "3\u20134 mo", "~3.8\u20134.2"]],
        MX, CT + Inches(0.5), tbl_w, text_size=Pt(11),
        col_widths=[Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.3),
                    Inches(1.1), Inches(1.2)],
        row_colors={3: {3: GREEN, 5: GREEN}})

    rx = MX + tbl_w + Inches(0.4)
    rw = CW - tbl_w - Inches(0.4)

    r1 = add_rect(slide, rx, CT + Inches(0.5), rw, Inches(2.8),
                   fill_color=NAVY2, border_color=GOLD, border_width=Pt(2),
                   corner_radius=True)
    add_text(slide, "Sweet Spot", rx + Inches(0.2), CT + Inches(0.6),
             rw - Inches(0.4), Inches(0.35), size=Pt(16), color=GOLD, bold=True)
    add_text(slide, "Phase 3: IS ~3.7",
             rx + Inches(0.2), CT + Inches(1.0),
             rw - Inches(0.4), Inches(0.35), size=Pt(20), color=GREEN, bold=True)
    add_bullets(slide, [
        "20K hrs = ~7% of AVSpeech",
        "Total ~$35K incl. curation",
        "Follows paper\u2019s 2-phase\ncurriculum: freeze \u2192 unfreeze",
    ], rx + Inches(0.15), CT + Inches(1.5), rw - Inches(0.3), Inches(1.2),
        size=Pt(11))

    r2 = add_rect(slide, rx, CT + Inches(3.5), rw, Inches(1.3),
                   fill_color=NAVY2, border_color=TEAL, border_width=Pt(1),
                   corner_radius=True)
    add_text(slide, "LLM Backbone Upgrade",
             rx + Inches(0.2), CT + Inches(3.6),
             rw - Inches(0.4), Inches(0.3), size=Pt(13), color=TEAL, bold=True)
    add_text(slide,
        "Llama 3.1 8B or Qwen 2.5 7B\n+0.3\u20130.5 IS independently\nOnly config change needed",
        rx + Inches(0.2), CT + Inches(3.95),
        rw - Inches(0.4), Inches(0.7), size=Pt(11), color=LGRAY)

    add_text(slide,
        "Training cost: p4d spot $9.39/hr (eu-west-1).  "
        "Curation includes: download, RetinaFace, mouth crop, AV-HuBERT features, Whisper v3 labels.",
        MX, Inches(6.5), CW, Inches(0.35), size=Pt(10), color=MGRAY, italic=True)

    _finish(slide, 0,
        "Cost projections for scaling to IS 3.5-4.0. Based on p4d.24xlarge spot "
        "pricing in eu-west-1 at $9.39/hr. Phase 3 (20K hours, ~$35K) is the sweet spot. "
        "LLM backbone upgrade to Llama 3.1 8B or Qwen 2.5 7B adds +0.3-0.5 IS independently.",
        [[tbl], [r1, r2]], click_reveal=True)



def slide_a16(prs):
    """A8: LLM Judge x IS Tier cross-tabulation."""
    slide = new_slide(prs)
    add_title(slide, "A8: LLM Judge \u00d7 IS Tier Cross-Tabulation")
    add_accent_line(slide)

    add_text(slide,
        "How the LLM judge verdict distributes across IS quality tiers (blind evaluation):",
        MX, CT, CW, Inches(0.4), size=Pt(14), color=LGRAY)

    tbl = add_table(slide,
        ["IS Tier", "Y (count)", "Y%", "P (count)", "P%", "N (count)", "N%"],
        [["5 \u2014 Excellent (4.0\u20135.0)", "157", "56.9%", "105", "38.0%", "14", "5.1%"],
         ["4 \u2014 Good (3.0\u20133.99)", "67", "20.9%", "189", "58.9%", "65", "20.2%"],
         ["3 \u2014 Fair (2.0\u20132.99)", "25", "7.7%", "167", "51.4%", "133", "40.9%"],
         ["2 \u2014 Poor (1.0\u20131.99)", "14", "4.2%", "115", "34.2%", "207", "61.6%"],
         ["1 \u2014 Failed (0.0\u20130.99)", "5", "2.1%", "41", "17.2%", "193", "80.8%"]],
        MX, CT + Inches(0.5), CW, text_size=Pt(11),
        row_height=Inches(0.4),
        col_widths=[Inches(2.8), Inches(1.1), Inches(0.9),
                    Inches(1.1), Inches(0.9), Inches(1.1), Inches(0.9)],
        row_colors={0: {2: GREEN}, 4: {6: CORAL}})

    # Key observations
    add_text(slide, "Key Observations:", MX, CT + Inches(3.0), CW, Inches(0.3),
             size=Pt(15), color=TEAL, bold=True)
    add_bullets(slide, [
        "IS Tier 5: 57% full Y \u2014 strong agreement on excellent output",
        "IS Tiers 2-3: majority P not N \u2014 judge sees partial value metrics miss",
        "IS Tier 1: 81% N \u2014 strong agreement on complete failure",
        ("Pearson r = 0.8495 between IS and judge verdict (coded Y=3, P=2, N=1)",
         {"color": TEAL}),
    ], MX, CT + Inches(3.4), CW, Inches(2.0), size=Pt(13))

    _finish(slide, "A8",
        "LLM Judge cross-tabulated with IS tiers. Strong agreement at the "
        "extremes: 57% Y for Tier 5, 81% N for Tier 1. The interesting "
        "middle: Tiers 2-3 get majority P verdicts — the LLM sees partial "
        "meaning preservation that strict metrics miss. Pearson r=0.8495.")


def slide_a17(prs):
    """A9: Context-aware transition matrix and per-topic deltas."""
    slide = new_slide(prs)
    add_title(slide, "A9: Context Evaluation \u2014 Transition Details")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — full transition matrix
    lt = add_text(slide, "Blind \u2192 Context Transition Matrix", MX, CT,
                  col_w, Inches(0.4), size=Pt(17), color=TEAL, bold=True)

    tbl1 = add_table(slide,
        ["Blind \u2193 / Ctx \u2192", "Y", "P", "N", "Total"],
        [["Y", "207", "138", "0", "345"],
         ["P", "17", "519", "90", "626"],
         ["N", "1", "48", "477", "526"]],
        MX, CT + Inches(0.5), col_w, text_size=Pt(12),
        col_widths=[Inches(1.5), Inches(0.9), Inches(0.9),
                    Inches(0.9), Inches(0.9)],
        row_colors={0: {2: CORAL}, 1: {3: CORAL}})

    add_text(slide, "Dominant transition: Y\u2192P (138 cases, 40% of all Y)\n"
             "Only 1 N\u2192Y rescue across all 1,497 pairs",
             MX, CT + Inches(2.2), col_w, Inches(0.6),
             size=Pt(12), color=LGRAY)

    # Summary stats
    tbl2 = add_table(slide,
        ["Metric", "Value"],
        [["Total downgrades", "230 (15.4%)"],
         ["Total upgrades", "68 (4.5%)"],
         ["Unchanged", "1,199 (80.1%)"],
         ["Cross-condition agree.", "80.0%"]],
        MX, CT + Inches(3.0), col_w * 0.7, text_size=Pt(11))

    # Right — per-topic deltas
    rx = MX + col_w + gap
    rt = add_text(slide, "Per-Topic Y+P Delta (Blind \u2192 Context)", rx, CT,
                  col_w, Inches(0.4), size=Pt(17), color=CORAL, bold=True)

    tbl3 = add_table(slide,
        ["Topic", "Blind Y+P", "Ctx Y+P", "\u0394"],
        [["Business/Finance", "72%", "70%", "\u22122pp"],
         ["Education/Lecture", "67%", "64%", "\u22123pp"],
         ["Entertainment", "64%", "61%", "\u22123pp"],
         ["News/Politics", "65%", "62%", "\u22123pp"],
         ["Tech/Science", "62%", "59%", "\u22123pp"],
         ["Sports/Health", "60%", "57%", "\u22123pp"],
         ["DIY/Home", "48%", "44%", "\u22124pp"]],
        rx, CT + Inches(0.5), col_w, text_size=Pt(11),
        row_colors={6: {3: CORAL}})

    add_text(slide,
        "Context is uniformly stricter across all topics. DIY/Home has the "
        "largest delta (\u22124pp) \u2014 context reveals the most visual-content "
        "vocabulary failures.",
        rx, CT + Inches(3.5), col_w, Inches(0.6),
        size=Pt(12), color=LGRAY, italic=True)

    _finish(slide, "A9",
        "Full transition matrix and per-topic deltas for context-aware "
        "evaluation. 230 downgrades vs 68 upgrades. Dominant: Y to P (138). "
        "Context is uniformly stricter across all 7 topics, with DIY/Home "
        "showing the largest delta. Cross-condition agreement: 80.0%.")


# ═══════════════════════════════════════════════════════════════════════
# SLIDE: CONFIDENCE SCORING — FUTURE DIRECTION
# ═══════════════════════════════════════════════════════════════════════

def slide_confidence_scoring(prs):
    """Future direction: per-segment confidence probabilities."""
    slide = new_slide(prs)
    add_title(slide, "Phase 1: Confidence Scoring")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left — what it is
    lt = add_text(slide, "What Is It?", MX, CT, col_w, Inches(0.35),
                  size=Pt(18), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        ("Assign a probability (0\u20131.0) to each decoded segment",
         {"bold": True}),
        "High confidence (> 0.8): trust the output as-is",
        "Medium (0.4\u20130.8): flag for human review",
        "Low (< 0.4): suppress or mark as unreliable",
        ("Goal: surface the 40% that already works", {"color": GREEN}),
    ], MX, CT + Inches(0.45), col_w, Inches(2.5), size=Pt(14))

    # How it works
    hwt = add_text(slide, "How It Works", MX, CT + Inches(3.2), col_w, Inches(0.35),
             size=Pt(16), color=TEAL, bold=True)
    hwb = add_bullets(slide, [
        "Combine decode-time signals: beam score, entropy, "
        "N-best agreement, length ratio",
        "Train a lightweight classifier on our 1,497 labeled segments",
        "Output: probability that IS \u2265 3.0 for each segment",
    ], MX, CT + Inches(3.65), col_w, Inches(2.0), size=Pt(13))

    # Right — impact
    rx = MX + col_w + gap
    rw = CW - col_w - gap
    rt = add_text(slide, "Impact", rx, CT, rw, Inches(0.35),
                  size=Pt(18), color=GREEN, bold=True)

    rb = add_bullets(slide, [
        ("Immediate value: 2\u20134 hours to implement", {"bold": True, "color": GREEN}),
        "Users see only high-confidence segments by default",
        "Reduces perceived error rate from 60% to ~20%",
        "No model changes needed \u2014 pure post-processing",
    ], rx, CT + Inches(0.45), rw, Inches(2.0), size=Pt(14))

    # Right — what we already have
    waht = add_text(slide, "What We Already Have", rx, CT + Inches(2.7), rw, Inches(0.35),
             size=Pt(16), color=CORAL, bold=True)
    headers = ["Signal", "Source"]
    rows = [
        ["Beam score", "Available from decode"],
        ["Token entropy", "Available from decode"],
        ["N-best agreement", "Requires beam > 1"],
        ["Length ratio", "Already in IS pipeline"],
        ["IS sub-scores", "Already computed"],
    ]
    tbl = add_table(slide, headers, rows, rx, CT + Inches(3.15), rw,
                    row_height=Inches(0.35), text_size=Pt(10),
                    col_widths=[Inches(2.4), Inches(3.0)])

    bottom = add_text(slide,
        "The fastest path to user value. No retraining, no new data, "
        "no infrastructure changes \u2014 just smarter filtering.",
        MX, Inches(6.35), CW, Inches(0.4),
        size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Phase 1 of the roadmap: confidence scoring. Assign a probability "
        "to each decoded segment indicating how likely it is to be correctly "
        "transcribed (IS >= 3.0). Uses decode-time signals like beam score, "
        "token entropy, N-best agreement, and length ratio. Can be trained on "
        "our existing 1,497 labeled segments. Implementation: 2-4 hours. "
        "Impact: users see only trusted output, perceived error rate drops "
        "from 60% to ~20%.",
        [[lt, lb], [rt, rb], [hwt, hwb, waht, tbl], [bottom]], click_reveal=True)


# ═══════════════════════════════════════════════════════════════════════
# SLIDE: THANK YOU / END
# ═══════════════════════════════════════════════════════════════════════

def slide_thank_you(prs):
    """Final slide: thank you and questions."""
    slide = new_slide(prs)

    add_text(slide, "Thank You",
             MX, Inches(2.0), CW, Inches(1.2),
             size=Pt(56), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(4.5), Inches(3.4), Inches(4.33), Inches(0.04),
             fill_color=TEAL)

    add_text(slide, "Questions & Discussion",
             MX, Inches(3.8), CW, Inches(0.6),
             size=Pt(24), color=TEAL, align=PP_ALIGN.CENTER)

    add_text(slide,
        "1,497 segments  \u2022  6 quality signals  \u2022  5 failure categories  "
        "\u2022  13 experiments\n"
        "8-stage pipeline  \u2022  37 bugs fixed  \u2022  8 research reports",
        MX, Inches(4.8), CW, Inches(0.8),
        size=Pt(15), color=LGRAY, align=PP_ALIGN.CENTER)

    _finish(slide, 0,
        "Final slide. Thank the audience and open for questions.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    _auto_num[0] = 0  # Reset auto-numbering

    prs = Presentation()
    prs.slide_width = SL_W
    prs.slide_height = SL_H

    print("Generating presentation...")

    builders = [
        # --- Section 0: Opening ---
        slide_01,           # Title
        slide_exec_summary, # Executive summary
        slide_wer_lies,     # [NEW] Side-by-side: WER lies, IS tells truth
        slide_toc,          # Table of contents
        # --- Section 1: Context ---
        slide_02,           # What is VSP? (video)
        slide_visemes,      # [MOD] Fundamental challenge + poster frames
        slide_03,           # Model Architecture
        slide_data_flow,    # How It Works
        slide_04,           # The Benchmark
        # --- Section 2: The Problem ---
        slide_eval_dataset, # Our evaluation dataset
        slide_05,           # The Reality Gap (64.1% WER)
        slide_wer_explained,# WER formula and limitations
        slide_06,           # WER Is Blind to Meaning
        slide_is_foreshadow,# Bridge: We Need a Better Metric
        # --- Section 3: Research Findings ---
        slide_research_transition, # Section divider
        slide_is_intro,     # Introducing IS
        slide_is_signals,   # IS: Six Signals
        slide_is_weight_rationale, # Why These Weights? 3 Dimensions
        slide_is_dimensions,# Three quality dimensions
        slide_is_calc_examples, # IS in Action: Two Real Segments
        slide_is_radar,     # [MOD] IS Radar: dual overlay if available
        slide_is_wer_scatter, # [NEW] The Gap: WER vs IS scatter
        slide_07,           # IS Results: 39.9% Captured
        slide_metric_transition, # [NEW] 64.1% → 39.9% → 50.9%
        # --- Section 4: Understanding Why ---
        slide_10,           # Three Root Causes
        slide_domain_mismatch, # Domain mismatch detail
        slide_11,           # Named Entity Accuracy
        slide_failure_deep_1a, # Failure Modes: 5-Category Taxonomy
        slide_failure_deep_2, # Failure Modes: Real Examples
        slide_08,           # Failure Mode Taxonomy
        slide_failure_deep_3, # Failure Modes: Impact & Fixes
        # --- Section 5: Can We Tune It? ---
        slide_tuning_summary, # 13 Experiments, Minimal Gain
        # --- Section 6: The Full Picture ---
        slide_is_deep_dive, # Why These 6 Signals? Validation
        slide_metric_disagreement, # When Metrics Disagree
        slide_metric_disagreement_2, # When Metrics Disagree pt 2
        slide_two_eval_systems, # Two evaluation systems
        slide_llm_judge,    # LLM-as-a-Judge
        slide_context_eval, # Context-aware re-evaluation
        # --- Salvage ---
        slide_llm_context_engine, # LLM as context engine
        slide_25,           # LLM Salvage overview: 39.9% -> 50.9%
        slide_25b,          # Salvage: 6 Recovery Categories
        slide_25d,          # Salvage: 3 Real Examples
        slide_25e,          # Salvage: 3 More Examples
        slide_25c,          # Salvage: How Detection Works
        # --- What good looks like ---
        slide_what_good_looks_like,
        slide_14b,          # Video Gallery
        slide_15,           # Demo: OK > Near-miss > Hallucination
        # --- Section 7: Engineering ---
        slide_eng_transition, # Section divider
        slide_three_repos,  # Starting point
        slide_17,           # [MOD] Pipeline: per-stage wipe reveal
        slide_18,           # Engineering Journey
        slide_19, slide_20,
        slide_web_ui,       # Web UI
        slide_21,
        slide_dual_env,     # Two environments
        # --- Section 8: Future Directions ---
        slide_future_transition, # Section divider
        slide_insights,     # Key research insights
        slide_24,           # Starting point better than WER
        slide_26,           # Five Phases roadmap
        slide_26b,          # IS trajectory roadmap
        slide_confidence_scoring, # Phase 1: Confidence Scoring detail
        slide_27,           # Phase 1 Confidence
        slide_28,           # Phase 2 N-Best
        slide_data_scaling, # [MOD] Data scaling with phases + timelines
        slide_price_tag,    # [NEW] Cost projections: GPU/data/IS
        slide_29,           # Phase 3-4 Fine-Tuning
        slide_30,           # Phase 5 LLM Upgrade
        slide_arabic_roadmap, # Arabic Pipeline Roadmap
        slide_31,           # Key Takeaways
        slide_thank_you,    # Thank You & Questions
        # --- Appendix (A1–A9) ---
        slide_a1,           # A1: Homophenes
        slide_a3,           # A2: Catastrophic lenpen
        slide_a8,           # A3: IS Component Correlation
        slide_a11,          # A4: LLM Salvage Recoverable
        slide_a11b,         # A5: LLM Salvage Examples
        slide_a13,          # A6: Failure Mode Examples
        slide_a15,          # A7: Video Gallery Map
        slide_a16,          # A8: LLM Judge × IS Tier
        slide_a17,          # A9: Context transition matrix
    ]
    total = len(builders)

    for i, builder in enumerate(builders, 1):
        print(f"  Slide {i:2d}/{total} ...", end=" ")
        try:
            builder(prs)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    # _fix_pptx_video_compat disabled — was causing PowerPoint repair
    # dialog and destroying video slide content. The minor repair warning
    # from bare p:pic elements is preferable to blank slides.
    # _fix_pptx_video_compat(str(OUTPUT))
    print(f"\nSaved: {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
