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
import sys

# -----------------------
# IS scoring (optional, via --compute-is)
# -----------------------

HAS_IS = False
try:
    # Try same-directory import first (works in container and EC2)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    # Also try docs path (EC2 development layout)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "docs" / "_research-tools" / "generators"))
    from generate_intelligibility_scores import (
        compute_is, compute_phonetic_similarity, compute_length_ratio,
        SemanticEncoder, TIER_LABELS, HAS_EMBEDDINGS,
    )
    HAS_IS = True
except ImportError:
    pass

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


# Segment-level reliability tiers (May 2026 finding — see
# docs/confidence/band_reliability_rollout_plan.md). Keyed on the segment's
# mean_word_prob (= sentence_confidence column). Boundaries are tuned to the
# current LLaMA-2-7B + 1,273-segment LoRA pipeline; expect them to shift as
# the system improves (better backbone, more training data, beam aggregation).
TIER_TRUST_MIN   = 0.82  # green ≥ 85% reliable in segments above this
TIER_SALVAGE_MIN = 0.65  # green ≥ 50% reliable; below this coloring is misleading


def classify_tier(sent_conf: Any) -> str:
    """Map sentence_confidence (mean_word_prob) → reliability tier name.

    Returns one of:
      "Trust"   — full per-word coloring is safe, original promise holds
      "Salvage" — show coloring with an "uncertainty banner"; user can extract
                  meaning but should verify names/numbers/critical details
      "Strip"   — strip per-word coloring; green is < 50% reliable here, paint
                  would mislead more than inform
      ""        — no confidence sidecar / not applicable
    """
    if not isinstance(sent_conf, (int, float)):
        return ""
    if sent_conf >= TIER_TRUST_MIN:
        return "Trust"
    if sent_conf >= TIER_SALVAGE_MIN:
        return "Salvage"
    return "Strip"


