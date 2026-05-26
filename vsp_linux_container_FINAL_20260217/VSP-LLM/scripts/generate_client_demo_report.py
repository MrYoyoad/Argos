#!/usr/bin/env python3
"""Argos client-styled HTML report from a VSP-LLM decode JSON.

Produces a polished, dark-themed HTML report with one card per segment and
per-word green/yellow/red confidence coloring. Suitable for client-facing
deliverables (zip downloads, demo recordings, screenshots).

Confidence source priority:

  1. If a `confidence-{fid}.json` sidecar exists alongside the decode JSON
     (produced when VSP_OUTPUT_SCORES=1 in vsp_llm_decode), use real
     per-token softmax probabilities aggregated to per-word.
  2. Otherwise, synthesize confidence from the WER alignment between
     REF and HYP:
        match        → conf-high (synthetic prob 0.85)
        substitution → conf-med  (synthetic prob 0.50)
        insertion    → conf-low  (synthetic prob 0.20)
     A "synthetic" badge appears on each segment in this case.

Run (all segments in a decode JSON, default branding):
    python3 generate_client_demo_report.py --decode <path>/hypo-NNNN.json --out report.html

Run (curated subset with custom branding, e.g. the Obama demo artifact):
    python3 generate_client_demo_report.py \\
        --decode english_full_results/decode_output/hypo-84361.json \\
        --filter "050111_OsamaBinLadenStatement_HD" \\
        --title "Argos VSP — Visual Speech Recognition" \\
        --subtitle "Client demo · Obama bin Laden announcement (May 1, 2011)" \\
        --source "Public TV broadcast" \\
        --out presentation_materials_20260224/01_plots_for_slides/obama_demo_report.html
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# Synthetic confidence thresholds — match the real ones in
# compute_word_confidence.py so the same CSS classes apply.
SYNTH_PROBS = {"match": 0.85, "sub": 0.50, "ins": 0.20}

# Outer strip gate: segment-level mean word probability below this floor
# means per-word coloring would mislead users (P(correct|green) drops to
# ~22% in the worst tier). Matches make_report.classify_tier and the
# May 2026 band-reliability rollout. See docs/confidence/band_reliability_lesson.md.
STRIP_TIER_FLOOR = 0.65

# Frame rate the pipeline uses to convert segment-name frame indices to
# seconds (e.g. Obama_00_000150_000450 → start_sec=6.0 at 25 fps).
PIPELINE_FPS = 25.0


def _normalize_words(text: str) -> List[str]:
    """Split text into lowercase word tokens. Strips punctuation."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    return [w for w in text.split() if w]


def align_ref_hyp(ref: str, hyp: str) -> List[tuple]:
    """Align reference and hypothesis word lists; tag each HYP word.

    Returns:
        list of (hyp_word, tag) where tag is "match" / "sub" / "ins".
    """
    ref_words = _normalize_words(ref)
    hyp_words = _normalize_words(hyp)
    matcher = difflib.SequenceMatcher(a=ref_words, b=hyp_words, autojunk=False)
    out: List[tuple] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            for j in range(j1, j2):
                out.append((hyp_words[j], "match"))
        elif op == "replace":
            for j in range(j1, j2):
                out.append((hyp_words[j], "sub"))
        elif op == "insert":
            for j in range(j1, j2):
                out.append((hyp_words[j], "ins"))
        elif op == "delete":
            # Words missing from HYP — not rendered (we color HYP only).
            pass
    return out


def words_with_synthetic_confidence(ref: str, hyp: str) -> List[dict]:
    """Build per-word confidence list from WER alignment."""
    tagged = align_ref_hyp(ref, hyp)
    out = []
    tag_to_class = {"match": "conf-high", "sub": "conf-med", "ins": "conf-low"}
    tag_to_prob = {
        "match": SYNTH_PROBS["match"],
        "sub": SYNTH_PROBS["sub"],
        "ins": SYNTH_PROBS["ins"],
    }
    for word, tag in tagged:
        out.append({
            "word": word,
            "prob": tag_to_prob[tag],
            "conf_class": tag_to_class[tag],
        })
    return out


