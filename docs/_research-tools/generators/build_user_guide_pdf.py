#!/usr/bin/env python3
"""Build the VSP user guide PDF from its source markdown.

Self-contained ReportLab renderer. No external markdown / pandoc / weasyprint
dependency — only `reportlab` (already installed in the system Python on
the EC2 box). Matches docs/_research-tools/generators/STYLE_GUIDE.md
visual conventions where feasible (navy headings, sans body, table grid).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Image,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    PageBreak,
)


SRC = Path("/home/ubuntu/docs/guides/user-guide-vsp-pipeline.md")
OUT = Path("/home/ubuntu/docs/guides/user-guide-vsp-pipeline.pdf")
LOGO = Path("/home/ubuntu/docs/_research-tools/assets/logo.png")


# -- colours (match STYLE_GUIDE navy palette for docx) ---------------------
NAVY_DEEP = HexColor("#1a3a5c")
NAVY_MID = HexColor("#2a5a8c")
NAVY_LITE = HexColor("#3a6a9c")
NAVY_TINT = HexColor("#f5f8fc")
INK = HexColor("#1a1a1a")
MUTED = HexColor("#666666")
TIER_GREEN = HexColor("#2e7d32")
TIER_YELLOW = HexColor("#b8860b")
TIER_RED = HexColor("#c62828")
RULE_GREY = HexColor("#cccccc")
CODE_BG = HexColor("#f0f3f8")


# -- styles -----------------------------------------------------------------
BASE_SS = getSampleStyleSheet()

S_TITLE = ParagraphStyle(
    "Title",
    parent=BASE_SS["Title"],
    fontName="Helvetica-Bold",
    fontSize=26,
    leading=32,
    textColor=NAVY_DEEP,
    spaceAfter=10,
)
S_SUBTITLE = ParagraphStyle(
    "Subtitle",
    parent=BASE_SS["Normal"],
    fontName="Helvetica",
    fontSize=12,
    leading=16,
    textColor=MUTED,
    spaceAfter=4,
)
S_H1 = ParagraphStyle(
    "H1",
    parent=BASE_SS["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=NAVY_DEEP,
    spaceBefore=16,
    spaceAfter=8,
    keepWithNext=1,
    borderPadding=(0, 0, 4, 0),
)
S_H2 = ParagraphStyle(
    "H2",
    parent=BASE_SS["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    textColor=NAVY_MID,
    spaceBefore=12,
    spaceAfter=6,
    keepWithNext=1,
)
S_H3 = ParagraphStyle(
    "H3",
    parent=BASE_SS["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=11.5,
    leading=14,
    textColor=NAVY_LITE,
    spaceBefore=8,
    spaceAfter=4,
    keepWithNext=1,
)
S_BODY = ParagraphStyle(
    "Body",
    parent=BASE_SS["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13.5,
    textColor=INK,
    spaceAfter=5,
)
S_BULLET = ParagraphStyle(
    "Bullet",
    parent=S_BODY,
    leftIndent=14,
    bulletIndent=2,
    spaceAfter=3,
)
S_QUOTE = ParagraphStyle(
    "Quote",
    parent=S_BODY,
    leftIndent=12,
    rightIndent=8,
    textColor=MUTED,
    fontName="Helvetica-Oblique",
    borderColor=NAVY_LITE,
    borderPadding=(4, 8, 4, 8),
    spaceBefore=4,
    spaceAfter=6,
)
S_CODE = ParagraphStyle(
    "Code",
    parent=BASE_SS["Code"],
    fontName="Courier",
    fontSize=7.0,
    leading=9.5,
    textColor=INK,
    leftIndent=8,
    rightIndent=8,
    spaceBefore=4,
    spaceAfter=8,
    backColor=CODE_BG,
    borderPadding=(4, 6, 4, 6),
    wordWrap="CJK",   # break long lines anywhere instead of overflowing the frame
)
S_FOOTER = ParagraphStyle(
    "Footer",
    parent=BASE_SS["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=MUTED,
    alignment=1,
)


# -- inline markdown ---------------------------------------------------------
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD_STAR = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDER = re.compile(r"__(.+?)__")
_ITAL_STAR = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")
_ITAL_UNDER = re.compile(r"(?<!_)_(?!\s)(.+?)(?<!\s)_(?!_)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inline(text: str) -> str:
    """Render a single line of markdown to reportlab inline-markup HTML."""

    # Pull out code spans first so their content isn't mangled.
    placeholders: list[str] = []

    def _stash(m):
        placeholders.append(m.group(1))
        return f"\x00{len(placeholders) - 1}\x00"

    text = _INLINE_CODE.sub(_stash, text)
    text = _escape(text)

    text = _LINK.sub(
        lambda m: f'<font color="#1a3a5c"><u>{m.group(1)}</u></font>', text
    )
    text = _BOLD_STAR.sub(r"<b>\1</b>", text)
    text = _BOLD_UNDER.sub(r"<b>\1</b>", text)
    text = _ITAL_STAR.sub(r"<i>\1</i>", text)
    text = _ITAL_UNDER.sub(r"<i>\1</i>", text)

    # Re-insert code spans.
    def _restore(m):
        idx = int(m.group(1))
        body = _escape(placeholders[idx])
        return f'<font name="Courier" color="#1a1a1a" backColor="#f0f3f8">{body}</font>'

    text = re.sub(r"\x00(\d+)\x00", _restore, text)
    return text


# -- table colouring (so "Green/Yellow/Red" cells visually carry meaning) ---
TIER_WORDS = {
    "green": TIER_GREEN,
    "trust": TIER_GREEN,
    "yellow": TIER_YELLOW,
    "salvage": TIER_YELLOW,
    "red": TIER_RED,
    "purple": TIER_RED,
    "strip": TIER_RED,
}


def _maybe_tier_colour(text: str):
    """If a cell's first word is a tier label, return its colour, else None."""
    plain = re.sub(r"<[^>]+>", "", text).strip().lower()
    plain = re.sub(r"\*\*", "", plain)
    # match either at start or after a leading marker
    for k, v in TIER_WORDS.items():
        if plain.startswith(k):
            return v
    return None


