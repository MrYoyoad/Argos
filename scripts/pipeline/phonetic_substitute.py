#!/usr/bin/env python3
"""Phonetic substitution — lexicon builder + beam-evidence candidate generator (P1).

Post-hoc correction pipeline for VSP-LLM lip-reading output, anchored on the
``hyp_mbr`` display text (production default since May 2 2026). This module
implements the first two stages:

  build-lexicon   metaphone-bucketed English lexicon from spaCy vocab + on-disk
                  .wrd corpora (+ best-effort LRS3 tar), with a HARD exclusion
                  of client-script-only tokens (asserted, recorded in meta).
  candidates      per-segment flagging of medium-confidence display words and
                  layered candidate generation (L1 beam mass / L2 token-top3 /
                  L3 lexicon neighbors) + span-level candidates + phonetic
                  admission scoring -> candidates.json

The ``apply`` subcommand and the context-plausibility engines are a later
agent's job (P2); they consume candidates.json as specified below.

candidates.json contract (consumed by P2 engines + in-session judging)
=====================================================================
{
  "meta": {
    "run", "method", "fid", "created",
    "constants": <CONSTANTS snapshot>,
    "inputs": {aggregated, nbest, wconf, lexicon},
    "lexicon_meta_hash": md5 of the lexicon file's meta block,
    "context_source": "seg_meta:<path>" | "utt_frame_ranges",
    "tokenizer": "LlamaTokenizerFast" | null (L2 skipped),
    "counts": {...}, "contract_notes": [...]
  },
  "segments": {
    "<utt_id>": {
      "video": str,                # stem (seg_meta) or utt-id base
      "order_key": float,          # t0 seconds (seg_meta) or start frame
      "display_text": str,         # aggregated[utt][method].text verbatim
      "n_words": int,
      "mean_word_prob": float|null,        # from word_confidence_mbr summary
      "segment_gate_passed": bool,         # mean_word_prob >= SEG_MEANPROB_FLOOR
      "context_before": [{"utt","text"}],  # <=2 nearest non-empty, playback order
      "context_after":  [{"utt","text"}],
      "flags": [ {
        "position": int,           # index into split_words(display_text)
        "word", "prob", "agreement", "conf_class", "is_numeric",
        "entity_suspect": bool,    # spaCy PROPN/NER overlap OR out-of-lexicon
        "display_only": bool,      # True => NEVER auto-substituted
        "display_only_reasons": [...],  # subset of {low_prob, numeric,
                                        #   entity_suspect, segment_quality}
        "original_mass": float,    # beam mass voting the anchor word itself
        "gap_mass": float,         # beam mass with no word aligned here
        "candidates": [ {
          "word": str,
          "beam_mass": float,      # sum of softmax(sequence_score) over beams
          "beam_mass_pct": float,  #   voting this word ("share of beam-search
          "n_beams": int,          #   probability mass", NOT P(correct))
          "evidence": [...],       # subset of {beam, token_top3, lexicon}
          "token_top3_p": float,   # (when token_top3 evidence) alt token prob
          "mass_floor": float,     # (pure token_top3) softmax(chosen)*p_alt
          "corpus_freq": int,
          "phon_dist_norm": float, # 0 = visually identical (see ADMISSION)
          "viseme_ok": bool,       # perfect homophene / same-class-only diffs
          "phon_scorer": "viseme_cmu"|"metaphone_fallback"|"none",
          "admissible": bool,      # phon_dist_norm <= PHON_ADMIT_NORM
          "display_only": bool,    # numeric / entity-suspect / no beam evidence
          "display_only_reasons": [...],
          "eligible_for_sub": bool,# precomputed convenience — P2 MUST re-validate
          "score": float           # BEAM_W*beam_mass + PHON_W*(1-phon_dist_norm)
        } ... sorted by score desc ]
      } ... one entry per flagged word, ascending position ],
      "span_flags": [ {
        "positions": [a, b],       # inclusive run of >=2 word-eligible flags
        "anchor_text": str,
        "candidates": [ {"text", "region_mass", "region_mass_pct", "n_beams",
                         "span_viseme_sim", "phon_scorer", "evidence":
                         ["beam_span"], "display_only",
                         "display_only_reasons"} ]  # <=2, mass desc
      } ]
    }
  }
}

Key definitions (canonical — P2 and the judging step rely on these):

FLAGGING. A display word is flagged iff its raw prob (word_confidence_mbr
``prob``) is < FLAG_P_HI (0.95). Green words (p>=0.95 AND agreement>=0.80) are
by construction never flagged. Within flags:
  p <  FLAG_P_LO (0.30)          -> display_only, reason "low_prob"
  is_numeric                     -> display_only, reason "numeric"
  entity-suspect (PROPN/NER on the sentence OR out-of-lexicon)
                                 -> display_only, reason "entity_suspect"
  segment mean_word_prob < SEG_MEANPROB_FLOOR (0.65)
                                 -> display_only, reason "segment_quality"
Only flags with display_only=false are auto-substitution candidates.
Empty-text segments are skipped entirely (not in "segments").

ADMISSION (single canonical definition). phon_dist_norm =
  1 - difflib.SequenceMatcher(None, vis(anchor), vis(candidate)).ratio()
where vis(w) maps the word's FIRST CMU pronunciation (via ``pronouncing``)
through the 11-viseme-class table (docs/nbest_viseme_handoff/snap.py:
P/B/M->p, F/V->f, TH/DH->T, T/D/S/Z/N/L->t, SH/ZH/CH/JH->S, K/G/NG/HH->k,
W/R->w, Y->y, UW/UH/OW/AO/OY->O, AA/AE/AH/AY/AW->A, IY/IH/EY/EH/ER->E).
When either word lacks a CMU pronunciation, the fallback is a viseme-class-
weighted edit distance on doublemetaphone primary codes (same-class
substitution costs VISEME_SUB_COST=0.5 over classes {P,M},{T,N,L,S,0},{K,H},
{X,J}; other subs and indels cost 1.0; normalized by max code length).
A candidate is admissible iff phon_dist_norm <= PHON_ADMIT_NORM (0.5),
i.e. viseme similarity >= 0.5 on the primary scorer. Calibration examples:
  goal->coal 0.0 pass; billion->million 0.0 pass (but numeric -> display-only);
  what->why 0.2 pass; had->hate 0.33 pass; diego->you 0.71 FAIL.
viseme_ok: primary scorer -> viseme strings identical (a perfect visual
homophene; viseme symbols ARE the classes, so any difference is cross-class);
fallback scorer -> alignment contains no indels and every substitution is
same-class.

SUBSTITUTION ELIGIBILITY. eligible_for_sub = flag not display_only AND
candidate not display_only AND admissible AND "beam" in evidence AND
beam_mass >= MIN_BEAM_MASS (0.05). P2's apply MUST re-validate all gates
mechanically (engine output is untrusted) and additionally enforce
MAX_SUBS_PER_SEG (2) — that constant is snapshot here but enforced at apply.

SPAN FLAGS (validation arm). Runs of >=2 consecutive positions that are
word-level eligible (all display_only_reasons, if any, == "segment_quality" —
i.e. eligible ignoring the segment gate). The segment gate would empty the
span validation arm on exactly the weak footage where cross-word
re-segmentation lives, so spans are GENERATED there but their candidates carry
display_only=true with reason "segment_quality" — shipping-safe, measurable.
Per beam, the candidate region is the beam's word slice spanning all its
words aligned into the run; identical region strings are grouped and their
softmax weights summed (region_mass). Kept iff region_mass >= MIN_BEAM_MASS
AND span viseme similarity >= SPAN_SIM_MIN (0.78). Word-level remains the
shipping default (plan: span arm ships only if it clearly wins fixes-vs-breaks).

L2 (token-top3): for each flagged word, the MBR-chosen beam's word-initial
token record's top3 alternates are mapped through the Llama-2 tokenizer;
word-initial (▁) alternates that are lexicon words either corroborate an
existing L1 candidate (evidence += token_top3) or enter as pseudo-floor
candidates with mass_floor = softmax_weight(chosen beam) * p_alt, listed only
when mass_floor >= MASS_FLOOR_DISPLAY (0.01), and NEVER eligible for
substitution (no beam evidence). MASS_FLOOR_DISPLAY is also the recommended
UI cutoff for showing tiny-mass candidates in transcript hovers (T).

L3 (lexicon): metaphone-bucket lookup (primary code + all one-edit code
variants), scored pool capped at the _L3_SCORE_POOL most corpus-frequent
members, admissible-only, top L3_MAX_CANDIDATES (5) by (phon_dist_norm asc,
corpus_freq desc). Always display-only ("no beam evidence").

Percentages are always "share of beam-search probability mass", never
P(correct).

Run with the VSP venv python: /home/ubuntu/vsp-llm-yoad-venv/bin/python
"""
from __future__ import annotations