def render_words_html(words: Sequence[Mapping]) -> str:
    """Render a list of {word, prob, conf_class} as an HTML span string.

    Each word carries a `data-prob` attribute that drives a CSS tooltip
    (see CSS `.word::after` rule). Native title= tooltips are unreliable
    in IDE-embedded previews and slow in browsers; the CSS approach
    renders instantly on hover.
    """
    parts = []
    for w in words:
        klass = escape(w.get("conf_class", "conf-unknown"))
        prob = w.get("prob")
        prob_str = f"{prob:.2f}" if prob is not None else "n/a"
        parts.append(
            f'<span class="word {klass}" data-prob="{prob_str}">'
            f'{escape(w["word"])}</span>'
        )
    return " ".join(parts)


def _segment_label(utt_id: str, prefix_alias: Optional[Mapping[str, str]] = None) -> str:
    """Return a human-friendly segment label from an utt_id.

    Format: '{prefix} · segment #N · S.Ss–E.Es' if the trailing numeric
    suffix is present, otherwise the raw utt_id. `prefix_alias` lets callers
    rewrite a known utt_id prefix to a friendlier display name.
    """
    base = utt_id.strip("_")
    if prefix_alias:
        for src, dst in prefix_alias.items():
            if src and src in base:
                base = base.replace(src, dst).strip("_")
                break
    m = re.match(r"(.+?)_(\d{2})_(\d{6})_(\d{6})$", base)
    if m:
        prefix, idx, start_ms, end_ms = m.groups()
        start_s = int(start_ms) / 100
        end_s = int(end_ms) / 100
        return f"{prefix}  ·  segment #{int(idx)}  ·  {start_s:.1f}s–{end_s:.1f}s"
    return base


def overall_badge(records: Sequence[dict]) -> Optional[float]:
    maxes = []
    for rec in records:
        words = rec.get("words", [])
        probs = [w["prob"] for w in words if w.get("prob") is not None]
        if probs:
            maxes.append(max(probs))
    if not maxes:
        return None
    return sum(maxes) / len(maxes)


def _badge_class(badge: Optional[float]) -> str:
    """Map mean per-word probability to the reliability tier badge.

    Thresholds match make_report.classify_tier and make_burn._classify_tier:
    >= 0.82 → trust, >= 0.65 → inspect, below → don't believe.
    """
    if badge is None:
        return "badge-unknown"
    if badge >= 0.82:
        return "badge-high"
    if badge >= 0.65:
        return "badge-med"
    return "badge-low"


def _badge_label(badge: Optional[float]) -> str:
    if badge is None:
        return "—"
    if badge >= 0.82:
        return "TRUST"
    if badge >= 0.65:
        return "INSPECT"
    return "DON'T BELIEVE"


