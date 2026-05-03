#!/usr/bin/env python3
"""Build a single self-contained HTML index page for the RealTalk demo deliverables:
all 5 Mode-B side-by-side composites front-and-center, then the 5 Clearly-Conveyed
single-speaker burns, then the rest of the burns grouped by outcome tier, with
inline metrics (IS/WER/sentence_conf) and a representative thumbnail.

Outputs `realtalk_demo_index.html` next to the burn clips so it can be opened
locally in any browser; all video tags use relative paths.
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path

OUT_DIR = Path("/home/ubuntu/presentation_materials_20260224/06_demo_videos/realtalk")
INDEX_PATH = OUT_DIR / "realtalk_demo_index.html"
ANALYSIS_JSON = OUT_DIR / "realtalk_analysis.json"
SIDEBYSIDES = sorted(OUT_DIR.glob("*__sidebyside.mp4"))


def niv(is_score: float | None) -> tuple[str, str]:
    if is_score is None:
        return "—", "#666"
    if is_score >= 3.80:
        return "Y", "#00B050"
    if is_score >= 2.00:
        return "P", "#1F77B4"
    return "N", "#888"


def fmt(v, fmt_str="{:.2f}"):
    return fmt_str.format(v) if isinstance(v, (int, float)) else "—"


def load_entries() -> list[dict]:
    if not ANALYSIS_JSON.exists():
        return []
    return json.loads(ANALYSIS_JSON.read_text())


def card(e: dict) -> str:
    burn = e.get("burn_path", "")
    frames = e.get("frames", [])
    thumb = frames[1] if len(frames) > 1 else (frames[0] if frames else "")
    is_score = e["is_score"] if isinstance(e["is_score"], (int, float)) else None
    niv_letter, niv_col = niv(is_score)
    bdg = (
        f'<span style="background:{niv_col};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:13px;font-weight:600;">'
        f'IS {fmt(is_score)} · {niv_letter}</span>'
    )
    return f"""
<div class="card">
  <div class="card-head">
    <div class="card-title">{html.escape(e['per_speaker_id'])} <span class="time">@ {e['start_sec']:.0f}s</span></div>
    {bdg}
  </div>
  <div class="card-body">
    <video controls preload="metadata" muted playsinline width="320" poster="{html.escape(thumb)}">
      <source src="{html.escape(burn)}" type="video/mp4">
    </video>
    <div class="meta">
      <div><b>WER</b>: {fmt(e['wer'], "{:.0f}")}% (top1) / {fmt(e['wer_mbr'], "{:.0f}")}% (MBR)</div>
      <div><b>sentence_conf</b>: {fmt(e['sentence_conf'], "{:.3f}")} → trust <b>{html.escape(e.get('trust_tier','—') or '—')}</b></div>
      <div class="ref"><b>REF</b>: {html.escape(e['ref'][:160])}{'…' if len(e['ref']) > 160 else ''}</div>
      <div class="hyp"><b>HYP</b>: {html.escape(e['hyp_mbr'][:160] or '[empty]')}{'…' if len(e['hyp_mbr']) > 160 else ''}</div>
    </div>
  </div>
</div>"""


def sidebyside_card(p: Path) -> str:
    name = p.name.replace("__sidebyside.mp4", "")
    return f"""
<div class="sxs-card">
  <h3>{html.escape(name)}</h3>
  <video controls preload="metadata" playsinline style="width:100%;max-width:920px;">
    <source src="{html.escape(p.name)}" type="video/mp4">
  </video>