import argparse
import difflib
import glob as globmod
import hashlib
import importlib.util
import json
import re
import sys
import tarfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ── CONSTANTS (single place; snapshot into candidates.json meta) ─────────────
CONSTANTS = {
    "FLAG_P_LO": 0.30,          # flags below this are display-only ("low_prob")
    "FLAG_P_HI": 0.95,          # words at/above this are never flagged
    "GREEN_AGREE": 0.80,        # joint-green agreement threshold (with p>=FLAG_P_HI)
    "L1_MIN_MASS_LIST": 0.02,   # min beam mass for a word candidate to be listed
    "PHON_ADMIT_NORM": 0.5,     # admission: phon_dist_norm <= this
    "VISEME_SUB_COST": 0.5,     # fallback same-viseme-class substitution cost
    "MIN_BEAM_MASS": 0.05,      # substitution mass gate (words) / span keep gate
    "MAX_SUBS_PER_SEG": 2,      # enforced by P2's apply, snapshot here
    "BEAM_W": 0.7,              # ranking score weight on beam_mass
    "PHON_W": 0.3,              # ranking score weight on (1 - phon_dist_norm)
    "SEG_MEANPROB_FLOOR": 0.65, # segment-quality gate (Salvage floor)
    "SPAN_SIM_MIN": 0.78,       # span viseme-similarity keep gate
    "L3_MAX_CANDIDATES": 5,     # lexicon-neighbor candidates per flag
    "MASS_FLOOR_DISPLAY": 0.01, # min mass_floor to list a pure token_top3 cand
}
# Implementation detail (not part of the specified CONSTANTS contract): cap on
# how many bucket members get viseme-scored per anchor, by corpus freq desc.
_L3_SCORE_POOL = 500

# ── Reused primitives (NOT reimplemented) ────────────────────────────────────
_GEN_CANDIDATES = [
    Path("/home/ubuntu/docs/_research-tools/generators"),
    Path("/workspace/VSP-LLM/scripts"),
]
_LIB_CANDIDATES = [
    Path("/home/ubuntu/lib"),
    Path("/workspace/VSP-LLM/scripts"),
]
_VSP_SCRIPTS_CANDIDATES = [
    Path("/home/ubuntu/VSP-LLM/scripts"),
    Path("/workspace/VSP-LLM/scripts"),
]
for _group in (_GEN_CANDIDATES, _LIB_CANDIDATES):
    _p = next((p for p in _group if p.is_dir()), None)
    if _p is not None and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
_VSP_SCRIPTS = next((p for p in _VSP_SCRIPTS_CANDIDATES if p.is_dir()), None)
if _VSP_SCRIPTS is None:
    sys.exit("phonetic_substitute: cannot locate VSP-LLM/scripts")

from _alignment import align_word_lists, split_words  # noqa: E402
from nbest_aggregate import softmax_scores  # noqa: E402

try:  # canonical special-token filter (private but stable; local fallback below)
    from nbest_aggregate import _is_special_token as _is_special  # noqa: E402
except ImportError:  # pragma: no cover
    _SPECIALS = {"<s>", "</s>", "<unk>", "<pad>"}

    def _is_special(t: str) -> bool:
        return not t or t.lstrip("▁") in _SPECIALS

# compute_word_confidence.py exists BOTH in VSP-LLM/scripts (canonical) and in
# docs/_research-tools/generators (stale prob-only copy). Pin by file path.
_cwc_spec = importlib.util.spec_from_file_location(
    "_cwc_pinned", str(_VSP_SCRIPTS / "compute_word_confidence.py"))
_cwc = importlib.util.module_from_spec(_cwc_spec)
_cwc_spec.loader.exec_module(_cwc)
is_numeric = _cwc.is_numeric

from metaphone import doublemetaphone  # noqa: E402

_SP_MARK = "▁"  # SentencePiece word-start marker

