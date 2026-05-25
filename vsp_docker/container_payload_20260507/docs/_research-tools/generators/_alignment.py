"""Shared word-level alignment utilities.

Used by:
- analyze_confidence_full.py: ref-vs-hyp correctness for calibration
- analyze_beam_variance.py: ref-vs-hyp correctness for word-level confusion stats
- lib/nbest_aggregate.py: hyp-vs-hyp alignment for ROVER-style voting

Pure NumPy, no torch/HF dependencies. CPU-only, container-compatible.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


def _normalize(words: Sequence[str]) -> List[str]:
    return [w.strip().lower() for w in words if w is not None]


def _edit_table(a: Sequence[str], b: Sequence[str]) -> np.ndarray:
    """Levenshtein DP table between two word lists.

    d[i][j] = edit distance between a[:i] and b[:j].
    Substitution cost 1; insertion/deletion cost 1.
    """
    n, m = len(a), len(b)
    d = np.zeros((n + 1, m + 1), dtype=np.int32)
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d


def align_word_lists(a: Sequence[str], b: Sequence[str]) -> List[Tuple[int, int]]:
    """Return aligned (i, j) column-index pairs.

    -1 indicates a gap (insertion/deletion) on that side. Pairs are returned in
    left-to-right order. Case-insensitive comparison; pairs report the original
    indices into `a` and `b`.

    Example:
        a = ["the", "cat"]; b = ["the", "fat", "cat"]
        → [(0, 0), (-1, 1), (1, 2)]   # 'fat' is an insertion in b
    """
    an = _normalize(a)
    bn = _normalize(b)
    n, m = len(an), len(bn)
    d = _edit_table(an, bn)

    pairs: List[Tuple[int, int]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and an[i - 1] == bn[j - 1] and d[i][j] == d[i - 1][j - 1]:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + 1:
            pairs.append((i - 1, j - 1))  # substitution: paired but mismatched
            i -= 1
            j -= 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            pairs.append((i - 1, -1))  # deletion (a-only)
            i -= 1
        else:
            pairs.append((-1, j - 1))  # insertion (b-only)
            j -= 1
    pairs.reverse()
    return pairs


def hyp_word_correctness(ref: str, hyp_words: Sequence[str]) -> List[int]:
    """1 if a hyp word matches its aligned ref word, 0 otherwise.

    Same semantics as the original `_word_correctness_alignment` in
    analyze_confidence_full.py — substitutions/insertions/deletions all yield 0.
    """
    rs = ref.strip().lower().split() if isinstance(ref, str) else _normalize(ref)
    hs = _normalize(hyp_words)
    pairs = align_word_lists(rs, hs)
    correct = [0] * len(hs)
    for ri, hi in pairs:
        if ri >= 0 and hi >= 0 and rs[ri] == hs[hi]:
            correct[hi] = 1
    return correct


def wer(ref_words: Sequence[str], hyp_words: Sequence[str]) -> float:
    """Word error rate (substitutions + insertions + deletions) / max(1, len(ref)).

    Case-insensitive; tokens are taken as-is (caller decides splitting).
    Returns 0.0 if both inputs are empty; returns 1.0 if ref is empty but hyp
    is not (every hyp word is an insertion).
    """
    rs = _normalize(ref_words)
    hs = _normalize(hyp_words)
    if not rs and not hs:
        return 0.0
    if not rs:
        return 1.0
    d = _edit_table(rs, hs)
    return float(d[len(rs)][len(hs)]) / max(1, len(rs))


def split_words(text: str) -> List[str]:
    """Pipeline-standard word splitter: matches the WER tokenization the rest of
    the codebase uses (`text.strip().split()`). Kept here so callers don't
    drift to alternative tokenizations.
    """
    return text.strip().split() if isinstance(text, str) else []
