#!/usr/bin/env python3
"""
Argos VSP — PPTX Presentation Generator

Creates the complete 30-slide "Argos VSP: Research Findings and Production
Roadmap" presentation with professional styling, real images, entrance
animations, fade transitions, and speaker notes.

Usage:
    python3 docs/_research-tools/generators/generate_presentation.py

Output:
    presentation_materials_20260224/Argos_VSP_Project_Review.pptx
"""

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
    "P1_quality": PLOTS / "P1_quality_tiers.png",
    "P2_paper": PLOTS / "P2_paper_vs_reality.png",
    "P3_trajectory": PLOTS / "P3_wer_trajectory.png",
    "P4_lenpen": PLOTS / "P4_lenpen_sensitivity.png",
    "boxplot": PLOTS / "09_boxplot_wwer_all_experiments.png",
    "wer_duration": PLOTS / "01_wer_vs_duration.png",
    "nea_scatter": PLOTS / "14_nea_vs_wwer_scatter.png",
    "empty_halluc": PLOTS / "10_empty_and_hallucination_rates.png",
    "cdf_wwer": PLOTS / "15_cdf_wwer_curated.png",
    "ft_dashboard": PLOTS / "finetune" / "FT_10_summary_dashboard.png",
}

VID = {
    "perfect": VIDEOS / "IEa7qEkMvfQ_3__c5447488_with_hyp.mp4",
    "bogo": VIDEOS / "d8BR6hsvzoY_31__2e9546df_with_hyp.mp4",
    "nearmiss": VIDEOS / "-POZpyVCN8k_9__c7b26ea8_with_hyp.mp4",
    "halluc": VIDEOS / "00MUdHQ7GGY_8__b1480c7a_with_hyp.mp4",
}

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
ORANGE  = RGBColor(0xFF, 0x98, 0x00)
RED     = RGBColor(0xF4, 0x43, 0x36)
DRED    = RGBColor(0xB7, 0x1C, 0x1C)
NAVY2   = RGBColor(0x15, 0x2A, 0x40)  # slightly lighter navy for cards
NAVY3   = RGBColor(0x1A, 0x35, 0x50)  # lighter still for hover cards

FONT = "Calibri"

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
    """Add fade transition to slide."""
    sld = slide._element
    # Remove existing transition
    for child in list(sld):
        if child.tag.endswith('transition'):
            sld.remove(child)
    transition = etree.SubElement(sld, qn('p:transition'))
    transition.set('spd', speed)
    transition.set('advClick', '1')
    etree.SubElement(transition, qn('p:fade'))


