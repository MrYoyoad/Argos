#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import editdistance

# -----------------------
# spaCy (optional, graceful fallback)
# -----------------------

try:
    import spacy
    _nlp = spacy.load('en_core_web_sm')
    HAS_SPACY = True
except (ImportError, OSError):
    HAS_SPACY = False

# Basic stopword list used as fallback when spaCy is not available
_STOPWORDS = frozenset(
    "a an the and or but if in on at to for of is am are was were be been being "
    "have has had do does did will would shall should may might can could "
    "i me my we us our you your he him his she her it its they them their "
    "that this these those who whom which what where when how not no nor "
    "so very too also just than more most such as with from by about between "
    "into through during before after above below up down out off over under "
    "again then once here there all each every both few many much some any "
    "other another same different new old".split()
)


# -----------------------
# Tokenization + alignment
# -----------------------

def toks(s: str) -> List[str]:
    s = (s or "").strip().lower()
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", s)

def align(ref: str, hyp: str) -> List[Tuple[str, str]]:
    """
    Return list of (word, tag) for hypothesis words.
    tag in {"ok","ins","rep"}.
    - ok (green): right word, right place
    - rep (yellow): word appears in reference, but wrong place
    - ins (red): word doesn't appear in reference at all (made up)
    """
    r = toks(ref)
    h = toks(hyp)

    # Build a multiset (counter) of reference words for lookup
    ref_words = {}
    for w in r:
        ref_words[w] = ref_words.get(w, 0) + 1

    tagged: List[Tuple[str, str]] = []

    for i, hyp_word in enumerate(h):
        # Check if word is in correct position
        if i < len(r) and hyp_word == r[i]:
            tagged.append((hyp_word, "ok"))
        # Check if word appears anywhere in reference
        elif hyp_word in ref_words:
            tagged.append((hyp_word, "rep"))
        # Word doesn't appear in reference at all
        else:
            tagged.append((hyp_word, "ins"))

    return tagged


# -----------------------
# HTML rendering
# -----------------------

def hyp_html(tagged: List[Tuple[str, str]]) -> str:
    cls = {"ok": "ok", "ins": "ins", "rep": "rep"}
    parts = []
    for w, t in tagged:
        parts.append(f'<span class="{cls.get(t,"rep")}">{escape(w)}</span>')
    return " ".join(parts)

HTML_HEAD = """<!doctype html>
<html><head><meta charset="utf-8">
<style>
body{font-family:system-ui,Arial; margin:20px}
table{border-collapse:collapse; width:100%}
td,th{border:1px solid #ddd; padding:10px; vertical-align:top}
th{background:#f5f5f5; text-align:left}
.ok{color:#0a7a0a; font-weight:700}
.rep{color:#b58900; font-weight:800}
.ins{color:#b00020; font-weight:800}
.nea-green{background:#d4edda; color:#155724; font-weight:700; text-align:center}
.nea-yellow{background:#fff3cd; color:#856404; font-weight:700; text-align:center}
.nea-red{background:#f8d7da; color:#721c24; font-weight:700; text-align:center}
small{color:#555}
pre{white-space:pre-wrap; word-break:break-word; margin:0}
.summary{background:#e9ecef; padding:12px; border-radius:6px; margin-bottom:16px}
</style></head><body>
<h2>ASR Report (REF vs HYP)</h2>
<p><span class="ok">green</span>=match, <span class="rep">yellow</span>=mismatch/shift, <span class="ins">red</span>=inserted/made-up</p>
"""

HTML_TAIL = "</table></body></html>"


# -----------------------
# ANSI rendering (terminal colors)
# -----------------------

ANSI = {
    "reset": "\x1b[0m",
    "ok": "\x1b[32;1m",   # bright green
    "rep": "\x1b[33;1m",  # bright yellow
    "ins": "\x1b[31;1m",  # bright red
    "dim": "\x1b[2m",
}

