#!/usr/bin/env python3
"""P3 — phonetic-substitution validation vs references (egla scene12+shaam, 1497).

Grades every substitution arm against the utt-aligned references, MBR-anchored:
the hypothesis side is ALWAYS `text_original` / `text_substituted` from the
substitution artifacts (hyp_mbr display text), never the top-1 hypo files; the
reference side is `run_*/hypo-corrected.json` (egla) / `hypo-172610.json`
(1497, parallel arrays). Produces the numbers behind
docs/evaluation/egla_kafe/phonetic_substitution_eval.md and the GO/NO-GO call.

Per (dataset, arm):
  - word-level classification of each applied substitution against the ref
    word aligned to its position (align on the ORIGINAL text; positions are
    identical in the substituted text since word subs are 1:1):
      fixed              orig != aligned-ref-word AND chosen == aligned-ref-word
      broke              orig == aligned-ref-word (chosen necessarily differs)
      neutral_both_wrong everything else (incl. position aligned to a ref gap)
  - dWER  : segment WER = editdistance(toks(hyp), toks(ref)) / len(toks(ref))
            (make_report.py convention, macro mean over segments with a ref);
            reported overall (all segments) and on touched segments only.
  - dIS   : canonical IS (make_report --compute-is recipe: MiniLM semantic sim,
            metaphone phonetic sim, WER, WWER, NEA-F1, length ratio ->
            compute_is) recomputed for original AND substituted text of
            TOUCHED segments only. Overall dIS = sum(touched deltas) / N_all —
            EXACT, not approximate, because untouched segments contribute a
            delta of exactly 0. Absolute whole-set IS levels are not
            recomputed (and would be top-1-vs-MBR shifted vs report.csv
            anyway; deltas are what the arms table needs).
  - content-word recall: the nbest_viseme_handoff metric mirrored verbatim
    from docs/nbest_viseme_handoff/snap.py (wl tokenizer, STOP list,
    content = not-stop AND (len>=3 or digit), hit = exact in hyp word set OR
    difflib ratio >= 0.87 vs any hyp word; per-segment recall averaged over
    segments with >=1 ref content word). NOTE the oracle row in
    snap_results.json is a threshold-binarized Y+P *proxy* on OCR turns —
    same hit machinery, different unit; comparable in spirit only.
  - safety audit for the GO gate: numeric introductions (module is_numeric on
    chosen where original was not numeric) and entity introductions (spaCy
    PROPN/NER status of the chosen token in the substituted sentence where the
    original token had no such status) — independent recheck, not a readback
    of the apply pipeline's own gates. Sub rate = subs / total display words.

Arms (generated ones go under <root>/eval_arms/ and run through the REAL
`phonetic_substitute.py apply` gate code — synthetic decisions files exercise
flag/candidate/segment gates + MAX_SUBS_PER_SEG exactly like engine output):
  noop            baseline row (zeros by construction)
  naive_max_mass  synthetic decisions: replace EVERY judgeable flag with its
                  highest-beam_mass eligible candidate -> real apply
  claude_only     engine (a) alone (egla: on-disk; 1497: generated — Claude
                  judged a 300-flag stratified sample only)
  llama_only      engine (b) alone (on-disk, full)
  ship_agree      SHIP ARM: claude+llama --agree-mode all (on-disk; on 1497
                  agreement is computable only within Claude's sample)
  span_gated      span-level mechanical arm: top span candidate with
                  display_only == false (segment gate respected), textual
                  application (spans are not in the apply pipeline), capped at
                  MAX_SUBS_PER_SEG spans/segment, scored span-level (fixed =
                  substituted span strictly closer to the aligned ref span by
                  word edit distance) AND text-level
  span_ungated    same but ignoring ONLY the segment-quality gate (reasons
                  subset of {segment_quality}; numeric/entity span reasons are
                  never ignored) — spans were exempted from run-selection per
                  the P1 contract, so this shows what the arm would do on the
                  weak footage it was generated-but-gated on
  l4_liberal      1497 only: on-disk substitutions_l4_liberal.json
                  (overlap-eligible candidates, llama_l4 decisions)
  margin sweep    llama margin_nats re-thresholded from the recorded
                  delta_nats (decisions carry delta_nats + best_candidate for
                  every judged flag) -> synthetic decisions -> real apply,
                  at MARGIN_SWEEP nats
Engine (c) `heuristic` emitted 0 replaces on all three runs (mass-dominance +
viseme_ok + POS never co-fire) — reported as a line, not an arm.

Engine agreement (Claude sample keys x Llama): raw agreement, Cohen's kappa,
both-replace chosen-word match, and — the payoff — who validation says was
right on each disagreement (replacer's chosen vs keeper's original vs the
aligned ref word).

Splits: egla is reported per run (scene12 / shaam; shaam additionally split
img_* vs shaam_* on fixed/broke where subs exist). 1497: NIV tier from
report.csv is_score (top-1-anchored difficulty stratifier; Y>=3.80, P>=2.00)
and MBR mean_word_prob bands from candidates.json.

Outputs: <root>/eval_results.json per dataset + a combined markdown dump to
stdout. Deterministic given the on-disk artifacts (IS: fp32 GPU/CPU encoder —
deltas stable to ~1e-3).

Run: /home/ubuntu/vsp-llm-yoad-venv/bin/python \
       scripts/pipeline/egla_kafe_substitution_eval.py [--datasets ...]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import editdistance

# ── Reused primitives (NOT reimplemented) ────────────────────────────────────
_GEN = Path("/home/ubuntu/docs/_research-tools/generators")
_VSP_SCRIPTS = Path("/home/ubuntu/VSP-LLM/scripts")
sys.path.insert(0, str(_GEN))
sys.path.insert(0, str(_VSP_SCRIPTS))

from _alignment import align_word_lists, split_words  # noqa: E402

VENV_PY = "/home/ubuntu/vsp-llm-yoad-venv/bin/python"
PHON_SUB = "/home/ubuntu/scripts/pipeline/phonetic_substitute.py"
MARGIN_SWEEP = [1.0, 2.0, 3.0, 4.0, 6.0]  # nats; 2.0 = shipped calibration

DATASETS: Dict[str, dict] = {
    "scene12": {
        "root": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/substitution/scene12",
        "refs": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_scene12_all/hypo-corrected.json",
        "report_csv": None,
    },
    "shaam": {
        "root": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/substitution/shaam",
        "refs": "/home/ubuntu/datasets/clients/egla_kafe/work/eval/run_shaam_all/hypo-corrected.json",
        "report_csv": None,
    },
    "english_1497": {
        "root": "/home/ubuntu/english_full_nbest_eval/substitution",
        "refs": "/home/ubuntu/english_full_nbest_eval/decode_output/hypo-172610.json",
        "report_csv": "/home/ubuntu/english_full_nbest_eval/report/report.csv",
    },
}

# ── handoff content-recall metric, mirrored from docs/nbest_viseme_handoff/snap.py
STOP = set(
    """a an the and or but if so to of in on at for with from by is are was were be been am