def add_animations(slide, groups):
    """
    Add entrance fade animations triggered by clicks.

    groups: list of lists of shape objects.
        Each inner list = one click group.
        Shapes within a group stagger by 300ms.
    """
    if not groups:
        return
    # Flatten empty groups
    groups = [g for g in groups if g]
    if not groups:
        return

    sld = slide._element
    # Remove existing timing
    for child in list(sld):
        if child.tag.endswith('timing'):
            sld.remove(child)

    _id = [1]  # mutable counter

    def nid():
        v = _id[0]
        _id[0] += 1
        return str(v)

    timing = etree.SubElement(sld, qn('p:timing'))
    tnLst = etree.SubElement(timing, qn('p:tnLst'))
    par_root = etree.SubElement(tnLst, qn('p:par'))

    cTn_root = etree.SubElement(par_root, qn('p:cTn'))
    cTn_root.set('id', nid())
    cTn_root.set('dur', 'indefinite')
    cTn_root.set('restart', 'never')
    cTn_root.set('nodeType', 'tmRoot')

    childTnLst_root = etree.SubElement(cTn_root, qn('p:childTnLst'))

    # Main sequence
    seq = etree.SubElement(childTnLst_root, qn('p:seq'))
    seq.set('concurrent', '1')
    seq.set('nextAc', 'seek')

    cTn_seq = etree.SubElement(seq, qn('p:cTn'))
    cTn_seq.set('id', nid())
    cTn_seq.set('dur', 'indefinite')
    cTn_seq.set('nodeType', 'mainSeq')

    childTnLst_seq = etree.SubElement(cTn_seq, qn('p:childTnLst'))

    for gi, group in enumerate(groups):
        # Click group container
        par_click = etree.SubElement(childTnLst_seq, qn('p:par'))
        cTn_click = etree.SubElement(par_click, qn('p:cTn'))
        cTn_click.set('id', nid())
        cTn_click.set('fill', 'hold')

        stCondLst = etree.SubElement(cTn_click, qn('p:stCondLst'))
        cond = etree.SubElement(stCondLst, qn('p:cond'))
        if gi == 0:
            # First group: auto-play on slide entry
            cond.set('delay', '0')
        else:
            # Subsequent groups: on click
            cond.set('delay', 'indefinite')

        childTnLst_click = etree.SubElement(cTn_click, qn('p:childTnLst'))

        for si, shape in enumerate(group):
            if shape is None:
                continue
            try:
                spid = str(shape.shape_id)
            except AttributeError:
                continue

            delay_ms = si * 300  # stagger within group

            # Animation container
            par_anim = etree.SubElement(childTnLst_click, qn('p:par'))
            cTn_anim = etree.SubElement(par_anim, qn('p:cTn'))
            cTn_anim.set('id', nid())
            cTn_anim.set('fill', 'hold')

            st_anim = etree.SubElement(cTn_anim, qn('p:stCondLst'))
            c_anim = etree.SubElement(st_anim, qn('p:cond'))
            c_anim.set('delay', str(delay_ms))

            child_anim = etree.SubElement(cTn_anim, qn('p:childTnLst'))

            # Set visibility
            p_set = etree.SubElement(child_anim, qn('p:set'))
            cBhvr_s = etree.SubElement(p_set, qn('p:cBhvr'))
            cTn_s = etree.SubElement(cBhvr_s, qn('p:cTn'))
            cTn_s.set('id', nid())
            cTn_s.set('dur', '1')
            cTn_s.set('fill', 'hold')
            st_s = etree.SubElement(cTn_s, qn('p:stCondLst'))
            c_s = etree.SubElement(st_s, qn('p:cond'))
            c_s.set('delay', '0')

            tgt_s = etree.SubElement(cBhvr_s, qn('p:tgtEl'))
            sp_s = etree.SubElement(tgt_s, qn('p:spTgt'))
            sp_s.set('spid', spid)

            attr_list = etree.SubElement(cBhvr_s, qn('p:attrNameLst'))
            attr_name = etree.SubElement(attr_list, qn('p:attrName'))
            attr_name.text = 'style.visibility'

            p_to = etree.SubElement(p_set, qn('p:to'))
            str_val = etree.SubElement(p_to, qn('p:strVal'))
            str_val.set('val', 'visible')

            # Fade effect
            anim_eff = etree.SubElement(child_anim, qn('p:animEffect'))
            anim_eff.set('transition', 'in')
            anim_eff.set('filter', 'fade')

            cBhvr_f = etree.SubElement(anim_eff, qn('p:cBhvr'))
            cTn_f = etree.SubElement(cBhvr_f, qn('p:cTn'))
            cTn_f.set('id', nid())
            cTn_f.set('dur', '500')

            tgt_f = etree.SubElement(cBhvr_f, qn('p:tgtEl'))
            sp_f = etree.SubElement(tgt_f, qn('p:spTgt'))
            sp_f.set('spid', spid)

    # Sequence navigation
    prev_cl = etree.SubElement(seq, qn('p:prevCondLst'))
    prev_c = etree.SubElement(prev_cl, qn('p:cond'))
    prev_c.set('evt', 'onPrev')
    prev_c.set('delay', '0')
    prev_t = etree.SubElement(prev_c, qn('p:tgtEl'))
    etree.SubElement(prev_t, qn('p:sldTgt'))

    next_cl = etree.SubElement(seq, qn('p:nextCondLst'))
    next_c = etree.SubElement(next_cl, qn('p:cond'))
    next_c.set('evt', 'onNext')
    next_c.set('delay', '0')
    next_t = etree.SubElement(next_c, qn('p:tgtEl'))
    etree.SubElement(next_t, qn('p:sldTgt'))

# ═══════════════════════════════════════════════════════════════════════
# REUSABLE SLIDE BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def _finish(slide, num, notes, anim_groups=None):
    """Add logo, slide number, transition, animations, and notes."""
    add_logo(slide)
    add_slide_num(slide, num)
    add_fade_transition(slide)
    if anim_groups:
        try:
            add_animations(slide, anim_groups)
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
        s = add_bullets(slide, bullets, MX, top, SLW,
                        CH - (top - CT) - Inches(0.3))
        left_shapes.append(s)

    if bottom_text:
        s = add_text(slide, bottom_text, MX, Inches(6.4), CW, Inches(0.5),
                     size=Pt(13), color=LGRAY, italic=True)
        left_shapes.append(s)

    img = add_image(slide, image_key, SRL, CT, width=SRW)
    _finish(slide, num, notes, [left_shapes, [img]])
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
    _finish(slide, num, notes, [[bul]])
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

    _finish(slide, num, notes, [[lt, lb], [rt, rb]])
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

    img = add_image(slide, image_key, MX, top, width=CW)

    if bottom_text:
        add_text(slide, bottom_text, MX, Inches(6.3), CW, Inches(0.5),
                 size=Pt(13), color=LGRAY, italic=True)

    _finish(slide, num, notes, [[img]])
    return slide

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
             MX, Inches(1.8), CW, Inches(0.5),
             size=Pt(20), color=LGRAY, align=PP_ALIGN.CENTER)

    pb = add_play_button(slide,
                         SL_W / 2 - Inches(0.9), Inches(2.8), Inches(1.8))

    add_text(slide, "Opening Demo: 33-Word Perfect Lip Reading",
             MX, Inches(5.0), CW, Inches(0.4),
             size=Pt(16), color=TEAL, align=PP_ALIGN.CENTER)
    add_text(slide, "▸ IEa7qEkMvfQ_3__c5447488_with_hyp.mp4",
             MX, Inches(5.5), CW, Inches(0.3),
             size=Pt(11), color=MGRAY, align=PP_ALIGN.CENTER)

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

    # Pipeline architecture image
    img = add_image(slide, "pipeline", MX, CT, width=CW)

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
                      size=Pt(12), color=WHITE, align=PP_ALIGN.CENTER)
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
             size=Pt(12), color=MGRAY, italic=True)

    _finish(slide, 3,
        "Three components. Visual encoder (AV-HuBERT) is frozen — pre-trained "
        "on LRS3 lip-reading data. It outputs 1024-dim features per frame. A "
        "linear projection maps to 4096-dim (LLM input space). Then LLaMA-2-7B "
        "generates text. Key: only the LoRA adapters and projection layer are "
        "trained — 12.6M of 7B parameters. And the LLM is swappable: Llama 3.1 "
        "8B has the same hidden dimension, making it a trivial 1-2 hour swap.",
        [[img], blocks])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════