CSS = """
:root {
  --bg: #0d1b2a;
  --bg-card: #152a40;
  --bg-card-2: #1a3550;
  --teal: #00b4d8;
  /* Confidence palette — matches make_report.py and make_burn.py */
  --conf-high: #4fc3f7;     /* trust   — bright blue   */
  --conf-med:  #ffb300;     /* inspect — warm amber    */
  --conf-low:  #ba68c8;     /* don't believe — purple  */
  --conf-high-bg: #16324a;
  --conf-med-bg:  #4a3a08;
  --conf-low-bg:  #3a1d4a;
  --gray: #aaaaaa;
  --gray-mid: #666666;
  --white: #ffffff;
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--white);
  font-family: 'Segoe UI', Calibri, system-ui, sans-serif;
  margin: 0;
  padding: 28px 36px;
  line-height: 1.45;
}
h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 4px 0;
  color: var(--white);
}
h1 .subtitle {
  display: block;
  font-size: 14px;
  font-weight: 400;
  color: var(--gray);
  margin-top: 4px;
}
.summary {
  display: flex;
  gap: 16px;
  align-items: stretch;
  margin: 22px 0 28px 0;
}
.summary-card {
  background: var(--bg-card);
  padding: 14px 18px;
  border-radius: 8px;
  flex: 1;
}
.summary-card .label {
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--gray);
}
.summary-card .value {
  font-size: 26px;
  font-weight: 700;
  color: var(--white);
  margin-top: 4px;
}
.badge {
  font-size: 38px;
  font-weight: 800;
  padding: 14px 22px;
  border-radius: 8px;
  text-align: center;
  min-width: 140px;
}
.badge-high   { background: var(--conf-high-bg); color: var(--conf-high); }
.badge-med    { background: var(--conf-med-bg);  color: var(--conf-med); }
.badge-low    { background: var(--conf-low-bg);  color: var(--conf-low); }
.badge-unknown{ background: var(--bg-card-2);    color: var(--gray); }
.legend {
  background: var(--bg-card);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 22px;
  font-size: 13px;
  color: var(--gray);
}
.legend .swatch {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  margin: 0 6px;
  font-weight: 600;
}
.swatch.conf-high { background: var(--conf-high-bg); color: var(--conf-high); }
.swatch.conf-med  { background: var(--conf-med-bg);  color: var(--conf-med); }
.swatch.conf-low  { background: var(--conf-low-bg);  color: var(--conf-low); }
.segment {
  background: var(--bg-card);
  border-radius: 10px;
  padding: 18px 22px;
  margin-bottom: 16px;
}
.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}
.segment-title {
  font-size: 13px;
  color: var(--teal);
  font-weight: 600;
  letter-spacing: 0.04em;
}
.segment-tag {
  font-size: 10px;
  color: var(--gray-mid);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.row {
  display: flex;
  gap: 18px;
  margin-top: 8px;
}
.row .label {
  flex: 0 0 60px;
  font-size: 11px;
  color: var(--gray);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding-top: 4px;
}
.row .text {
  flex: 1;
  font-size: 17px;
  line-height: 1.55;
}
.row.ref .text {
  color: var(--gray);
  font-style: italic;
}
.word {
  padding: 1px 5px;
  border-radius: 3px;
  margin: 0 1px;
  font-weight: 500;
  cursor: help;
  position: relative;
}
.word.conf-high { color: var(--conf-high); }
.word.conf-med  { color: var(--conf-med); }
.word.conf-low  { color: var(--conf-low); text-decoration: underline wavy var(--conf-low); }
/* Stripped: segment-level confidence was too low to trust per-word coloring.
   Render plain text without bands so the colors don't mislead. */
.word.conf-stripped { color: var(--gray); }
.swatch.conf-stripped { background: var(--bg-card-2); color: var(--gray); }
/* Thin per-video header that groups segments without adding stats noise. */
.video-header {
  margin: 26px 0 10px 0;
  padding: 6px 4px 4px 4px;
  border-bottom: 1px solid var(--gray-mid);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}
.video-header .video-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--white);
  letter-spacing: 0.04em;
}
.video-header .video-count {
  font-size: 11px;
  color: var(--gray);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.segment-tag.stripped {
  color: var(--conf-low);
}
/* CSS-driven hover tooltip — renders instantly, no browser delay,
   works in IDE-embedded HTML previews where title= often does not. */
.word::after {
  content: "p = " attr(data-prob);
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  background: #0a0f17;
  color: var(--white);
  font-size: 12px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid var(--gray-mid);
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
  z-index: 10;
}
.word:hover::after { opacity: 1; }
.footer-note {
  margin-top: 30px;
  font-size: 11px;
  color: var(--gray-mid);
  font-style: italic;
  text-align: center;
}
"""