def conf_html(words: List[Dict[str, Any]], tier: str = "Trust") -> str:
    """Render per-word confidence-colored HTML from a word_confidence.json segment.

    The `tier` arg controls coloring policy:
      - Trust:   full per-word coloring (default; preserves prior behavior)
      - Salvage: full per-word coloring (visible banner is added separately at
                 the row level by the caller; this fn only handles per-word paint)
      - Strip:   NO per-word coloring — render plain text. Below 0.65 segment
                 mean_word_prob, green leakage > 50% and coloring misleads.
    """
    if tier == "Strip":
        plain = " ".join(escape(str(w.get("word", ""))) for w in (words or []) if w.get("word"))
        return f'<span class="conf-stripped">{plain}</span>' if plain else ""
    parts = []
    for w in words or []:
        word = str(w.get("word", ""))
        if not word:
            continue
        cc = w.get("conf_class") or ""
        prob = w.get("prob")
        if cc not in ("conf-high", "conf-med", "conf-low"):
            parts.append(escape(word))
            continue
        title = f' title="prob={prob:.2f}"' if isinstance(prob, (int, float)) else ""
        parts.append(f'<span class="{cc}"{title}>{escape(word)}</span>')
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
.m-green{background:#d4edda; color:#155724; font-weight:700; text-align:center}
.m-yellow{background:#fff3cd; color:#856404; font-weight:700; text-align:center}
.m-red{background:#f8d7da; color:#721c24; font-weight:700; text-align:center}
.conf-high{background:#cfe2ff; color:#084298; font-weight:700; padding:0 2px; border-radius:2px}
.conf-med {background:#ffe5b4; color:#8a4b00; font-weight:700; padding:0 2px; border-radius:2px}
.conf-low {background:#e2c4f0; color:#4b0082; font-weight:800; padding:0 2px; border-radius:2px}
.conf-stripped{color:#666; font-style:italic}
.tier-banner{display:block; padding:6px 10px; margin-bottom:6px; border-radius:4px;
             font-size:0.82em; font-weight:600}
.tier-banner.salvage{background:#fff7e0; color:#7a5800; border-left:3px solid #d4a017}
.tier-banner.strip  {background:#f0e0e8; color:#5a1a3a; border-left:3px solid #a04060}
.tier-pill{display:inline-block; padding:1px 7px; border-radius:9px;
           font-size:0.78em; font-weight:700; vertical-align:middle}
.tier-pill.trust  {background:#d4edda; color:#155724}
.tier-pill.salvage{background:#fff3cd; color:#856404}
.tier-pill.strip  {background:#f8d7da; color:#721c24}
.label-acc{display:inline-block; min-width:6.5em; color:#555; font-size:0.85em; font-weight:600}
.label-conf{display:inline-block; min-width:6.5em; color:#555; font-size:0.85em; font-weight:600}
small{color:#555}
pre{white-space:pre-wrap; word-break:break-word; margin:0}
.summary{background:#e9ecef; padding:12px; border-radius:6px; margin-bottom:16px}
</style></head><body>
<h2>ASR Report (REF vs HYP)</h2>
<p><b>Accuracy:</b> <span class="ok">green</span>=match, <span class="rep">yellow</span>=mismatch/shift, <span class="ins">red</span>=inserted/made-up</p>
<p><b>Confidence (model softmax):</b> <span class="conf-high">blue</span>=high (&ge;0.85), <span class="conf-med">orange</span>=medium (0.40&ndash;0.85), <span class="conf-low">purple</span>=low (&lt;0.40) &mdash; <i>only shown when per-token scores were captured during decode</i></p>
<p><b>Reliability tier</b> (segment-level, keyed on sentence_confidence):
   <span class="tier-pill trust">Trust</span> &ge;0.82 — coloring is reliable as labeled.
   <span class="tier-pill salvage">Salvage</span> 0.65&ndash;0.82 — coloring shown with caveat banner; verify names, numbers, critical details.
   <span class="tier-pill strip">Strip</span> &lt;0.65 — per-word coloring removed because green leakage exceeds 50% in this regime; treat the whole hypothesis as unreliable.</p>
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


_NUMBER_WORDS = frozenset(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty "
    "thirty forty fifty sixty seventy eighty ninety hundred thousand million "
    "billion trillion first second third fourth fifth sixth seventh eighth "
    "ninth tenth once twice double triple half quarter".split()
)


def _classify_token_basic(word: str) -> str:
    """Classify a word without spaCy (stopword-based fallback)."""
    w = word.lower().strip()
    if not w:
        return "low"
    # Digits, digit-prefixed tokens, and number words → high
    if w.isdigit() or re.match(r'^[0-9]', w) or w in _NUMBER_WORDS:
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
    When the reference has no high-value tokens, falls back to content words
    (nouns, verbs, adjectives, adverbs) so the metric stays meaningful.
    - Recall: how many important ref words appear in hyp
    - Precision: how much of hyp's important content is real
    - F1: harmonic mean
    """
    ref_classified = classify_tokens(ref)
    hyp_classified = classify_tokens(hyp)

    ref_high = [w for w, c in ref_classified if c == "high"]
    hyp_high = [w for w, c in hyp_classified if c == "high"]

    # When ref has no high-value tokens, fall back to content words (high + med)
    # so we don't trivially return 100% for completely wrong outputs
    if ref_high:
        ref_important = ref_high
        hyp_important = hyp_high
    else:
        ref_important = [w for w, c in ref_classified if c in ("high", "med")]
        hyp_important = [w for w, c in hyp_classified if c in ("high", "med")]

    if not ref_important and not hyp_important:
        return MetricsResult(0.0, 100.0, 100.0, 100.0, [], _metrics_mode())

    ref_set = set(ref_important)
    hyp_set = set(hyp_important)

    matched = ref_set & hyp_set
    missed = sorted(ref_set - hyp_set)

    recall = (len(matched) / len(ref_set) * 100) if ref_set else 100.0
    precision = (len(matched) / len(hyp_set) * 100) if hyp_set else 100.0
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
    hyp_tokens = classify_tokens(hyp)
    hyp_words = [w for w, _ in hyp_tokens]

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


def _error_color(error_pct: float) -> str:
    """Color for error-rate metrics (WER, WWER) — lower is better."""
    if error_pct <= 30:
        return "green"
    elif error_pct <= 60:
        return "yellow"
    return "red"


def _recall_color(recall_pct: float) -> str:
    """Color for recall/accuracy metrics (NEA) — higher is better."""
    if recall_pct >= 70:
        return "green"
    elif recall_pct >= 40:
        return "yellow"
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
# Run parameters formatting (optional, for documentation)
# -----------------------

def _format_params_txt(params: Dict[str, Any]) -> str:
    """Format decode parameters as a plain-text header block."""
    lines = ["=== Run Parameters ==="]
    lines.append(f"beam: {params.get('beam', '?')} | length_penalty: {params.get('length_penalty', '?')} | repetition_penalty: {params.get('repetition_penalty', '?')}")
    lines.append(f"max_len: {params.get('max_len_a', '?')} * src + {params.get('max_len_b', '?')} (cap {params.get('max_len', '?')}) | no_repeat_ngram: {params.get('no_repeat_ngram_size', '?')}")
    lines.append(f"lm_weight: {params.get('lm_weight', '?')} | max_tokens: {params.get('max_tokens', '?')} | GPU: {params.get('gpu_mem_gb', '?')} GB{' (small)' if params.get('small_gpu') else ''}")
    ckpt = params.get('model_checkpoint', '')
    if ckpt:
        lines.append(f"Model: .../{Path(ckpt).name}" if '/' in ckpt else f"Model: {ckpt}")
    ts = params.get('timestamp', '')
    segs = params.get('num_segments', '')
    if ts or segs:
        parts = []
        if ts:
            parts.append(f"Decoded: {ts}")
        if segs:
            parts.append(f"Segments: {segs}")
        lines.append(" | ".join(parts))
    lines.append("=" * 23)
    return "\n".join(lines)


def _format_params_ansi(params: Dict[str, Any]) -> str:
    """Format decode parameters as an ANSI-colored header block."""
    dim = ANSI['dim']
    rst = ANSI['reset']
    txt = _format_params_txt(params)
    # Dim the border lines, keep content normal
    out_lines = []
    for line in txt.split("\n"):
        if line.startswith("="):
            out_lines.append(f"{dim}{line}{rst}")
        else:
            out_lines.append(f"{dim}{line.split(':')[0]}:{rst}{':'.join(line.split(':')[1:])}" if ':' in line else line)
    return "\n".join(out_lines)


def _format_params_html(params: Dict[str, Any]) -> str:
    """Format decode parameters as an HTML box."""
    rows = []
    rows.append(f"<b>beam:</b> {escape(str(params.get('beam', '?')))}")
    rows.append(f"<b>length_penalty:</b> {escape(str(params.get('length_penalty', '?')))}")
    rows.append(f"<b>repetition_penalty:</b> {escape(str(params.get('repetition_penalty', '?')))}")
    rows.append(f"<b>max_len:</b> {escape(str(params.get('max_len_a', '?')))} &times; src + {escape(str(params.get('max_len_b', '?')))} (cap {escape(str(params.get('max_len', '?')))})")
    rows.append(f"<b>no_repeat_ngram:</b> {escape(str(params.get('no_repeat_ngram_size', '?')))}")
    rows.append(f"<b>lm_weight:</b> {escape(str(params.get('lm_weight', '?')))}")
    rows.append(f"<b>max_tokens:</b> {escape(str(params.get('max_tokens', '?')))}")
    gpu = params.get('gpu_mem_gb', '')
    if gpu:
        rows.append(f"<b>GPU:</b> {escape(str(gpu))} GB{' (small)' if params.get('small_gpu') else ''}")
    ckpt = params.get('model_checkpoint', '')
    if ckpt:
        name = Path(ckpt).name if '/' in ckpt else ckpt
        rows.append(f"<b>Model:</b> {escape(name)}")
    ts = params.get('timestamp', '')
    if ts:
        rows.append(f"<b>Decoded:</b> {escape(ts)}")
    segs = params.get('num_segments', '')
    if segs:
        rows.append(f"<b>Segments:</b> {escape(str(segs))}")

    return (
        '<div class="summary" style="font-size:0.9em">'
        '<b>Run Parameters</b><br>'
        + " &nbsp;|&nbsp; ".join(rows)
        + '</div>'
    )


# -----------------------
# Main
# -----------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="decode outputs (.jsonl OR hypo-*.json)")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--params", default=None, help="decode_params JSON file (optional)")
    ap.add_argument("--compute-is", action="store_true", help="Compute Intelligibility Scores")
    ap.add_argument("--word-confidence", default=None,
                    help="word_confidence.json (from compute_word_confidence.py); enables per-word confidence rendering and per-segment confidence columns")
    ap.add_argument("--aggregated", default=None,
                    help="aggregated-{fid}.json (from lib/nbest_aggregate.py); enables per-method aggregated hypotheses and their WER in the report")
    args = ap.parse_args()

    # Word-level confidence (optional). Format: {utt_id: {words: [...], summary: {...}}}
    word_conf: Dict[str, Dict[str, Any]] = {}
    if args.word_confidence:
        try:
            word_conf = json.loads(Path(args.word_confidence).read_text(encoding="utf-8"))
            print(f"[INFO] Loaded word-confidence for {len(word_conf)} segments from {args.word_confidence}")
        except Exception as e:
            print(f"[WARN] Could not load --word-confidence {args.word_confidence}: {e}")
            word_conf = {}
    do_conf = bool(word_conf)

    # N-best aggregated hypotheses (optional). Format from lib/nbest_aggregate.py:
    # {utt_id: {hyp_top1: str, hyp_mbr: {text: ...}, hyp_vote_score: {...},
    #           hyp_vote_conf: {...}, hyp_safe: {...}, hyp_xseg_merge: {...}}}
    AGG_METHODS = ["hyp_mbr", "hyp_vote_score", "hyp_vote_conf", "hyp_safe", "hyp_xseg_merge"]
    aggregated: Dict[str, Dict[str, Any]] = {}
    if args.aggregated:
        try:
            aggregated = json.loads(Path(args.aggregated).read_text(encoding="utf-8"))
            print(f"[INFO] Loaded n-best aggregated hypotheses for {len(aggregated)} segments from {args.aggregated}")
        except Exception as e:
            print(f"[WARN] Could not load --aggregated {args.aggregated}: {e}")
            aggregated = {}
    do_agg = bool(aggregated)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load run parameters (optional — backward compatible)
    run_params: Optional[Dict[str, Any]] = None
    if args.params:
        try:
            run_params = json.loads(Path(args.params).read_text())
            print(f"[INFO] Loaded run parameters from {args.params}")
        except Exception as e:
            print(f"[WARN] Could not load params file {args.params}: {e}")

    recs = load_records(Path(args.jsonl))
    if not recs:
        print(f"[WARN] No records loaded from {args.jsonl}")
        return

    # Build display names and sort by (base_video_id, segment_index)
    display_names = build_display_names(recs)
    recs.sort(key=lambda r: (parse_segment_id(r.utt_id)[0], parse_segment_id(r.utt_id)[1]))

    print(f"[INFO] Metrics mode: {_metrics_mode()}")

    # IS computation (optional, EC2 only)
    do_is = args.compute_is and HAS_IS
    is_data = {}  # utt_id -> (score, tier, label)
    if args.compute_is and not HAS_IS:
        print("[WARN] --compute-is requested but IS dependencies not available")
    if do_is:
        print("[INFO] Computing Intelligibility Scores...")
        refs_list = [r.ref or "" for r in recs]
        hyps_list = [r.hypo or "" for r in recs]

        # Semantic similarity
        sem_sims = [0.0] * len(recs)
        if HAS_EMBEDDINGS:
            try:
                encoder = SemanticEncoder(device="auto")
                safe_refs = [r if r.strip() else "empty" for r in refs_list]
                safe_hyps = [h if h.strip() else "empty" for h in hyps_list]
                import numpy as np
                sem_arr = encoder.similarities(safe_refs, safe_hyps)
                for i, (r, h) in enumerate(zip(refs_list, hyps_list)):
                    if not r.strip() or not h.strip():
                        sem_arr[i] = 0.0
                sem_sims = [float(s) for s in sem_arr]
                print(f"[INFO] Semantic similarity computed (mean={sum(sem_sims)/len(sem_sims):.3f})")
            except Exception as e:
                print(f"[WARN] Semantic similarity failed: {e}")
        else:
            print("[INFO] Semantic similarity disabled (no transformers/torch)")

        # Phonetic similarity + length ratio + IS per segment
        for i, r in enumerate(recs):
            ref = r.ref or ""
            hyp = r.hypo or ""
            if not ref.strip():
                is_data[r.utt_id] = (0.0, 1, "Failed")
                continue
            phon = compute_phonetic_similarity(ref, hyp)
            lr = compute_length_ratio(ref, hyp)
            r_toks_is = toks(ref)
            h_toks_is = toks(hyp)
            wer_pct = (editdistance.eval(h_toks_is, r_toks_is) / len(r_toks_is) * 100) if r_toks_is else 0.0
            m_is = compute_all_metrics(ref, hyp)
            score, tier, label = compute_is(
                semantic_sim=sem_sims[i],
                phonetic_sim=phon["phonetic_sim"],
                wer_pct=wer_pct,
                wwer_pct=m_is.wwer,
                nea_f1_pct=m_is.nea_f1,
                length_ratio=lr,
            )
            is_data[r.utt_id] = (score, tier, label)
        mean_is = sum(s for s, _, _ in is_data.values()) / len(is_data) if is_data else 0.0
        captured = sum(1 for _, t, _ in is_data.values() if t >= 4)
        print(f"[INFO] IS computed: mean={mean_is:.2f}/5.0, captured={captured}/{len(is_data)} ({captured/len(is_data)*100:.1f}%)")

    # Build outputs with metrics
    rows_csv = []
    html_rows = []
    txt_blocks = []
    ansi_blocks = []

    # Accumulators for overall summary
    total_wer_num = 0.0
    total_wwer_num = 0.0
    total_wwer_den = 0.0
    total_nea_recall = 0.0
    total_nea_f1 = 0.0
    # Per-method aggregated-WER accumulators (mean over segments with refs)
    total_agg_wer = {m: 0.0 for m in AGG_METHODS}
    total_is = 0.0
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
            # Compute simple WER
            r_toks = toks(ref)
            h_toks = toks(hyp)
            simple_wer = (editdistance.eval(h_toks, r_toks) / len(r_toks) * 100) if r_toks else 0.0

            total_wer_num += simple_wer
            total_wwer_num += m.wwer
            total_nea_recall += m.nea_recall
            total_nea_f1 += m.nea_f1
            if do_is and r.utt_id in is_data:
                total_is += is_data[r.utt_id][0]
            n_with_ref += 1
        else:
            m = None
            simple_wer = 0.0

        # IS data for this record
        seg_is = is_data.get(r.utt_id) if do_is else None  # (score, tier, label)

        # Per-segment word-confidence summary (if available) — needed for both CSV and HTML below
        seg_conf = word_conf.get(r.utt_id) if do_conf else None
        seg_words = (seg_conf or {}).get("words") or []
        seg_summary = (seg_conf or {}).get("summary") or {}
        sent_conf_val = seg_summary.get("mean_word_prob") if seg_summary else None

        # Reliability tier — derived from sentence_confidence (mean_word_prob).
        # Empty string when do_conf is off or sentence confidence is unavailable.
        seg_tier = classify_tier(sent_conf_val) if do_conf else ""

        def _conf_csv_cells():
            """Return [sentence_confidence, min_word_conf, n_low_conf_words, tier] cells."""
            if not do_conf:
                return []
            if seg_summary:
                sc = seg_summary.get("mean_word_prob")
                mn = seg_summary.get("min_word_prob")
                nl = seg_summary.get("n_low")
                return [
                    f"{sc:.3f}" if isinstance(sc, (int, float)) else "",
                    f"{mn:.3f}" if isinstance(mn, (int, float)) else "",
                    str(nl) if isinstance(nl, int) else "",
                    seg_tier,
                ]
            return ["", "", "", ""]

        def _agg_csv_cells():
            """Return [hyp_<method>, wer_<method>_%] cells for each aggregated method.

            Order matches AGG_METHODS. WER uses the same simple-WER formula
            as the top-1 column, computed against the same reference. When
            the aggregated sidecar is absent, returns an empty list.
            """
            if not do_agg:
                return []
            agg_rec = aggregated.get(r.utt_id) or {}
            cells: list = []
            for method in AGG_METHODS:
                v = agg_rec.get(method)
                # v is either a string (hyp_top1) or a dict with 'text' (everything else)
                if isinstance(v, str):
                    text = v
                elif isinstance(v, dict):
                    text = v.get("text", "")
                else:
                    text = ""
                cells.append(text)
                if has_ref and r_toks:
                    h_method = toks(text) if text else []
                    w = (editdistance.eval(h_method, r_toks) / len(r_toks) * 100) if r_toks else 0.0
                    total_agg_wer[method] += w
                    cells.append(f"{w:.1f}")
                else:
                    cells.append("")
            return cells

        # CSV row
        if m:
            csv_row = [
                r.utt_id, dname, ref, hyp,
                " ".join([f"{w}:{t}" for w, t in tagged]),
                f"{simple_wer:.1f}", f"{m.wwer:.1f}", f"{m.nea_recall:.1f}", f"{m.nea_precision:.1f}",
                f"{m.nea_f1:.1f}", ", ".join(m.missed_entities) if m.missed_entities else "",
            ]
            if do_is:
                csv_row += [f"{seg_is[0]:.2f}", str(seg_is[1]), seg_is[2]] if seg_is else ["", "", ""]
            csv_row += _conf_csv_cells()
            csv_row += _agg_csv_cells()
            rows_csv.append(tuple(csv_row))
        else:
            csv_row = [
                r.utt_id, dname, ref, hyp,
                " ".join([f"{w}:{t}" for w, t in tagged]),
                "", "", "", "", "", "",
            ]
            if do_is:
                csv_row += ["", "", ""]
            csv_row += _conf_csv_cells()
            csv_row += _agg_csv_cells()
            rows_csv.append(tuple(csv_row))

        # HTML row — consistent coloring on all metric cells
        metrics_cells = ""
        if m:
            wer_css = f"m-{_error_color(simple_wer)}"
            wwer_css = f"m-{_error_color(m.wwer)}"
            nea_css = f"m-{_recall_color(m.nea_recall)}"
            missed_tip = f' title="Missed: {escape(", ".join(m.missed_entities))}"' if m.missed_entities else ""
            metrics_cells = (
                f'<td class="{wer_css}">{simple_wer:.1f}%</td>'
                f'<td class="{wwer_css}">{m.wwer:.1f}%</td>'
                f'<td class="{nea_css}"{missed_tip}>{m.nea_recall:.0f}%</td>'
            )
            if do_is and seg_is:
                is_css = f"m-{_recall_color(seg_is[0] * 20)}"  # 5.0 -> 100%
                metrics_cells += f'<td class="{is_css}" title="{escape(seg_is[2])}">{seg_is[0]:.2f}</td>'
            elif do_is:
                metrics_cells += '<td>-</td>'
            if do_conf:
                if isinstance(sent_conf_val, (int, float)):
                    sc_css = f"m-{_recall_color(sent_conf_val * 100)}"
                    metrics_cells += f'<td class="{sc_css}" title="mean word prob">{sent_conf_val:.2f}</td>'
                else:
                    metrics_cells += '<td>-</td>'
                if seg_tier:
                    metrics_cells += f'<td><span class="tier-pill {seg_tier.lower()}">{seg_tier}</span></td>'
                else:
                    metrics_cells += '<td>-</td>'
        else:
            metrics_cells = '<td>-</td><td>-</td><td>-</td>'
            if do_is:
                metrics_cells += '<td>-</td>'
            if do_conf:
                metrics_cells += '<td>-</td><td>-</td>'

        # Confidence-colored hyp goes in its own column when do_conf is on.
        # The reliability tier (Trust / Salvage / Strip) governs whether per-word
        # coloring is applied and whether a banner is prepended:
        #   - Trust   → full coloring, no banner
        #   - Salvage → full coloring + advisory banner ("verify names/numbers")
        #   - Strip   → coloring stripped; whole hyp rendered plain grey-italic
        # If no per-segment confidence data, render plain (uncolored) hyp.
        if do_conf:
            if seg_words:
                if seg_tier == "Salvage":
                    banner = (
                        '<span class="tier-banner salvage">'
                        'Model uncertain — verify names, numbers, and critical details.'
                        '</span>'
                    )
                    conf_cell = f'<td>{banner}<pre>{conf_html(seg_words, tier=seg_tier)}</pre></td>'
                elif seg_tier == "Strip":
                    banner = (
                        '<span class="tier-banner strip">'
                        'Low-confidence segment — per-word coloring removed. '
                        'Treat hypothesis as unreliable even where it looks fluent.'
                        '</span>'
                    )
                    conf_cell = f'<td>{banner}<pre>{conf_html(seg_words, tier=seg_tier)}</pre></td>'
                else:  # Trust or empty tier — original behavior
                    conf_cell = f'<td><pre>{conf_html(seg_words, tier=seg_tier or "Trust")}</pre></td>'
            else:
                conf_cell = f'<td><pre>{escape(hyp)}</pre></td>'
        else:
            conf_cell = ""

        html_rows.append(
            f"<tr><td><b>{escape(dname)}</b><br>"
            f"<small>{escape(r.utt_id)}</small></td>"
            f"<td><pre>{escape(ref)}</pre></td>"
            f"<td><pre>{hyp_html(tagged)}</pre></td>"
            f"{conf_cell}"
            f"{metrics_cells}</tr>"
        )

        # Plain text block
        metrics_line = ""
        if m:
            metrics_line = f"WER: {simple_wer:.1f}% | WWER: {m.wwer:.1f}% | NEA: R={m.nea_recall:.0f}% P={m.nea_precision:.0f}% F1={m.nea_f1:.0f}%"
            if do_is and seg_is:
                metrics_line += f" | IS: {seg_is[0]:.2f}/5.0 ({seg_is[2]})"
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

        # ANSI block — consistent coloring on all metrics
        ansi_metrics = ""
        if m:
            ac = {"green": ANSI["ok"], "yellow": ANSI["rep"], "red": ANSI["ins"]}
            wer_c = ac[_error_color(simple_wer)]
            wwer_c = ac[_error_color(m.wwer)]
            nea_c = ac[_recall_color(m.nea_recall)]
            is_ansi_part = ""
            if do_is and seg_is:
                is_c = ac[_recall_color(seg_is[0] * 20)]
                is_ansi_part = (
                    f" | {ANSI['dim']}IS:{ANSI['reset']} "
                    f"{is_c}{seg_is[0]:.2f}/5.0 ({seg_is[2]}){ANSI['reset']}"
                )
            ansi_metrics = (
                f"\n{ANSI['dim']}WER:{ANSI['reset']} {wer_c}{simple_wer:.1f}%{ANSI['reset']} | "
                f"{ANSI['dim']}WWER:{ANSI['reset']} {wwer_c}{m.wwer:.1f}%{ANSI['reset']} | "
                f"{nea_c}"
                f"NEA: R={m.nea_recall:.0f}% P={m.nea_precision:.0f}% F1={m.nea_f1:.0f}%"
                f"{ANSI['reset']}"
                f"{is_ansi_part}"
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
        avg_wer = total_wer_num / n_with_ref
        avg_wwer = total_wwer_num / n_with_ref
        avg_nea_recall = total_nea_recall / n_with_ref
        avg_nea_f1 = total_nea_f1 / n_with_ref
        summary = f"OVERALL | WER: {avg_wer:.1f}% | WWER: {avg_wwer:.1f}% | NEA Recall: {avg_nea_recall:.0f}% | NEA F1: {avg_nea_f1:.0f}%"
        if do_is and n_with_ref > 0:
            avg_is = total_is / n_with_ref
            captured = sum(1 for _, t, _ in is_data.values() if t >= 4)
            summary += f" | IS: {avg_is:.2f}/5.0 | Captured: {captured}/{n_with_ref} ({captured/n_with_ref*100:.1f}%)"
        summary += f" | Mode: {_metrics_mode()} | Segments: {n_with_ref}"
    else:
        summary = "OVERALL | No reference transcriptions available for metrics"

    # Write CSV (params go to a separate JSON to keep CSV clean)
    with open(out_dir / "report.csv", "w", newline="", encoding="utf-8") as cf:
        w = csv.writer(cf)
        csv_header = ["utt_id", "display_name", "ref", "hyp", "hyp_tagged",
                       "wer_%", "wwer_%", "nea_recall_%", "nea_precision_%", "nea_f1_%", "missed_entities"]
        if do_is:
            csv_header += ["is_score", "is_tier", "is_label"]
        if do_conf:
            csv_header += ["sentence_confidence", "min_word_conf", "n_low_conf_words", "tier"]
        if do_agg:
            for method in AGG_METHODS:
                csv_header += [method, f"wer_{method}_%"]
        w.writerow(csv_header)
        w.writerows(rows_csv)

    # Per-method aggregated WER summary (logged at end)
    if do_agg and n_with_ref > 0:
        method_summary = {m: total_agg_wer[m] / n_with_ref for m in AGG_METHODS}
        baseline_wer = total_wer_num / n_with_ref
        print(f"[INFO] Top-1 mean WER: {baseline_wer:.2f}%")
        for m, mw in method_summary.items():
            delta = mw - baseline_wer
            arrow = "↓" if delta < 0 else ("↑" if delta > 0 else "=")
            print(f"[INFO]   {m}: {mw:.2f}% ({arrow}{abs(delta):.2f}pp vs top-1)")
        # Also persist to a sidecar for downstream consumers.
        try:
            (out_dir / "aggregator_method_wer.json").write_text(
                json.dumps({"top1": baseline_wer, **method_summary, "n_segments": n_with_ref}, indent=2),
                encoding="utf-8",
            )
        except Exception as _e:
            pass

    if run_params:
        (out_dir / "report_params.json").write_text(
            json.dumps(run_params, indent=2), encoding="utf-8"
        )

    # Write HTML
    html_params = _format_params_html(run_params) if run_params else ""
    html_summary = f'<div class="summary"><b>{escape(summary)}</b></div>'
    is_th = '<th>IS</th>' if do_is else ''
    sent_conf_th = '<th title="mean per-word softmax probability">Sent Conf</th>' if do_conf else ''
    tier_th = '<th title="reliability tier — see legend above">Tier</th>' if do_conf else ''
    conf_hyp_th = '<th title="hypothesis colored by per-word model confidence">Hypothesis (Confidence)</th>' if do_conf else ''
    hyp_th_label = 'Hypothesis (Accuracy)' if do_conf else 'Hypothesis (colored)'
    html_table = (
        '<table>\n'
        f'<tr><th>ID</th><th>Reference</th><th>{hyp_th_label}</th>{conf_hyp_th}'
        f'<th>WER</th><th>WWER</th><th>NEA Recall</th>{is_th}{sent_conf_th}{tier_th}</tr>\n'
        + "\n".join(html_rows)
    )
    (out_dir / "report.html").write_text(
        HTML_HEAD + html_params + html_summary + html_table + HTML_TAIL,
        encoding="utf-8"
    )

    # Write plain txt
    txt_params = (_format_params_txt(run_params) + "\n") if run_params else ""
    (out_dir / "report.txt").write_text(
        txt_params + summary + "\n" + block_sep() + "\n"
        + "\n".join(txt_blocks) + "\n(END)\n",
        encoding="utf-8"
    )

    # Write ANSI txt
    ansi_params = (_format_params_ansi(run_params) + "\n") if run_params else ""
    ansi_summary = f"{ANSI['ok']}{summary}{ANSI['reset']}"
    (out_dir / "report.ansi.txt").write_text(
        ansi_params + ansi_summary + "\n" + f"{ANSI['dim']}{block_sep()}{ANSI['reset']}\n"
        + "\n".join(ansi_blocks) + f"\n{ANSI['dim']}(END){ANSI['reset']}\n",
        encoding="utf-8"
    )

    print(summary)
    print("Wrote:", out_dir / "report.csv")
    print("Wrote:", out_dir / "report.html")
    print("Wrote:", out_dir / "report.ansi.txt")
    print("Wrote:", out_dir / "report.txt")
    if run_params:
        print("Wrote:", out_dir / "report_params.json")
    print("Tip: view ANSI with: less -R report.ansi.txt")


if __name__ == "__main__":
    main()