def slide_04(prs):
    build_split(prs, 4, "The Benchmark: Paper vs Reality", "P2_paper",
        big_num="25.4%", num_color=TEAL,
        num_label="WER on LRS3 (TED Talks)",
        bullets=[
            "Curated data, controlled conditions",
            ("Real-world YouTube: 64.1% WER — 2.5× worse", {"color": CORAL}),
        ],
        bottom_text="Two questions: How does this hold on real-world video? "
                    "And is WER even the right metric?",
        notes="The paper claims 25.4% Word Error Rate on LRS3 — a curated dataset "
              "of TED talks with clear speech, frontal faces, good lighting. Our "
              "question: what happens on real-world YouTube video? The chart on the "
              "right previews the answer: 64.1% WER, 2.5x worse. And more "
              "importantly — is WER even the right way to measure this?")

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
    add_text(slide, "WER 33%  •  IS 3.0 — Unintelligible",
             rx + Inches(0.3), by + Inches(0.2), bw - Inches(0.6), Inches(0.4),
             size=Pt(14), color=RED, bold=True)
    add_text(slide, 'Ref: "today i\'m talking with admiral mcrae"\n'
                    'Hyp: "today i\'m talking with animal migratory"',
             rx + Inches(0.3), by + Inches(0.8), bw - Inches(0.6), Inches(2.5),
             size=Pt(15), color=WHITE)

    # Bottom
    add_text(slide,
             "WER says equal. Meaning says opposite. So we built a metric to "
             "capture this.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 6,
        "Same WER, opposite meaning. Left: minor grammatical change, meaning "
        "fully preserved. Right: a name destroyed — 'admiral mcrae' becomes "
        "'animal migratory.' WER sees ~30% error in both. But one is usable "
        "and the other is garbage. This motivated our Intelligibility Score.",
        [[r1], [r2]])

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
        "IS ≥ 3.0 = Properly Captured: 39.9% — 3.5× more than WER's 11.4%",
        MX, by + bh + Inches(0.3), CW, Inches(0.4),
        size=Pt(16), color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # 5 tier bars
    tiers = [
        ("18.4% Excellent", 18.4, GREEN),
        ("21.4% Good", 21.4, TEAL),
        ("21.7% Fair", 21.7, YELLOW),
        ("22.4% Poor", 22.4, ORANGE),
        ("16.0% Failed", 16.0, RED),
    ]
    bar_y = by + bh + Inches(1.0)
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
        "failure. Methodology: LLM-distilled evaluation — Claude designed the "
        "rubric, selected signals and weights, defined tier boundaries. "
        "Validated across 16 decode configs: LLM heuristic judge r=0.925 "
        "with IS, 88.6% agreement.",
        [signal_shapes, [callout], tier_shapes])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 8 — FAILURE MODE TAXONOMY (BAR CHART)
# ═══════════════════════════════════════════════════════════════════════

