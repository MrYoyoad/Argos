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
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence

# SentencePiece word-start marker used by LLaMA-2 / Llama 3.x tokenizers.
WORD_START_MARKER = "▁"

# Confidence-class thresholds (initial heuristic; tune after looking at ~10 real outputs).
CONF_HIGH = 0.7
CONF_MED = 0.3


def classify(prob: Optional[float]) -> str:
    """Map a probability to a CSS-friendly confidence class."""
    if prob is None:
        return "conf-unknown"
    if prob >= CONF_HIGH:
        return "conf-high"
    if prob >= CONF_MED:
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
) -> dict:
    """Aggregate every segment in a confidence sidecar into word-level confidence.

    Args:
        confidence_records: mapping of utt_id -> {"sequence_score", "tokens"}.

    Returns:
        mapping of utt_id -> {
            "sequence_score": float | None,
            "words": [...],
            "summary": {"max_word_prob", "min_word_prob", "mean_word_prob",
                        "n_words", "n_high", "n_med", "n_low"},
        }
    """
    out: dict = {}
    for utt_id, rec in confidence_records.items():
        tokens = rec.get("tokens", [])
        words = aggregate_subtokens_to_words(tokens)
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

    Defined as the mean of per-segment max-word probabilities. Returns None
    if no segment has any non-None word probabilities.
    """
    maxes = [
        s["summary"]["max_word_prob"]
        for s in per_segment.values()
        if s["summary"].get("max_word_prob") is not None
    ]
    if not maxes:
        return None
    return sum(maxes) / len(maxes)


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
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as f:
        confidence_records = json.load(f)

    per_segment = aggregate_segment_records(confidence_records)

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