def render_html(records: Sequence[dict], badge: Optional[float],
                synthetic_confidence: bool,
                title: str = "Confidence Breakdown",
                subtitle: Optional[str] = None,
                source: str = "Pipeline output",
                prefix_alias: Optional[Mapping[str, str]] = None) -> str:
    """Build the full HTML page."""
    badge_text = _badge_label(badge)
    badge_class = _badge_class(badge)
    n = len(records)
    if subtitle is None:
        subtitle = f"{n} segments"

    def _render_segment(rec: dict) -> str:
        label = _segment_label(rec["utt_id"], prefix_alias=prefix_alias)
        ref_text = escape(rec["ref"])
        words_html = render_words_html(rec["words"])
        if rec.get("stripped"):
            tag_text = "low confidence — coloring stripped"
            tag_class = "segment-tag stripped"
        elif synthetic_confidence:
            tag_text = "synthetic confidence (B3 data pending)"
            tag_class = "segment-tag"
        else:
            tag_text = "live model confidence"
            tag_class = "segment-tag"
        return f"""
        <div class="segment">
          <div class="segment-header">
            <span class="segment-title">{escape(label)}</span>
            <span class="{tag_class}">{escape(tag_text)}</span>
          </div>
          <div class="row ref">
            <span class="label">REF</span>
            <span class="text">{ref_text}</span>
          </div>
          <div class="row hyp">
            <span class="label">HYP</span>
            <span class="text">{words_html}</span>
          </div>
        </div>
        """

    # Group segments under thin per-video headers. Keeps the page scannable
    # without piling aggregate stats on top — coloring carries the trust signal.
    body_blocks: List[str] = []
    for base, recs in _group_by_video(records):
        body_blocks.append(
            f'<div class="video-header">'
            f'<span class="video-name">{escape(base)}</span>'
            f'<span class="video-count">{len(recs)} segment{"s" if len(recs) != 1 else ""}</span>'
            f'</div>'
        )
        for rec in recs:
            body_blocks.append(_render_segment(rec))
    segments_html = "\n".join(body_blocks)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Confidence Breakdown</title>
  <style>{CSS}</style>
</head>
<body>
  <h1>
    {escape(title)}
    <span class="subtitle">{escape(subtitle)}</span>
  </h1>

  <div class="summary">
    <div class="badge {badge_class}">{badge_text}<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;margin-top:4px">OVERALL TIER</div></div>
    <div class="summary-card">
      <div class="label">Segments</div>
      <div class="value">{n}</div>
    </div>
    <div class="summary-card">
      <div class="label">Source</div>
      <div class="value" style="font-size:18px">{escape(source)}</div>
    </div>
    <div class="summary-card">
      <div class="label">Audio</div>
      <div class="value" style="font-size:18px">Not used — vision only</div>
    </div>
  </div>

  <div class="legend">
    Per-word confidence:
    <span class="swatch conf-high">trust</span>
    <span class="swatch conf-med">inspect</span>
    <span class="swatch conf-low">don't believe</span>
    <span class="swatch conf-stripped">stripped (segment too low)</span>
    &nbsp; · &nbsp;Hover any word to see its confidence value.
  </div>

  {segments_html}