def slide_08(prs):
    slide = new_slide(prs)
    add_title(slide, "10 Classified Failure Modes (900 failed segments)")
    add_accent_line(slide)

    modes = [
        ("Total Topic Drift", 15.9, 143, DRED),
        ("Phonetic Wrong Topic", 15.7, 141, RED),
        ("Accumulated Small Errors", 12.3, 111, ORANGE),
        ("Hallucination", 12.3, 111, DRED),
        ("High Error Rate", 12.1, 109, ORANGE),
        ("Entity Destruction", 12.0, 108, RED),
        ("Content Word Errors", 10.7, 96, YELLOW),
        ("Empty Output", 7.8, 70, MGRAY),
        ("Truncation", 1.1, 10, MGRAY),
        ("Over-generation", 0.1, 1, MGRAY),
    ]

    bar_h = Inches(0.36)
    bar_gap = Inches(0.1)
    label_w = Inches(3.2)
    max_bar_w = Inches(6.5)
    bar_x = MX + label_w + Inches(0.2)
    start_y = CT

    bar_shapes = []
    for i, (name, pct, count, color) in enumerate(modes):
        y = start_y + i * (bar_h + bar_gap)
        # Label
        add_text(slide, name, MX, y, label_w, bar_h,
                 size=Pt(12), color=WHITE, align=PP_ALIGN.RIGHT)
        # Bar
        w = max(Inches(0.1), int(max_bar_w * pct / 16.0))
        bar = add_rect(slide, bar_x, y, w, bar_h, fill_color=color)
        bar_shapes.append(bar)
        # Value label
        add_text(slide, f"{pct}% ({count})",
                 bar_x + w + Inches(0.1), y, Inches(1.5), bar_h,
                 size=Pt(11), color=LGRAY)

    add_text(slide,
             "Failures are diverse — no single fix. Each roadmap phase "
             "targets specific modes.",
             MX, Inches(6.4), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True)

    _finish(slide, 8,
        "900 failed segments classified into 10 failure modes. The top two — "
        "topic drift and phonetically-similar-wrong-topic — account for 31.6%. "
        "Hallucination (12.3%) is the most dangerous: fluent, confident, "
        "completely fabricated. Entity destruction (12.0%) loses names and "
        "numbers. This taxonomy maps directly to our roadmap.",
        [bar_shapes])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 9 — PERFORMANCE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════