# ── Viseme scoring ────────────────────────────────────────────────────────────
# CMU-phoneme -> 11 viseme classes, verbatim from docs/nbest_viseme_handoff/snap.py
VIS = {**{p: "p" for p in ["P", "B", "M"]}, **{p: "f" for p in ["F", "V"]},
       **{p: "T" for p in ["TH", "DH"]},
       **{p: "t" for p in ["T", "D", "S", "Z", "N", "L"]},
       **{p: "S" for p in ["SH", "ZH", "CH", "JH"]},
       **{p: "k" for p in ["K", "G", "NG", "HH"]},
       "W": "w", "R": "w", "Y": "y",
       **{p: "O" for p in ["UW", "UH", "OW", "AO", "OY"]},
       **{p: "A" for p in ["AA", "AE", "AH", "AY", "AW"]},
       **{p: "E" for p in ["IY", "IH", "EY", "EH", "ER"]}}

_pron = None
_pron_err: Optional[str] = None
_pron_tried = False


def _pronouncing():
    global _pron, _pron_tried, _pron_err
    if not _pron_tried:
        _pron_tried = True
        try:
            import pronouncing as p
            _pron = p
        except Exception as e:  # pragma: no cover
            _pron_err = f"{type(e).__name__}: {e}"
            print(f"[phon] pronouncing unavailable ({_pron_err}) — "
                  "metaphone fallback only", file=sys.stderr)
    return _pron


_STRESS = re.compile(r"\d")
_vis_cache: Dict[str, Optional[str]] = {}


def vis_word(w: str) -> Optional[str]:
    """Viseme-class string of a word via its first CMU pronunciation, or None
    if the word is OOV of cmudict (or pronouncing is unavailable)."""
    v = _vis_cache.get(w)
    if w in _vis_cache:
        return v
    p = _pronouncing()
    v = None
    if p is not None:
        ph = p.phones_for_word(w)
        if ph:
            v = "".join(VIS.get(_STRESS.sub("", s), "?") for s in ph[0].split())
    _vis_cache[w] = v
    return v


def vis_seq(words: Sequence[str]) -> Optional[str]:
    parts = [vis_word(w) for w in words]
    return None if (not parts or any(p is None for p in parts)) else "".join(parts)


# Fallback: viseme-class-weighted edit distance on doublemetaphone codes.
_FALLBACK_CLASSES = [frozenset("PM"), frozenset("TNLS0"),
                     frozenset("KH"), frozenset("XJ")]


def _same_class(a: str, b: str) -> bool:
    return any(a in c and b in c for c in _FALLBACK_CLASSES)


def _weighted_code_dist(ca: str, cb: str) -> Tuple[float, bool]:
    """(normalized weighted edit distance, viseme_ok) between metaphone codes.
    viseme_ok: alignment has no indels and every substitution is same-class."""
    n, m = len(ca), len(cb)
    sub_cost = CONSTANTS["VISEME_SUB_COST"]
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = float(i)
    for j in range(1, m + 1):
        D[0][j] = float(j)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            a, b = ca[i - 1], cb[j - 1]
            sc = 0.0 if a == b else (sub_cost if _same_class(a, b) else 1.0)
            D[i][j] = min(D[i - 1][j - 1] + sc, D[i - 1][j] + 1.0, D[i][j - 1] + 1.0)
    dist = D[n][m] / max(1, n, m)
    ok = True  # traceback, diagonal-first
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            a, b = ca[i - 1], cb[j - 1]
            sc = 0.0 if a == b else (sub_cost if _same_class(a, b) else 1.0)
            if abs(D[i][j] - (D[i - 1][j - 1] + sc)) < 1e-9:
                if a != b and not _same_class(a, b):
                    ok = False
                i, j = i - 1, j - 1
                continue
        if i > 0 and abs(D[i][j] - (D[i - 1][j] + 1.0)) < 1e-9:
            ok = False
            i -= 1
            continue
        ok = False
        j -= 1
    return dist, ok


_phon_cache: Dict[Tuple[str, str], dict] = {}


def phon_score(anchor: str, cand: str) -> dict:
    """Canonical phonetic/viseme scoring + admission (see module docstring)."""
    key = (anchor, cand)
    hit = _phon_cache.get(key)
    if hit is not None:
        return hit
    va, vb = vis_word(anchor), vis_word(cand)
    if va and vb:
        sim = difflib.SequenceMatcher(None, va, vb).ratio()
        out = {"phon_dist_norm": round(1.0 - sim, 4), "viseme_ok": va == vb,
               "phon_scorer": "viseme_cmu"}
    else:
        ca, cb = doublemetaphone(anchor)[0], doublemetaphone(cand)[0]
        if not ca or not cb:
            out = {"phon_dist_norm": 1.0, "viseme_ok": False, "phon_scorer": "none"}
        else:
            d, ok = _weighted_code_dist(ca, cb)
            out = {"phon_dist_norm": round(d, 4), "viseme_ok": ok,
                   "phon_scorer": "metaphone_fallback"}
    out["admissible"] = out["phon_dist_norm"] <= CONSTANTS["PHON_ADMIT_NORM"]
    _phon_cache[key] = out
    return out


_span_cache: Dict[Tuple[str, str], Tuple[float, str]] = {}


def span_phon_sim(anchor_words: Sequence[str], cand_words: Sequence[str]) -> Tuple[float, str]:
    """Viseme-string similarity between word spans (primary), or difflib ratio
    on concatenated metaphone primary codes (fallback when any word is OOV)."""
    key = (" ".join(anchor_words), " ".join(cand_words))
    hit = _span_cache.get(key)
    if hit is not None:
        return hit
    va, vb = vis_seq(anchor_words), vis_seq(cand_words)
    if va and vb:
        out = (difflib.SequenceMatcher(None, va, vb).ratio(), "viseme_cmu")
    else:
        ca = "".join(doublemetaphone(w)[0] for w in anchor_words)
        cb = "".join(doublemetaphone(w)[0] for w in cand_words)
        out = ((difflib.SequenceMatcher(None, ca, cb).ratio(), "metaphone_fallback")
               if ca and cb else (0.0, "none"))
    _span_cache[key] = out
    return out


# ── Token normalization + lexicon ────────────────────────────────────────────
_APOS = re.compile(r"[‘’ʼ′`´]")
_EDGE = re.compile(r"^[^a-z']+|[^a-z']+$")
_TOKEN_OK = re.compile(r"[a-z][a-z']*")


def norm_token(t) -> Optional[str]:
    """Lowercase; unify apostrophes; strip edge punctuation; reject anything
    that is not purely [a-z'] (digit-bearing tokens are rejected, not mangled)."""
    if t is None:
        return None
    s = _APOS.sub("'", str(t).lower().strip())
    s = _EDGE.sub("", s).strip("'")
    return s if s and _TOKEN_OK.fullmatch(s) else None


_SRC_CHAR = {"spacy": "S", "train_wrd": "W", "lrs3_test": "T", "lrs3_tar": "R"}
_NON_CLIENT_SOURCES = frozenset(_SRC_CHAR)
_CONTR_SUFFIXES = ("'s", "n't", "'re", "'ll", "'ve", "'m", "'d")