def hyp_ansi(tagged: List[Tuple[str, str]]) -> str:
    out = []
    for w, t in tagged:
        color = ANSI.get(t, ANSI["rep"])
        out.append(f"{color}{w}{ANSI['reset']}")
    return " ".join(out)

def block_sep() -> str:
    return "-" * 96

def safe_one_line(s: str) -> str:
    s = (s or "").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s


# -----------------------
# Semantic metrics (NEA + Weighted WER)
# -----------------------

# Token value categories for weighted metrics
_HIGH_POS = {"PROPN", "NUM"}         # proper nouns, numbers
_HIGH_ENT = {"PERSON", "ORG", "GPE", "LOC", "MONEY", "DATE", "TIME", "PERCENT", "QUANTITY", "NORP", "FAC", "EVENT"}
_MED_POS  = {"NOUN", "VERB", "ADJ", "ADV"}  # content words
# Everything else (DET, AUX, PRON, ADP, CONJ, PUNCT, etc.) = low value

_WEIGHT_HIGH = 2.0
_WEIGHT_MED  = 1.0
_WEIGHT_LOW  = 0.5


def _classify_token_spacy(token) -> str:
    """Classify a spaCy token as 'high', 'med', or 'low' value."""
    if token.ent_type_ in _HIGH_ENT or token.pos_ in _HIGH_POS:
        return "high"
    if token.pos_ in _MED_POS:
        return "med"
    return "low"


def _classify_token_basic(word: str) -> str:
    """Classify a word without spaCy (stopword-based fallback)."""
    w = word.lower().strip()
    if not w:
        return "low"
    # Numbers and words starting with uppercase-like patterns → high
    if w.isdigit() or re.match(r'^[0-9]', w):
        return "high"
    if w in _STOPWORDS:
        return "low"
    return "med"


def classify_tokens(text: str) -> List[Tuple[str, str]]:
    """
    Classify each token in text as 'high', 'med', or 'low' value.
    Returns: [(word, category), ...]

    With spaCy: Uses POS tags + NER for classification.
    Without spaCy: Uses stopword filtering (basic but functional).
    """
    words = toks(text)
    if not words:
        return []

    if HAS_SPACY:
        doc = _nlp(text.lower())
        result = []
        for token in doc:
            w = re.sub(r'[^a-z0-9\']', '', token.text.lower())
            if not w:
                continue
            result.append((w, _classify_token_spacy(token)))
        return result
    else:
        return [(w, _classify_token_basic(w)) for w in words]


def _weight_for(cat: str) -> float:
    if cat == "high":
        return _WEIGHT_HIGH
    if cat == "med":
        return _WEIGHT_MED
    return _WEIGHT_LOW


@dataclass
class MetricsResult:
    wwer: float               # Weighted WER (%)
    nea_recall: float         # NEA recall (%)
    nea_precision: float      # NEA precision (%)
    nea_f1: float             # NEA F1 (%)
    missed_entities: List[str]  # High-value ref tokens not found in hyp
    mode: str                 # "spaCy POS/NER" or "basic stopword filter"


def nea_metrics(ref: str, hyp: str) -> MetricsResult:
    """
    Compute Named Entity Accuracy (NEA) metrics.

    NEA focuses on high-value tokens (proper nouns, numbers, named entities).
    - Recall: how many important ref words appear in hyp
    - Precision: how much of hyp's important content is real
    - F1: harmonic mean
    """
    ref_classified = classify_tokens(ref)
    hyp_classified = classify_tokens(hyp)

    ref_high = [w for w, c in ref_classified if c == "high"]
    hyp_high = [w for w, c in hyp_classified if c == "high"]

    if not ref_high and not hyp_high:
        return MetricsResult(0.0, 100.0, 100.0, 100.0, [], _metrics_mode())

    ref_high_set = set(ref_high)
    hyp_high_set = set(hyp_high)

    matched = ref_high_set & hyp_high_set
    missed = sorted(ref_high_set - hyp_high_set)

    recall = (len(matched) / len(ref_high_set) * 100) if ref_high_set else 100.0
    precision = (len(matched) / len(hyp_high_set) * 100) if hyp_high_set else 100.0
    f1 = (2 * recall * precision / (recall + precision)) if (recall + precision) > 0 else 0.0

    return MetricsResult(0.0, recall, precision, f1, missed, _metrics_mode())


