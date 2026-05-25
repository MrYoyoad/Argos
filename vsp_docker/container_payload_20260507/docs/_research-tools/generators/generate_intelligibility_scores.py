#!/usr/bin/env python3
"""
Argos -- Intelligibility Assessment Engine

Computes a composite Intelligibility Score (IS) for each segment in a
report.csv, combining 6 signals: semantic similarity, phonetic similarity,
inverse WER, inverse WWER, named entity accuracy, and length ratio.

Usage:
    python3 generate_intelligibility_scores.py \
        --csv /path/to/report.csv \
        --out_dir /path/to/output

Output:
    - intelligibility_scores.csv  (augmented CSV with IS columns)
    - intelligibility_summary.json (aggregate stats, tier counts)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import editdistance
import numpy as np

# ── Phonetic encoding ────────────────────────────────────────────────
try:
    from metaphone import doublemetaphone
    HAS_METAPHONE = True
except ImportError:
    HAS_METAPHONE = False

# ── Sentence embeddings ──────────────────────────────────────────────
HAS_EMBEDDINGS = False
try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    HAS_EMBEDDINGS = True
except ImportError:
    pass

# ── Tokenizer (matches make_report.py) ───────────────────────────────

def toks(s: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words (same as make_report.py)."""
    s = (s or "").strip().lower()
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", s)


# ── Signal 1: Semantic Similarity ────────────────────────────────────

class SemanticEncoder:
    """Batch sentence encoder using all-MiniLM-L6-v2."""

    def __init__(self, device: str = "auto"):
        if not HAS_EMBEDDINGS:
            raise RuntimeError("transformers/torch not available")
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()

    @torch.no_grad()
    def encode(self, texts: List[str], batch_size: int = 128) -> np.ndarray:
        all_emb = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            encoded = self.tokenizer(
                batch, padding=True, truncation=True,
                max_length=128, return_tensors="pt"
            ).to(self.device)
            out = self.model(**encoded)
            # Mean pooling over token embeddings
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1)
            all_emb.append(emb.cpu().numpy())
        return np.vstack(all_emb)

    def similarities(self, refs: List[str], hyps: List[str],
                     batch_size: int = 128) -> np.ndarray:
        ref_emb = self.encode(refs, batch_size)
        hyp_emb = self.encode(hyps, batch_size)
        # Cosine similarity per pair
        ref_norm = ref_emb / (np.linalg.norm(ref_emb, axis=1, keepdims=True) + 1e-9)
        hyp_norm = hyp_emb / (np.linalg.norm(hyp_emb, axis=1, keepdims=True) + 1e-9)
        return np.sum(ref_norm * hyp_norm, axis=1)


# ── Signal 2: Phonetic Similarity ───────────────────────────────────

def phonetic_code(word: str) -> str:
    """Return primary Double Metaphone code for a word."""
    if HAS_METAPHONE:
        codes = doublemetaphone(word)
        return codes[0] or ""
    return ""


def compute_phonetic_similarity(
    ref_text: str, hyp_text: str
) -> Dict:
    """
    Compute phonetic similarity between ref and hyp.

    Returns dict with:
      - phonetic_sim: 0-1 score (fraction of ref words with phonetic match)
      - phonetic_matches: count of exact phonetic matches
      - phonetic_near_misses: count of near-matches (metaphone dist <= 2)
      - confusions: list of (ref_word, hyp_word, ref_code, hyp_code, dist)
    """
    r_words = toks(ref_text)
    h_words = toks(hyp_text)

    if not r_words:
        return {
            "phonetic_sim": 0.0 if not h_words else 0.0,
            "phonetic_matches": 0,
            "phonetic_near_misses": 0,
            "confusions": [],
        }

    if not h_words:
        return {
            "phonetic_sim": 0.0,
            "phonetic_matches": 0,
            "phonetic_near_misses": 0,
            "confusions": [],
        }

    if not HAS_METAPHONE:
        # Fallback: use raw edit distance ratio as rough phonetic proxy
        exact = sum(1 for rw, hw in zip(r_words, h_words) if rw == hw)
        return {
            "phonetic_sim": exact / len(r_words),
            "phonetic_matches": exact,
            "phonetic_near_misses": 0,
            "confusions": [],
        }

    # Align ref and hyp using SequenceMatcher to find substitutions
    from difflib import SequenceMatcher
    sm = SequenceMatcher(None, r_words, h_words)

    exact_matches = 0       # Same word (exact text match)
    phonetic_exact = 0      # Different word but same Metaphone code
    phonetic_near = 0       # Different word, Metaphone distance <= 2
    confusions = []

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            exact_matches += (i2 - i1)
        elif op == "replace":
            for ri, hi in zip(range(i1, i2), range(j1, j2)):
                rw, hw = r_words[ri], h_words[hi]
                rc, hc = phonetic_code(rw), phonetic_code(hw)
                if not rc or not hc:
                    continue
                dist = editdistance.eval(rc, hc)
                if dist == 0:
                    phonetic_exact += 1
                elif dist <= 2:
                    phonetic_near += 1
                if dist > 0:
                    confusions.append((rw, hw, rc, hc, dist))

    # Phonetic sim = (exact text matches + phonetic matches) / ref length
    # Phonetic near-misses count at 0.5 weight
    total_matched = exact_matches + phonetic_exact + 0.5 * phonetic_near
    sim = min(1.0, total_matched / len(r_words))

    return {
        "phonetic_sim": sim,
        "phonetic_matches": phonetic_exact,
        "phonetic_near_misses": phonetic_near,
        "confusions": confusions,
    }


# ── Signal 6: Length Ratio ───────────────────────────────────────────

def compute_length_ratio(ref_text: str, hyp_text: str) -> float:
    """Ratio of hyp length to ref length. 1.0 is ideal."""
    r = toks(ref_text)
    h = toks(hyp_text)
    if not r:
        return 0.0
    return len(h) / len(r)


