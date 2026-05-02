"""Aggregate sub-token softmax probabilities into per-word confidence.

Reads a confidence-{fid}.json sidecar (written by vsp_llm_decode.py when
VSP_OUTPUT_SCORES=1) and emits a word-confidence JSON suitable for the
vsp-ui report renderer (green/yellow/red coloring).

Aggregation: minimum probability across the sub-tokens that make up a word
(conservative — flag the word if any of its pieces is uncertain).

LLaMA / SentencePiece tokens use the U+2581 "lower one eighth block" (▁)
prefix to mark the start of a new word. Tokens without that prefix continue
the current word (this is how contractions like "don't" land — `▁don` + `'t`).

CLI:
    python compute_word_confidence.py path/to/confidence-{fid}.json [--out path]

Module:
    from compute_word_confidence import aggregate_subtokens_to_words, classify
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence

# SentencePiece word-start marker used by LLaMA-2 / Llama 3.x tokenizers.
WORD_START_MARKER = "▁"

# Confidence-class thresholds. Tightened from initial 0.7/0.3 to 0.85/0.4
# on 2026-04-30 after running on real per-token data and reading the
# Llama-2 confidence literature review (docs/confidence/llama2_confidence_literature_review.md).
# Rationale:
#   - LLaMA-2 is mildly over-confident in the 0.7-0.95 band (5-15pp ECE).
#   - On the 33-Obama-segment B3 sample, 89.7% of words landed at p>=0.7
#     under the old threshold — green coverage was meaningless.
#   - Literature norm for "trust without review" is p>=0.85 in calibrated
#     speech / NER / MT pipelines (Whisper, NeMo, OpenAI).
CONF_HIGH = 0.85
CONF_MED = 0.40

# Joint conf + beam-agreement thresholds (see TRUST_DIAGNOSTIC.md, May 2 2026).
T_GREEN_CONF = 0.95
T_GREEN_AGREE = 0.80
T_YELLOW_CONF = 0.65
T_YELLOW_AGREE = 0.50

_NUMBER_WORDS = frozenset(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty "
    "thirty forty fifty sixty seventy eighty ninety hundred thousand "
    "million billion trillion".split()
)


def is_numeric(word: Optional[str]) -> bool:
    """True if word contains a digit or is a known number-word."""
    if not word:
        return False
    w = re.sub(r"[^a-z0-9]", "", str(word).lower())
    if not w:
        return False
    if any(c.isdigit() for c in w):
        return True
    return w in _NUMBER_WORDS


def classify(prob: Optional[float]) -> str:
    """Map a probability to a CSS-friendly confidence class."""
    if prob is None:
        return "conf-unknown"
    if prob >= CONF_HIGH:
        return "conf-high"
    if prob >= CONF_MED:
        return "conf-med"
    return "conf-low"


def classify_joint(prob: Optional[float], agreement: Optional[float], is_num: bool) -> str:
    """Joint confidence + beam-agreement band. Numbers cap at conf-med — empirically
    they hit only P(correct)=0.744 at the joint green threshold (conf>=0.95 AND
    agree>=0.80), well below the 0.85 promise. See SAFETY_ANALYSIS.md."""
    if prob is None:
        return "conf-unknown"
    if is_num:
        if prob >= T_YELLOW_CONF and (agreement is None or agreement >= T_YELLOW_AGREE):
            return "conf-med"
        return "conf-low"
    if agreement is None:
        return classify(prob)
    if prob >= T_GREEN_CONF and agreement >= T_GREEN_AGREE:
        return "conf-high"
    if prob >= T_YELLOW_CONF and agreement >= T_YELLOW_AGREE:
        return "conf-med"
    return "conf-low"


def _is_special(token_text: str) -> bool:
    """Skip BOS/EOS/UNK and other angle-bracketed special tokens."""
    if not token_text:
        return True
    t = token_text.strip()
    return t.startswith("<") and t.endswith(">") and len(t) >= 2


def _starts_new_word(token_text: str) -> bool:
    """A SentencePiece token that begins with the word-start marker (or a
    plain leading space) starts a new word. Pure-punctuation tokens
    without a marker continue the current word."""
    if not token_text:
        return False
    return token_text.startswith(WORD_START_MARKER) or token_text.startswith(" ")


def _strip_marker(token_text: str) -> str:
    """Remove the leading word-start marker (or space) for display."""
    if token_text.startswith(WORD_START_MARKER):
        return token_text[len(WORD_START_MARKER):]
    if token_text.startswith(" "):
        return token_text[1:]
    return token_text


def _combine(group: Sequence[Mapping]) -> dict:
    """Combine a group of sub-tokens into a single word entry.

    `prob` is the minimum sub-token probability (conservative). If any
    sub-token has a None prob, the word's prob is None (treated as unknown).
    """
    word_text = "".join(_strip_marker(t["token"]) if i == 0 else t["token"]
                        for i, t in enumerate(group))
    probs = [t["prob"] for t in group]
    word_prob: Optional[float]
    if any(p is None for p in probs):
        word_prob = None
    else:
        word_prob = min(float(p) for p in probs)
    return {
        "word": word_text,
        "prob": word_prob,
        "conf_class": classify(word_prob),
        "n_subtokens": len(group),
    }


def aggregate_subtokens_to_words(tokens: Iterable[Mapping]) -> List[dict]:
    """Group consecutive sub-tokens into words and aggregate confidence.

    Args:
        tokens: iterable of {"token", "prob", ...} dicts in generation order.

    Returns:
        list of {"word", "prob", "conf_class", "n_subtokens"} dicts.
    """
    words: List[dict] = []
    group: List[Mapping] = []
    for tok in tokens:
        text = tok.get("token", "")
        if _is_special(text):
            continue
        if _starts_new_word(text) and group:
            words.append(_combine(group))
            group = []
        group.append(tok)
    if group:
        words.append(_combine(group))
    return words


def aggregate_segment_records(
    confidence_records: Mapping[str, Mapping],
    agreement_records: Optional[Mapping[str, List[float]]] = None,
) -> dict:
    """Aggregate every segment in a confidence sidecar into word-level confidence.

    When ``agreement_records`` is provided, each per-word dict gains
    ``agreement`` and ``is_numeric`` keys, and ``conf_class`` reflects the
    joint conf+agreement rule from ``classify_joint``.
    """
    out: dict = {}
    use_joint = agreement_records is not None
    for utt_id, rec in confidence_records.items():
        tokens = rec.get("tokens", [])
        words = aggregate_subtokens_to_words(tokens)
        if use_joint:
            agreements = list(agreement_records.get(utt_id, []) or [])
            for i, w in enumerate(words):
                a = agreements[i] if i < len(agreements) else None
                num = is_numeric(w.get("word"))
                w["agreement"] = a
                w["is_numeric"] = num
                w["conf_class"] = classify_joint(w.get("prob"), a, num)
        probs = [w["prob"] for w in words if w["prob"] is not None]
        summary = {
            "max_word_prob": max(probs) if probs else None,
            "min_word_prob": min(probs) if probs else None,
            "mean_word_prob": (sum(probs) / len(probs)) if probs else None,
            "n_words": len(words),
            "n_high": sum(1 for w in words if w["conf_class"] == "conf-high"),
            "n_med": sum(1 for w in words if w["conf_class"] == "conf-med"),
            "n_low": sum(1 for w in words if w["conf_class"] == "conf-low"),
        }
        out[utt_id] = {
            "sequence_score": rec.get("sequence_score"),
            "words": words,
            "summary": summary,
        }
    return out


def overall_confidence_badge(per_segment: Mapping[str, Mapping]) -> Optional[float]:
    """Compute the overall-confidence badge value for the UI Complete screen.

    Defined as the **fraction of all words classified conf-high** across
    all segments. Returns a value in [0, 1] or None if no words exist.

    Rationale: directly interpretable as "of all words across the run, this
    fraction passed the conf-high threshold (>=CONF_HIGH)". The earlier
    "mean of per-segment max-word-prob" was always near 1.0 on real data
    (every segment has at least one near-perfect word) — uninformative.
    """
    n_high = 0
    n_classified = 0
    for s in per_segment.values():
        summary = s.get("summary", {})
        n_high += summary.get("n_high", 0)
        # Only count words that have a real probability (not conf-unknown).
        n_classified += (summary.get("n_high", 0)
                         + summary.get("n_med", 0)
                         + summary.get("n_low", 0))
    if n_classified == 0:
        return None
    return n_high / n_classified


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="confidence-{fid}.json sidecar produced by vsp_llm_decode",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path (default: <input>.words.json next to input)",
    )
    parser.add_argument(
        "--agreement",
        type=Path,
        default=None,
        help="optional agreement-{fid}.json (from compute_word_agreement.py); "
             "enables the joint conf+beam-agreement band rule",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as f:
        confidence_records = json.load(f)

    agreement_records: Optional[Mapping[str, List[float]]] = None
    if args.agreement is not None:
        with args.agreement.open("r", encoding="utf-8") as f:
            agreement_records = json.load(f)

    per_segment = aggregate_segment_records(confidence_records, agreement_records)

    out_path = args.out or args.input.with_suffix("").with_name(
        args.input.stem + ".words.json"
    )
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(per_segment, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path} ({len(per_segment)} segments)")

    badge = overall_confidence_badge(per_segment)
    if badge is not None:
        print(f"Overall confidence badge: {badge:.3f}")


if __name__ == "__main__":
    main()