def slide_09(prs):
    build_full_image(prs, 9, "Distribution Across 13 Experiments", "boxplot",
        subtitle=None,
        bottom_text="Most segments: 50-80% WER. Stable core of ~11% "
                    "always-good segments across all configs.",
        notes="This boxplot shows WWER distribution across all 13 decode "
              "experiments. The box is consistently in the 50-80% range. "
              "About 11% of segments are always good regardless of parameters, "
              "and about 16% are always bad. The bottleneck is the visual "
              "encoder, not decode strategy.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 10 — WHY THE GAP: ROOT CAUSES
# ═══════════════════════════════════════════════════════════════════════

def slide_10(prs):
    build_split(prs, 10, "Three Root Causes — With Data", "wer_duration",
        bullets=[
            ("Domain Mismatch — Business: IS 3.08, 57% captured (best). "
             "DIY/Home: IS 2.13, 30% (worst)", {"bold": True}),
            ("Short Segments — 5-10 words: 32% captured, 74% WER. "
             "20+ words: 49% captured, 55% WER", {}),
            ("Hallucination — LLM prior overwhelms weak visual signal. "
             "15.9% topic drift, 12.3% hallucination",
             {"color": CORAL}),
        ],
        notes="Three root causes. Domain mismatch: the model was trained on "
              "formal TED talks, so business/finance content works best (57% "
              "captured). DIY/home improvement is worst (30%). Short segments "
              "fail catastrophically — under 10 words gives only 32% capture "
              "rate. And hallucination: when the visual signal is weak, the "
              "LLM's language prior takes over.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 11 — NAMED ENTITY ACCURACY
# ═══════════════════════════════════════════════════════════════════════

def slide_11(prs):
    build_split(prs, 11, "NEA F1: 38.8% — The Largest Differentiator",
        "nea_scatter",
        bullets=[
            "Names, numbers, proper nouns — what context cannot recover",
            ("NEA F1: 74% vs 16% (gap: 58pp — LARGEST)", {"bold": True}),
            "Semantic: 0.74 vs 0.24",
            "Phonetic: 0.81 vs 0.38",
            ("NEA contributes 17.3% of IS variance — disproportionate to "
             "its 15% weight", {"color": TEAL}),
        ],
        notes="Named Entity Accuracy is the single largest differentiator "
              "between success and failure: 74% vs 16%, a 58 percentage "
              "point gap. You can guess a missing 'the' from context, but "
              "you cannot recover 'Admiral McRae' if the model says 'animal "
              "migratory.'")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 12 — 13 TUNING EXPERIMENTS
# ═══════════════════════════════════════════════════════════════════════

def slide_12(prs):
    slide = new_slide(prs)
    add_title(slide, "Systematic Parameter Search: 13 Configurations")
    add_accent_line(slide)

    col_w = Inches(5.5)
    gap = Inches(1.13)

    # Left column — Parameters Tested
    lt = add_text(slide, "Parameters Tested", MX, CT, col_w, Inches(0.35),
                  size=Pt(17), color=TEAL, bold=True)
    lb = add_bullets(slide, [
        "Beam size (5-50)",
        "Length penalty (-0.5 to 2.0)",
        "Temperature (0.3-1.5)",
        "Sampling strategy",
        "Repetition penalty",
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
    ], rx, CT + Inches(0.45), col_w, Inches(3.0))

    # Right image
    img = add_image(slide, "empty_halluc", rx, CT + Inches(2.8), width=col_w)

    _finish(slide, 12,
        "13 systematic experiments across beam size, length penalty, "
        "temperature, and sampling. Config J achieved the best IS. Key "
        "trade-off: eliminated all 70 empty outputs but added 41 "
        "hallucinations. Net IS gain: only +0.08.",
        [[lt, lb], [rt, rb, img]])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 13 — LIMITS OF TUNING
# ═══════════════════════════════════════════════════════════════════════

def slide_13(prs):
    build_split(prs, 13, "Tuning Is Mitigation, Not a Cure", "P4_lenpen",
        bullets=[
            ("Config J: eliminates empties but doubles hallucinations",
             {"color": CORAL}),
            "Net IS gain: only +0.08 across 1,497 segments",
            "Cross-config proof: per-segment rankings identical (r > 0.92)",
            ('"Hard" and "easy" segments stay the same — '
             "bottleneck is the visual encoder", {"bold": True}),
            ("Three levers remain: more data, stronger LLM, smart prompts",
             {"color": TEAL}),
        ],
        notes="Tuning is mitigation, not a cure. Config J's fundamental "
              "trade-off: silent failures (empties) vs noisy failures "
              "(hallucinations). Cross-config analysis proves: per-segment "
              "IS rankings are nearly identical across all 16 configs "
              "(r > 0.92). The bottleneck is the visual encoder. Three "
              "levers: (1) scale data, (2) swap LLM, (3) smart prompts.")

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
        ["Entity Lost", "talking with admiral mcrae", "talking with animal migratory", "33%", "3.0"],
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
        "Row 3: same WER range but a name destroyed, meaning lost. Row 4: "
        "complete hallucination — 'carry strap' becomes 'holocaust denier.' "
        "This is why WER alone is insufficient.",
        [[tbl]])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 15 — LIVE DEMO (VIDEO)
# ═══════════════════════════════════════════════════════════════════════

def slide_15(prs):
    slide = new_slide(prs)
    add_title(slide, "Demo: Three Videos")
    add_accent_line(slide)

    add_text(slide, "Perfect  →  Near-miss  →  Hallucination",
             MX, Inches(1.6), CW, Inches(0.4),
             size=Pt(20), color=TEAL, align=PP_ALIGN.CENTER)

    pb = add_play_button(slide,
                         SL_W / 2 - Inches(0.9), Inches(2.5), Inches(1.8))

    add_text(slide, "Three demonstrations played from external files.",
             MX, Inches(4.8), CW, Inches(0.3),
             size=Pt(14), color=LGRAY, align=PP_ALIGN.CENTER)

    # Video file list
    vids = [
        "1. d8BR6hsvzoY — 'buy one get one free' (WER 0%)",
        "2. -POZpyVCN8k — 'admiral mcrae' → 'animal migratory'",
        "3. 00MUdHQ7GGY — hallucination: fabricates narrative (WER 100%)",
    ]
    add_bullets(slide, vids, MX + Inches(2), Inches(5.2), CW - Inches(4),
                Inches(1.5), size=Pt(12), color=LGRAY, bullet_color=MGRAY)

    _finish(slide, 15,
        "PLAY VIDEOS in order: (1) d8BR6hsvzoY_31 — 'buy one get one free' "
        "(WER 0%, short and punchy). (2) -POZpyVCN8k_9 — 'admiral mcrae' "
        "becomes 'animal migratory' (funny near-miss). (3) 00MUdHQ7GGY_8 — "
        "hallucination: fabricates 'David Irving' narrative (WER 100%).")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 16 — RESEARCH OUTPUT
# ═══════════════════════════════════════════════════════════════════════

def slide_16(prs):
    build_bullets(prs, 16,
        "Eight Research Reports + Training Analysis",
        [
            "Executive Assessment — reality gap, quality tiers, 1,497 segments",
            "Hyperparameter Tuning — 13 experiments, parameter sensitivity",
            "Prompt Engineering — context injection, 7 prompt strategies",
            "Confidence Scoring — beam score extraction, quality filtering",
            "N-Best Aggregation — ROVER/MBR hypothesis combination",
            "Fine-Tuning Analysis — LoRA domain adaptation strategy",
            "Intelligibility Scoring — 6-signal composite metric, failure taxonomy",
            "LLM Upgrade Analysis — Llama 3.1 8B drop-in, data scaling, GER",
            ("+ Exp A Training Report — overfitting analysis, 10 diagnostic plots",
             {"color": TEAL}),
        ],
        "Eight formal research reports plus the Exp A training analysis. Each "
        "report is a deep dive with methodology, results, and recommendations. "
        "The Intelligibility Score report is the main methodological "
        "contribution. The LLM Upgrade Analysis maps the path forward.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 17 — PIPELINE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def slide_17(prs):
    build_full_image(prs, 17, "8-Stage Automated Pipeline", "pipeline",
        subtitle="3 research repos → single orchestrated system",
        notes="The pipeline orchestrates three separate research codebases "
              "into a single automated system. Eight stages: video "
              "normalization, ASR transcription, mouth cropping, LRS3 format "
              "conversion, manifest generation, feature clustering, LLM "
              "decode, and output generation. Each stage is a separate "
              "module with its own tests.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 18 — ENGINEERING CHALLENGES
# ═══════════════════════════════════════════════════════════════════════

def slide_18(prs):
    build_two_col(prs, 18, "37 Bugs Fixed: Research Code → Production",
        "Critical Fixes", [
            "NVENC silent corruption (destroyed 43% of videos)",
            "HDR/10-bit tone mapping",
            "Cython extension compilation",
            "fairseq patching",
            "spaCy offline installation",
            "Docker networking",
            "Python venv conflicts",
        ],
        "Result", [
            "Any format: MP4, MKV, AVI, MOV",
            "Any resolution, any codec",
            "GPU detection with CPU fallback",
            ("All 37 bugs documented with root cause", {"color": TEAL}),
        ],
        "37 bugs found and fixed turning research code into production. "
        "The most critical: NVENC silent video corruption that destroyed "
        "43% of processed videos without any error message. Every bug "
        "documented with root cause analysis.",
        left_color=CORAL, right_color=GREEN)

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
        [[r1], [r2]])

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
    ]

    cw = Inches(3.6)
    ch = Inches(4.0)
    gap = Inches(0.5)
    total = 3 * cw + 2 * gap
    cx = (SL_W - total) / 2
    cy = CT + Inches(0.2)

    card_shapes = []
    for i, (title, desc, color) in enumerate(cards):
        x = cx + i * (cw + gap)
        r = add_rect(slide, x, cy, cw, ch, fill_color=NAVY2,
                     border_color=color, border_width=Pt(2), corner_radius=True)
        add_text(slide, title, x + Inches(0.25), cy + Inches(0.3),
                 cw - Inches(0.5), Inches(0.5),
                 size=Pt(18), color=color, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, desc, x + Inches(0.25), cy + Inches(1.0),
                 cw - Inches(0.5), Inches(2.5),
                 size=Pt(14), color=WHITE)
        card_shapes.append(r)

    _finish(slide, 21,
        "Three intelligent features. Transcription reuse: if you manually "
        "correct a segment's transcription, it persists across all future "
        "runs. Golden k-means: a 1,396-video baseline model ensures "
        "consistent clustering. Smart segmentation: configurable overlap "
        "ensures context isn't lost at boundaries.",
        [card_shapes])

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
            "Failure mode classification (10 modes)",
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
    ], MX + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(14), bullet_color=CORAL)

    # Middle column — IS Says (teal)
    mx2 = MX + col_w + gap
    r2 = add_rect(slide, mx2, CT, col_w, Inches(2.2), fill_color=NAVY2,
                  border_color=TEAL, border_width=Pt(2), corner_radius=True)
    add_text(slide, "IS Says", mx2 + Inches(0.2), CT + Inches(0.1),
             col_w - Inches(0.4), Inches(0.35),
             size=Pt(16), color=TEAL, bold=True)
    add_bullets(slide, [
        ("39.9% properly captured", {"bold": True}),
        "43-51% context-recoverable",
        "Validated across 16 decode configs",
        "LLM judge: 88.6% agreement, r=0.925",
    ], mx2 + Inches(0.2), CT + Inches(0.55), col_w - Inches(0.4),
       Inches(1.2), size=Pt(13), bullet_color=TEAL)

    # Right — image
    img = add_image(slide, "P1_quality", MX + 2 * col_w + 2 * gap, CT,
                    width=img_w)

    # Bottom
    add_text(slide,
             "The gap is real — but WER dramatically overstates failure. "
             "40% already works.",
             MX, Inches(6.3), CW, Inches(0.5),
             size=Pt(14), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 24,
        "This is the turning point. WER says 11.4% usable. Our "
        "Intelligibility Score says 39.9% properly captured — 3.5x more. "
        "And 43-51% is context-recoverable. This isn't wishful thinking: "
        "IS is validated across all 16 decode configs.",
        [[r1], [r2, img]])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 25 — RESEARCH ROADMAP (STAIRCASE)