i you he she it we they that this these those there here what who how when where why will would
can could should shall may might must do does did done have has had not no yes oh uh um my your
his her its our their me him them us as its it's don't didn't isn't aren't i'm you're he's she's
we're they're that's what's let's very just really then than too also about into over under
again once know knows going go get got""".split()
)


def wl(s: str) -> List[str]:
    s = re.sub(r"[^a-z0-9' ]", " ", (s or "").lower())
    return [w for w in s.split() if w and (len(w) > 1 or w in ("a", "i"))]


def content(ws: Sequence[str]) -> List[str]:
    return [w for w in ws if w not in STOP and (len(w) >= 3 or w.isdigit())]


def content_recall(ref: str, hyp: str) -> Optional[float]:
    """Per-segment content-word recall, fuzzy >= 0.87 (snap.py hit rule)."""
    ref_c = content(wl(ref))
    if not ref_c:
        return None
    hset = set(wl(hyp))
    hits = 0
    for w in ref_c:
        if w in hset or any(
            difflib.SequenceMatcher(None, w, h).ratio() >= 0.87 for h in hset
        ):
            hits += 1
    return hits / len(ref_c)


# ── make_report conventions ──────────────────────────────────────────────────

def toks(s: str) -> List[str]:
    s = (s or "").strip().lower()
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", s)


def seg_wer(ref: str, hyp: str) -> Optional[float]:
    r = toks(ref)
    if not r:
        return None
    return editdistance.eval(toks(hyp), r) / len(r) * 100.0


# ── binomial sign test (fixed vs broke, two-sided, p0=0.5) ───────────────────

def sign_test_p(a: int, b: int) -> Optional[float]:
    n = a + b
    if n == 0:
        return None
    k = min(a, b)
    p = 2.0 * sum(comb(n, i) for i in range(k + 1)) / (2.0 ** n)
    return min(1.0, p)


# ── loading ──────────────────────────────────────────────────────────────────

def load_refs(path: str) -> Dict[str, str]:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return dict(zip(d["utt_id"], d["ref"]))


def load_candidates(root: str) -> dict:
    with open(Path(root) / "candidates.json", encoding="utf-8") as f:
        return json.load(f)


def rebuild_sub_text(text_original: str, subs: List[dict]) -> str:
    """Marking-independent substituted text (word subs are 1:1 by position)."""
    words = split_words(text_original)
    for s in subs:
        words[s["pos"]] = s["chosen"]["word"]
    return " ".join(words)


def load_arm_subs(path: Path) -> Dict[str, dict]:
    """substitutions.json -> {utt: {"text_original", "text_sub", "subs"}} for
    touched segments only; cross-checks the marking-stripped on-disk text."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for utt, seg in d["segments"].items():
        if not seg.get("n_subs"):
            continue
        text_sub = rebuild_sub_text(seg["text_original"], seg["subs"])
        stripped = seg["text_substituted"].replace("°", "")
        if d["meta"].get("marking") in ("subtle", "none") and stripped != text_sub:
            raise AssertionError(f"rebuild mismatch {path.name}:{utt}")
        out[utt] = {
            "text_original": seg["text_original"],
            "text_sub": text_sub,
            "subs": seg["subs"],
        }
    return out