</div>"""


def main() -> None:
    entries = load_entries()
    # Group entries by outcome
    def bucket(e):
        s = e["is_score"]
        if not isinstance(s, (int, float)):
            return "Unknown"
        if s >= 3.80:
            return "Clearly Conveyed"
        if s >= 2.00:
            return "Salvage"
        return "Failed"

    groups: dict[str, list[dict]] = {"Clearly Conveyed": [], "Salvage": [], "Failed": [], "Unknown": []}
    for e in entries:
        groups[bucket(e)].append(e)
    for k in groups:
        groups[k].sort(key=lambda e: -(e["is_score"] if isinstance(e["is_score"], (int, float)) else -999))

    css = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1280px;margin:30px auto;padding:0 24px;color:#222;background:#fafafa;line-height:1.45}
h1{font-size:28px;margin-bottom:6px}
h2{margin-top:48px;border-bottom:2px solid #1F77B4;padding-bottom:6px}
.tagline{color:#666;font-size:15px;margin-bottom:30px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}
.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.card-title{font-weight:600;font-size:14px}
.card-title .time{color:#888;font-weight:400;margin-left:6px}
.card-body video{width:100%;height:auto;border-radius:4px;background:#000}
.meta{font-size:13px;margin-top:10px;line-height:1.6}
.meta .ref{color:#555}
.meta .hyp{color:#1F77B4;font-weight:500}
.sxs-card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:18px;margin-bottom:24px}
.sxs-card h3{margin-top:0;font-size:16px}
.summary{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:18px;margin-bottom:30px}
.summary table{border-collapse:collapse;width:100%}
.summary td,.summary th{padding:8px 14px;border-bottom:1px solid #eee;text-align:left}
.summary th{background:#f4f6f9}
"""

    summary_table = ""
    if entries:
        clearly = sum(1 for e in entries if isinstance(e["is_score"], (int, float)) and e["is_score"] >= 3.80)
        salvage = sum(1 for e in entries if isinstance(e["is_score"], (int, float)) and 2.00 <= e["is_score"] < 3.80)
        failed = sum(1 for e in entries if isinstance(e["is_score"], (int, float)) and e["is_score"] < 2.00)
        wers = [e["wer"] for e in entries if isinstance(e["wer"], (int, float))]
        iss = [e["is_score"] for e in entries if isinstance(e["is_score"], (int, float))]
        mean_wer = sum(wers) / len(wers) if wers else 0
        mean_is = sum(iss) / len(iss) if iss else 0
        summary_table = f"""
<div class="summary">
  <table>
    <tr><th>Total candidates</th><td>{len(entries)}</td></tr>
    <tr><th>Clearly Conveyed (IS ≥ 3.80)</th><td>{clearly} ({100*clearly/len(entries):.0f}%)</td></tr>
    <tr><th>Salvage (2.00 ≤ IS < 3.80)</th><td>{salvage} ({100*salvage/len(entries):.0f}%)</td></tr>
    <tr><th>Failed (IS < 2.00)</th><td>{failed} ({100*failed/len(entries):.0f}%)</td></tr>
    <tr><th>Mean WER (top-1 = MBR)</th><td>{mean_wer:.1f}%</td></tr>
    <tr><th>Mean IS</th><td>{mean_is:.2f}</td></tr>
  </table>
</div>
"""

    sxs_html = "\n".join(sidebyside_card(p) for p in SIDEBYSIDES)

    sections_html = ""
    for label in ("Clearly Conveyed", "Salvage", "Failed"):
        items = groups[label]
        if not items:
            continue
        sections_html += f'\n<h2>{label} ({len(items)})</h2>\n<div class="grid">\n'
        sections_html += "\n".join(card(e) for e in items)
        sections_html += "\n</div>\n"

    INDEX_PATH.write_text(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RealTalk demo — VSP-LLM lip-reading on conversational data</title>
<style>{css}</style>
</head>
<body>
<h1>RealTalk demo deliverables</h1>
<p class="tagline">25 candidate windows, 5 Mode-B side-by-sides, hyp_mbr displayed, agreement-aware trust bands.
Pipeline run: <code>flat_runs_archive/20260503_000805</code> · partner run: <code>20260503_004919</code>.</p>

{summary_table}

<h2>Mode-B side-by-side composites (5)</h2>
<p>Both speakers, original two-shot audio, agreement-aware colored hypothesis on each half.
The "active speaker" is visually self-evident — listener side has empty / red / hallucinated output that the trust layer flags.</p>
{sxs_html}

{sections_html}

</body>
</html>
""")
    print(f"wrote {INDEX_PATH}")


if __name__ == "__main__":
    main()