# ═══════════════════════════════════════════════════════════════════════

def slide_25(prs):
    slide = new_slide(prs)
    add_title(slide, "Five Phases — From 67% to Target 27-42% WER")
    add_accent_line(slide)

    phases = [
        ("Phase 1", "Surface the good 40%", "Confidence scoring (2-4 hrs)", TEAL),
        ("Phase 2", "Improve the fair 22%", "N-best aggregation (-5 to -15%)", TEAL),
        ("Phase 3", "LLM swap + smart prompts", "Llama 3.1 8B + prompts (-8 to -18pp)", GREEN),
        ("Phase 4", "Scale data 20K-50K", "Fine-tune (-15 to -25pp)", GREEN),
        ("Phase 5", "GER post-processing", "No retraining needed (-8 to -15pp)", LGRAY),
    ]

    # Staircase on left side
    step_w = Inches(5.8)
    step_h = Inches(0.85)
    step_indent = Inches(0.35)
    start_y = CT
    start_x = MX

    step_shapes = []
    for i, (phase, desc, detail, color) in enumerate(phases):
        x = start_x + i * step_indent
        y = start_y + i * (step_h + Inches(0.08))
        w = step_w - i * step_indent
        r = add_rect(slide, x, y, w, step_h, fill_color=NAVY2,
                     border_color=color, border_width=Pt(1.5), corner_radius=True)
        # Phase label + description
        add_rich_text(slide, [
            [(phase, {"size": Pt(13), "color": color, "bold": True}),
             (f"  {desc}", {"size": Pt(13), "color": WHITE})],
            [(detail, {"size": Pt(11), "color": LGRAY, "italic": True})],
        ], x + Inches(0.2), y + Inches(0.05), w - Inches(0.4), step_h - Inches(0.1))
        step_shapes.append(r)

    # WER trajectory image on right
    img = add_image(slide, "P3_trajectory",
                    SRL - Inches(0.2), CT, width=SRW + Inches(0.2))

    add_text(slide,
             "Combined target: 27-42% WER. Multiplicative scaling law "
             "(ICLR 2024).",
             MX, Inches(6.35), CW, Inches(0.4),
             size=Pt(13), color=LGRAY, italic=True, align=PP_ALIGN.CENTER)

    _finish(slide, 25,
        "Five phases, each targeting different bottlenecks. Phase 1 is "
        "immediate: confidence scoring to surface the 40% that's already "
        "good (2-4 hours). Phase 2: N-best aggregation. Phase 3: swap LLM "
        "to Llama 3.1 8B plus smart prompts. Phase 4: the biggest gain — "
        "scale training data. Phase 5: GER post-processing. Key: ICLR 2024 "
        "shows these gains are multiplicative.",
        [step_shapes, [img]])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 26 — PHASE 1: CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════════════