# ── arm generation through the real apply gate code ──────────────────────────

def run_apply(candidates: Path, decisions: List[Path], agree: str, out: Path,
              overlap_eligible: bool = False) -> None:
    cmd = [VENV_PY, PHON_SUB, "apply", "--candidates", str(candidates),
           "--decisions", ",".join(str(p) for p in decisions),
           "--agree-mode", agree, "--marking", "none", "--out", str(out)]
    if overlap_eligible:
        cmd.append("--overlap-eligible")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"apply failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def synth_naive_decisions(cands: dict, out: Path) -> int:
    """decision=replace with the highest-beam_mass eligible candidate, for
    every judgeable flag (>=1 eligible_for_sub candidate)."""
    decs = []
    for utt, seg in sorted(cands["segments"].items()):
        for fl in seg.get("flags", []):
            elig = [c for c in fl.get("candidates", []) if c.get("eligible_for_sub")]
            if not elig:
                continue
            best = max(elig, key=lambda c: c.get("beam_mass", 0.0))
            decs.append({"utt_id": utt, "pos": fl["position"],
                         "decision": "replace", "chosen": best["word"],
                         "verdict": "clearly_better",
                         "rationale": f"naive max-mass ({best['beam_mass']:.3f})"})
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump({"engine": "naive_max_mass", "decisions": decs}, f, indent=1)
    return len(decs)


def synth_margin_decisions(llama_path: Path, margin: float, out: Path) -> int:
    """Re-threshold llama's recorded delta_nats at a different margin."""
    with open(llama_path, encoding="utf-8") as f:
        d = json.load(f)
    decs = []
    n_rep = 0
    for x in d["decisions"]:
        rep = x.get("delta_nats") is not None and x["delta_nats"] >= margin \
            and x.get("best_candidate")
        n_rep += bool(rep)
        decs.append({"utt_id": x["utt_id"], "pos": x["pos"],
                     "decision": "replace" if rep else "keep",
                     "chosen": x["best_candidate"] if rep else "",
                     "verdict": "clearly_better" if rep else "worse",
                     "rationale": f"margin sweep {margin}: d={x.get('delta_nats')}"})
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump({"engine": f"llama_margin_{margin}", "decisions": decs}, f, indent=1)
    return n_rep


# ── span arm (textual; spans are not in the apply pipeline) ──────────────────

def span_arm(cands: dict, ignore_segment_gate: bool) -> Dict[str, dict]:
    """{utt: {"text_original","text_sub","spans":[{positions,anchor,cand,mass,sim}]}}
    Top candidate per span under the variant policy; numeric/entity span
    reasons are NEVER ignored; <= MAX_SUBS_PER_SEG spans/segment by mass."""
    max_spans = int(cands["meta"]["constants"].get("MAX_SUBS_PER_SEG", 2))
    out = {}
    for utt, seg in cands["segments"].items():
        picked = []
        for sf in seg.get("span_flags", []):
            for c in sf.get("candidates", []):  # already sorted mass desc
                reasons = set(c.get("display_only_reasons", []))
                ok = (not c.get("display_only")) if not ignore_segment_gate \
                    else reasons <= {"segment_quality"}
                if ok:
                    picked.append({"positions": sf["positions"],
                                   "anchor_text": sf["anchor_text"],
                                   "cand_text": c["text"],
                                   "region_mass": c["region_mass"],
                                   "span_viseme_sim": c["span_viseme_sim"]})
                    break
        if not picked:
            continue
        picked.sort(key=lambda s: -s["region_mass"])
        picked = picked[:max_spans]
        words = split_words(seg["display_text"])
        for sp in sorted(picked, key=lambda s: -s["positions"][0]):  # right→left
            a, b = sp["positions"]
            words[a:b + 1] = split_words(sp["cand_text"])
        out[utt] = {"text_original": seg["display_text"],
                    "text_sub": " ".join(words), "spans": picked}
    return out


