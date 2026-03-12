#!/usr/bin/env python3
"""Generate HTML report for LLM-as-a-Judge evaluation results.

Produces a styled HTML table with: Reference, Hypothesis (color-coded),
WER, WWER, NEA F1, IS, LLM Judge verdict (Y/P/N), and justification notes.

Usage:
    python generate_llm_judge_html.py [--limit N] [--output PATH]
"""

import csv
import argparse
import html
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "evaluation" / "llm_judge" / "llm_judge_results.csv"
CONTEXT_FILE = Path(__file__).resolve().parent.parent.parent / "evaluation" / "llm_judge" / "context_eval" / "context_eval_results.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation" / "llm_judge"


def color_class_for_metric(value, thresholds=(33, 66)):
    """Return CSS class based on metric value (lower is better for WER/WWER)."""
    if value <= thresholds[0]:
        return "m-green"
    elif value <= thresholds[1]:
        return "m-yellow"
    return "m-red"


def color_class_for_metric_higher_better(value, thresholds=(33, 66)):
    """Return CSS class based on metric value (higher is better for NEA/IS)."""
    if value >= thresholds[1]:
        return "m-green"
    elif value >= thresholds[0]:
        return "m-yellow"
    return "m-red"


def is_color_class(score):
    """IS-specific coloring: 0-2 red, 2-3 yellow, 3-5 green."""
    if score >= 3.0:
        return "m-green"
    elif score >= 2.0:
        return "m-yellow"
    return "m-red"


def judge_badge(verdict):
    """Return styled badge HTML for Y/P/N."""
    if verdict == "Y":
        return '<span class="badge badge-y">Y</span>'
    elif verdict == "P":
        return '<span class="badge badge-p">P</span>'
    return '<span class="badge badge-n">N</span>'


def render_hyp_tagged(hyp_tagged):
    """Convert hyp_tagged field (word:tag pairs) into colored HTML spans."""
    if not hyp_tagged:
        return "<em>(empty)</em>"
    parts = []
    for token in hyp_tagged.split():
        if ":" in token:
            idx = token.rfind(":")
            word = html.escape(token[:idx])
            tag = token[idx + 1:]
            if tag == "ok":
                parts.append(f'<span class="ok">{word}</span>')
            elif tag == "rep":
                parts.append(f'<span class="rep">{word}</span>')
            elif tag == "ins":
                parts.append(f'<span class="ins">{word}</span>')
            else:
                parts.append(html.escape(token))
        else:
            parts.append(html.escape(token))
    return " ".join(parts)


def _describe_what_happened(row):
    """Return a single plain-English sentence describing what the model did."""
    sp = row.get("success_pattern", "").strip()
    fm = row.get("failure_mode", "").strip()
    wer = float(row.get("wer_%", 0))
    sem = float(row.get("semantic_sim", 0))
    phon = float(row.get("phonetic_sim", 0))
    nea = float(row.get("nea_f1_%", 0))
    hyp = row.get("hyp", "").strip()

    # Empty output
    if not hyp:
        return "Model produced no output"

    # Use success_pattern or failure_mode as primary signal
    pattern = sp or fm or ""

    descriptions = {
        "Near-Perfect Output": "Almost perfect transcription",
        "Minor Errors, High Semantic Match": "Small word errors but the meaning is correct",
        "Phonetically Preserved": "Words sound similar to the original (phonetic bridge)",
        "Entities Preserved": "Important names and numbers are correct",
        "Combined Semantic + Phonetic Bridge": "Meaning preserved through similar-sounding words",
        "Phonetically Similar but Wrong Topic": "Words sound right but the topic is completely wrong",
        "Content Word Errors": "Important content words are wrong",
        "Entity Destruction": "Names, numbers, and key terms are lost",
        "Hallucination": "Model invented fluent but completely wrong text",
        "Empty Output": "Model produced no output",
        "Severe Degradation": "Output is mostly garbage",
        "Accumulated Small Errors": "Many small errors that add up to lost meaning",
        "Total Topic Drift": "Output is about a completely different topic",
    }

    if pattern in descriptions:
        return descriptions[pattern]

    # Fallback: describe based on metrics
    if wer == 0:
        return "Perfect match"
    if wer <= 20:
        return "Very close, just a few word differences"
    if sem > 0.7 and wer < 50:
        return "Words differ but the meaning comes through"
    if phon > 0.7 and sem < 0.4:
        return "Words sound similar but meaning is lost"
    if wer >= 100:
        return "Model invented text (hallucination)"
    if wer > 70:
        return "Most words are wrong"
    return "Partial match with significant errors"


def build_justification(row):
    """Build a human-readable justification: what happened + topic."""
    topic = row.get("topic", "").strip()
    description = _describe_what_happened(row)

    if topic:
        return f'{description}  <span style="opacity:0.6">[{topic}]</span>'
    return description