class Lexicon:
    """Loaded lexicon: membership (contraction-aware), freqs, metaphone buckets."""

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.path = path
        self.meta = data["meta"]
        self.meta_hash = hashlib.md5(
            json.dumps(self.meta, sort_keys=True).encode()).hexdigest()
        self.entries: Dict[str, list] = data["words"]  # word -> [freq, srcs, dm0]
        self.words = set(self.entries)
        self.buckets: Dict[str, List[str]] = defaultdict(list)
        for w, (freq, _srcs, code) in self.entries.items():
            if len(w) >= 2 and code:
                self.buckets[code].append(w)
        for code in self.buckets:
            self.buckets[code].sort(key=lambda w: -self.entries[w][0])
        self.alphabet = sorted({ch for code in self.buckets for ch in code})

    def freq(self, w: str) -> int:
        e = self.entries.get(w)
        return int(e[0]) if e else 0

    def __contains__(self, word: str) -> bool:
        n = norm_token(word)
        if not n:
            return False
        if n in self.words:
            return True
        return any(n.endswith(suf) and n[: -len(suf)] in self.words
                   for suf in _CONTR_SUFFIXES)


def _one_edit_codes(code: str, alphabet: Sequence[str]) -> set:
    out = set()
    for i in range(len(code)):
        out.add(code[:i] + code[i + 1:])                       # deletion
        for ch in alphabet:
            if ch != code[i]:
                out.add(code[:i] + ch + code[i + 1:])          # substitution
    for i in range(len(code) + 1):
        for ch in alphabet:
            out.add(code[:i] + ch + code[i:])                  # insertion
    out.discard(code)
    out.discard("")
    return out


# ── build-lexicon ─────────────────────────────────────────────────────────────

def _read_tar_texts(tar_path: str) -> Tuple[List[str], Optional[str], int]:
    """Best-effort stream of .txt members' 'Text:' lines. Tolerates truncation."""
    texts: List[str] = []
    n_members = 0
    err = None
    try:
        with tarfile.open(tar_path, "r") as tf:
            for m in tf:
                if not (m.isfile() and m.name.endswith(".txt")):
                    continue
                fo = tf.extractfile(m)
                if fo is None:
                    continue
                try:
                    data = fo.read().decode("utf-8", "replace")
                finally:
                    fo.close()
                n_members += 1
                mm = re.search(r"^Text:\s*(.+)$", data, re.MULTILINE)
                if mm:
                    texts.append(mm.group(1))
    except (tarfile.ReadError, EOFError, OSError) as e:
        err = f"{type(e).__name__}: {e} (kept {n_members} members read so far)"
        print(f"[lexicon] tar truncated/unreadable, tolerated: {err}", file=sys.stderr)
    return texts, err, n_members