def classify_span(orig_words: List[str], ref_toks: List[str], span: dict) -> str:
    """fixed = substituted span STRICTLY closer to the aligned ref span by word
    edit distance; broke = strictly worse; else neutral (incl. ref-gap)."""
    a, b = span["positions"]
    pairs = align_word_lists(orig_words, ref_toks)
    ref_idx = [rj for hi, rj in ((p[0], p[1]) for p in pairs)
               if hi != -1 and a <= hi <= b and rj != -1]
    if not ref_idx:
        return "neutral_both_wrong"
    ref_span = [t.lower() for t in ref_toks[min(ref_idx):max(ref_idx) + 1]]
    anchor = [w.lower() for w in orig_words[a:b + 1]]
    cand = [w.lower() for w in split_words(span["cand_text"])]
    d_anchor = editdistance.eval(anchor, ref_span)
    d_cand = editdistance.eval(cand, ref_span)
    if d_cand < d_anchor:
        return "fixed"
    if d_cand > d_anchor:
        return "broke"
    return "neutral_both_wrong"


# ── word-level classification ────────────────────────────────────────────────

def aligned_ref_word(orig_words: List[str], ref_toks: List[str], pos: int
                     ) -> Optional[str]:
    pairs = align_word_lists(orig_words, ref_toks)
    for hi, rj in pairs:
        if hi == pos:
            return ref_toks[rj].lower() if rj != -1 else None
    return None


def classify_sub(orig: str, chosen: str, refw: Optional[str]) -> str:
    o, c = orig.lower(), chosen.lower()
    if refw is None:
        return "neutral_both_wrong"
    if o == refw:
        return "broke"
    if c == refw:
        return "fixed"
    return "neutral_both_wrong"


# ── safety audit (independent recheck for the GO gate) ───────────────────────

def safety_audit(touched: Dict[str, dict], nlp, is_numeric) -> dict:
    """Numeric/entity INTRODUCTIONS among applied subs (word-level arms)."""
    num_intro, ent_intro, details = 0, 0, []

    def ent_status(text: str, pos: int) -> bool:
        doc = nlp(text)
        w = split_words(text)[pos].lower()
        for t in doc:
            if re.sub(r"[^a-z0-9']", "", t.text.lower()) == w:
                if t.pos_ == "PROPN" or t.ent_type_:
                    return True
        return False

    for utt, seg in touched.items():
        for s in seg["subs"]:
            o, c, p = s["original"]["word"], s["chosen"]["word"], s["pos"]
            if is_numeric(c) and not is_numeric(o):
                num_intro += 1
                details.append({"utt": utt, "pos": p, "type": "numeric",
                                "orig": o, "chosen": c})
            if ent_status(seg["text_sub"], p) and not ent_status(seg["text_original"], p):
                ent_intro += 1
                details.append({"utt": utt, "pos": p, "type": "entity",
                                "orig": o, "chosen": c})
    return {"numeric_introductions": num_intro,
            "entity_introductions": ent_intro, "details": details}


# ── IS (canonical make_report --compute-is recipe) ───────────────────────────