# ── Composite Intelligibility Score ──────────────────────────────────

DEFAULT_WEIGHTS = {
    "semantic_sim": 0.25,
    "phonetic_sim": 0.15,
    "inv_wer": 0.15,
    "inv_wwer": 0.15,
    "nea_f1": 0.15,
    "length_ratio": 0.15,
}

TIER_LABELS = {
    5: "Excellent",
    4: "Good",
    3: "Fair",
    2: "Poor",
    1: "Failed",
}


def scale_semantic(sim: float) -> float:
    """Scale cosine similarity (typically 0-0.9) to 0-5."""
    return min(5.0, max(0.0, (sim / 0.85) * 5.0))


def scale_phonetic(sim: float) -> float:
    """Scale phonetic similarity (0-1) to 0-5."""
    return sim * 5.0


def scale_inverse_rate(rate_pct: float) -> float:
    """Scale inverse error rate: WER 0% → 5, WER 100% → 0, WER>100% → 0."""
    return max(0.0, (1.0 - rate_pct / 100.0)) * 5.0


def scale_nea_f1(f1_pct: float) -> float:
    """Scale NEA F1 (0-100%) to 0-5."""
    return (f1_pct / 100.0) * 5.0


def scale_length_ratio(ratio: float) -> float:
    """Scale length ratio: 1.0 → 5, deviations penalized."""
    if ratio <= 0:
        return 0.0
    # Penalty for deviation from 1.0, capped
    deviation = abs(1.0 - ratio)
    return max(0.0, (1.0 - deviation) * 5.0)


# ── Context Recovery Estimation ──────────────────────────────────────

def estimate_context_recovery(
    semantic_sim: float,
    wwer_pct: float,
    wer_pct: float,
    length_ratio: float,
) -> Tuple[bool, str]:
    """
    Estimate whether a viewer WITH topic context could understand the segment.

    A viewer who already knows the general topic (e.g., "this is a cooking video")
    can fill in gaps that a cold reader cannot. This estimates that recoverability.

    Returns: (recoverable: bool, reason: str)
    """
    # Definite floor: WER <= 15% is almost always understandable
    if wer_pct <= 15:
        return True, "low_wer"

    # Definite ceiling: WER > 100% is never understandable (hallucination)
    if wer_pct > 100:
        return False, "hallucination"

    # Empty output
    if length_ratio < 0.1:
        return False, "empty_output"

    # Extreme length mismatch (> 2x or < 0.3x) suggests hallucination
    if length_ratio > 2.0 or length_ratio < 0.3:
        return False, "length_mismatch"

    # High semantic similarity + moderate WWER = likely recoverable with context
    if semantic_sim > 0.5 and wwer_pct < 60:
        return True, "semantic_coherent"

    # Moderate semantic + low WWER = recoverable
    if semantic_sim > 0.35 and wwer_pct < 40:
        return True, "moderate_semantic_low_error"

    # High WWER means content words are destroyed — not recoverable even with context
    if wwer_pct > 70:
        return False, "content_destroyed"

    # WER > 70% with low semantic sim = not recoverable
    if wer_pct > 70 and semantic_sim < 0.4:
        return False, "high_wer_low_semantic"

    # Middle ground: marginal
    if semantic_sim > 0.3 and wwer_pct < 55:
        return True, "marginal_recoverable"

    return False, "insufficient_signal"


def estimate_llm_context_recovery(
    ref_text: str,
    hyp_text: str,
    semantic_sim: float,
    phonetic_sim: float,
    wwer_pct: float,
    wer_pct: float,
    nea_f1_pct: float,
    length_ratio: float,
) -> Tuple[float, str]:
    """
    LLM-knowledge-based context recovery estimation.

    Uses multiple heuristics that approximate how an expert LLM would assess
    whether a viewer with topic context could understand the segment.

    Unlike the rule-based approach, this considers:
    - Topic word overlap (do key nouns/verbs match?)
    - Phonetic plausibility (are errors typical lip-reading confusions?)
    - Sentence structure preservation (does the hypothesis follow the same grammar?)
    - Information density (does the hypothesis contain specific, useful info?)

    Returns: (probability 0-1, reasoning_category)
    """
    r_words = toks(ref_text)
    h_words = toks(hyp_text)

    # Empty cases
    if not r_words or not h_words:
        return 0.0, "empty"

    # ── Factor 1: Content word overlap (topic preservation) ──
    # If key nouns/verbs survive, the topic is preserved
    r_set = set(r_words)
    h_set = set(h_words)
    overlap = r_set & h_set
    overlap_rate = len(overlap) / len(r_set) if r_set else 0

    # ── Factor 2: Sequence preservation ──
    # Do overlapping words appear in roughly the same order?
    # Use longest common subsequence ratio
    from difflib import SequenceMatcher
    seq_ratio = SequenceMatcher(None, r_words, h_words).ratio()

    # ── Factor 3: Phonetic plausibility ──
    # If most substitutions are phonetically close, errors are natural
    # lip-reading confusions (not hallucinations)
    phon_plausible = phonetic_sim > 0.5

    # ── Factor 4: Length sanity ──
    # Extreme length differences indicate hallucination/truncation
    length_ok = 0.4 <= length_ratio <= 1.8

    # ── Factor 5: Semantic domain coherence ──
    # High semantic similarity means the hypothesis is about the same topic
    domain_coherent = semantic_sim > 0.35

    # ── Factor 6: Information density check ──
    # Very short hypotheses for long references indicate truncation/failure
    info_present = len(h_words) >= max(3, len(r_words) * 0.3)

    # ── Combine factors into probability ──
    prob = 0.0
    reason = "not_recoverable"

    # Strong positive signals
    if wer_pct <= 15:
        return 1.0, "near_perfect"

    if seq_ratio > 0.7 and overlap_rate > 0.5:
        return 0.95, "strong_structure_match"

    if semantic_sim > 0.6 and overlap_rate > 0.4 and length_ok:
        return 0.9, "high_semantic_good_overlap"

    if semantic_sim > 0.5 and phon_plausible and length_ok:
        return 0.8, "semantic_plus_phonetic"

    if overlap_rate > 0.5 and domain_coherent and length_ok:
        return 0.75, "good_overlap_coherent"

    if semantic_sim > 0.4 and wwer_pct < 55 and info_present:
        return 0.65, "moderate_semantic_preserved_content"

    if seq_ratio > 0.5 and domain_coherent and info_present:
        return 0.6, "moderate_structure_coherent"

    if phonetic_sim > 0.6 and semantic_sim > 0.3 and length_ok:
        return 0.55, "phonetic_bridge_semantic"

    # Weak positive
    if overlap_rate > 0.3 and semantic_sim > 0.3 and length_ok:
        return 0.4, "partial_overlap"

    if domain_coherent and info_present and nea_f1_pct > 40:
        return 0.45, "entities_preserved_coherent"

    # Negative signals
    if wer_pct > 100:
        return 0.05, "hallucination"

    if not length_ok:
        return 0.1, "length_mismatch"

    if not info_present:
        return 0.1, "insufficient_information"

    if semantic_sim < 0.2 and overlap_rate < 0.2:
        return 0.1, "no_semantic_no_overlap"

    # Default weak
    if semantic_sim > 0.25 or overlap_rate > 0.2:
        return 0.3, "marginal"

    return 0.15, "unlikely_recoverable"