def slide_26(prs):
    build_bullets(prs, 26,
        "Phase 1: Automatic Quality Flagging",
        [
            "IS proves 40% is good — beam scores can flag it at decode time",
            "No additional inference needed — scores already computed",
            ("Effort: 2-4 hours implementation", {"color": TEAL, "bold": True}),
            "Priority: Business/Finance segments (57% captured) most reliable",
            "Short segments (<10 words, 32%) need lower confidence thresholds",
            ("This is the immediate next step", {"bold": True}),
        ],
        "Phase 1 is the quick win. We know 40% is already good; beam scores "
        "computed during decode can flag quality automatically. "
        "Business/Finance content should get highest confidence. 2-4 hours "
        "of implementation.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 27 — PHASE 2: N-BEST AGGREGATION
# ═══════════════════════════════════════════════════════════════════════

def slide_27(prs):
    build_bullets(prs, 27,
        "Phase 2: Exploit All 20 Hypotheses",
        [
            "Currently discarding 19 of 20 beam candidates",
            "ROVER/MBR — established technique, consistent gains",
            ("Expected: 5-15% relative improvement", {"color": TEAL, "bold": True}),
            "Targets: Accumulated Small Errors (12.3%) and Content Word "
            "Errors (10.7%)",
            'Moves "fair" tier segments up to "good"',
        ],
        "We're currently throwing away 19 of 20 hypotheses. N-best "
        "aggregation (ROVER/MBR) is an established technique that combines "
        "multiple hypotheses to reduce errors. Targets the 'death by 1000 "
        "cuts' failure mode.")

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 28 — FINE-TUNING + DATA SCALING
# ═══════════════════════════════════════════════════════════════════════

def slide_28(prs):
    slide = new_slide(prs)
    add_title(slide, "Domain Adaptation: Data Is the Bottleneck")
    add_accent_line(slide)

    # Dashboard image — top half
    img = add_image(slide, "ft_dashboard", MX, CT, width=CW,
                    height=Inches(2.8))

    # Two columns below
    col_w = Inches(5.5)
    gap = Inches(1.13)
    col_y = CT + Inches(3.0)

    # Left — Exp A/B Results
    lt = add_text(slide, "Exp A/B Results", MX, col_y, col_w, Inches(0.3),
                  size=Pt(15), color=CORAL, bold=True)
    lb = add_bullets(slide, [
        "Exp A (r=16): best val acc 62.94% at epoch 2, severe overfitting",
        ("Exp B (r=64): 3.1pp WORSE — more params = faster overfitting",
         {"color": CORAL}),
        ("KEY: 1,273 segments too small for LoRA generalization",
         {"bold": True}),
    ], MX, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    # Right — Data Scaling
    rx = MX + col_w + gap
    rt = add_text(slide, "Data Scaling (ICLR 2024)", rx, col_y, col_w,
                  Inches(0.3), size=Pt(15), color=TEAL, bold=True)
    rb = add_bullets(slide, [
        "5K segments: 55-60% WER",
        "20K segments: 45-50% / 40-45% (Llama 3.1)",
        "50K segments: 40-45% / 35-40%",
        ("AVSpeech: 290K videos available", {"color": TEAL}),
    ], rx, col_y + Inches(0.35), col_w, Inches(2.0), size=Pt(13))

    _finish(slide, 28,
        "Exp A: 1,273 segments, 17 hours on Tesla T4. Best validation "
        "accuracy 62.94% at epoch 2 out of 19 — severe overfitting. Exp B "
        "with r=64: 3.1pp WORSE. This is NOT a model capacity problem. "
        "Data scaling projections: 20K segments brings WER to 45-50%. "
        "AVSpeech has 290K videos — data curation is tractable.",
        [[img], [lt, lb], [rt, rb]])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 29 — LLM UPGRADE + ADVANCED CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════

def slide_29(prs):
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

    _finish(slide, 29,
        "Three columns of future capability. Left: LLM swap to Llama 3.1 "
        "8B is trivial — same hidden dimension, 1-2 hours. Center: 7 prompt "
        "strategies are a force multiplier — more effective on stronger "
        "models. GER uses N-best hypotheses + correction LLM for +8-15pp "
        "with no retraining. Right: Arabic support exists, VALLR achieves "
        "18.7% WER with a 3B model.",
        [col_shapes])

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 30 — SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def slide_30(prs):
    slide = new_slide(prs)
    add_title(slide, "Key Takeaways")
    add_accent_line(slide)

    takeaways = [
        ("1", "Rigorous assessment: 2.5× WER gap on 1,497 segments. "
              "Novel IS metric reveals 40% properly captured. "
              "10 classified failure modes."),
        ("2", "Production system delivered: standalone container, 37 bugs "
              "fixed, 8-stage pipeline, 37 tests, 8 research reports."),
        ("3", "Data is the bottleneck: Exp A/B proved 1,273 segments too "
              "small. Multiplicative scaling law: stronger LLM + more data "
              "compounds."),
        ("4", "Actionable roadmap to 27-42% WER: LLM swap + smart prompts "
              "+ data scaling + GER. Each targets a different bottleneck."),
    ]

    point_h = Inches(1.1)
    gap = Inches(0.15)
    start_y = CT

    point_shapes = []
    for i, (num, text) in enumerate(takeaways):
        y = start_y + i * (point_h + gap)

        # Number circle
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, MX, y + Inches(0.15), Inches(0.6), Inches(0.6))
        circle.fill.solid()
        circle.fill.fore_color.rgb = TEAL
        circle.line.fill.background()
        add_text(slide, num, MX + Inches(0.05), y + Inches(0.15),
                 Inches(0.5), Inches(0.6),
                 size=Pt(22), color=WHITE, bold=True, align=PP_ALIGN.CENTER)

        # Text
        tb = add_text(slide, text,
                      MX + Inches(0.85), y, CW - Inches(1.0), point_h,
                      size=Pt(15), color=WHITE)
        point_shapes.append(tb)

    _finish(slide, 30,
        "Four takeaways. One: we know exactly where we stand — rigorous "
        "assessment with a novel metric that reveals the true picture. "
        "Two: production system delivered and deployed. Three: data, not "
        "model capacity, is the bottleneck. Four: clear roadmap from 67% "
        "to 27-42% WER.",
        [point_shapes])

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    prs = Presentation()
    prs.slide_width = SL_W
    prs.slide_height = SL_H

    print("Generating 30-slide presentation...")

    builders = [
        slide_01, slide_02, slide_03, slide_04, slide_05,
        slide_06, slide_07, slide_08, slide_09, slide_10,
        slide_11, slide_12, slide_13, slide_14, slide_15,
        slide_16, slide_17, slide_18, slide_19, slide_20,
        slide_21, slide_22, slide_23, slide_24, slide_25,
        slide_26, slide_27, slide_28, slide_29, slide_30,
    ]

    for i, builder in enumerate(builders, 1):
        print(f"  Slide {i:2d}/30 ...", end=" ")
        try:
            builder(prs)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"\nSaved: {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