def load_context_eval(path):
    """Load context-aware eval results, return dict keyed by utt_id."""
    context = {}
    if not path.exists():
        return context
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            context[row["utt_id"]] = {
                "context_judge": row.get("context", ""),
                "context_full": row.get("context_full", ""),
                "transition": row.get("transition", ""),
            }
    return context


def generate_html(rows, context_map, limit=None, title_suffix=""):
    """Generate full HTML string from rows."""
    if limit:
        rows = rows[:limit]

    n = len(rows)
    # Compute summary stats
    wers = [float(r["wer_%"]) for r in rows if r.get("wer_%")]
    is_scores = [float(r["intelligibility_score"]) for r in rows if r.get("intelligibility_score")]
    judge_counts = {"Y": 0, "P": 0, "N": 0}
    for r in rows:
        j = r.get("llm_judge", "").strip()
        if j in judge_counts:
            judge_counts[j] += 1

    mean_wer = sum(wers) / len(wers) if wers else 0
    mean_is = sum(is_scores) / len(is_scores) if is_scores else 0
    yp_pct = (judge_counts["Y"] + judge_counts["P"]) / n * 100 if n else 0

    title = f"LLM-as-a-Judge Report{title_suffix}"

    html_parts = [f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: system-ui, -apple-system, Arial, sans-serif; margin: 20px; background: #fafafa; }}
h2 {{ color: #1a1a2e; margin-bottom: 4px; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
td, th {{ border: 1px solid #ddd; padding: 8px 10px; vertical-align: top; font-size: 0.88em; }}
th {{ background: #f0f0f5; text-align: left; position: sticky; top: 0; z-index: 1; }}
pre {{ white-space: pre-wrap; word-break: break-word; margin: 0; font-family: inherit; }}
small {{ color: #555; }}

/* Word-level coloring */
.ok {{ color: #0a7a0a; font-weight: 700; }}
.rep {{ color: #b58900; font-weight: 800; }}
.ins {{ color: #b00020; font-weight: 800; }}

/* Metric cells */
.m-green {{ background: #d4edda; color: #155724; font-weight: 700; text-align: center; }}
.m-yellow {{ background: #fff3cd; color: #856404; font-weight: 700; text-align: center; }}
.m-red {{ background: #f8d7da; color: #721c24; font-weight: 700; text-align: center; }}

/* Judge badges */
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-weight: 800; font-size: 0.95em; letter-spacing: 0.5px; }}
.badge-y {{ background: #28a745; color: #fff; }}
.badge-p {{ background: #ffc107; color: #333; }}
.badge-n {{ background: #dc3545; color: #fff; }}

/* Context badge (smaller) */
.ctx {{ font-size: 0.8em; margin-left: 4px; opacity: 0.85; }}

/* Summary bar */
.summary {{ background: #e9ecef; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 0.92em; }}
.legend {{ margin-bottom: 12px; font-size: 0.9em; }}

/* IS tier label */
.tier {{ font-size: 0.78em; display: block; color: #555; margin-top: 2px; }}

/* Justification */
.just {{ font-size: 0.82em; color: #444; max-width: 280px; }}

/* Row hover */
tr:hover td {{ background: #f8f9fa; }}

/* Alternating rows */
tbody tr:nth-child(even) {{ background: #fcfcfc; }}
</style></head><body>
<h2>{html.escape(title)}</h2>
<div class="legend">
<b>Hypothesis coloring:</b>
<span class="ok">green</span> = match,
<span class="rep">yellow</span> = substitution/shift,
<span class="ins">red</span> = inserted/hallucinated
&nbsp;&nbsp;|&nbsp;&nbsp;
<b>LLM Judge:</b>
<span class="badge badge-y">Y</span> = Yes (intelligible),
<span class="badge badge-p">P</span> = Partial,
<span class="badge badge-n">N</span> = No (failed)
</div>
<div class="summary">
<b>Segments: {n}</b> &nbsp;|&nbsp;
<b>Mean WER: {mean_wer:.1f}%</b> &nbsp;|&nbsp;
<b>Mean IS: {mean_is:.2f}/5.0</b> &nbsp;|&nbsp;
<b>LLM Judge:</b> Y={judge_counts["Y"]} ({judge_counts["Y"]/n*100:.1f}%),
P={judge_counts["P"]} ({judge_counts["P"]/n*100:.1f}%),
N={judge_counts["N"]} ({judge_counts["N"]/n*100:.1f}%) &nbsp;|&nbsp;
<b>Y+P: {yp_pct:.1f}%</b>
</div>
<table>
<thead>
<tr>
<th style="width:3%">#</th>
<th style="width:10%">ID</th>
<th style="width:22%">Reference</th>
<th style="width:22%">Hypothesis</th>
<th style="width:5%">WER</th>
<th style="width:5%">WWER</th>
<th style="width:5%">NEA&nbsp;F1</th>
<th style="width:6%">IS</th>
<th style="width:5%">LLM</th>
<th style="width:17%">Justification</th>
</tr>
</thead>
<tbody>"""]

    for i, row in enumerate(rows, 1):
        utt_id = row.get("utt_id", "")
        display = row.get("display_name", "")
        ref_text = html.escape(row.get("ref", ""))
        hyp_tagged = render_hyp_tagged(row.get("hyp_tagged", ""))

        wer = float(row.get("wer_%", 0))
        wwer = float(row.get("wwer_%", 0))
        nea_f1 = float(row.get("nea_f1_%", 0))
        is_score = float(row.get("intelligibility_score", 0))
        is_tier = row.get("intelligibility_label", "")
        llm_j = row.get("llm_judge", "").strip()
        justification = build_justification(row)

        wer_cls = color_class_for_metric(wer)
        wwer_cls = color_class_for_metric(wwer)
        nea_cls = color_class_for_metric_higher_better(nea_f1)
        is_cls = is_color_class(is_score)

        # Context-aware judge if available
        ctx = context_map.get(utt_id, {})
        ctx_judge = ctx.get("context_judge", "")
        transition = ctx.get("transition", "")
        ctx_html = ""
        if ctx_judge:
            ctx_html = f'<br><span class="ctx" title="{html.escape(transition)}">(ctx: {html.escape(ctx_judge)})</span>'

        html_parts.append(f"""<tr>
<td style="text-align:center">{i}</td>
<td><b>{html.escape(display)}</b><br><small>{html.escape(utt_id)}</small></td>
<td><pre>{ref_text}</pre></td>
<td><pre>{hyp_tagged}</pre></td>
<td class="{wer_cls}">{wer:.1f}%</td>
<td class="{wwer_cls}">{wwer:.1f}%</td>
<td class="{nea_cls}">{nea_f1:.1f}%</td>
<td class="{is_cls}">{is_score:.2f}<span class="tier">{html.escape(is_tier)}</span></td>
<td style="text-align:center">{judge_badge(llm_j)}{ctx_html}</td>
<td class="just">{justification}</td>
</tr>""")

    html_parts.append("""</tbody></table>
<p style="font-size:0.8em; color:#999; margin-top:20px">
Generated by generate_llm_judge_html.py | Data: LLM-as-a-Judge blind evaluation (Claude Opus 4.6)
</p>
</body></html>""")

    return "\n".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate LLM Judge HTML report")
    parser.add_argument("--limit", type=int, default=None, help="Limit to N rows (default: all)")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--sort", choices=["is", "wer", "judge", "default"], default="default",
                        help="Sort order (default=file order)")
    args = parser.parse_args()

    # Load data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    context_map = load_context_eval(CONTEXT_FILE)

    # Sort
    if args.sort == "is":
        rows.sort(key=lambda r: float(r.get("intelligibility_score", 0)))
    elif args.sort == "wer":
        rows.sort(key=lambda r: float(r.get("wer_%", 0)), reverse=True)
    elif args.sort == "judge":
        order = {"N": 0, "P": 1, "Y": 2}
        rows.sort(key=lambda r: (order.get(r.get("llm_judge", "").strip(), 1),
                                  float(r.get("intelligibility_score", 0))))

    # Pick representative sample for limited view
    if args.limit and args.limit < len(rows):
        # Stratified sample: pick from each judge category proportionally
        y_rows = [r for r in rows if r.get("llm_judge", "").strip() == "Y"]
        p_rows = [r for r in rows if r.get("llm_judge", "").strip() == "P"]
        n_rows = [r for r in rows if r.get("llm_judge", "").strip() == "N"]

        n_total = args.limit
        n_y = max(1, round(n_total * len(y_rows) / len(rows)))
        n_n = max(1, round(n_total * len(n_rows) / len(rows)))
        n_p = n_total - n_y - n_n

        # Pick evenly spaced samples from each category (sorted by IS for variety)
        def pick_spaced(lst, count):
            if count >= len(lst):
                return lst
            step = len(lst) / count
            return [lst[int(i * step)] for i in range(count)]

        y_rows.sort(key=lambda r: float(r.get("intelligibility_score", 0)), reverse=True)
        p_rows.sort(key=lambda r: float(r.get("intelligibility_score", 0)), reverse=True)
        n_rows.sort(key=lambda r: float(r.get("intelligibility_score", 0)), reverse=True)

        sampled = pick_spaced(y_rows, n_y) + pick_spaced(p_rows, n_p) + pick_spaced(n_rows, n_n)
        # Sort final by IS descending for readability
        sampled.sort(key=lambda r: float(r.get("intelligibility_score", 0)), reverse=True)
        rows = sampled

    suffix = f" ({len(rows)} samples)" if args.limit else f" (All {len(rows)} segments)"
    html_content = generate_html(rows, context_map, title_suffix=suffix)

    if args.output:
        out_path = Path(args.output)
    elif args.limit:
        out_path = OUTPUT_DIR / f"llm_judge_report_{args.limit}.html"
    else:
        out_path = OUTPUT_DIR / "llm_judge_report.html"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")
    print(f"Written {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