def cmd_build_lexicon(args: argparse.Namespace) -> None:
    t_start = time.time()
    entries: Dict[str, dict] = {}

    def add(word: str, src: str, freq: int = 1) -> None:
        e = entries.get(word)
        if e is None:
            e = entries[word] = {"freq": 0, "src": set()}
        e["freq"] += freq
        e["src"].add(src)

    sources_meta: Dict[str, dict] = {}

    # 1. spaCy vocab: lowercase, is_alpha, len>=2, has a metaphone code.
    import spacy
    nlp = spacy.load(args.spacy_model)
    n_spacy = 0
    for s in nlp.vocab.strings:
        if not (isinstance(s, str) and s.isascii() and s.isalpha()
                and s.islower() and len(s) >= 2):
            continue
        if not doublemetaphone(s)[0]:
            continue
        add(s, "spacy", freq=0)
        n_spacy += 1
    sources_meta["spacy"] = {"model": args.spacy_model, "words_kept": n_spacy}

    # 2. Corpus .wrd files (frequency counts). Identical files are deduped.
    def add_lines(lines: Sequence[str], src: str) -> Tuple[int, int]:
        n_tok, n_new = 0, 0
        for line in lines:
            for raw in line.split():
                w = norm_token(raw)
                if w is None:
                    continue
                n_tok += 1
                if w not in entries:
                    n_new += 1
                add(w, src)
        return n_tok, n_new

    seen_hashes: Dict[str, str] = {}
    corpus_files: List[Tuple[str, str]] = []
    if Path(args.train_wrd).is_file():
        corpus_files.append((args.train_wrd, "train_wrd"))
    for p in sorted(globmod.glob(args.test_wrd_glob)):
        corpus_files.append((p, "lrs3_test"))
    used, deduped = [], []
    for path, src in corpus_files:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        h = hashlib.md5(text.lower().encode()).hexdigest()
        if h in seen_hashes:
            deduped.append({"path": path, "duplicate_of": seen_hashes[h]})
            continue
        seen_hashes[h] = path
        n_tok, n_new = add_lines(text.splitlines(), src)
        used.append({"path": path, "source": src, "tokens": n_tok, "new_words": n_new})
    sources_meta["wrd_files"] = {"used": used, "deduped_identical": deduped}

    # 3. Best-effort LRS3 tar ('Text:' line of each .txt member).
    if args.lrs3_tar and Path(args.lrs3_tar).is_file():
        texts, err, n_members = _read_tar_texts(args.lrs3_tar)
        n_tok, n_new = add_lines(texts, "lrs3_tar")
        sources_meta["lrs3_tar"] = {"path": args.lrs3_tar, "txt_members": n_members,
                                    "tokens": n_tok, "new_words": n_new,
                                    "truncation_error": err}
    else:
        sources_meta["lrs3_tar"] = {"path": args.lrs3_tar, "skipped": "not found"}

    # 4. HARD EXCLUSION of client-script-only tokens.
    script_tokens: set = set()
    script_paths = []
    for sp in args.scripts:
        with open(sp, encoding="utf-8") as f:
            scr = json.load(f)
        n_before = len(script_tokens)
        for turn in scr.get("turns", []):
            for tok in turn.get("tokens", []):
                w = norm_token(tok)
                if w:
                    script_tokens.add(w)
        script_paths.append({"path": sp, "new_tokens": len(script_tokens) - n_before})

    excluded = sorted(script_tokens - set(entries))
    backed = sorted(script_tokens & set(entries))
    # Assertions: scripts are NEVER a lexicon source; every script-overlapping
    # word must be backed by a non-client source; excluded words must be absent.
    for w, e in entries.items():
        assert e["src"] and e["src"] <= _NON_CLIENT_SOURCES, \
            f"lexicon entry {w!r} has non-corpus source {e['src']}"
    for w in backed:
        assert entries[w]["src"] & _NON_CLIENT_SOURCES, \
            f"script word {w!r} lacks a non-client source"
    assert not (set(excluded) & set(entries)), "script-only token leaked into lexicon"

    meta = {
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "phonetic_substitute.py build-lexicon",
        "n_words": len(entries),
        "sources": sources_meta,
        "source_char_map": _SRC_CHAR,
        "normalization": "lowercase; unicode apostrophes -> '; edge punctuation "
                         "stripped; tokens must match [a-z][a-z']*; spaCy words "
                         "additionally require is_alpha & len>=2 & a metaphone code",
        "client_script_exclusion": {
            "scripts": script_paths,
            "script_tokens_total": len(script_tokens),
            "script_tokens_backed_by_non_client_sources": len(backed),
            "script_only_excluded_count": len(excluded),
            "script_only_excluded": excluded,
            "guarantee": "no token unique to the client scripts is a lexicon "
                         "entry; scripts are never a lexicon source (asserted)",
        },
    }
    words_out = {
        w: [e["freq"], "".join(sorted(_SRC_CHAR[s] for s in e["src"])),
            doublemetaphone(w)[0]]
        for w, e in sorted(entries.items())
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump({"meta": meta, "words": words_out}, f, ensure_ascii=False)
    meta_hash = hashlib.md5(json.dumps(meta, sort_keys=True).encode()).hexdigest()
    print(f"[lexicon] wrote {out} — {len(entries)} words in "
          f"{time.time() - t_start:.1f}s (meta md5 {meta_hash})")
    print(f"  spacy={n_spacy}  script_tokens={len(script_tokens)} "
          f"(backed={len(backed)}, excluded_script_only={len(excluded)})")
    print(f"  excluded sample: {excluded[:15]}")


# ── candidates ────────────────────────────────────────────────────────────────

def _group_tokens_to_words(tokens: Sequence[dict]) -> List[Tuple[str, List[dict]]]:
    """Group per-token records into words, mirroring nbest_aggregate.
    words_with_conf (special-token flush, ▁ word starts, empty filter)."""
    groups: List[List[dict]] = []
    cur: List[dict] = []
    for rec in tokens:
        tstr = rec.get("token") or ""
        if not tstr:
            continue
        if _is_special(tstr):
            if cur:
                groups.append(cur)
                cur = []
            continue
        if tstr.startswith(_SP_MARK) and cur:
            groups.append(cur)
            cur = []
        cur.append(rec)
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        word = "".join((r.get("token") or "").lstrip(_SP_MARK) for r in g)
        if word.strip():
            out.append((word, g))
    return out


def _parse_utt_order(utt: str) -> Tuple[str, float]:
    """Fallback context ordering from the utt id: '<base>_<seg>_<f0>_<f1>' ->
    (base video, start frame). Works for both egla and the 1497 naming."""
    parts = utt.split("_")
    if len(parts) >= 4 and parts[-1].isdigit() and parts[-2].isdigit() \
            and parts[-3].isdigit():
        return "_".join(parts[:-3]), float(int(parts[-2]))
    return utt, 0.0


def _word_char_spans(text: str) -> List[Tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]


def _suspect_positions(text: str, doc) -> List[bool]:
    """Per display word: True if any overlapping spaCy token is PROPN or any
    named-entity span overlaps the word."""
    spans = _word_char_spans(text)
    sus = [False] * len(spans)

    def mark(cs: int, ce: int) -> None:
        for k, (s, e) in enumerate(spans):
            if not (ce <= s or cs >= e):
                sus[k] = True

    for t in doc:
        if t.pos_ == "PROPN":
            mark(t.idx, t.idx + len(t.text))
    for ent in doc.ents:
        mark(ent.start_char, ent.end_char)
    return sus


def cmd_candidates(args: argparse.Namespace) -> None:
    C = CONSTANTS
    t_start = time.time()
    lex = Lexicon(args.lexicon)
    print(f"[candidates] lexicon: {len(lex.words)} words, "
          f"{len(lex.buckets)} buckets (meta md5 {lex.meta_hash})")

    with open(args.aggregated, encoding="utf-8") as f:
        aggregated = json.load(f)
    with open(args.wconf, encoding="utf-8") as f:
        wconf = json.load(f)
    print(f"[candidates] loading nbest {args.nbest} ...")
    with open(args.nbest, encoding="utf-8") as f:
        nbest = json.load(f)

    fid = args.fid
    if not fid:
        m = re.search(r"nbest-([A-Za-z0-9]+)\.json$", Path(args.nbest).name)
        fid = m.group(1) if m else "unknown"

    # Context ordering: seg_meta (t0) or utt-id frame ranges.
    seg_meta = None
    if args.context and args.context != "auto":
        with open(args.context, encoding="utf-8") as f:
            seg_meta = json.load(f)
        context_source = f"seg_meta:{args.context}"
    else:
        context_source = "utt_frame_ranges"

    method = args.method
    texts: Dict[str, str] = {}
    video_of: Dict[str, str] = {}
    order_of: Dict[str, float] = {}
    for utt, agg in aggregated.items():
        texts[utt] = ((agg.get(method) or {}).get("text") or "")
        if seg_meta is not None and utt in seg_meta:
            sm = seg_meta[utt]
            video_of[utt] = sm.get("stem") or _parse_utt_order(utt)[0]
            order_of[utt] = float(sm.get("t0") or 0.0)
        else:
            video_of[utt], order_of[utt] = _parse_utt_order(utt)

    by_video: Dict[str, List[str]] = defaultdict(list)
    for utt in aggregated:
        by_video[video_of[utt]].append(utt)
    for vid in by_video:
        by_video[vid].sort(key=lambda u: (order_of[u], u))
    context: Dict[str, Tuple[List[dict], List[dict]]] = {}
    for vid, utts in by_video.items():
        for k, utt in enumerate(utts):
            before: List[dict] = []
            for u2 in reversed(utts[:k]):
                if texts[u2].strip():
                    before.append({"utt": u2, "text": texts[u2]})
                    if len(before) == 2:
                        break
            before.reverse()
            after: List[dict] = []
            for u2 in utts[k + 1:]:
                if texts[u2].strip():
                    after.append({"utt": u2, "text": texts[u2]})
                    if len(after) == 2:
                        break
            context[utt] = (before, after)

    # spaCy NER/PROPN pass over all display texts.
    import spacy
    nlp = spacy.load(args.spacy_model, disable=["parser", "lemmatizer"])
    utt_order = list(aggregated.keys())
    suspects: Dict[str, List[bool]] = {}
    for utt, doc in zip(utt_order,
                        nlp.pipe([texts[u] for u in utt_order], batch_size=64)):
        suspects[utt] = _suspect_positions(texts[utt], doc)

    # Tokenizer for L2 (tokenizer only, no weights). Graceful skip on failure.
    tok = None
    tok_name = None
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.tokenizer_dir)
        tok_name = type(tok).__name__
        print(f"[candidates] L2 tokenizer: {tok_name} from {args.tokenizer_dir}")
    except Exception as e:
        print(f"[candidates] L2 tokenizer load FAILED ({type(e).__name__}: {e}) "
              "— skipping token-top3 layer", file=sys.stderr)
    _tok_cache: Dict[int, Optional[str]] = {}

    def alt_word(alt_id: int) -> Optional[str]:
        """Word-initial single-token alternate -> normalized word, else None."""
        if alt_id in _tok_cache:
            return _tok_cache[alt_id]
        w = None
        try:
            tstr = tok.convert_ids_to_tokens(int(alt_id))
            if isinstance(tstr, str) and tstr.startswith(_SP_MARK):
                n = norm_token(tstr[len(_SP_MARK):])
                if n and n in lex.words:
                    w = n
        except Exception:
            w = None
        _tok_cache[alt_id] = w
        return w

    # L3 cache: anchor word -> top-5 admissible lexicon neighbors.
    _l3_cache: Dict[str, List[str]] = {}

    def l3_neighbors(anchor_l: str) -> List[str]:
        hit = _l3_cache.get(anchor_l)
        if hit is not None:
            return hit
        code = doublemetaphone(anchor_l)[0]
        out: List[str] = []
        if code:
            pool: List[str] = []
            seen = set()
            for c in [code, *_one_edit_codes(code, lex.alphabet)]:
                for w in lex.buckets.get(c, ()):
                    if w != anchor_l and w not in seen:
                        seen.add(w)
                        pool.append(w)
            pool.sort(key=lambda w: -lex.freq(w))
            scored = []
            for w in pool[:_L3_SCORE_POOL]:
                ph = phon_score(anchor_l, w)
                if ph["admissible"]:
                    scored.append((ph["phon_dist_norm"], -lex.freq(w), w))
            scored.sort()
            out = [w for _, _, w in scored[:C["L3_MAX_CANDIDATES"]]]
        _l3_cache[anchor_l] = out
        return out

    counts: Counter = Counter()
    reason_counts: Counter = Counter()
    cand_reason_counts: Counter = Counter()
    evidence_counts: Counter = Counter()
    mass_dev_max = 0.0
    segments_out: Dict[str, dict] = {}

    for utt in utt_order:
        counts["segments_total"] += 1
        text = texts[utt]
        words = split_words(text)
        if not words:
            counts["segments_skipped_empty"] += 1
            continue
        wrec = wconf.get(utt) or {}
        wwords = wrec.get("words") or []
        aligned_wconf = (
            len(wwords) == len(words)
            and all((ww.get("word") or "").strip().lower() == w.strip().lower()
                    for ww, w in zip(wwords, words))
        )
        if not aligned_wconf:
            counts["segments_wconf_misaligned"] += 1
        mean_prob = (wrec.get("summary") or {}).get("mean_word_prob")
        seg_gate_passed = mean_prob is not None and mean_prob >= C["SEG_MEANPROB_FLOOR"]
        if seg_gate_passed:
            counts["segments_gate_passed"] += 1

        # ── L1: align all beams to the display words, accumulate vote mass ──
        hyps = (nbest.get(utt) or {}).get("hypotheses") or []
        n_pos = len(words)
        votes: List[Dict[str, float]] = [defaultdict(float) for _ in range(n_pos)]
        vote_beams: List[Counter] = [Counter() for _ in range(n_pos)]
        gap_mass = [0.0] * n_pos
        weights: List[float] = []
        beam_words_all: List[List[str]] = []
        beam_pairs_all: List[List[Tuple[int, int]]] = []
        chosen_idx = None
        if hyps:
            weights = softmax_scores([h.get("sequence_score") for h in hyps])
            rank_chosen = (aggregated[utt].get(method) or {}).get("rank_chosen", -1)
            for bi, h in enumerate(hyps):
                if h.get("rank") == rank_chosen:
                    chosen_idx = bi
                bw = split_words(h.get("text") or "")
                pairs = align_word_lists(words, bw)
                beam_words_all.append(bw)
                beam_pairs_all.append(pairs)
                wt = weights[bi]
                for i, j in pairs:
                    if i < 0:
                        continue  # beam-side insertion: belongs to no display slot
                    if j >= 0:
                        wl = bw[j].strip().lower()
                        votes[i][wl] += wt
                        vote_beams[i][wl] += 1
                    else:
                        gap_mass[i] += wt
            # Mass conservation: per position, votes + gap == 1.0 (softmax total).
            for i in range(n_pos):
                total = sum(votes[i].values()) + gap_mass[i]
                dev = abs(total - 1.0)
                mass_dev_max = max(mass_dev_max, dev)
                counts["mass_positions_checked"] += 1
                assert dev <= 1e-6, (
                    f"mass conservation violated at {utt} pos {i}: total={total!r}")
        else:
            counts["segments_missing_from_nbest"] += 1

        # ── L2 word-group prep on the chosen beam ──
        l2_groups: Optional[List[Tuple[str, List[dict]]]] = None
        if tok is not None and chosen_idx is not None:
            pairs_wg = _group_tokens_to_words(hyps[chosen_idx].get("tokens") or [])
            if (len(pairs_wg) == len(words)
                    and all(gw.strip().lower() == w.strip().lower()
                            for (gw, _), w in zip(pairs_wg, words))):
                l2_groups = pairs_wg
            else:
                counts["segments_l2_group_mismatch"] += 1

        # ── Flags ──
        flags: List[dict] = []
        word_eligible = [False] * n_pos  # eligible ignoring the segment gate
        for i, w in enumerate(words):
            ww = wwords[i] if aligned_wconf else {}
            p = ww.get("prob")
            if p is None:
                counts["words_prob_unknown"] += 1
                continue
            if p >= C["FLAG_P_HI"]:
                continue  # green or high-prob non-green: never flagged
            counts["flags_total"] += 1
            if p >= C["FLAG_P_LO"]:
                counts["flags_in_band"] += 1
            anchor_l = w.strip().lower()
            num = bool(ww.get("is_numeric"))
            ent = bool(suspects.get(utt, [False] * n_pos)[i]) or (w not in lex)
            reasons: List[str] = []
            if p < C["FLAG_P_LO"]:
                reasons.append("low_prob")
            if num:
                reasons.append("numeric")
            if ent:
                reasons.append("entity_suspect")
            if not seg_gate_passed:
                reasons.append("segment_quality")
            for r in reasons:
                reason_counts[r] += 1
            display_only = bool(reasons)
            if not display_only:
                counts["flags_eligible"] += 1
            word_eligible[i] = all(r == "segment_quality" for r in reasons)

            # Candidate assembly (dedup across layers by word).
            cands: Dict[str, dict] = {}

            def get_cand(word_l: str) -> dict:
                c = cands.get(word_l)
                if c is None:
                    ph = phon_score(anchor_l, word_l)
                    c = cands[word_l] = {
                        "word": word_l,
                        "beam_mass": 0.0, "beam_mass_pct": 0.0, "n_beams": 0,
                        "evidence": [],
                        "corpus_freq": lex.freq(word_l),
                        "phon_dist_norm": ph["phon_dist_norm"],
                        "viseme_ok": ph["viseme_ok"],
                        "phon_scorer": ph["phon_scorer"],
                        "admissible": ph["admissible"],
                    }
                return c

            # L1 beams
            for word_l, mass in votes[i].items():
                if word_l == anchor_l or mass < C["L1_MIN_MASS_LIST"]:
                    continue
                c = get_cand(word_l)
                c["beam_mass"] = mass
                c["beam_mass_pct"] = round(100.0 * mass, 1)
                c["n_beams"] = int(vote_beams[i][word_l])
                c["evidence"].append("beam")

            # L2 token-top3 (word-initial single-token alternates in lexicon)
            if l2_groups is not None:
                rec0 = l2_groups[i][1][0]
                w_chosen = weights[chosen_idx] if chosen_idx is not None else 0.0
                for alt in (rec0.get("top3") or []):
                    if alt.get("id") == rec0.get("token_id"):
                        continue
                    wa = alt_word(alt.get("id"))
                    if not wa or wa == anchor_l:
                        continue
                    p_alt = float(alt.get("p") or 0.0)
                    if wa in cands and "beam" in cands[wa]["evidence"]:
                        c = cands[wa]
                        if "token_top3" not in c["evidence"]:
                            c["evidence"].append("token_top3")
                        c["token_top3_p"] = round(p_alt, 4)
                        counts["l2_corroborations"] += 1
                    else:
                        floor = w_chosen * p_alt
                        if floor >= C["MASS_FLOOR_DISPLAY"]:
                            c = get_cand(wa)
                            if "token_top3" not in c["evidence"]:
                                c["evidence"].append("token_top3")
                            c["token_top3_p"] = round(p_alt, 4)
                            c["mass_floor"] = round(floor, 4)
                            counts["l2_pseudo_candidates"] += 1

            # L3 lexicon neighbors (display-only)
            for wn in l3_neighbors(anchor_l):
                c = get_cand(wn)
                if "lexicon" not in c["evidence"]:
                    c["evidence"].append("lexicon")

            # Finalize candidates
            cand_list: List[dict] = []
            for word_l, c in cands.items():
                c_reasons: List[str] = []
                if is_numeric(word_l):
                    c_reasons.append("numeric")
                if word_l not in lex:
                    c_reasons.append("entity_suspect")
                if "beam" not in c["evidence"]:
                    c_reasons.append("no_beam_evidence")
                for r in c_reasons:
                    cand_reason_counts[r] += 1
                c["display_only"] = bool(c_reasons)
                c["display_only_reasons"] = c_reasons
                c["eligible_for_sub"] = (
                    not display_only and not c["display_only"] and c["admissible"]
                    and c["beam_mass"] >= C["MIN_BEAM_MASS"])
                c["score"] = round(C["BEAM_W"] * c["beam_mass"]
                                   + C["PHON_W"] * (1.0 - c["phon_dist_norm"]), 4)
                c["beam_mass"] = round(c["beam_mass"], 6)
                evidence_counts["+".join(sorted(c["evidence"]))] += 1
                counts["candidates_total"] += 1
                if c["admissible"]:
                    counts["candidates_admissible"] += 1
                cand_list.append(c)
            cand_list.sort(key=lambda c: (-c["score"], c["word"]))
            if any(c["admissible"] and "beam" in c["evidence"] for c in cand_list):
                counts["flags_with_admissible_beam_candidate"] += 1
            if any(c["eligible_for_sub"] for c in cand_list):
                counts["flags_with_substitutable_candidate"] += 1

            flags.append({
                "position": i,
                "word": w,
                "prob": p,
                "agreement": ww.get("agreement"),
                "conf_class": ww.get("conf_class"),
                "is_numeric": num,
                "entity_suspect": ent,
                "display_only": display_only,
                "display_only_reasons": reasons,
                "original_mass": round(votes[i].get(anchor_l, 0.0), 6),
                "gap_mass": round(gap_mass[i], 6),
                "candidates": cand_list,
            })

        # ── Span flags: runs of >=2 word-eligible positions ──
        span_flags: List[dict] = []
        if hyps:
            i = 0
            while i < n_pos:
                if not word_eligible[i]:
                    i += 1
                    continue
                j = i
                while j + 1 < n_pos and word_eligible[j + 1]:
                    j += 1
                if j > i:  # run length >= 2
                    anchor_words = [words[k].strip().lower() for k in range(i, j + 1)]
                    anchor_text = " ".join(anchor_words)
                    regions: Dict[str, dict] = {}
                    for bi in range(len(hyps)):
                        J = [jj for (ii, jj) in beam_pairs_all[bi]
                             if i <= ii <= j and jj >= 0]
                        if not J:
                            continue
                        seg_words = beam_words_all[bi][min(J):max(J) + 1]
                        rtext = " ".join(x.strip().lower() for x in seg_words)
                        r = regions.setdefault(rtext, {"mass": 0.0, "n_beams": 0})
                        r["mass"] += weights[bi]
                        r["n_beams"] += 1
                    span_cands: List[dict] = []
                    for rtext, r in regions.items():
                        if not rtext or rtext == anchor_text:
                            continue
                        if r["mass"] < C["MIN_BEAM_MASS"]:
                            continue
                        sim, scorer = span_phon_sim(anchor_words, rtext.split())
                        if sim < C["SPAN_SIM_MIN"]:
                            continue
                        anchor_set = set(anchor_words)
                        introduced = [x for x in rtext.split() if x not in anchor_set]
                        s_reasons: List[str] = []
                        if not seg_gate_passed:
                            s_reasons.append("segment_quality")
                        if any(is_numeric(x) for x in introduced):
                            s_reasons.append("numeric_introduction")
                        if any(x not in lex for x in introduced):
                            s_reasons.append("entity_suspect")
                        span_cands.append({
                            "text": rtext,
                            "region_mass": round(r["mass"], 6),
                            "region_mass_pct": round(100.0 * r["mass"], 1),
                            "n_beams": r["n_beams"],
                            "span_viseme_sim": round(sim, 4),
                            "phon_scorer": scorer,
                            "evidence": ["beam_span"],
                            "display_only": bool(s_reasons),
                            "display_only_reasons": s_reasons,
                        })
                    span_cands.sort(key=lambda c: (-c["region_mass"],
                                                   -c["span_viseme_sim"]))
                    span_cands = span_cands[:2]
                    if span_cands:
                        counts["span_flags_total"] += 1
                        counts["span_candidates_total"] += len(span_cands)
                        counts["span_candidates_display_only"] += sum(
                            1 for c in span_cands if c["display_only"])
                        span_flags.append({
                            "positions": [i, j],
                            "anchor_text": anchor_text,
                            "candidates": span_cands,
                        })
                i = j + 1

        before, after = context.get(utt, ([], []))
        segments_out[utt] = {
            "video": video_of[utt],
            "order_key": order_of[utt],
            "display_text": text,
            "n_words": n_pos,
            "mean_word_prob": mean_prob,
            "segment_gate_passed": seg_gate_passed,
            "context_before": before,
            "context_after": after,
            "flags": flags,
            "span_flags": span_flags,
        }
        counts["segments_included"] += 1

    del nbest  # free the big blob before serialization

    meta = {
        "run": args.run_name or Path(args.out).parent.name,
        "method": method,
        "fid": fid,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "constants": CONSTANTS,
        "inputs": {"aggregated": args.aggregated, "nbest": args.nbest,
                   "wconf": args.wconf, "lexicon": args.lexicon},
        "lexicon_meta_hash": lex.meta_hash,
        "context_source": context_source,
        "tokenizer": tok_name,
        "counts": {
            **{k: counts[k] for k in sorted(counts)},
            "flag_display_only_reasons": dict(reason_counts),
            "candidate_display_only_reasons": dict(cand_reason_counts),
            "candidates_by_evidence": dict(evidence_counts),
            "mass_conservation_max_abs_dev": mass_dev_max,
        },
        "contract_notes": [
            "flags[].position indexes split_words(display_text) (whitespace split)",
            "beam_mass/percentages are share of beam-search probability mass, "
            "never P(correct)",
            "admission: phon_dist_norm <= PHON_ADMIT_NORM on the CMU-viseme "
            "scorer (metaphone class-weighted fallback for OOV) — see module "
            "docstring for the canonical definition",
            "eligible_for_sub is a convenience precomputation; P2 apply MUST "
            "re-validate every gate and enforce MAX_SUBS_PER_SEG",
            "span runs ignore the segment gate for RUN SELECTION; their "
            "candidates inherit display_only (reason segment_quality) so the "
            "validation arm has data on weak footage without shipping risk",
            "pure token_top3 candidates are listed only when mass_floor >= "
            "MASS_FLOOR_DISPLAY and are never substitutable (no beam evidence)",
            f"L3 scoring pool capped at the {_L3_SCORE_POOL} most corpus-"
            "frequent bucket members per anchor",
            "segments with empty display text are skipped; all other segments "
            "are present (flags may be []) so engines can rebuild full "
            "per-video transcripts from (video, order_key, display_text)",
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump({"meta": meta, "segments": segments_out}, f,
                  indent=1, ensure_ascii=False)
    print(f"[candidates] wrote {out} in {time.time() - t_start:.1f}s")
    print(f"  segments: total={counts['segments_total']} "
          f"included={counts['segments_included']} "
          f"empty={counts['segments_skipped_empty']} "
          f"gate_passed={counts['segments_gate_passed']} "
          f"no_nbest={counts['segments_missing_from_nbest']}")
    print(f"  flags: total={counts['flags_total']} "
          f"in_band={counts['flags_in_band']} "
          f"eligible={counts['flags_eligible']} "
          f"w_admissible_beam_cand={counts['flags_with_admissible_beam_candidate']} "
          f"w_substitutable={counts['flags_with_substitutable_candidate']}")
    print(f"  spans: flags={counts['span_flags_total']} "
          f"cands={counts['span_candidates_total']}")
    print(f"  mass conservation: {counts['mass_positions_checked']} positions, "
          f"max |dev| = {mass_dev_max:.2e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Phonetic substitution (P1): lexicon builder + "
                    "beam-evidence candidate generator",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    bl = sub.add_parser("build-lexicon",
                        help="build metaphone-bucketed lexicon.json")
    bl.add_argument("--out", required=True)
    bl.add_argument("--spacy-model", default="en_core_web_sm")
    bl.add_argument("--train-wrd", default="/home/ubuntu/finetune_data/train.wrd")
    bl.add_argument("--test-wrd-glob", default="/tmp/lrs3_decode/dataset*/test.wrd")
    bl.add_argument("--lrs3-tar", default="/home/ubuntu/datasets/lrs3orig_sync.tar")
    bl.add_argument("--scripts", nargs="*", default=[
        "/home/ubuntu/datasets/clients/egla_kafe/work/eval/script_scene1.json",
        "/home/ubuntu/datasets/clients/egla_kafe/work/eval/script_scene2.json",
    ], help="client scripts whose unique tokens are HARD-excluded")
    bl.set_defaults(func=cmd_build_lexicon)

    ca = sub.add_parser("candidates",
                        help="flag words + generate candidates.json")
    ca.add_argument("--aggregated", required=True)
    ca.add_argument("--nbest", required=True)
    ca.add_argument("--wconf", required=True,
                    help="word_confidence_mbr.json (anchored on --method text)")
    ca.add_argument("--method", default="hyp_mbr")
    ca.add_argument("--lexicon", required=True)
    ca.add_argument("--out", required=True)
    ca.add_argument("--context", default="auto",
                    help="'auto' (order by utt-id frame ranges) or a "
                         "seg_meta.json path (order by t0)")
    ca.add_argument("--run-name", default=None)
    ca.add_argument("--fid", default=None)
    ca.add_argument("--spacy-model", default="en_core_web_sm")
    ca.add_argument("--tokenizer-dir",
                    default="/home/ubuntu/VSP-LLM/checkpoints/Llama-2-7b-hf")
    ca.set_defaults(func=cmd_candidates)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