class ISScorer:
    def __init__(self):
        import make_report as mr  # noqa
        from generate_intelligibility_scores import (  # noqa
            SemanticEncoder, compute_is, compute_phonetic_similarity,
            compute_length_ratio)
        self.mr = mr
        self.compute_is = compute_is
        self.phon = compute_phonetic_similarity
        self.lr = compute_length_ratio
        self.encoder = SemanticEncoder(device="auto")

    def score(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """pairs = [(ref, hyp)] -> IS list (canonical recipe)."""
        if not pairs:
            return []
        refs = [r if (r or "").strip() else "empty" for r, _ in pairs]
        hyps = [h if (h or "").strip() else "empty" for _, h in pairs]
        sems = self.encoder.similarities(refs, hyps, batch_size=128)
        out = []
        for i, (ref, hyp) in enumerate(pairs):
            if not (ref or "").strip():
                out.append(0.0)
                continue
            sem = 0.0 if not (hyp or "").strip() else float(sems[i])
            ph = self.phon(ref, hyp)["phonetic_sim"]
            lr = self.lr(ref, hyp)
            r_t, h_t = toks(ref), toks(hyp)
            wer_pct = (editdistance.eval(h_t, r_t) / len(r_t) * 100) if r_t else 0.0
            m = self.mr.compute_all_metrics(ref, hyp)
            score, _, _ = self.compute_is(sem, ph, wer_pct, m.wwer, m.nea_f1, lr)
            out.append(score)
        return out


# ── arm scoring ──────────────────────────────────────────────────────────────

def score_arm(name: str, refs: Dict[str, str], orig_texts: Dict[str, str],
              touched: Dict[str, dict], base_wer: Dict[str, Optional[float]],
              base_recall: Dict[str, Optional[float]],
              niv: Dict[str, str], bands: Dict[str, str],
              is_scorer: Optional[ISScorer], nlp, is_numeric,
              span_mode: bool = False) -> dict:
    n_words_total = sum(len(split_words(t)) for t in orig_texts.values())
    all_utts = sorted(refs)
    subs_flat, cls_counter = [], Counter()
    split_niv = defaultdict(Counter)
    split_band = defaultdict(Counter)
    split_prefix = defaultdict(Counter)

    for utt, seg in sorted(touched.items()):
        orig_words = split_words(seg["text_original"])
        ref_toks = toks(refs.get(utt, ""))
        if span_mode:
            for sp in seg["spans"]:
                cls = classify_span(orig_words, ref_toks, sp)
                cls_counter[cls] += 1
                subs_flat.append({"utt": utt, "positions": sp["positions"],
                                  "orig": sp["anchor_text"],
                                  "chosen": sp["cand_text"],
                                  "region_mass": round(sp["region_mass"], 4),
                                  "class": cls})
                _bump_splits(utt, cls, niv, bands, split_niv, split_band, split_prefix)
        else:
            for s in seg["subs"]:
                refw = aligned_ref_word(orig_words, ref_toks, s["pos"])
                cls = classify_sub(s["original"]["word"], s["chosen"]["word"], refw)
                cls_counter[cls] += 1
                subs_flat.append({
                    "utt": utt, "pos": s["pos"], "orig": s["original"]["word"],
                    "chosen": s["chosen"]["word"], "ref_word": refw,
                    "orig_prob": round(s["original"].get("prob", 0.0), 3),
                    "chosen_mass_pct": s["chosen"].get("beam_mass_pct"),
                    "class": cls,
                    "engine": s.get("engine", ""),
                    "rationale": (s.get("rationale") or "")[:300]})
                _bump_splits(utt, cls, niv, bands, split_niv, split_band, split_prefix)

    # dWER (macro mean, make_report convention) — exact via touched-only deltas
    wer_vals = [v for v in base_wer.values() if v is not None]
    n_wer = len(wer_vals)
    d_overall_sum, d_touch = 0.0, []
    for utt, seg in touched.items():
        b = base_wer.get(utt)
        if b is None:
            continue
        w = seg_wer(refs[utt], seg["text_sub"])
        d_overall_sum += (w - b)
        d_touch.append(w - b)
    dwer_overall = d_overall_sum / n_wer if n_wer else 0.0
    dwer_touched = sum(d_touch) / len(d_touch) if d_touch else 0.0

    # content recall — same exact-delta trick
    rec_vals = [v for v in base_recall.values() if v is not None]
    n_rec = len(rec_vals)
    dr_sum, dr_touch = 0.0, []
    for utt, seg in touched.items():
        b = base_recall.get(utt)
        if b is None:
            continue
        r = content_recall(refs[utt], seg["text_sub"])
        dr_sum += (r - b)
        dr_touch.append(r - b)
    drec_overall = (dr_sum / n_rec * 100) if n_rec else 0.0
    drec_touched = (sum(dr_touch) / len(dr_touch) * 100) if dr_touch else 0.0

    # dIS — touched pairs only; overall = sum/N (exact)
    dis_overall = dis_touched = 0.0
    if is_scorer is not None and touched:
        t_utts = sorted(touched)
        is_orig = is_scorer.score([(refs[u], touched[u]["text_original"]) for u in t_utts])
        is_sub = is_scorer.score([(refs[u], touched[u]["text_sub"]) for u in t_utts])
        deltas = [s - o for o, s in zip(is_orig, is_sub)]
        dis_touched = sum(deltas) / len(deltas)
        dis_overall = sum(deltas) / len(all_utts)

    audit = ({"numeric_introductions": 0, "entity_introductions": 0, "details": []}
             if span_mode or not touched
             else safety_audit(touched, nlp, is_numeric))
    if span_mode and touched:  # numeric/entity audit for spans: word-set diff
        audit = span_safety_audit(touched, nlp, is_numeric)

    n_subs = sum(cls_counter.values())
    fixed, broke = cls_counter["fixed"], cls_counter["broke"]
    return {
        "arm": name, "n_subs": n_subs, "segments_touched": len(touched),
        "fixed": fixed, "broke": broke,
        "neutral_both_wrong": cls_counter["neutral_both_wrong"],
        "sign_test_p_fixed_vs_broke": sign_test_p(fixed, broke),
        "dwer_overall_pp": round(dwer_overall, 4),
        "dwer_touched_pp": round(dwer_touched, 3),
        "dis_overall": round(dis_overall, 5),
        "dis_touched": round(dis_touched, 4),
        "drecall_overall_pp": round(drec_overall, 4),
        "drecall_touched_pp": round(drec_touched, 3),
        "numeric_introductions": audit["numeric_introductions"],
        "entity_introductions": audit["entity_introductions"],
        "audit_details": audit["details"],
        "sub_rate_pct_words": round(n_subs / n_words_total * 100, 3) if n_words_total else 0.0,
        "splits": {"niv": {k: dict(v) for k, v in split_niv.items()},
                   "mean_prob_band": {k: dict(v) for k, v in split_band.items()},
                   "prefix": {k: dict(v) for k, v in split_prefix.items()}},
        "subs": subs_flat,
    }


def _bump_splits(utt, cls, niv, bands, split_niv, split_band, split_prefix):
    if utt in niv:
        split_niv[niv[utt]][cls] += 1
    if utt in bands:
        split_band[bands[utt]][cls] += 1
    split_prefix["img" if utt.startswith("img_") else utt.split("_")[0]][cls] += 1


def span_safety_audit(touched: Dict[str, dict], nlp, is_numeric) -> dict:
    """Span variant: introductions = numeric/entity tokens present in the
    candidate span words but absent from the anchor span words."""
    num_intro, ent_intro, details = 0, 0, []
    for utt, seg in touched.items():
        for sp in seg["spans"]:
            a_ws = set(split_words(sp["anchor_text"].lower()))
            c_ws = [w for w in split_words(sp["cand_text"].lower()) if w not in a_ws]
            for w in c_ws:
                if is_numeric(w):
                    num_intro += 1
                    details.append({"utt": utt, "type": "numeric", "chosen": w,
                                    "span": sp["cand_text"]})
            doc = nlp(sp["cand_text"])
            for t in doc:
                w = re.sub(r"[^a-z0-9']", "", t.text.lower())
                if w in set(c_ws) and (t.pos_ == "PROPN" or t.ent_type_):
                    ent_intro += 1
                    details.append({"utt": utt, "type": "entity", "chosen": w,
                                    "span": sp["cand_text"]})
    return {"numeric_introductions": num_intro,
            "entity_introductions": ent_intro, "details": details}


# ── engine agreement ─────────────────────────────────────────────────────────

def engine_agreement(root: Path, refs: Dict[str, str],
                     orig_texts: Dict[str, str],
                     claude_file="decisions_claude.json",
                     llama_file="decisions_llama.json") -> dict:
    with open(root / "judge" / claude_file, encoding="utf-8") as f:
        cd = json.load(f)
    with open(root / "judge" / llama_file, encoding="utf-8") as f:
        ld = json.load(f)
    c_by = {(x["utt_id"], x["pos"]): x for x in cd["decisions"]}
    l_by = {(x["utt_id"], x["pos"]): x for x in ld["decisions"]}
    keys = sorted(set(c_by) & set(l_by))

    n = len(keys)
    cells = Counter()
    resolution = defaultdict(Counter)
    disagreements = []
    for k in keys:
        c, l = c_by[k], l_by[k]
        cr, lr_ = c["decision"] == "replace", l["decision"] == "replace"
        if cr and lr_:
            same = (c.get("chosen", "").lower() == l.get("chosen", "").lower())
            cells["both_replace_same" if same else "both_replace_diff"] += 1
        elif not cr and not lr_:
            cells["both_keep"] += 1
        else:
            cells["claude_replace_llama_keep" if cr else "llama_replace_claude_keep"] += 1
        # who-was-right on any non-both-keep key
        if cr or lr_:
            utt, pos = k
            refw = aligned_ref_word(split_words(orig_texts.get(utt, "")),
                                    toks(refs.get(utt, "")), pos)
            orig_w = None
            # original word: from either decision's context — recover from text
            ws = split_words(orig_texts.get(utt, ""))
            orig_w = ws[pos].lower() if pos < len(ws) else None
            cell = ("both_replace" if (cr and lr_) else
                    "claude_replace_llama_keep" if cr else "llama_replace_claude_keep")
            verdict = "neither"
            if refw is not None:
                if cr and (c.get("chosen", "").lower() == refw):
                    verdict = "claude_right" if not lr_ or l.get("chosen", "").lower() != refw else "both_right"
                elif lr_ and (l.get("chosen", "").lower() == refw):
                    verdict = "llama_right"
                elif orig_w == refw:
                    verdict = "keep_was_right"
            resolution[cell][verdict] += 1
            if not (cr and lr_):
                disagreements.append({
                    "utt": utt, "pos": pos, "orig": orig_w, "ref_word": refw,
                    "claude": c["decision"], "claude_chosen": c.get("chosen", ""),
                    "llama": l["decision"], "llama_chosen": l.get("chosen", ""),
                    "who_right": verdict,
                    "claude_rationale": (c.get("rationale") or "")[:200],
                    "llama_delta_nats": l.get("delta_nats")})

    # Cohen's kappa on replace/keep
    c_rep = sum(1 for k in keys if c_by[k]["decision"] == "replace")
    l_rep = sum(1 for k in keys if l_by[k]["decision"] == "replace")
    agree_raw = (cells["both_replace_same"] + cells["both_replace_diff"]
                 + cells["both_keep"])
    po = agree_raw / n if n else 0.0
    pe = ((c_rep / n) * (l_rep / n) + ((n - c_rep) / n) * ((n - l_rep) / n)) if n else 0.0
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 1e-9 else None
    return {"n_joint_keys": n, "cells": dict(cells),
            "claude_replace": c_rep, "llama_replace": l_rep,
            "raw_agreement": round(po, 4),
            "cohens_kappa": round(kappa, 4) if kappa is not None else None,
            "resolution": {k: dict(v) for k, v in resolution.items()},
            "disagreements": disagreements}


# ── main per-dataset driver ──────────────────────────────────────────────────

def eval_dataset(name: str, cfg: dict, do_is: bool, do_sweep: bool) -> dict:
    import spacy
    from compute_word_confidence import is_numeric
    nlp = spacy.load("en_core_web_sm")

    root = Path(cfg["root"])
    refs = load_refs(cfg["refs"])
    cands = load_candidates(root)
    orig_texts = {u: (cands["segments"][u]["display_text"] if u in cands["segments"] else "")
                  for u in refs}
    # every candidates segment must be in refs
    missing = [u for u in cands["segments"] if u not in refs]
    if missing:
        raise AssertionError(f"{name}: {len(missing)} candidate utts missing refs")

    # difficulty stratifiers
    niv: Dict[str, str] = {}
    if cfg["report_csv"]:
        import csv as _csv
        with open(cfg["report_csv"], encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                try:
                    s = float(row.get("is_score") or 0.0)
                except ValueError:
                    continue
                niv[row["utt_id"]] = "Y" if s >= 3.80 else ("P" if s >= 2.00 else "N")
    bands: Dict[str, str] = {}
    for u, seg in cands["segments"].items():
        p = seg.get("mean_word_prob")
        if p is None:
            continue
        bands[u] = ("high>=0.85" if p >= 0.85 else
                    "0.75-0.85" if p >= 0.75 else
                    "0.65-0.75" if p >= 0.65 else "low<0.65")

    # baselines (per-utt)
    base_wer = {u: seg_wer(refs[u], orig_texts[u]) for u in refs}
    base_recall = {u: content_recall(refs[u], orig_texts[u]) for u in refs}
    wer_vals = [v for v in base_wer.values() if v is not None]
    baseline_wer = sum(wer_vals) / len(wer_vals) if wer_vals else 0.0
    rec_vals = [v for v in base_recall.values() if v is not None]
    baseline_recall = sum(rec_vals) / len(rec_vals) * 100 if rec_vals else 0.0

    is_scorer = ISScorer() if do_is else None

    arms_dir = root / "eval_arms"
    arms_dir.mkdir(exist_ok=True)
    arm_files: Dict[str, Path] = {}

    # naive max-mass through the REAL apply gates
    naive_dec = arms_dir / "decisions_naive_max_mass.json"
    n_naive = synth_naive_decisions(cands, naive_dec)
    arm_files["naive_max_mass"] = arms_dir / "substitutions_naive_max_mass.json"
    run_apply(root / "candidates.json", [naive_dec], "any",
              arm_files["naive_max_mass"])

    # engine arms
    if (root / "substitutions_claude_only.json").exists():
        arm_files["claude_only"] = root / "substitutions_claude_only.json"
    else:  # 1497: generate (sample-only)
        arm_files["claude_only"] = arms_dir / "substitutions_claude_only.json"
        run_apply(root / "candidates.json",
                  [root / "judge" / "decisions_claude.json"], "any",
                  arm_files["claude_only"])
    arm_files["llama_only"] = root / "substitutions_llama_only.json"
    arm_files["ship_agree"] = root / "substitutions.json"
    if (root / "substitutions_l4_liberal.json").exists():
        arm_files["l4_liberal"] = root / "substitutions_l4_liberal.json"

    results: Dict[str, dict] = {}
    results["noop"] = score_arm("noop", refs, orig_texts, {}, base_wer,
                                base_recall, niv, bands, is_scorer, nlp,
                                is_numeric)
    for arm, path in arm_files.items():
        touched = load_arm_subs(path)
        results[arm] = score_arm(arm, refs, orig_texts, touched, base_wer,
                                 base_recall, niv, bands, is_scorer, nlp,
                                 is_numeric)

    # span arms (textual)
    for arm, ignore in (("span_gated", False), ("span_ungated", True)):
        touched = span_arm(cands, ignore)
        results[arm] = score_arm(arm, refs, orig_texts, touched, base_wer,
                                 base_recall, niv, bands, is_scorer, nlp,
                                 is_numeric, span_mode=True)

    agreement = engine_agreement(root, refs, orig_texts)

    sweep = []
    if do_sweep:
        for m in MARGIN_SWEEP:
            dec = arms_dir / f"decisions_llama_margin_{m}.json"
            n_rep = synth_margin_decisions(root / "judge" / "decisions_llama.json",
                                           m, dec)
            outp = arms_dir / f"substitutions_llama_margin_{m}.json"
            run_apply(root / "candidates.json", [dec], "any", outp)
            r = score_arm(f"llama_margin_{m}", refs, orig_texts,
                          load_arm_subs(outp), base_wer, base_recall, niv,
                          bands, is_scorer if m == 2.0 else None, nlp,
                          is_numeric)
            r["margin_nats"] = m
            r["n_replace_decisions"] = n_rep
            r.pop("subs")
            r.pop("audit_details")
            sweep.append(r)

    heur_path = root / "judge" / "decisions_heuristic.json"
    heur_replaces = None
    if heur_path.exists():
        with open(heur_path, encoding="utf-8") as f:
            heur_replaces = sum(1 for x in json.load(f)["decisions"]
                                if x["decision"] == "replace")

    return {
        "dataset": name,
        "n_utts": len(refs),
        "n_words_display": sum(len(split_words(t)) for t in orig_texts.values()),
        "baseline_wer_pct": round(baseline_wer, 2),
        "baseline_content_recall_pct": round(baseline_recall, 2),
        "n_judgeable_flags": n_naive,
        "heuristic_engine_replaces": heur_replaces,
        "arms": results,
        "engine_agreement": agreement,
        "margin_sweep": sweep,
    }


# ── markdown dump ────────────────────────────────────────────────────────────

def fmt_p(p):
    return "—" if p is None else (f"{p:.3f}" if p >= 0.001 else f"{p:.1e}")


def arms_table(res: dict) -> str:
    hdr = ("| arm | n subs | fixed | broke | neutral | sign p | dWER overall (pp) | "
           "dWER touched (pp) | dIS overall | dIS touched | dRecall overall (pp) | "
           "dRecall touched (pp) | num/ent intro | sub rate % |")
    sep = "|" + "---|" * 14
    lines = [hdr, sep]
    order = ["noop", "naive_max_mass", "claude_only", "llama_only",
             "ship_agree", "span_gated", "span_ungated", "l4_liberal"]
    for a in order:
        if a not in res["arms"]:
            continue
        r = res["arms"][a]
        lines.append(
            f"| {a} | {r['n_subs']} | {r['fixed']} | {r['broke']} | "
            f"{r['neutral_both_wrong']} | {fmt_p(r['sign_test_p_fixed_vs_broke'])} | "
            f"{r['dwer_overall_pp']:+.3f} | {r['dwer_touched_pp']:+.2f} | "
            f"{r['dis_overall']:+.4f} | {r['dis_touched']:+.3f} | "
            f"{r['drecall_overall_pp']:+.3f} | {r['drecall_touched_pp']:+.2f} | "
            f"{r['numeric_introductions']}/{r['entity_introductions']} | "
            f"{r['sub_rate_pct_words']:.2f} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datasets", default="scene12,shaam,english_1497")
    ap.add_argument("--no-is", action="store_true", help="skip IS recompute")
    ap.add_argument("--no-sweep", action="store_true", help="skip margin sweep")
    ap.add_argument("--out-name", default="eval_results.json")
    args = ap.parse_args()

    for ds in [d.strip() for d in args.datasets.split(",") if d.strip()]:
        cfg = DATASETS[ds]
        print(f"\n{'=' * 80}\n### {ds}\n{'=' * 80}")
        res = eval_dataset(ds, cfg, do_is=not args.no_is,
                           do_sweep=not args.no_sweep and ds == "english_1497")
        outp = Path(cfg["root"]) / args.out_name
        with outp.open("w", encoding="utf-8") as f:
            json.dump(res, f, indent=1, ensure_ascii=False)
        print(f"baseline WER {res['baseline_wer_pct']}%  "
              f"content-recall {res['baseline_content_recall_pct']}%  "
              f"utts {res['n_utts']}  judgeable flags {res['n_judgeable_flags']}")
        print(arms_table(res))
        ea = res["engine_agreement"]
        print(f"\nengine agreement: n={ea['n_joint_keys']} "
              f"raw={ea['raw_agreement']} kappa={ea['cohens_kappa']} "
              f"cells={ea['cells']}")
        print(f"resolution: {json.dumps(ea['resolution'])}")
        if res["margin_sweep"]:
            print("\nmargin sweep (llama, re-thresholded delta_nats -> real apply):")
            for r in res["margin_sweep"]:
                print(f"  m={r['margin_nats']:>3} subs={r['n_subs']:>4} "
                      f"fixed={r['fixed']:>3} broke={r['broke']:>3} "
                      f"neutral={r['neutral_both_wrong']:>4} "
                      f"dWER={r['dwer_overall_pp']:+.3f}pp "
                      f"dRecall={r['drecall_overall_pp']:+.3f}pp")
        print(f"wrote {outp}")


if __name__ == "__main__":
    main()
