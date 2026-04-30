#!/usr/bin/env python3
"""Stricter PPTX -> real-PowerPoint compatibility scan.

Flags the three categories most likely to break silently between
LibreOffice (where the deck is rendered for QA) and real PowerPoint
(where the deck is actually presented):

  1. Embedded video codecs that PowerPoint can't decode.
  2. Non-Latin / non-Calibri-supported glyphs.
  3. Fonts not in PowerPoint's default Mac/Windows bundle.

Usage:
    python3 scripts/build/scan_pptx_pp_compat.py path/to/deck.pptx
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

# Calibri (Office 2007+) is on every default Office install (Mac + Win).
# These are the other fonts that ship in PowerPoint's default theme set
# OR are reliably present on both Mac and Windows out-of-the-box.
SAFE_FONTS = {
    # Office default theme fonts
    "calibri", "cambria", "calibri light", "cambria math",
    # Cross-platform standards
    "arial", "arial black", "arial narrow",
    "times new roman", "times",
    "verdana", "tahoma", "trebuchet ms",
    "georgia", "courier new", "courier",
    "comic sans ms",
    "impact",
    # PowerPoint's auto-substitution placeholders
    "+mn-lt", "+mj-lt", "+mn-ea", "+mj-ea", "+mn-cs", "+mj-cs",
}

# Calibri's coverage is broad but has gaps. Glyphs outside basic Latin
# (U+0000-U+007F) plus a small set of punctuation/symbol blocks are at
# risk of font-substitution on machines without Calibri.
SAFE_UNICODE_BLOCKS = [
    (0x0000, 0x007F),  # Basic Latin
    (0x00A0, 0x00FF),  # Latin-1 Supplement
    (0x2000, 0x206F),  # General Punctuation (em/en dashes, bullets, quotes)
    (0x2190, 0x21FF),  # Arrows (→ ↓ ← ↑) — Calibri has these
    (0x2200, 0x22FF),  # Math (≥ ≤ × ÷) — Calibri has these
]


def _is_safe_glyph(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in SAFE_UNICODE_BLOCKS)


def _glyph_name(ch: str) -> str:
    try:
        return unicodedata.name(ch)
    except ValueError:
        return f"U+{ord(ch):04X}"


def _detect_video_codec(media_bytes: bytes) -> str:
    """Best-effort codec detection for an MP4 / MOV byte blob.

    Returns one of: "h264", "hevc/h265", "vp9", "av1", "unknown",
    "not-mp4", or "(short)". We look for the `ftyp` brand and any
    `avcC` / `hvcC` / `vp09` / `av01` boxes in the file header.
    """
    if len(media_bytes) < 16:
        return "(short)"
    head = media_bytes[:65536]  # search the first 64KB
    if head[4:8] != b"ftyp":
        return "not-mp4"
    # ftyp brand
    brand = head[8:12].decode("latin-1", errors="replace")
    # Codec boxes
    if b"avcC" in head:
        return f"h264 (brand={brand})"
    if b"hvcC" in head or b"hev1" in head[:512] or b"hvc1" in head[:512]:
        return f"hevc/h265 (brand={brand})"
    if b"vp09" in head:
        return f"vp9 (brand={brand})"
    if b"av01" in head:
        return f"av1 (brand={brand})"
    return f"unknown (brand={brand})"


def scan(pptx_path: Path) -> dict:
    report = {
        "path": str(pptx_path),
        "videos": [],
        "fonts_used": Counter(),
        "fonts_unsafe": Counter(),
        "non_safe_glyphs": Counter(),
        "non_safe_glyph_locations": defaultdict(list),
        "n_slides": 0,
        "slide_files": [],
    }

    with zipfile.ZipFile(pptx_path) as zf:
        slide_files = sorted(
            n for n in zf.namelist()
            if n.startswith("ppt/slides/slide") and n.endswith(".xml")
        )
        report["n_slides"] = len(slide_files)
        report["slide_files"] = slide_files

        # Embedded videos
        for n in zf.namelist():
            if n.startswith("ppt/media/") and n.lower().endswith(
                (".mp4", ".m4v", ".avi", ".mov", ".webm", ".mkv")
            ):
                media_bytes = zf.read(n)
                codec = _detect_video_codec(media_bytes)
                report["videos"].append({
                    "path": n,
                    "size_bytes": len(media_bytes),
                    "codec": codec,
                })

        # Fonts + glyph audit per slide
        for sf in slide_files:
            slide_num = int(re.search(r"slide(\d+)\.xml", sf).group(1))
            xml = zf.read(sf).decode("utf-8", errors="replace")

            for m in re.finditer(r'typeface="([^"]+)"', xml):
                face = m.group(1)
                report["fonts_used"][face] += 1
                if face.lower() not in SAFE_FONTS:
                    report["fonts_unsafe"][face] += 1

            for m in re.finditer(r"<a:t[^>]*>([^<]*)</a:t>", xml):
                for ch in m.group(1):
                    if not _is_safe_glyph(ch):
                        report["non_safe_glyphs"][ch] += 1
                        if slide_num not in report["non_safe_glyph_locations"][ch]:
                            report["non_safe_glyph_locations"][ch].append(slide_num)

    return report


def print_report(rep: dict) -> int:
    print(f"=== PPTX -> PowerPoint compatibility scan ===")
    print(f"File: {rep['path']}")
    print(f"Slides: {rep['n_slides']}")
    print()

    # 1. Videos
    print("[1] EMBEDDED VIDEOS")
    if not rep["videos"]:
        print("  (none — slide 6 placeholder will need video embedded later)")
    else:
        for v in rep["videos"]:
            mb = v["size_bytes"] / 1024 / 1024
            warn = ""
            if "hevc" in v["codec"].lower():
                warn = "  ⚠ HEVC may not play in older PowerPoint"
            elif v["codec"] == "not-mp4":
                warn = "  ⚠ NOT an MP4 — re-encode to H.264 MP4"
            elif "unknown" in v["codec"]:
                warn = "  ⚠ codec not detected — verify it plays in PowerPoint"
            print(f"  - {v['path']}  ({mb:.1f} MB, codec={v['codec']}){warn}")
    print()

    # 2. Glyphs
    print("[2] NON-LATIN / NON-CALIBRI-SAFE GLYPHS")
    if not rep["non_safe_glyphs"]:
        print("  (none — all glyphs in Latin / extended-Latin / punctuation / arrows / math)")
    else:
        for ch, n in rep["non_safe_glyphs"].most_common():
            slides = ", ".join(str(s) for s in sorted(rep["non_safe_glyph_locations"][ch])[:6])
            if len(rep["non_safe_glyph_locations"][ch]) > 6:
                slides += f", … (+{len(rep['non_safe_glyph_locations'][ch]) - 6})"
            print(f"  - '{ch}' (U+{ord(ch):04X} {_glyph_name(ch)}): {n}x  on slides {slides}")
        print()
        print("  These may render as boxes (□) on machines without the right font.")
        print("  Verify each in real PowerPoint; replace with text or safer glyph if absent.")
    print()

    # 3. Fonts
    print("[3] FONT FACES")
    print("  Used:")
    for f, n in rep["fonts_used"].most_common():
        print(f"    {f}: {n} runs")
    print()
    if rep["fonts_unsafe"]:
        print("  ⚠ NON-DEFAULT fonts (may be substituted on presenter machine):")
        for f, n in rep["fonts_unsafe"].most_common():
            print(f"    - {f} ({n} runs)")
        print("  Install on the presenter machine, or change to Calibri/Arial.")
    else:
        print("  All fonts are PowerPoint default-bundle / cross-platform safe. ✓")

    # Exit code
    issues = (
        len([v for v in rep["videos"]
             if "hevc" in v["codec"].lower()
             or v["codec"] == "not-mp4"
             or "unknown" in v["codec"]])
        + len(rep["non_safe_glyphs"])
        + len(rep["fonts_unsafe"])
    )
    print()
    print(f"Total flagged items: {issues}")
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pptx", type=Path, help="path to .pptx file")
    args = ap.parse_args()
    if not args.pptx.exists():
        sys.exit(f"file not found: {args.pptx}")
    report = scan(args.pptx)
    print_report(report)


if __name__ == "__main__":
    main()