# ── Failure Mode Classification ─────────────────────────────────────

def classify_failure_mode(
    ref_text: str, hyp_text: str,
    wer_pct: float, semantic_sim: float, phonetic_sim: float,
    nea_f1_pct: float, length_ratio: float,
) -> str:
    """
    Classify the dominant failure mode for a non-recoverable segment.

    Returns a human-readable failure mode label. Designed for segments
    with IS < 3.0 (tiers 1-3).
    """
    hyp = (hyp_text or "").strip()
    if not hyp:
        return "Empty Output"
    if wer_pct > 100:
        return "Hallucination"
    if length_ratio > 1.8:
        return "Over-generation"
    if length_ratio < 0.3:
        return "Truncation"
    if semantic_sim < 0.2 and phonetic_sim < 0.3:
        return "Total Topic Drift"
    if semantic_sim < 0.2 and phonetic_sim >= 0.3:
        return "Phonetically Similar but Wrong Topic"
    if semantic_sim >= 0.2 and nea_f1_pct < 10 and wer_pct > 60:
        return "Entity Destruction"
    if wer_pct > 70:
        return "High Error Rate"
    if semantic_sim >= 0.3 and wer_pct > 50:
        return "Content Word Errors"
    return "Accumulated Small Errors"


# ── Success Pattern Classification ──────────────────────────────────

def classify_success_pattern(
    wer_pct: float, semantic_sim: float, phonetic_sim: float,
    nea_f1_pct: float, length_ratio: float,
) -> str:
    """
    Classify what makes a properly-captured segment succeed.

    Returns a human-readable success pattern label. Designed for segments
    with IS >= 3.0 (tiers 4-5).
    """
    if wer_pct <= 10:
        return "Near-Perfect Output"
    if wer_pct <= 25 and semantic_sim > 0.6:
        return "Minor Errors, High Semantic Match"
    if phonetic_sim > 0.7 and wer_pct > 25:
        return "Phonetically Preserved"
    if nea_f1_pct > 60 and wer_pct > 25:
        return "Entities Preserved"
    if semantic_sim > 0.5 and 0.7 <= length_ratio <= 1.3:
        return "Good Semantic + Correct Length"
    if wer_pct <= 35:
        return "Low-Moderate WER"
    if semantic_sim > 0.4 and phonetic_sim > 0.5:
        return "Combined Semantic + Phonetic Bridge"
    return "Multiple Partial Signals"


# ── Topic Classification ────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "Medical/Health": ["doctor", "medical", "patient", "health", "cancer", "disease",
        "blood", "pressure", "surgery", "hospital", "diagnosis", "treatment",
        "therapy", "medicine", "symptom", "pain", "clinical", "heart", "brain", "vitamin"],
    "Cooking/Food": ["cook", "recipe", "food", "eat", "kitchen", "oven", "ingredient",
        "cup", "tablespoon", "teaspoon", "bake", "fry", "boil", "sauce", "pepper",
        "salt", "chicken", "beef", "vegetable", "meal"],
    "Technology": ["computer", "software", "phone", "app", "internet", "digital",
        "technology", "code", "program", "data", "website", "online", "iphone",
        "android", "camera", "samsung", "battery", "screen"],
    "Sports/Fitness": ["game", "team", "player", "score", "coach", "training",
        "exercise", "workout", "football", "basketball", "soccer", "fitness",
        "muscle", "weight", "gym", "race", "championship"],
    "Education/Academic": ["study", "research", "university", "school", "professor",
        "student", "learn", "education", "science", "theory", "experiment", "exam",
        "class", "lecture", "knowledge", "course"],
    "Business/Finance": ["business", "company", "money", "market", "invest", "stock",
        "price", "profit", "economy", "financial", "bank", "trade", "revenue",
        "customer", "product", "sales"],
    "Politics/News": ["president", "government", "political", "election", "vote",
        "congress", "law", "policy", "country", "nation", "democrat", "republican",
        "senator", "war", "military"],
    "Entertainment": ["movie", "music", "show", "film", "song", "star", "celebrity",
        "dance", "concert", "comedy", "drama", "actor", "singer", "performance"],
    "Religion/Spirituality": ["god", "church", "bible", "pray", "faith", "spiritual",
        "soul", "worship", "jesus", "christian", "muslim", "jewish", "religion", "blessing"],
    "DIY/Home": ["house", "build", "paint", "wood", "tool", "repair", "install",
        "garden", "project", "material", "measure", "cut", "glue", "drill"],
}