# -- markdown parser --------------------------------------------------------
class MDParser:
    """Tiny line-oriented markdown parser sufficient for this guide.

    Supports: H1-H4, paragraphs, unordered lists (- / *), ordered lists
    (1. style), block quotes (>), fenced code blocks (```), pipe tables,
    horizontal rules (---), inline bold/italic/code/link.
    """

    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.i = 0
        self.story: list = []

    # ---- helpers ----
    def _peek(self, off=0):
        j = self.i + off
        return self.lines[j] if 0 <= j < len(self.lines) else None

    def _take(self):
        line = self.lines[self.i]
        self.i += 1
        return line

    # ---- emit ----
    def _para(self, text: str, style=S_BODY):
        if not text.strip():
            return
        self.story.append(Paragraph(_inline(text), style))

    def _spacer(self, h=4):
        self.story.append(Spacer(1, h))

    # ---- block parsers ----
    def _consume_code(self):
        self._take()  # opening ```
        buf = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.strip().startswith("```"):
                self.i += 1
                break
            buf.append(line)
            self.i += 1
        body = "\n".join(buf).rstrip()
        if body:
            self.story.append(Preformatted(body, S_CODE))
            self._spacer(2)

    def _consume_list(self):
        items: list[tuple[str, str]] = []  # (marker, text)
        while self.i < len(self.lines):
            line = self.lines[self.i]
            m = re.match(r"^(\s*)([-*])\s+(.*)$", line)
            n = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
            if m:
                items.append(("bullet", m.group(3)))
                self.i += 1
            elif n:
                items.append((n.group(2) + ".", n.group(3)))
                self.i += 1
            elif (
                line.startswith("  ")
                and items
                and not line.lstrip().startswith(">")
                and not line.lstrip().startswith("```")
            ):
                # continuation
                marker, prev = items[-1]
                items[-1] = (marker, prev + " " + line.strip())
                self.i += 1
            else:
                break
        bullet_flowables = []
        for marker, txt in items:
            bullet = "•" if marker == "bullet" else marker
            bullet_flowables.append(
                Paragraph(
                    f'<para leftIndent="14" bulletIndent="2">'
                    f'<bullet>{bullet}</bullet>{_inline(txt)}</para>',
                    S_BULLET,
                )
            )

        # Keep an immediately-preceding heading attached to its list.
        # ReportLab's keepWithNext=1 on the heading is unreliable when the
        # following flowable is a Paragraph styled as a bullet; wrap the
        # heading + any trailing spacers + the bullet block in a
        # KeepTogether so they stay on the same page. Fixes the page-5
        # "Quick decision" orphan in the user guide PDF.
        heading_idx = None
        for j in range(len(self.story) - 1, -1, -1):
            fl = self.story[j]
            if isinstance(fl, Spacer):
                continue
            if isinstance(fl, Paragraph) and fl.style.name in {"H1", "H2", "H3"}:
                heading_idx = j
            break
        if heading_idx is not None:
            tail = self.story[heading_idx:]
            del self.story[heading_idx:]
            self.story.append(KeepTogether([*tail, *bullet_flowables]))
        else:
            self.story.extend(bullet_flowables)
        self._spacer(3)

    def _consume_quote(self):
        buf = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            stripped = line.lstrip()
            if stripped.startswith(">"):
                buf.append(stripped.lstrip(">").strip())
                self.i += 1
            elif line.strip() == "":
                break
            else:
                break
        if buf:
            joined = " ".join(buf)
            self.story.append(Paragraph(_inline(joined), S_QUOTE))
            self._spacer(2)

    def _consume_table(self):
        rows: list[list[str]] = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if "|" not in line:
                break
            stripped = line.strip()
            if stripped.startswith("|"):
                stripped = stripped[1:]
            if stripped.endswith("|"):
                stripped = stripped[:-1]
            cells = [c.strip() for c in stripped.split("|")]
            # separator row (---|---)
            if all(re.match(r"^:?-{3,}:?$", c) for c in cells if c):
                self.i += 1
                continue
            rows.append(cells)
            self.i += 1
        if not rows:
            return
        # Render with first row as header.
        ncols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < ncols:
                r.append("")
        # Convert each cell to a Paragraph (auto-wraps).
        cell_style = ParagraphStyle(
            "Cell",
            parent=S_BODY,
            fontSize=8.5,
            leading=11,
            spaceAfter=0,
        )
        head_style = ParagraphStyle(
            "CellHead",
            parent=cell_style,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
        data = []
        cell_colours: list[tuple[int, int, HexColor]] = []
        for ri, row in enumerate(rows):
            new_row = []
            for ci, cell in enumerate(row):
                if ri == 0:
                    new_row.append(Paragraph(_inline(cell), head_style))
                else:
                    tier = _maybe_tier_colour(cell)
                    if tier is not None:
                        col_style = ParagraphStyle(
                            "CellTier",
                            parent=cell_style,
                            textColor=tier,
                            fontName="Helvetica-Bold",
                        )
                        new_row.append(Paragraph(_inline(cell), col_style))
                    else:
                        new_row.append(Paragraph(_inline(cell), cell_style))
            data.append(new_row)
        # Column widths: even split inside content frame width (~16 cm).
        content_w = 16.0 * cm
        col_w = content_w / ncols
        t = Table(data, colWidths=[col_w] * ncols, repeatRows=1)
        ts = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_DEEP),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.4, RULE_GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, NAVY_TINT]),
        ])
        t.setStyle(ts)
        self.story.append(t)
        self._spacer(6)

    # ---- main loop ----
    def parse(self):
        while self.i < len(self.lines):
            line = self.lines[self.i]
            stripped = line.rstrip()

            # placeholder for screenshots
            if stripped.lstrip().startswith("[screenshot:"):
                self.story.append(
                    Paragraph(
                        f'<i>[Figure placeholder: {_escape(stripped.strip()[1:-1])}]</i>',
                        ParagraphStyle("Fig", parent=S_BODY, textColor=MUTED, alignment=1),
                    )
                )
                self._spacer(4)
                self.i += 1
                continue

            # horizontal rule
            if re.match(r"^\s*---+\s*$", stripped):
                self.story.append(Spacer(1, 2))
                # draw a thin grey rule by inserting a 1-row table
                rule = Table([[""]], colWidths=[16 * cm], rowHeights=[0.4])
                rule.setStyle(TableStyle([
                    ("LINEABOVE", (0, 0), (-1, 0), 0.6, RULE_GREY),
                ]))
                self.story.append(rule)
                self.story.append(Spacer(1, 4))
                self.i += 1
                continue

            # headings
            m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
            if m:
                level = len(m.group(1))
                txt = m.group(2)
                if level == 1:
                    # main document title — only fire once at top
                    if not any(isinstance(s, Paragraph) and getattr(s.style, "name", "") == "Title" for s in self.story):
                        self.story.append(Paragraph(_inline(txt), S_TITLE))
                    else:
                        self.story.append(Paragraph(_inline(txt), S_H1))
                elif level == 2:
                    self.story.append(Paragraph(_inline(txt), S_H1))
                elif level == 3:
                    self.story.append(Paragraph(_inline(txt), S_H2))
                else:
                    self.story.append(Paragraph(_inline(txt), S_H3))
                self.i += 1
                continue

            # fenced code
            if stripped.startswith("```"):
                self._consume_code()
                continue

            # block quote (flush-left or indented)
            if line.lstrip().startswith(">"):
                self._consume_quote()
                continue

            # list
            if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
                self._consume_list()
                continue

            # table (pipe-delimited)
            if "|" in stripped and self._peek(1) and re.match(r"^\s*\|?\s*:?-{3,}", self._peek(1)):
                self._consume_table()
                continue

            # blank line
            if not stripped.strip():
                self._spacer(4)
                self.i += 1
                continue

            # default: paragraph — accumulate continued lines
            buf = [stripped]
            self.i += 1
            while self.i < len(self.lines):
                nxt = self.lines[self.i]
                if not nxt.strip():
                    break
                if re.match(r"^(#{1,4})\s+", nxt):
                    break
                if nxt.lstrip().startswith(("- ", "* ", "> ", "```", "|")):
                    break
                if re.match(r"^\s*\d+\.\s+", nxt):
                    break
                buf.append(nxt.rstrip())
                self.i += 1
            self._para(" ".join(buf))

        return self.story