def weighted_wer(ref: str, hyp: str) -> float:
    """
    Compute Weighted WER where errors on high-value tokens cost more.

    Uses editdistance-style alignment but weights errors by token category:
    - High-value (PROPN, NUM, entities): 2.0x
    - Medium (NOUN, VERB, ADJ, ADV): 1.0x
    - Low (function words): 0.5x
    """
    ref_tokens = classify_tokens(ref)
    hyp_words = toks(hyp)

    if not ref_tokens:
        return 0.0

    ref_words = [w for w, _ in ref_tokens]
    ref_cats = {i: c for i, (_, c) in enumerate(ref_tokens)}

    # Use SequenceMatcher for alignment
    sm = SequenceMatcher(None, ref_words, hyp_words)
    weighted_errors = 0.0
    weighted_total = 0.0

    # Total weighted reference length
    for i, (_, cat) in enumerate(ref_tokens):
        weighted_total += _weight_for(cat)

    # Count weighted errors from alignment opcodes
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        elif op == 'replace':
            for i in range(i1, i2):
                weighted_errors += _weight_for(ref_cats.get(i, "med"))
        elif op == 'delete':
            for i in range(i1, i2):
                weighted_errors += _weight_for(ref_cats.get(i, "med"))
        elif op == 'insert':
            # Insertions: use medium weight (no ref token to categorize)
            weighted_errors += (j2 - j1) * _WEIGHT_MED

    if weighted_total == 0:
        return 0.0
    return weighted_errors / weighted_total * 100


def _metrics_mode() -> str:
    return "spaCy POS/NER" if HAS_SPACY else "basic stopword filter"


def compute_all_metrics(ref: str, hyp: str) -> MetricsResult:
    """Compute NEA + Weighted WER for a single ref/hyp pair."""
    nea = nea_metrics(ref, hyp)
    wwer = weighted_wer(ref, hyp)
    nea.wwer = wwer
    return nea


def nea_color(nea_recall: float, wer: float) -> str:
    """
    Data-driven coloring: compare NEA recall to word accuracy.
    Green: entities preserved at least as well as average words.
    Yellow: slight entity loss (within 10 points).
    Red: disproportionate entity loss (>10 points below word accuracy).
    """
    word_accuracy = max(0.0, 100.0 - wer)
    if nea_recall >= word_accuracy:
        return "green"
    elif nea_recall >= word_accuracy - 10:
        return "yellow"
    else:
        return "red"


# -----------------------
# Loading decode outputs
# -----------------------

@dataclass
class Rec:
    utt_id: str
    ref: str
    hypo: str
    instruction: str = ""

