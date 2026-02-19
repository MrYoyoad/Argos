# Argos Document Generator Style Guide

Standard formatting rules for all python-docx report generators.

## Header

- Logo (logo.png) on the **left** margin
- "Argos — The Orchard" on the **right** margin via tab stop
- 8pt Calibri, gray italic
- No "INTERNAL" or classification labels
- Use `WD_TAB_ALIGNMENT.RIGHT` tab stop at `page_width - left_margin - right_margin`

```python
text_width = section.page_width - section.left_margin - section.right_margin
hp.paragraph_format.tab_stops.add_tab_stop(text_width, WD_TAB_ALIGNMENT.RIGHT)
hp.add_run("\t")
run = hp.add_run("Argos \u2014 The Orchard")
```

## Cover Page

1. Two spacer paragraphs at top
2. Peacock logo centered, 2.0-2.5 inches — use `doc.add_picture()` (not `run.add_picture()`)
3. "ARGOS" title, 48pt bold, primary color
4. Document subtitle, 22pt
5. "The Orchard", 20pt
6. Author: "Yoad Oxman", 14pt, centered
7. Metadata key-value pairs (centered)
8. Page break

## Table of Contents

Use a **standard Word TOC field** (not manual hyperlinks):

```python
paragraph = doc.add_paragraph()
run = paragraph.add_run()
# begin field
fld_begin = OxmlElement('w:fldChar')
fld_begin.set(qn('w:fldCharType'), 'begin')
run._r.append(fld_begin)
instr = OxmlElement('w:instrText')
instr.set(qn('xml:space'), 'preserve')
instr.text = ' TOC \\o "1-2" \\h \\z \\u '
run._r.append(instr)
# separate
fld_sep = OxmlElement('w:fldChar')
fld_sep.set(qn('w:fldCharType'), 'separate')
run._r.append(fld_sep)
# placeholder entries (shown until Word updates the field)
for title in toc_titles:
    placeholder = paragraph.add_run(title + "\n")
# end field
fld_end_run = paragraph.add_run()
fld_end = OxmlElement('w:fldChar')
fld_end.set(qn('w:fldCharType'), 'end')
fld_end_run._r.append(fld_end)
```

Set `updateFields` so Word auto-populates on open:

```python
settings = doc.settings.element
update_fields = OxmlElement('w:updateFields')
update_fields.set(qn('w:val'), 'true')
settings.append(update_fields)
```

Push the TOC heading down slightly from the top of the page (3 zero-height spacer paragraphs).

## Page Breaks After Tables

When a table is the last element before a page break, use a tight break to avoid a visible blank gap:

```python
def _tight_page_break(doc):
    last_p = doc.paragraphs[-1]
    last_p.add_run().add_break(WD_BREAK.PAGE)
```

This adds the break to the table's trailing paragraph instead of creating a new empty one.

## Logo Paths

Logos live in `docs/_research-tools/assets/`:
- `logo.png` — header (orchard tree)
- `peacock.png` — cover page

Reference via: `ASSETS_DIR = SCRIPT_DIR.parent / "assets"`

## General Rules

- Font: Calibri throughout
- No "INTERNAL" or "Classification" labels anywhere
- Author "Yoad Oxman" on every cover page
- A4 page size (21.0 x 29.7 cm), 2.5 cm side margins, 2.0 cm top/bottom
- Page numbers in footer (centered, 8pt gray)