# -- page template (header w/ logo + footer w/ page number) ----------------
def _page_header_footer(canvas, doc):
    canvas.saveState()
    # header
    if LOGO.exists():
        try:
            canvas.drawImage(
                str(LOGO),
                doc.leftMargin,
                A4[1] - doc.topMargin + 4 * mm,
                width=14 * mm,
                height=14 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(
        A4[0] - doc.rightMargin,
        A4[1] - doc.topMargin + 9 * mm,
        "Argos — VSP Pipeline — User Guide",
    )
    # accent line under header
    canvas.setStrokeColor(NAVY_DEEP)
    canvas.setLineWidth(0.6)
    canvas.line(
        doc.leftMargin,
        A4[1] - doc.topMargin + 3 * mm,
        A4[0] - doc.rightMargin,
        A4[1] - doc.topMargin + 3 * mm,
    )
    # footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(
        A4[0] / 2.0,
        doc.bottomMargin - 8 * mm,
        f"Page {doc.page}",
    )
    canvas.drawString(
        doc.leftMargin,
        doc.bottomMargin - 8 * mm,
        "VSP — Argos / The Orchard",
    )
    canvas.drawRightString(
        A4[0] - doc.rightMargin,
        doc.bottomMargin - 8 * mm,
        "Confidential — operator copy",
    )
    canvas.restoreState()


def build():
    if not SRC.exists():
        sys.exit(f"missing source: {SRC}")
    text = SRC.read_text(encoding="utf-8")

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.6 * cm,
        bottomMargin=2.4 * cm,
        title="VSP Pipeline — User Guide",
        author="Yoad Oxman",
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="body",
        leftPadding=0,
        bottomPadding=0,
        rightPadding=0,
        topPadding=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="all", frames=[frame], onPage=_page_header_footer),
    ])

    parser = MDParser(text)
    story = parser.parse()
    doc.build(story)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