def _loads_json_or_py(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return ast.literal_eval(text)

def parse_segment_id(segment_id: str) -> Tuple[str, int, int, int]:
    """
    Parse segment ID to extract components.
    Format: {video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}

    Returns: (base_video_id, seg_idx, start_frame, end_frame)
    For non-segmented IDs, returns (segment_id, -1, -1, -1).
    """
    parts = segment_id.split('_')

    if len(parts) < 4:
        return segment_id, -1, -1, -1

    try:
        end_frame = int(parts[-1])
        start_frame = int(parts[-2])
        seg_idx = int(parts[-3])
        base_video_id = '_'.join(parts[:-3])
        return base_video_id, seg_idx, start_frame, end_frame
    except (ValueError, IndexError):
        return segment_id, -1, -1, -1


def build_display_names(recs: List[Rec]) -> Dict[str, str]:
    """
    Build user-friendly display names for segment IDs.

    Single-segment videos  -> just base name (e.g., "Obama")
    Multi-segment videos   -> "Obama - Part 1", "Obama - Part 2", etc.
    Non-segmented IDs      -> returned as-is (e.g., "00008")
    """
    # Group records by base video ID
    groups: Dict[str, List[Tuple[int, str]]] = {}
    for r in recs:
        base, seg_idx, _, _ = parse_segment_id(r.utt_id)
        if base not in groups:
            groups[base] = []
        groups[base].append((seg_idx, r.utt_id))

    names: Dict[str, str] = {}
    for base, entries in groups.items():
        if len(entries) == 1:
            # Single segment (or non-segmented) -> just base name
            _, utt_id = entries[0]
            names[utt_id] = base
        else:
            # Multi-segment -> sort by seg_idx and assign Part numbers
            entries.sort(key=lambda x: x[0])
            for part_num, (_, utt_id) in enumerate(entries, 1):
                names[utt_id] = f"{base} - Part {part_num}"

    return names


def load_records(path: Path) -> List[Rec]:
    """
    Returns list of records:
      Rec(utt_id=..., ref=..., hypo=..., instruction=...)

    Supports:
      - jsonl (dict per line)
      - hypo-*.json columnar dict: {"utt_id":[...], "ref":[...], "hypo":[...], ...}
      - hypo-*.json list of dicts
      - mapping dict: {utt_id -> "hyp"} or {utt_id -> {"ref":..,"hypo":..}}
      - python repr variants (single quotes)
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.strip():
        return []

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    # JSONL case
    if len(lines) >= 2 and all(ln.startswith("{") for ln in lines[:2]):
        out: List[Rec] = []
        for ln in lines:
            d = _loads_json_or_py(ln)
            if not isinstance(d, dict):
                continue
            uid = d.get("utt_id") or d.get("id") or ""
            if not uid:
                continue
            ref = d.get("ref") or ""
            hyp = d.get("hypo") or d.get("hyp") or d.get("text") or ""
            inst = d.get("instruction") or ""
            out.append(Rec(str(uid), str(ref), str(hyp), str(inst)))
        return out

    obj = _loads_json_or_py(raw)

    # List-of-dicts case
    if isinstance(obj, list):
        out: List[Rec] = []
        for d in obj:
            if not isinstance(d, dict):
                continue
            uid = d.get("utt_id") or d.get("id") or ""
            if not uid:
                continue
            ref = d.get("ref") or ""
            hyp = d.get("hypo") or d.get("hyp") or d.get("text") or ""
            inst = d.get("instruction") or ""
            out.append(Rec(str(uid), str(ref), str(hyp), str(inst)))
        return out

    # Dict case: handle BOTH {uid->...} and columnar {"utt_id":[...],...}
    if isinstance(obj, dict):
        # Columnar dict detection: utt_id is a list
        if isinstance(obj.get("utt_id"), list):
            uids = obj.get("utt_id") or []
            refs = obj.get("ref") or []
            hyps = obj.get("hypo") or obj.get("hyp") or obj.get("text") or []
            inst = obj.get("instruction") or []

            n = len(uids)

            def get(arr, i) -> str:
                if isinstance(arr, list) and i < len(arr):
                    return "" if arr[i] is None else str(arr[i])
                return ""

            out: List[Rec] = []
            for i in range(n):
                uid = get(uids, i).strip()
                if not uid:
                    continue
                out.append(Rec(
                    utt_id=uid,
                    ref=get(refs, i),
                    hypo=get(hyps, i),
                    instruction=get(inst, i),
                ))
            return out

        # Mapping dict: {uid -> ...}
        out: List[Rec] = []
        for k, v in obj.items():
            uid = str(k).strip()
            if not uid:
                continue
            if isinstance(v, dict):
                ref = v.get("ref") or ""
                hyp = v.get("merged_hypo") or v.get("hypo") or v.get("hyp") or v.get("text") or ""
                inst = v.get("instruction") or ""
                out.append(Rec(uid, str(ref), str(hyp), str(inst)))
            else:
                out.append(Rec(uid, "", str(v), ""))
        return out

    return []


# -----------------------
# Main
# -----------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="decode outputs (.jsonl OR hypo-*.json)")
    ap.add_argument("--out_dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    recs = load_records(Path(args.jsonl))
    if not recs:
        print(f"[WARN] No records loaded from {args.jsonl}")
        return

    # Build display names and sort by (base_video_id, segment_index)
    display_names = build_display_names(recs)
    recs.sort(key=lambda r: (parse_segment_id(r.utt_id)[0], parse_segment_id(r.utt_id)[1]))

    print(f"[INFO] Metrics mode: {_metrics_mode()}")

    # Build outputs with metrics
    rows_csv = []
    html_rows = []
    txt_blocks = []
    ansi_blocks = []

    # Accumulators for overall summary
    total_wwer_num = 0.0
    total_wwer_den = 0.0
    total_nea_recall = 0.0
    total_nea_f1 = 0.0
    n_with_ref = 0

    for r in recs:
        ref = r.ref or ""
        hyp = r.hypo or ""
        tagged = align(ref, hyp)
        dname = display_names.get(r.utt_id, r.utt_id)

        # Compute metrics (only meaningful when ref is available)
        has_ref = bool(ref.strip())
        if has_ref:
            m = compute_all_metrics(ref, hyp)
            # Compute simple WER for color comparison
            r_toks = toks(ref)
            h_toks = toks(hyp)
            simple_wer = (editdistance.eval(h_toks, r_toks) / len(r_toks) * 100) if r_toks else 0.0
            color = nea_color(m.nea_recall, simple_wer)

            total_wwer_num += m.wwer
            total_nea_recall += m.nea_recall
            total_nea_f1 += m.nea_f1
            n_with_ref += 1
        else:
            m = None
            simple_wer = 0.0
            color = "green"

        # CSV row
        if m:
            rows_csv.append((
                r.utt_id, dname, ref, hyp,
                " ".join([f"{w}:{t}" for w, t in tagged]),
                f"{m.wwer:.1f}", f"{m.nea_recall:.1f}", f"{m.nea_precision:.1f}",
                f"{m.nea_f1:.1f}", ", ".join(m.missed_entities) if m.missed_entities else ""
            ))
        else:
            rows_csv.append((
                r.utt_id, dname, ref, hyp,
                " ".join([f"{w}:{t}" for w, t in tagged]),
                "", "", "", "", ""
            ))

        # HTML row
        nea_cell = ""
        if m:
            css = f"nea-{color}"
            missed_tip = f' title="Missed: {escape(", ".join(m.missed_entities))}"' if m.missed_entities else ""
            nea_cell = (
                f'<td class="{css}"{missed_tip}>'
                f'{m.nea_recall:.0f}%</td>'
                f'<td style="text-align:center">{m.wwer:.1f}%</td>'
            )
        else:
            nea_cell = '<td>-</td><td>-</td>'

        html_rows.append(
            f"<tr><td><b>{escape(dname)}</b><br>"
            f"<small>{escape(r.utt_id)}</small></td>"
            f"<td><pre>{escape(ref)}</pre></td>"
            f"<td><pre>{hyp_html(tagged)}</pre></td>"
            f"{nea_cell}</tr>"
        )

        # Plain text block
        metrics_line = ""
        if m:
            metrics_line = f"WWER: {m.wwer:.1f}% | NEA: R={m.nea_recall:.0f}% P={m.nea_precision:.0f}% F1={m.nea_f1:.0f}%"
            if m.missed_entities:
                metrics_line += f" | Missed: [{', '.join(m.missed_entities)}]"
            metrics_line = f"\n{metrics_line}"

        txt_blocks.append(
            f"{dname}\n"
            f"REF: {ref if ref.strip() else '(no ref available)'}\n"
            f"HYP: {hyp if hyp.strip() else '(no hyp available)'}"
            f"{metrics_line}\n"
            f"{block_sep()}"
        )

        # ANSI block
        ansi_metrics = ""
        if m:
            c = {"green": ANSI["ok"], "yellow": ANSI["rep"], "red": ANSI["ins"]}
            ansi_metrics = (
                f"\n{ANSI['dim']}WWER:{ANSI['reset']} {m.wwer:.1f}% | "
                f"{c.get(color, '')}"
                f"NEA: R={m.nea_recall:.0f}% P={m.nea_precision:.0f}% F1={m.nea_f1:.0f}%"
                f"{ANSI['reset']}"
            )
            if m.missed_entities:
                ansi_metrics += f" | {ANSI['ins']}Missed: [{', '.join(m.missed_entities)}]{ANSI['reset']}"

        ansi_blocks.append(
            f"{dname}\n"
            f"{ANSI['dim']}REF:{ANSI['reset']} {ref if ref.strip() else '(no ref available)'}\n"
            f"{ANSI['dim']}HYP:{ANSI['reset']} {hyp_ansi(tagged) if hyp.strip() else '(no hyp available)'}"
            f"{ansi_metrics}\n"
            f"{ANSI['dim']}{block_sep()}{ANSI['reset']}"
        )

    # Overall summary
    if n_with_ref > 0:
        avg_wwer = total_wwer_num / n_with_ref
        avg_nea_recall = total_nea_recall / n_with_ref
        avg_nea_f1 = total_nea_f1 / n_with_ref
        summary = f"OVERALL | WWER: {avg_wwer:.1f}% | NEA Recall: {avg_nea_recall:.0f}% | NEA F1: {avg_nea_f1:.0f}% | Mode: {_metrics_mode()} | Segments: {n_with_ref}"
    else:
        summary = "OVERALL | No reference transcriptions available for metrics"

    # Write CSV
    with open(out_dir / "report.csv", "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        w.writerow(["utt_id", "display_name", "ref", "hyp", "hyp_tagged",
                     "wwer_%", "nea_recall_%", "nea_precision_%", "nea_f1_%", "missed_entities"])
        w.writerows(rows_csv)

    # Write HTML
    html_summary = f'<div class="summary"><b>{escape(summary)}</b></div>'
    html_table = (
        '<table>\n'
        '<tr><th>ID</th><th>Reference</th><th>Hypothesis (colored)</th>'
        '<th>NEA Recall</th><th>WWER</th></tr>\n'
        + "\n".join(html_rows)
    )
    (out_dir / "report.html").write_text(
        HTML_HEAD + html_summary + html_table + HTML_TAIL,
        encoding="utf-8"
    )

    # Write plain txt
    (out_dir / "report.txt").write_text(
        summary + "\n" + block_sep() + "\n"
        + "\n".join(txt_blocks) + "\n(END)\n",
        encoding="utf-8"
    )

    # Write ANSI txt
    ansi_summary = f"{ANSI['ok']}{summary}{ANSI['reset']}"
    (out_dir / "report.ansi.txt").write_text(
        ansi_summary + "\n" + f"{ANSI['dim']}{block_sep()}{ANSI['reset']}\n"
        + "\n".join(ansi_blocks) + f"\n{ANSI['dim']}(END){ANSI['reset']}\n",
        encoding="utf-8"
    )

    print(summary)
    print("Wrote:", out_dir / "report.csv")
    print("Wrote:", out_dir / "report.html")
    print("Wrote:", out_dir / "report.ansi.txt")
    print("Wrote:", out_dir / "report.txt")
    print("Tip: view ANSI with: less -R report.ansi.txt")


if __name__ == "__main__":
    main()