</body>
</html>
"""


# Segment-id parser matching make_report.parse_segment_id / make_burn.parse_segment_id.
# Format: {video_id}_{seg_idx:02d}_{start_frame:06d}_{end_frame:06d}
def parse_segment_id(segment_id: str) -> Tuple[str, int, int, int]:
    """Return (base_video_id, seg_idx, start_frame, end_frame). For
    non-segmented IDs, returns (segment_id, -1, -1, -1)."""
    parts = segment_id.split("_")
    if len(parts) < 4:
        return segment_id, -1, -1, -1
    try:
        end_frame = int(parts[-1])
        start_frame = int(parts[-2])
        seg_idx = int(parts[-3])
        base_video_id = "_".join(parts[:-3])
        return base_video_id, seg_idx, start_frame, end_frame
    except (ValueError, IndexError):
        return segment_id, -1, -1, -1


def _segment_time_window(utt_id: str) -> Tuple[float, float]:
    """Derive (start_sec, end_sec) from segment-name frame indices at PIPELINE_FPS."""
    _, _, start_frame, end_frame = parse_segment_id(utt_id)
    if start_frame < 0 or end_frame < 0:
        return 0.0, 0.0
    return start_frame / PIPELINE_FPS, end_frame / PIPELINE_FPS


def _group_by_video(records: Sequence[dict]) -> List[Tuple[str, List[dict]]]:
    """Group records by base video id, preserving first-seen order, with
    segments within each group sorted by seg_idx (then start_frame)."""
    order: List[str] = []
    groups: Dict[str, List[dict]] = {}
    for rec in records:
        base, _, _, _ = parse_segment_id(rec["utt_id"])
        if base not in groups:
            groups[base] = []
            order.append(base)
        groups[base].append(rec)
    for base, recs in groups.items():
        recs.sort(key=lambda r: (parse_segment_id(r["utt_id"])[1],
                                 parse_segment_id(r["utt_id"])[2]))
    return [(base, groups[base]) for base in order]


def _apply_trust_stack(words: List[dict], agreement: Optional[List[float]]) -> Tuple[float, bool, List[dict]]:
    """Re-classify each word using classify_joint (agreement-aware + numeric
    cap) and apply the segment-level strip gate.

    Returns: (sentence_confidence, stripped, words_with_updated_conf_class).

    - sentence_confidence = mean of non-None word probs (0.0 if all None).
    - stripped = True iff sentence_confidence < STRIP_TIER_FLOOR. When True,
      each word's conf_class is overwritten to 'conf-stripped'.
    """
    from compute_word_confidence import classify_joint, is_numeric

    probs = [w["prob"] for w in words if w.get("prob") is not None]
    sent_conf = (sum(probs) / len(probs)) if probs else 0.0
    stripped = bool(probs) and sent_conf < STRIP_TIER_FLOOR

    out_words: List[dict] = []
    for i, w in enumerate(words):
        prob = w.get("prob")
        agree = None
        if agreement and i < len(agreement):
            try:
                agree = float(agreement[i])
            except (TypeError, ValueError):
                agree = None
        new = dict(w)
        if stripped:
            new["conf_class"] = "conf-stripped"
        else:
            new["conf_class"] = classify_joint(prob, agree, is_numeric(w.get("word")))
        if agree is not None:
            new["agreement"] = agree
        out_words.append(new)

    return sent_conf, stripped, out_words


def _resolve_display_method(default: str = "hyp_mbr") -> str:
    """Pick the displayed aggregation method. Matches lib/outputs.sh:200."""
    return os.environ.get("VSP_DISPLAY_METHOD", default)


def load_records(decode_json: Path, segment_filter: str,
                 display_method: Optional[str] = None) -> List[dict]:
    """Load decoded segments matching `segment_filter` and attach confidence.

    Trust stack applied per record:
      1. synthetic WER confidence as fallback;
      2. real per-word probs from confidence-{fid}.json if present;
      3. aggregated method's per-word entries from aggregated.json when
         display_method != 'top1' and entries exist;
      4. classify_joint() with agreement-{fid}.json + numeric cap;
      5. segment-level strip gate (sentence_confidence < STRIP_TIER_FLOOR).
    """
    data = json.loads(decode_json.read_text(encoding="utf-8"))
    ids = data.get("utt_id", [])
    refs = data.get("ref", [])
    hyps = data.get("hypo", [])

    out: List[dict] = []
    for i, utt_id in enumerate(ids):
        if segment_filter not in utt_id:
            continue
        ref = refs[i] if i < len(refs) else ""
        hyp = hyps[i] if i < len(hyps) else ""
        # Skip empty / placeholder refs
        if not hyp.strip():
            continue
        words = words_with_synthetic_confidence(ref, hyp)
        out.append({
            "utt_id": utt_id,
            "ref": ref,
            "hyp": hyp,
            "words": words,
            "synthetic": True,
        })

    # Optional: load a real confidence-{fid}.json sidecar if it exists alongside
    # the decode JSON (produced when VSP_OUTPUT_SCORES=1 was set).
    fid_match = re.search(r"hypo-(\d+)\.json", decode_json.name)
    fid = fid_match.group(1) if fid_match else None
    sidecar = decode_json.with_name(f"confidence-{fid}.json") if fid else None
    agree_sidecar = decode_json.with_name(f"agreement-{fid}.json") if fid else None
    aggregated_path = decode_json.with_name("aggregated.json")

    real: Dict[str, dict] = {}
    if sidecar and sidecar.exists():
        real = json.loads(sidecar.read_text(encoding="utf-8"))
        from compute_word_confidence import aggregate_subtokens_to_words
        for rec in out:
            seg = real.get(rec["utt_id"])
            if seg and seg.get("tokens"):
                rec["words"] = aggregate_subtokens_to_words(seg["tokens"])
                rec["synthetic"] = False

    agreement_by_utt: Dict[str, List[float]] = {}
    if agree_sidecar and agree_sidecar.exists():
        try:
            agreement_by_utt = json.loads(agree_sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            agreement_by_utt = {}

    # Aggregated method swap (MBR / vote_score / vote_conf / safe). When the
    # displayed method is non-top1 and an aggregated.json sidecar exists,
    # replace each record's hypo + per-word entries with the method's output.
    method = (display_method or _resolve_display_method()).strip()
    if aggregated_path.exists() and method and method != "top1":
        try:
            agg = json.loads(aggregated_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            agg = {}
        for rec in out:
            entry = (agg or {}).get(rec["utt_id"]) or {}
            method_entry = entry.get(method) or {}
            method_hyp = method_entry.get("hyp")
            method_words = method_entry.get("words")
            if method_hyp:
                rec["hyp"] = method_hyp
            if method_words:
                # Each word: {"word": str, "prob": float|None, "agreement"?: float}
                rec["words"] = [
                    {
                        "word": w.get("word", ""),
                        "prob": w.get("prob"),
                        # carry agreement if the aggregated entry has it; we'll
                        # still consult the global agreement sidecar below as
                        # a fallback.
                        **({"agreement": float(w["agreement"])} if "agreement" in w and w["agreement"] is not None else {}),
                        "n_subtokens": w.get("n_subtokens", 1),
                    }
                    for w in method_words
                ]
                rec["synthetic"] = False
                rec["display_method"] = method

    # Apply the multi-layered trust rule (joint conf+agreement + numeric cap
    # + segment-level strip gate) to every record. Non-synthetic records get
    # the agreement signal when available; synthetic records still get the
    # numeric cap but agreement is None.
    for rec in out:
        agreement = agreement_by_utt.get(rec["utt_id"]) if not rec.get("synthetic") else None
        # Prefer per-word agreement carried by the aggregated method entry
        # when present (more accurate alignment to the displayed text).
        if all("agreement" in w for w in rec["words"]) and rec["words"]:
            agreement = [w.get("agreement") for w in rec["words"]]
        sent_conf, stripped, new_words = _apply_trust_stack(rec["words"], agreement)
        rec["words"] = new_words
        rec["sentence_confidence"] = sent_conf
        rec["stripped"] = stripped

    return out


def build_whole_video_cc(records: Sequence[dict]) -> dict:
    """Build the whole_video_cc.json payload: per-parent-video segment
    timeline with REF, HYP, per-word bands, sentence_confidence, and the
    strip flag. Times are derived from segment-name frame indices at
    PIPELINE_FPS (no Whisper word_timestamps needed)."""
    grouped = _group_by_video(records)
    videos: Dict[str, dict] = {}
    for base, recs in grouped:
        segments = []
        max_end = 0.0
        for r in recs:
            start_sec, end_sec = _segment_time_window(r["utt_id"])
            max_end = max(max_end, end_sec)
            segments.append({
                "segment_id": r["utt_id"],
                "start_sec": round(start_sec, 3),
                "end_sec": round(end_sec, 3),
                "ref": r.get("ref", ""),
                "hyp": r.get("hyp", ""),
                "words": [
                    {k: v for k, v in w.items() if k in ("word", "prob", "agreement", "conf_class")}
                    for w in r.get("words", [])
                ],
                "sentence_confidence": round(float(r.get("sentence_confidence", 0.0)), 4),
                "stripped": bool(r.get("stripped", False)),
            })
        videos[base] = {"duration_sec": round(max_end, 3), "segments": segments}
    return {"videos": videos}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--decode", type=Path, required=True,
                        help="decode JSON file (hypo-NNNN.json from VSP-LLM decode)")
    parser.add_argument("--out", type=Path, required=True,
                        help="output HTML path")
    parser.add_argument("--filter", type=str, default="",
                        help="utt_id substring filter — only segments containing this "
                             "substring are rendered. Default: '' (all segments).")
    parser.add_argument("--title", type=str,
                        default="Confidence Breakdown",
                        help="page H1 title")
    parser.add_argument("--subtitle", type=str, default=None,
                        help="page subtitle under H1 (default: 'N segments')")
    parser.add_argument("--source", type=str, default="Pipeline output",
                        help="value shown in the 'Source' summary card "
                             "(e.g. 'Public TV broadcast', dataset name)")
    parser.add_argument("--prefix-alias", type=str, default=None,
                        help="rewrite an utt_id prefix in segment labels, format "
                             "'src=dst' (e.g. '050111_OsamaBinLadenStatement_HD"
                             "=Obama bin Laden speech')")
    parser.add_argument("--display-method", type=str, default=None,
                        help="aggregated-method hypothesis to render (top1, "
                             "hyp_mbr, hyp_vote_score, hyp_vote_conf, hyp_safe). "
                             "Defaults to $VSP_DISPLAY_METHOD or hyp_mbr.")
    parser.add_argument("--whole-video-cc", type=Path, default=None,
                        help="if set, write whole_video_cc.json to this path "
                             "(per-parent-video segment timeline used by the "
                             "vsp-ui 'Watch with CC' viewer)")
    args = parser.parse_args()

    if not args.decode.exists():
        raise SystemExit(f"decode JSON not found: {args.decode}")

    records = load_records(args.decode, args.filter,
                           display_method=args.display_method)
    if not records:
        raise SystemExit(f"no segments matching filter '{args.filter}' in {args.decode}")

    synthetic = all(rec.get("synthetic", True) for rec in records)
    badge = overall_badge(records)

    prefix_alias = None
    if args.prefix_alias:
        if "=" not in args.prefix_alias:
            raise SystemExit("--prefix-alias must be of the form 'src=dst'")
        src, dst = args.prefix_alias.split("=", 1)
        prefix_alias = {src: dst}

    html = render_html(records, badge, synthetic,
                       title=args.title, subtitle=args.subtitle,
                       source=args.source, prefix_alias=prefix_alias)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"  segments: {len(records)}")
    print(f"  badge: {badge:.3f}" if badge else "  badge: n/a")
    print(f"  confidence source: {'synthetic (WER-derived)' if synthetic else 'real (sidecar)'}")

    if args.whole_video_cc is not None:
        payload = build_whole_video_cc(records)
        args.whole_video_cc.parent.mkdir(parents=True, exist_ok=True)
        args.whole_video_cc.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.whole_video_cc}  ({len(payload['videos'])} videos)")


if __name__ == "__main__":
    main()
