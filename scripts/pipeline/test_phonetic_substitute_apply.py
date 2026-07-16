#!/usr/bin/env python3
"""Adversarial gate tests for `phonetic_substitute.py apply` (P2).

Every test feeds apply_substitutions() FAKE engine decisions that violate one
gate and asserts the substitution is blocked (with the expected reason) while
valid substitutions still pass. Also: MAX_SUBS_PER_SEG capping, --agree-mode
all agreement arm, L4 --overlap-eligible policy, marking modes, non-mutation
of the candidates dict, and CLI byte-idempotence.

The candidates fixture is SYNTHETIC (no real run data): some fields are
deliberately falsified relative to P1 semantics (e.g. a numeric flag whose
display_only bit claims False) — apply must catch these mechanically because
engine decisions are untrusted and convenience bits are re-validated.

Run:  /home/ubuntu/vsp-llm-yoad-venv/bin/python -m pytest -q \
          scripts/pipeline/test_phonetic_substitute_apply.py
  or: /home/ubuntu/vsp-llm-yoad-venv/bin/python \
          scripts/pipeline/test_phonetic_substitute_apply.py   (standalone)
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phonetic_substitute as ps  # noqa: E402


# ── synthetic fixture ─────────────────────────────────────────────────────────

def cand(word, mass, admissible=True, evidence=("beam",), reasons=(),
         viseme_ok=True, **kw):
    c = {"word": word,
         "beam_mass": mass, "beam_mass_pct": round(100.0 * mass, 1),
         "n_beams": max(1, int(mass * 20)) if "beam" in evidence else 0,
         "evidence": list(evidence), "corpus_freq": 5,
         "phon_dist_norm": 0.2, "viseme_ok": viseme_ok,
         "phon_scorer": "viseme_cmu", "admissible": admissible,
         "display_only": bool(reasons), "display_only_reasons": list(reasons),
         "eligible_for_sub": (not reasons and admissible
                              and "beam" in evidence and mass >= 0.05),
         "score": round(0.7 * mass + 0.3 * (1.0 - 0.2), 4)}
    c.update(kw)
    return c


def flag(pos, word, prob=0.6, display_only=False, reasons=(), numeric=False,
         entity=False, cands=(), agreement=0.7, orig_mass=0.5):
    return {"position": pos, "word": word, "prob": prob,
            "agreement": agreement, "conf_class": "conf-low",
            "is_numeric": numeric, "entity_suspect": entity,
            "display_only": display_only,
            "display_only_reasons": list(reasons),
            "original_mass": orig_mass, "gap_mass": 0.0,
            "candidates": list(cands)}


def seg(text, flags, mean_prob=0.80, gate=True):
    return {"video": "vid", "order_key": 0.0, "display_text": text,
            "n_words": len(text.split()), "mean_word_prob": mean_prob,
            "segment_gate_passed": gate, "context_before": [],
            "context_after": [], "flags": flags, "span_flags": []}


def make_candidates():
    return {
        "meta": {"run": "synthetic", "method": "hyp_mbr", "fid": "test",
                 "constants": dict(ps.CONSTANTS), "inputs": {}},
        "segments": {
            # healthy segment: 3 individually valid targets (max-subs test)
            # + one flag with one bad candidate per candidate-level gate
            "seg_good": seg(
                "the cat sat on the mat today",
                [flag(1, "cat", cands=[cand("bat", 0.30), cand("rat", 0.10)]),
                 flag(2, "sat", cands=[cand("sit", 0.25)]),
                 flag(3, "on", cands=[cand("in", 0.20)]),
                 flag(5, "mat", cands=[
                     cand("mad", 0.04),                       # mass below floor
                     cand("mate", 0.30, admissible=False),    # inadmissible
                     cand("matte", 0.0, evidence=("lexicon",),
                          reasons=("no_beam_evidence",)),     # no beam evidence
                     # falsified: numeric candidate claiming clean reasons —
                     # apply must recompute is_numeric("12")
                     cand("12", 0.30),
                     cand("kranowitz", 0.30,
                          reasons=("entity_suspect",))])]),   # entity candidate
            # flag-level gates (display_only honest; the rest falsified clean)
            "seg_display": seg(
                "hello there world",
                [flag(1, "there", prob=0.2, display_only=True,
                      reasons=("low_prob",),
                      cands=[cand("their", 0.40, eligible_for_sub=True)])]),
            "seg_numeric": seg(
                "pay two dollars now",
                [flag(1, "two", numeric=True,           # display_only falsified
                      cands=[cand("to", 0.40)])]),
            "seg_entity": seg(
                "ask diego about it",
                [flag(1, "diego", entity=True,          # display_only falsified
                      cands=[cand("dingo", 0.40)])]),
            # segment gate: mean 0.50 < 0.65 but stored gate bit falsified True
            "seg_weak": seg(
                "very mumbly words here",
                [flag(1, "mumbly", cands=[cand("humbly", 0.40)])],
                mean_prob=0.50, gate=True),
            # L4: pure overlap-evidence candidate (green-gated, no beam mass)
            "seg_overlap": seg(
                "we walked to the store",
                [flag(1, "walked",
                      cands=[cand("worked", 0.0, evidence=("overlap",),
                                  reasons=("no_beam_evidence",),
                                  overlap_weight=0.9215,
                                  eligible_via=["overlap"],
                                  overlap_sources=[{"utt": "nb", "pos": 3,
                                                    "prob": 0.97,
                                                    "agreement": 0.95}])])]),
        },
    }


def eng(name, *decisions):
    return ps.decisions_index(
        {"engine": name, "decisions": list(decisions)}, path=f"<{name}>")


def dec(utt, pos, chosen, decision="replace", verdict="clearly_better",
        rationale="test"):
    return {"utt_id": utt, "pos": pos, "decision": decision,
            "chosen": chosen, "verdict": verdict, "rationale": rationale}


def run(decisions_by_engine, agree_mode="any", **kw):
    cands = make_candidates()
    engines = [eng(name, *ds) for name, ds in decisions_by_engine]
    return ps.apply_substitutions(cands, engines, agree_mode, **kw)


def subs_at(out, utt):
    s = out["segments"].get(utt)
    return [x["pos"] for x in (s or {}).get("subs", [])]


def blocked_reasons(out, utt, pos):
    return [r for b in out["meta"]["blocked"]
            if b["utt_id"] == utt and b["pos"] == pos for r in b["reasons"]]


# ── gate tests (each fake decision must be blocked) ──────────────────────────

def test_valid_replace_applies():
    out = run([("e1", [dec("seg_good", 1, "bat")])])
    assert subs_at(out, "seg_good") == [1]
    s = out["segments"]["seg_good"]
    assert s["n_subs"] == 1 and s["subs"][0]["chosen"]["word"] == "bat"
    assert s["text_substituted"] == "the bat° sat on the mat today"
    assert s["text_original"] == "the cat sat on the mat today"
    # non-substituted flags surface as flags_kept with top-2-by-mass hovers
    kept = {f["pos"]: f for f in s["flags_kept"]}
    assert 1 not in kept and {2, 3, 5} <= set(kept)
    # top-2 by mass with deterministic word tie-break (mate/12/kranowitz @0.30)
    assert [c["word"] for c in kept[5]["candidates"]] == ["12", "kranowitz"]


def test_display_only_flag_blocked():
    out = run([("e1", [dec("seg_display", 1, "their")])])
    assert subs_at(out, "seg_display") == []
    assert "flag_display_only" in blocked_reasons(out, "seg_display", 1)


def test_numeric_flag_blocked():
    out = run([("e1", [dec("seg_numeric", 1, "to")])])
    assert subs_at(out, "seg_numeric") == []
    assert "flag_numeric" in blocked_reasons(out, "seg_numeric", 1)


def test_entity_flag_blocked():
    out = run([("e1", [dec("seg_entity", 1, "dingo")])])
    assert subs_at(out, "seg_entity") == []
    assert "flag_entity_suspect" in blocked_reasons(out, "seg_entity", 1)


def test_segment_gate_blocked():
    out = run([("e1", [dec("seg_weak", 1, "humbly")])])
    assert subs_at(out, "seg_weak") == []
    assert "segment_gate" in blocked_reasons(out, "seg_weak", 1)


def test_unknown_utt_pos_blocked():
    out = run([("e1", [dec("no_such_seg", 0, "x"), dec("seg_good", 99, "bat")])])
    assert "unknown_utt_pos" in blocked_reasons(out, "no_such_seg", 0)
    assert "unknown_utt_pos" in blocked_reasons(out, "seg_good", 99)


def test_non_candidate_chosen_blocked():
    out = run([("e1", [dec("seg_good", 1, "zebra")])])
    assert subs_at(out, "seg_good") == []
    assert "chosen_not_a_listed_candidate" in blocked_reasons(out, "seg_good", 1)


def test_mass_below_floor_blocked():
    out = run([("e1", [dec("seg_good", 5, "mad")])])
    assert subs_at(out, "seg_good") == []
    assert "candidate_mass_below_floor" in blocked_reasons(out, "seg_good", 5)


def test_inadmissible_candidate_blocked():
    out = run([("e1", [dec("seg_good", 5, "mate")])])
    assert "candidate_inadmissible" in blocked_reasons(out, "seg_good", 5)


def test_no_beam_evidence_blocked():
    out = run([("e1", [dec("seg_good", 5, "matte")])])
    assert "candidate_no_beam_evidence" in blocked_reasons(out, "seg_good", 5)


def test_numeric_candidate_blocked():
    out = run([("e1", [dec("seg_good", 5, "12")])])
    assert "candidate_numeric" in blocked_reasons(out, "seg_good", 5)


def test_entity_candidate_blocked():
    out = run([("e1", [dec("seg_good", 5, "kranowitz")])])
    assert "candidate_entity_suspect" in blocked_reasons(out, "seg_good", 5)


def test_verdict_not_clearly_better_blocked():
    out = run([("e1", [dec("seg_good", 1, "bat", verdict="somewhat_better")])])
    assert subs_at(out, "seg_good") == []
    assert "verdict_not_clearly_better" in blocked_reasons(out, "seg_good", 1)


def test_keep_decision_never_substitutes():
    # a keep with a filled-in chosen word must not create a proposal at all
    out = run([("e1", [dec("seg_good", 1, "bat", decision="keep")])])
    assert subs_at(out, "seg_good") == []
    assert out["meta"]["counts"]["replace_proposal_keys"] == 0


def test_max_subs_per_seg():
    out = run([("e1", [dec("seg_good", 1, "bat"), dec("seg_good", 2, "sit"),
                       dec("seg_good", 3, "in")])])
    # priority by candidate score: bat(0.30) > sit(0.25) > in(0.20)
    assert subs_at(out, "seg_good") == [1, 2]
    assert "max_subs_per_seg" in blocked_reasons(out, "seg_good", 3)


# ── agreement arm ─────────────────────────────────────────────────────────────

def test_agree_all_same_choice_passes():
    out = run([("e1", [dec("seg_good", 1, "bat")]),
               ("e2", [dec("seg_good", 1, "bat")])], agree_mode="all")
    assert subs_at(out, "seg_good") == [1]
    assert out["segments"]["seg_good"]["subs"][0]["engine"] == "e1+e2"


def test_agree_all_chosen_differs_blocked():
    out = run([("e1", [dec("seg_good", 1, "bat")]),
               ("e2", [dec("seg_good", 1, "rat")])], agree_mode="all")
    assert subs_at(out, "seg_good") == []
    assert any(r.startswith("engine_disagreement:chosen_differs")
               for r in blocked_reasons(out, "seg_good", 1))


def test_agree_all_missing_or_keep_blocked():
    for e2_decisions in ([], [dec("seg_good", 1, "", decision="keep",
                                  verdict="equal")]):
        out = run([("e1", [dec("seg_good", 1, "bat")]),
                   ("e2", e2_decisions)], agree_mode="all")
        assert subs_at(out, "seg_good") == []
        assert any(r.startswith("engine_disagreement:not_all_replace")
                   for r in blocked_reasons(out, "seg_good", 1))


def test_agree_all_weak_verdict_blocked():
    out = run([("e1", [dec("seg_good", 1, "bat")]),
               ("e2", [dec("seg_good", 1, "bat", verdict="somewhat_better")])],
              agree_mode="all")
    assert subs_at(out, "seg_good") == []
    assert any(r.startswith("verdict_not_clearly_better")
               for r in blocked_reasons(out, "seg_good", 1))


def test_agree_any_first_passing_engine_wins():
    out = run([("e1", [dec("seg_good", 1, "zebra")]),   # fails validation
               ("e2", [dec("seg_good", 1, "bat")])], agree_mode="any")
    assert subs_at(out, "seg_good") == [1]
    assert out["segments"]["seg_good"]["subs"][0]["engine"] == "e2"
    assert "chosen_not_a_listed_candidate" in blocked_reasons(out, "seg_good", 1)


# ── L4 overlap-eligibility policy ────────────────────────────────────────────

def test_overlap_candidate_blocked_by_default():
    out = run([("e1", [dec("seg_overlap", 1, "worked")])])
    assert subs_at(out, "seg_overlap") == []
    assert "candidate_no_beam_evidence" in blocked_reasons(out, "seg_overlap", 1)


def test_overlap_candidate_passes_with_flag():
    out = run([("e1", [dec("seg_overlap", 1, "worked")])],
              overlap_eligible=True)
    assert subs_at(out, "seg_overlap") == [1]


def test_overlap_flag_needs_eligible_via():
    cands = make_candidates()
    c = cands["segments"]["seg_overlap"]["flags"][0]["candidates"][0]
    c["eligible_via"] = []          # green gate not met at injection time
    out = ps.apply_substitutions(
        cands, [eng("e1", dec("seg_overlap", 1, "worked"))], "any",
        overlap_eligible=True)
    assert subs_at(out, "seg_overlap") == []


# ── marking modes ─────────────────────────────────────────────────────────────

def test_marking_modes():
    for marking, expect in (("subtle", "the bat° sat on the mat today"),
                            ("none", "the bat sat on the mat today"),
                            ("debug", "the [cat→bat] sat on the mat today")):
        out = run([("e1", [dec("seg_good", 1, "bat")])], marking=marking)
        assert out["segments"]["seg_good"]["text_substituted"] == expect, marking
    # untouched segments keep the display text verbatim in both fields
    out = run([("e1", [dec("seg_good", 1, "bat")])])
    s = out["segments"]["seg_numeric"]
    assert s["text_substituted"] == s["text_original"]


# ── purity: never mutates candidates ──────────────────────────────────────────

def test_candidates_not_mutated():
    cands = make_candidates()
    snapshot = copy.deepcopy(cands)
    ps.apply_substitutions(
        cands, [eng("e1", dec("seg_good", 1, "bat"), dec("seg_good", 5, "12"))],
        "any")
    assert cands == snapshot


# ── idempotence: CLI re-run -> byte-identical output ─────────────────────────

def test_cli_idempotent_byte_identical(tmp_path):
    cpath = tmp_path / "candidates.json"
    dpath = tmp_path / "decisions.json"
    cpath.write_text(json.dumps(make_candidates()))
    dpath.write_text(json.dumps(
        {"engine": "e1", "decisions": [dec("seg_good", 1, "bat"),
                                       dec("seg_good", 5, "12"),
                                       dec("seg_weak", 1, "humbly")]}))
    script = Path(__file__).resolve().parent / "phonetic_substitute.py"
    outs = []
    for name in ("out1.json", "out2.json"):
        op = tmp_path / name
        r = subprocess.run(
            [sys.executable, str(script), "apply", "--candidates", str(cpath),
             "--decisions", str(dpath), "--agree-mode", "all",
             "--marking", "subtle", "--out", str(op)],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(op.read_bytes())
    assert outs[0] == outs[1]
    parsed = json.loads(outs[0])
    assert [x["pos"] for x in parsed["segments"]["seg_good"]["subs"]] == [1]


# ── standalone runner ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import inspect
    import tempfile
    import traceback

    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            if "tmp_path" in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
            print(f"  PASS {name}")
        except Exception:
            failed += 1
            print(f"  FAIL {name}")
            traceback.print_exc()
    print(f"{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