def classify_topic(ref_text: str) -> str:
    """Classify a reference sentence into a topic category by keyword matching."""
    ref_lower = (ref_text or "").lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in ref_lower for kw in keywords):
            return topic
    return "Other"


# ── Composite Intelligibility Score ──────────────────────────────────

def compute_is(
    semantic_sim: float,
    phonetic_sim: float,
    wer_pct: float,
    wwer_pct: float,
    nea_f1_pct: float,
    length_ratio: float,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, int, str]:
    """
    Compute Intelligibility Score.

    Returns: (score, tier_num, tier_label)
    """
    w = weights or DEFAULT_WEIGHTS

    s_sem = scale_semantic(semantic_sim)
    s_phon = scale_phonetic(phonetic_sim)
    s_wer = scale_inverse_rate(wer_pct)
    s_wwer = scale_inverse_rate(wwer_pct)
    s_nea = scale_nea_f1(nea_f1_pct)
    s_len = scale_length_ratio(length_ratio)

    score = (
        w["semantic_sim"] * s_sem +
        w["phonetic_sim"] * s_phon +
        w["inv_wer"] * s_wer +
        w["inv_wwer"] * s_wwer +
        w["nea_f1"] * s_nea +
        w["length_ratio"] * s_len
    )

    score = max(0.0, min(5.0, score))

    if score >= 4.0:
        tier = 5
    elif score >= 3.0:
        tier = 4
    elif score >= 2.0:
        tier = 3
    elif score >= 1.0:
        tier = 2
    else:
        tier = 1

    return score, tier, TIER_LABELS[tier]


# ── NIV (Net Intelligibility Verdict) thresholds ─────────────────────
# Calibrated against Opus 4.6 LLM judge on 1,497 segments (March 2026).
# See docs/evaluation/threshold_calibration_vs_opus.md.
#   Y  : IS >= 3.80  -> kappa=0.690 vs judge Y      (clearly conveyed)
#   Y+P: IS >= 2.00  -> kappa=0.818 vs judge Y+P    (any useful)
NIV_Y_THRESHOLD = 3.80
NIV_P_THRESHOLD = 2.00


def niv_label(is_score: float) -> str:
    """Map IS to Net Intelligibility Verdict (Y / P / N)."""
    if is_score >= NIV_Y_THRESHOLD:
        return "Y"
    if is_score >= NIV_P_THRESHOLD:
        return "P"
    return "N"


# ── CSV Loading ──────────────────────────────────────────────────────

def load_csv(path: str) -> List[Dict]:
    """Load report CSV and parse numeric fields."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ["wer_%", "wwer_%", "nea_recall_%", "nea_precision_%", "nea_f1_%"]:
                try:
                    row[key] = float(row.get(key, 0) or 0)
                except (ValueError, TypeError):
                    row[key] = 0.0
            rows.append(row)
    return rows


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Compute Intelligibility Scores")
    parser.add_argument("--csv", required=True, help="Path to report.csv")
    parser.add_argument("--out_dir", required=True, help="Output directory")
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading CSV: {args.csv}")
    rows = load_csv(args.csv)
    print(f"  Loaded {len(rows)} segments")

    refs = [r.get("ref", "") or "" for r in rows]
    hyps = [r.get("hyp", "") or "" for r in rows]

    # ── Signal 1: Semantic Similarity ──
    if HAS_EMBEDDINGS:
        print("Computing semantic similarity (all-MiniLM-L6-v2)...")
        encoder = SemanticEncoder(device=args.device)
        # Handle empty strings
        safe_refs = [r if r.strip() else "empty" for r in refs]
        safe_hyps = [h if h.strip() else "empty" for h in hyps]
        sem_sims = encoder.similarities(safe_refs, safe_hyps, args.batch_size)
        # Zero out similarity for empty pairs
        for i, (r, h) in enumerate(zip(refs, hyps)):
            if not r.strip() or not h.strip():
                sem_sims[i] = 0.0
        print(f"  Mean semantic similarity: {sem_sims.mean():.3f}")
    else:
        print("WARNING: transformers/torch not available. Semantic similarity disabled.")
        sem_sims = np.zeros(len(rows))

    # ── Signal 2: Phonetic Similarity ──
    print("Computing phonetic similarity...")
    phonetic_results = []
    all_confusions = Counter()
    for r, h in zip(refs, hyps):
        pr = compute_phonetic_similarity(r, h)
        phonetic_results.append(pr)
        for conf in pr["confusions"]:
            ref_w, hyp_w = conf[0], conf[1]
            all_confusions[(ref_w, hyp_w)] += 1

    phon_sims = np.array([pr["phonetic_sim"] for pr in phonetic_results])
    print(f"  Mean phonetic similarity: {phon_sims.mean():.3f}")

    # ── Signal 6: Length Ratio ──
    print("Computing length ratios...")
    length_ratios = np.array([compute_length_ratio(r, h) for r, h in zip(refs, hyps)])

    # ── Composite IS ──
    print("Computing Intelligibility Scores...")
    is_scores = []
    is_tiers = []
    is_labels = []

    for i, row in enumerate(rows):
        score, tier, label = compute_is(
            semantic_sim=float(sem_sims[i]),
            phonetic_sim=float(phon_sims[i]),
            wer_pct=row["wer_%"],
            wwer_pct=row["wwer_%"],
            nea_f1_pct=row["nea_f1_%"],
            length_ratio=float(length_ratios[i]),
        )
        is_scores.append(score)
        is_tiers.append(tier)
        is_labels.append(label)

    is_scores = np.array(is_scores)
    is_tiers = np.array(is_tiers)

    # ── Context Recovery Estimation (Rule-Based) ──
    print("Estimating context recoverability (rule-based)...")
    ctx_recoverable = []
    ctx_reasons = []
    for i, row in enumerate(rows):
        rec, reason = estimate_context_recovery(
            semantic_sim=float(sem_sims[i]),
            wwer_pct=row["wwer_%"],
            wer_pct=row["wer_%"],
            length_ratio=float(length_ratios[i]),
        )
        ctx_recoverable.append(rec)
        ctx_reasons.append(reason)
    n_recoverable = sum(ctx_recoverable)
    print(f"  Context-recoverable (rules): {n_recoverable}/{len(rows)}"
          f" ({n_recoverable/len(rows)*100:.1f}%)")

    # ── Context Recovery Estimation (LLM-Knowledge-Based) ──
    print("Estimating context recoverability (LLM-knowledge-based)...")
    llm_ctx_probs = []
    llm_ctx_reasons = []
    for i, row in enumerate(rows):
        prob, reason = estimate_llm_context_recovery(
            ref_text=refs[i],
            hyp_text=hyps[i],
            semantic_sim=float(sem_sims[i]),
            phonetic_sim=float(phon_sims[i]),
            wwer_pct=row["wwer_%"],
            wer_pct=row["wer_%"],
            nea_f1_pct=row["nea_f1_%"],
            length_ratio=float(length_ratios[i]),
        )
        llm_ctx_probs.append(prob)
        llm_ctx_reasons.append(reason)
    llm_ctx_probs_arr = np.array(llm_ctx_probs)
    n_llm_recoverable = int(np.sum(llm_ctx_probs_arr >= 0.5))
    print(f"  Context-recoverable (LLM, prob>=0.5): {n_llm_recoverable}/{len(rows)}"
          f" ({n_llm_recoverable/len(rows)*100:.1f}%)")
    print(f"  Mean recovery probability: {llm_ctx_probs_arr.mean():.3f}")

    # ── Failure Mode & Success Pattern Classification ──
    print("Classifying failure modes and success patterns...")
    failure_modes = []
    success_patterns = []
    for i, row in enumerate(rows):
        score = float(is_scores[i])
        if score < 3.0:
            fm = classify_failure_mode(
                ref_text=refs[i], hyp_text=hyps[i],
                wer_pct=row["wer_%"], semantic_sim=float(sem_sims[i]),
                phonetic_sim=float(phon_sims[i]), nea_f1_pct=row["nea_f1_%"],
                length_ratio=float(length_ratios[i]),
            )
            failure_modes.append(fm)
            success_patterns.append("")
        else:
            failure_modes.append("")
            sp = classify_success_pattern(
                wer_pct=row["wer_%"], semantic_sim=float(sem_sims[i]),
                phonetic_sim=float(phon_sims[i]), nea_f1_pct=row["nea_f1_%"],
                length_ratio=float(length_ratios[i]),
            )
            success_patterns.append(sp)

    fm_counts = Counter(fm for fm in failure_modes if fm)
    sp_counts = Counter(sp for sp in success_patterns if sp)
    n_failed_segs = sum(1 for fm in failure_modes if fm)
    n_success_segs = sum(1 for sp in success_patterns if sp)
    print(f"  Failed segments: {n_failed_segs}, Success segments: {n_success_segs}")

    # ── Topic Classification ──
    print("Classifying topics...")
    topics = [classify_topic(r) for r in refs]
    topic_counts = Counter(topics)

    # ── Signal comparison: success vs failure ──
    success_indices = [i for i, sp in enumerate(success_patterns) if sp]
    failure_indices = [i for i, fm in enumerate(failure_modes) if fm]

    def _signal_stats(indices):
        if not indices:
            return {}
        return {
            "semantic_sim": round(float(np.mean([sem_sims[i] for i in indices])), 4),
            "phonetic_sim": round(float(np.mean([phon_sims[i] for i in indices])), 4),
            "wer": round(float(np.mean([rows[i]["wer_%"] for i in indices])), 2),
            "wwer": round(float(np.mean([rows[i]["wwer_%"] for i in indices])), 2),
            "nea_f1": round(float(np.mean([rows[i]["nea_f1_%"] for i in indices])), 2),
            "length_ratio": round(float(np.mean([length_ratios[i] for i in indices])), 4),
        }

    success_signal_stats = _signal_stats(success_indices)
    failure_signal_stats = _signal_stats(failure_indices)

    # ── Write augmented CSV ──
    csv_path = out_dir / "intelligibility_scores.csv"
    print(f"Writing {csv_path}...")
    fieldnames = list(rows[0].keys()) + [
        "semantic_sim", "phonetic_sim", "phonetic_matches",
        "phonetic_near_misses", "length_ratio",
        "intelligibility_score", "intelligibility_tier", "intelligibility_label",
        "niv",
        "context_recoverable", "context_reason",
        "llm_context_prob", "llm_context_reason",
        "failure_mode", "success_pattern",
        "topic", "ref_words",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows):
            row["semantic_sim"] = f"{sem_sims[i]:.4f}"
            row["phonetic_sim"] = f"{phon_sims[i]:.4f}"
            row["phonetic_matches"] = phonetic_results[i]["phonetic_matches"]
            row["phonetic_near_misses"] = phonetic_results[i]["phonetic_near_misses"]
            row["length_ratio"] = f"{length_ratios[i]:.3f}"
            row["intelligibility_score"] = f"{is_scores[i]:.3f}"
            row["intelligibility_tier"] = is_tiers[i]
            row["intelligibility_label"] = is_labels[i]
            row["niv"] = niv_label(float(is_scores[i]))
            row["context_recoverable"] = ctx_recoverable[i]
            row["context_reason"] = ctx_reasons[i]
            row["llm_context_prob"] = f"{llm_ctx_probs[i]:.3f}"
            row["llm_context_reason"] = llm_ctx_reasons[i]
            row["failure_mode"] = failure_modes[i]
            row["success_pattern"] = success_patterns[i]
            row["topic"] = topics[i]
            row["ref_words"] = len(toks(refs[i]))
            writer.writerow(row)

    # ── Compute summary stats ──
    n = len(rows)
    n_empty = sum(1 for h in hyps if not h.strip())
    properly_captured = int(np.sum(is_tiers >= 4))  # Legacy: IS >= 3.0

    # NIV (Net Intelligibility Verdict) counts -- supersede legacy IS >= 3.0
    niv_per_segment = np.array([niv_label(float(s)) for s in is_scores])
    n_niv_y = int(np.sum(niv_per_segment == "Y"))
    n_niv_p = int(np.sum(niv_per_segment == "P"))
    n_niv_n = int(np.sum(niv_per_segment == "N"))
    n_niv_yp = n_niv_y + n_niv_p
    # Backward-compat aliases (used by older container reports)
    niv_useful = n_niv_yp
    niv_clearly_conveyed = n_niv_y

    tier_dist = {}
    for t in [5, 4, 3, 2, 1]:
        count = int(np.sum(is_tiers == t))
        tier_dist[f"{t}_{TIER_LABELS[t].lower()}"] = {
            "count": count,
            "pct": round(count / n * 100, 1),
        }

    # Top phonetic confusions
    top_confusions = [
        {"ref": k[0], "hyp": k[1], "count": v}
        for k, v in all_confusions.most_common(30)
    ]

    summary = {
        "source_csv": str(Path(args.csv).resolve()),
        "n_segments": n,
        "n_empty_hyp": n_empty,
        "mean_is": round(float(is_scores.mean()), 3),
        "median_is": round(float(np.median(is_scores)), 3),
        "std_is": round(float(is_scores.std()), 3),
        "properly_captured_count": properly_captured,
        "properly_captured_pct": round(properly_captured / n * 100, 1),
        "niv_distribution": {
            "Y_clearly_conveyed": {
                "count": n_niv_y,
                "pct": round(n_niv_y / n * 100, 1),
                "threshold": f"IS >= {NIV_Y_THRESHOLD}",
            },
            "P_partial_useful": {
                "count": n_niv_p,
                "pct": round(n_niv_p / n * 100, 1),
                "threshold": f"{NIV_P_THRESHOLD} <= IS < {NIV_Y_THRESHOLD}",
            },
            "N_failed": {
                "count": n_niv_n,
                "pct": round(n_niv_n / n * 100, 1),
                "threshold": f"IS < {NIV_P_THRESHOLD}",
            },
            "Y_pct": round(n_niv_y / n * 100, 1),
            "YP_pct": round(n_niv_yp / n * 100, 1),
        },
        "niv_useful_count": niv_useful,
        "niv_useful_pct": round(niv_useful / n * 100, 1),
        "niv_clearly_conveyed_count": niv_clearly_conveyed,
        "niv_clearly_conveyed_pct": round(niv_clearly_conveyed / n * 100, 1),
        "tier_distribution": tier_dist,
        "signal_stats": {
            "semantic_sim": {
                "mean": round(float(sem_sims.mean()), 4),
                "median": round(float(np.median(sem_sims)), 4),
            },
            "phonetic_sim": {
                "mean": round(float(phon_sims.mean()), 4),
                "median": round(float(np.median(phon_sims)), 4),
            },
            "inv_wer_mean": round(float(np.mean([
                max(0, 1 - r["wer_%"] / 100) for r in rows
            ])), 4),
            "inv_wwer_mean": round(float(np.mean([
                max(0, 1 - r["wwer_%"] / 100) for r in rows
            ])), 4),
            "nea_f1_mean": round(float(np.mean([
                r["nea_f1_%"] for r in rows
            ])), 4),
            "length_ratio": {
                "mean": round(float(length_ratios.mean()), 4),
                "median": round(float(np.median(length_ratios)), 4),
            },
        },
        "context_recoverable_count": n_recoverable,
        "context_recoverable_pct": round(n_recoverable / n * 100, 1),
        "context_recovery_reasons": dict(Counter(ctx_reasons)),
        "llm_context_recoverable_count": n_llm_recoverable,
        "llm_context_recoverable_pct": round(n_llm_recoverable / n * 100, 1),
        "llm_context_mean_prob": round(float(llm_ctx_probs_arr.mean()), 3),
        "llm_context_median_prob": round(float(np.median(llm_ctx_probs_arr)), 3),
        "llm_context_reasons": dict(Counter(llm_ctx_reasons)),
        "wer_thresholds": {
            "almost_certainly_understandable": "WER <= 15%",
            "probably_understandable": "WER 15-30%",
            "coin_flip": "WER 30-50%",
            "probably_not_understandable": "WER 50-70%",
            "almost_certainly_not_understandable": "WER > 70%",
            "guaranteed_not_understandable": "WER > 100%",
        },
        "is_histogram": {
            f"{b:.1f}-{b+0.5:.1f}": int(np.sum((is_scores >= b) & (is_scores < b + 0.5)))
            for b in np.arange(0.0, 5.0, 0.5)
        },
        "failure_mode_distribution": {
            mode: {"count": count, "pct": round(count / max(1, n_failed_segs) * 100, 1)}
            for mode, count in fm_counts.most_common()
        },
        "success_pattern_distribution": {
            pat: {"count": count, "pct": round(count / max(1, n_success_segs) * 100, 1)}
            for pat, count in sp_counts.most_common()
        },
        "signal_comparison": {
            "success": success_signal_stats,
            "failure": failure_signal_stats,
        },
        "topic_analysis": {},
        "length_analysis": {},
        "weights": DEFAULT_WEIGHTS,
        "top_phonetic_confusions": top_confusions,
    }

    # ── Topic analysis ──
    def _group_stats(indices):
        """Compute full stats for a subset of indices."""
        if not indices:
            return {}
        grp_is = [float(is_scores[i]) for i in indices]
        grp_cap = sum(1 for i in indices if float(is_scores[i]) >= 3.0)
        grp_ctx = sum(1 for i in indices if ctx_recoverable[i])
        grp_llm = sum(1 for i in indices if llm_ctx_probs[i] >= 0.5)
        g_n = len(indices)
        return {
            "count": g_n,
            "mean_is": round(np.mean(grp_is), 3),
            "mean_wer": round(float(np.mean([rows[i]["wer_%"] for i in indices])), 1),
            "mean_wwer": round(float(np.mean([rows[i]["wwer_%"] for i in indices])), 1),
            "mean_nea_f1": round(float(np.mean([rows[i]["nea_f1_%"] for i in indices])), 1),
            "mean_phonetic": round(float(np.mean([phon_sims[i] for i in indices])), 3),
            "mean_semantic": round(float(np.mean([sem_sims[i] for i in indices])), 3),
            "captured_count": grp_cap,
            "captured_pct": round(grp_cap / g_n * 100, 1),
            "ctx_rule_count": grp_ctx,
            "ctx_rule_pct": round(grp_ctx / g_n * 100, 1),
            "ctx_llm_count": grp_llm,
            "ctx_llm_pct": round(grp_llm / g_n * 100, 1),
        }

    topic_indices = {}
    for i, t in enumerate(topics):
        topic_indices.setdefault(t, []).append(i)

    for topic, indices in sorted(topic_indices.items(),
                                 key=lambda x: -np.mean([float(is_scores[i]) for i in x[1]])):
        if len(indices) >= 10:
            summary["topic_analysis"][topic] = _group_stats(indices)

    # ── Length-filtered analysis ──
    ref_word_counts = [len(toks(r)) for r in refs]
    length_filters = [
        ("all", lambda i: True),
        ("gte_5_words", lambda i: ref_word_counts[i] >= 5),
        ("gte_7_words", lambda i: ref_word_counts[i] >= 7),
        ("gte_10_words", lambda i: ref_word_counts[i] >= 10),
        ("gte_15_words", lambda i: ref_word_counts[i] >= 15),
        ("gte_20_words", lambda i: ref_word_counts[i] >= 20),
        ("5_to_10_words", lambda i: 5 <= ref_word_counts[i] < 10),
        ("10_to_15_words", lambda i: 10 <= ref_word_counts[i] < 15),
        ("15_to_20_words", lambda i: 15 <= ref_word_counts[i] < 20),
        ("20_plus_words", lambda i: ref_word_counts[i] >= 20),
    ]

    for label, filt_fn in length_filters:
        indices = [i for i in range(n) if filt_fn(i)]
        if len(indices) >= 10:
            summary["length_analysis"][label] = _group_stats(indices)

    # ── Optional: confidence_summary block (only if word_confidence.json present) ──
    word_conf_path = out_dir / "word_confidence.json"
    if word_conf_path.exists():
        try:
            wc = json.loads(word_conf_path.read_text(encoding="utf-8"))
            sent_means = []
            n_high_total = n_med_total = n_low_total = 0
            n_words_total = 0
            for seg in wc.values():
                summ = (seg or {}).get("summary") or {}
                mw = summ.get("mean_word_prob")
                if isinstance(mw, (int, float)):
                    sent_means.append(float(mw))
                n_high_total += int(summ.get("n_high", 0) or 0)
                n_med_total  += int(summ.get("n_med", 0) or 0)
                n_low_total  += int(summ.get("n_low", 0) or 0)
                n_words_total += int(summ.get("n_words", 0) or 0)
            if sent_means:
                arr = np.array(sent_means)
                summary["confidence_summary"] = {
                    "n_segments_with_confidence": len(sent_means),
                    "mean_sentence_conf": round(float(arr.mean()), 3),
                    "median_sentence_conf": round(float(np.median(arr)), 3),
                    "n_high_words_total": n_high_total,
                    "n_med_words_total":  n_med_total,
                    "n_low_words_total":  n_low_total,
                    "n_words_total":      n_words_total,
                    "pct_low_conf_words": (round(n_low_total / n_words_total * 100, 1)
                                            if n_words_total else 0.0),
                    "thresholds": {"high": 0.85, "med": 0.40},
                }
        except Exception as e:
            print(f"[WARN] Could not load {word_conf_path} for confidence_summary: {e}")

    json_path = out_dir / "intelligibility_summary.json"
    print(f"Writing {json_path}...")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # ── Print summary ──
    print()
    print("=" * 60)
    print(f"  INTELLIGIBILITY ASSESSMENT RESULTS")
    print(f"  {n} segments analyzed")
    print("=" * 60)
    print()
    print(f"  Mean IS:   {summary['mean_is']:.2f} / 5.0")
    print(f"  Median IS: {summary['median_is']:.2f} / 5.0")
    print()
    print(f"  NIV Y   (clearly conveyed, IS >= {NIV_Y_THRESHOLD}): {n_niv_y:5d} / {n}"
          f"  ({n_niv_y / n * 100:5.1f}%)")
    print(f"  NIV P   (partial useful):                    {n_niv_p:5d} / {n}"
          f"  ({n_niv_p / n * 100:5.1f}%)")
    print(f"  NIV N   (failed, IS < {NIV_P_THRESHOLD}):                {n_niv_n:5d} / {n}"
          f"  ({n_niv_n / n * 100:5.1f}%)")
    print(f"  NIV Y+P (any useful, IS >= {NIV_P_THRESHOLD}):           {n_niv_yp:5d} / {n}"
          f"  ({n_niv_yp / n * 100:5.1f}%)")
    print(f"  Legacy captured (IS >= 3.0):                 {properly_captured:5d} / {n}"
          f"  ({summary['properly_captured_pct']:5.1f}%)")
    print()
    print("  Tier Distribution:")
    for t in [5, 4, 3, 2, 1]:
        key = f"{t}_{TIER_LABELS[t].lower()}"
        td = tier_dist[key]
        bar = "#" * (td["count"] * 40 // n)
        print(f"    {t} {TIER_LABELS[t]:10s}: {td['count']:5d} ({td['pct']:5.1f}%)  {bar}")
    print()
    print(f"  Empty hypotheses: {n_empty}")
    print()
    print("  Signal Means:")
    print(f"    Semantic similarity: {summary['signal_stats']['semantic_sim']['mean']:.3f}")
    print(f"    Phonetic similarity: {summary['signal_stats']['phonetic_sim']['mean']:.3f}")
    print(f"    Inverse WER:        {summary['signal_stats']['inv_wer_mean']:.3f}")
    print(f"    Inverse WWER:       {summary['signal_stats']['inv_wwer_mean']:.3f}")
    print(f"    NEA F1:             {summary['signal_stats']['nea_f1_mean']:.1f}%")
    print(f"    Length ratio (mean): {summary['signal_stats']['length_ratio']['mean']:.3f}")
    print()

    print(f"  CONTEXT-RECOVERABLE (rule-based):  {n_recoverable} / {n}"
          f"  ({n_recoverable/n*100:.1f}%)")
    print(f"  CONTEXT-RECOVERABLE (LLM-based):   {n_llm_recoverable} / {n}"
          f"  ({n_llm_recoverable/n*100:.1f}%)")
    print(f"    LLM mean recovery probability:   {llm_ctx_probs_arr.mean():.3f}")
    print(f"    LLM median recovery probability: {np.median(llm_ctx_probs_arr):.3f}")
    print()
    print("  LLM Recovery Reason Breakdown:")
    for reason, count in sorted(Counter(llm_ctx_reasons).items(),
                                key=lambda x: -x[1]):
        print(f"    {reason:35s}: {count:5d} ({count/n*100:5.1f}%)")
    print()

    if top_confusions:
        print("  Top 10 Phonetic Confusions (ref -> hyp, count):")
        for c in top_confusions[:10]:
            print(f"    {c['ref']:15s} -> {c['hyp']:15s}  ({c['count']}x)")
    print()

    # WER threshold analysis
    wer_vals = np.array([r["wer_%"] for r in rows])
    print("  WER Threshold Analysis:")
    for thresh, label in [(15, "certainly understandable"),
                          (30, "probably understandable"),
                          (50, "coin flip zone"),
                          (70, "probably NOT understandable"),
                          (100, "certainly NOT understandable")]:
        count = int(np.sum(wer_vals <= thresh))
        print(f"    WER <= {thresh:3d}%: {count:5d} ({count/n*100:5.1f}%)  -- {label}")
    print(f"    WER > 100%: {int(np.sum(wer_vals > 100)):5d}"
          f" ({np.sum(wer_vals > 100)/n*100:5.1f}%)  -- hallucinated")
    print()

    # IS Histogram
    print("  IS HISTOGRAM (score distribution):")
    for b in np.arange(0.0, 5.0, 0.5):
        bucket = f"{b:.1f}-{b+0.5:.1f}"
        count = int(np.sum((is_scores >= b) & (is_scores < b + 0.5)))
        bar = "\u2588" * (count * 40 // n)
        print(f"    IS {bucket}: {count:4d} ({count/n*100:5.1f}%)  {bar}")
    print()

    # Failure mode breakdown
    print(f"  FAILURE MODE ANALYSIS ({n_failed_segs} segments with IS < 3.0):")
    for mode, count in fm_counts.most_common():
        bar = "\u2588" * (count * 30 // max(1, n_failed_segs))
        print(f"    {mode:40s}: {count:4d} ({count/n_failed_segs*100:5.1f}%)  {bar}")
    print()

    # Success pattern breakdown
    print(f"  SUCCESS PATTERN ANALYSIS ({n_success_segs} segments with IS >= 3.0):")
    for pat, count in sp_counts.most_common():
        bar = "\u2588" * (count * 30 // max(1, n_success_segs))
        print(f"    {pat:40s}: {count:4d} ({count/n_success_segs*100:5.1f}%)  {bar}")
    print()

    # Signal comparison
    print("  SIGNAL COMPARISON (Success vs Failure):")
    print(f"    {'Signal':20s} {'Success':>10s} {'Failure':>10s} {'Gap':>10s}")
    for sig_name in ["semantic_sim", "phonetic_sim", "wer", "wwer", "nea_f1", "length_ratio"]:
        sv = success_signal_stats.get(sig_name, 0)
        fv = failure_signal_stats.get(sig_name, 0)
        print(f"    {sig_name:20s} {sv:10.2f} {fv:10.2f} {sv-fv:+10.2f}")
    print()

    # Topic analysis
    print("  TOPIC ANALYSIS:")
    print(f"    {'Topic':25s} {'N':>4s} {'IS':>6s} {'WER':>6s} {'Cap%':>6s} {'CtxR%':>6s} {'CtxL%':>6s}")
    for topic, stats in summary["topic_analysis"].items():
        print(f"    {topic:25s} {stats['count']:4d} {stats['mean_is']:6.2f} "
              f"{stats['mean_wer']:6.1f} {stats['captured_pct']:6.1f} "
              f"{stats['ctx_rule_pct']:6.1f} {stats['ctx_llm_pct']:6.1f}")
    print()

    # Length-filtered analysis
    print("  LENGTH-FILTERED ANALYSIS:")
    print(f"    {'Filter':25s} {'N':>4s} {'IS':>6s} {'WER':>6s} {'Cap%':>6s} {'CtxR%':>6s} {'CtxL%':>6s}")
    for label, stats in summary["length_analysis"].items():
        print(f"    {label:25s} {stats['count']:4d} {stats['mean_is']:6.2f} "
              f"{stats['mean_wer']:6.1f} {stats['captured_pct']:6.1f} "
              f"{stats['ctx_rule_pct']:6.1f} {stats['ctx_llm_pct']:6.1f}")
    print()

    print(f"  Output: {csv_path}")
    print(f"  Summary: {json_path}")


if __name__ == "__main__":
    main()
