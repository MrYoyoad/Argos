# Phonetic substitution — validation vs references & GO/NO-GO (July 2026)

**Date**: July 16, 2026 (Workstream P, Agent P3). **Question**: the post-hoc substitution module ([phonetic_substitute.py](../../../scripts/pipeline/phonetic_substitute.py)) proposes replacing medium-confidence display words with beam-mass-backed, viseme-close, context-arbitrated alternatives — does it fix more than it breaks, and may the dual-engine "ship arm" go into the client guessing-game package?
**Verdict in one line**: **GO for the egla package arm** (2 substitutions, 1 fixed / 0 broke, all gate clauses pass; n is tiny and stated as such) — with mechanism-level evidence from 1,497 wild segments showing the current calibration is net-neutral-to-mildly-positive (not 3×-safe) in the wild, the naive/mechanical arms are actively destructive, and one clean knob (Llama margin 2.0→4.0 nats) that takes the solo engine over the 3× ship gate.
**Evaluator**: [egla_kafe_substitution_eval.py](../../../scripts/pipeline/egla_kafe_substitution_eval.py); per-dataset results JSONs sit next to each run's `candidates.json` (`.../substitution/<run>/eval_results.json`).

## The ship gate (binding, set in the plan)

For the client-package arm (= egla ship arm, `claude+llama --agree-mode all`):
**fixed ≥ 3× broke** AND **ΔWER ≤ 0 (overall + touched)** AND **zero entity/number introductions** AND **sub rate ≤ 5 % of words**. Partial-GO fallback if failed: display-only candidates (transcript hovers, no text rewrites).

## Method

- **Anchoring**: hypothesis side is always the `hyp_mbr` display text (`text_original` / `text_substituted` from the substitution artifacts, marking stripped); references are used **only to grade**: egla `work/eval/run_{scene12,shaam}_all/hypo-corrected.json` (utt-aligned corrected script lines, 448 + 330), 1497 `decode_output/hypo-172610.json` (parallel `utt_id/ref/hypo` arrays).
- **Per-substitution classification** against the ref word aligned to the substitution's position (`_alignment.align_word_lists` on the original text; word subs are 1:1 so positions are stable): **fixed** = original ≠ aligned ref word AND chosen == it; **broke** = original == aligned ref word; **neutral_both_wrong** = everything else, incl. positions aligned to a ref gap. Two-sided binomial sign test on fixed-vs-broke.
- **ΔWER**: per-segment `editdistance(toks(hyp), toks(ref))/len(toks(ref))`, macro-averaged (the `make_report.py` convention behind all project WER numbers), reported overall and on touched segments.
- **ΔIS**: the canonical IS recipe (`make_report --compute-is` path: MiniLM semantic sim, metaphone phonetic sim, WER, WWER, NEA-F1, length ratio → `compute_is`) recomputed for original and substituted text of **touched segments only**; overall ΔIS = Σ touched deltas / N_all — **exact**, since untouched segments contribute a delta of exactly 0 (whole-set absolute IS is not recomputed).
- **Content-word recall**: the handoff's metric mirrored verbatim from [snap.py](../../nbest_viseme_handoff/snap.py) (its tokenizer + STOP list; content = non-stop AND (len ≥ 3 or digit); hit = exact in hyp word set OR difflib ratio ≥ 0.87), per-segment recall averaged over segments with ≥ 1 ref content word.
- **Safety audit** (independent of the apply pipeline's own gates): numeric introductions via the module's `is_numeric` on chosen-but-not-original; entity introductions via spaCy PROPN/NER status of the chosen token in the substituted sentence where the original had none.
- **Generated arms run through the real gate code**: naive max-mass and the margin sweep are synthetic `decisions.json` files fed to the actual `phonetic_substitute.py apply` (flag/candidate/segment gates + `MAX_SUBS_PER_SEG` enforced identically to engine output). Span arms are applied textually by the evaluator (spans are not in the apply pipeline) and additionally scored **span-level**: fixed = substituted span strictly closer to the aligned ref span by word edit distance, broke = strictly worse.

**Flag funnel** (from each `candidates.json` meta): scene12 1,926 flags → 1,233 in-band → 252 eligible → **72 with a substitutable candidate** (= judged keys); shaam 1,516 → 832 → 103 → **19**; 1497 15,436 → 12,205 → 7,233 → **1,338** (Llama judged all; Claude a 300-key stratified sample). Engine (c) heuristic (mass-dominance + viseme_ok + POS match) proposed **0 replaces on all three runs** — the no-LLM fallback never fires at current constants; reported here as a line, not an arm.

## Arms — scene12 (448 turns, 2,173 display words; baseline WER 118.7 %*, content-recall 22.3 %)

| arm | n subs | fixed | broke | neutral | sign p | ΔWER overall (pp) | ΔWER touched (pp) | ΔIS overall | ΔIS touched | ΔRecall overall (pp) | ΔRecall touched (pp) | num/ent intro | sub rate % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noop | 0 | 0 | 0 | 0 | — | +0.000 | +0.00 | +0.0000 | +0.000 | +0.000 | +0.00 | 0/0 | 0.00 |
| naive_max_mass | 59 | 6 | 16 | 37 | 0.052 | +0.564 | +5.79 | −0.0210 | −0.230 | −0.746 | −7.46 | 0/1 | 2.71 |
| claude_only | 2 | 1 | 0 | 1 | 1.000 | −0.030 | −6.25 | +0.0010 | +0.227 | +0.066 | +12.50 | 0/0 | 0.09 |
| llama_only | 11 | 2 | 2 | 7 | 1.000 | +0.004 | +0.16 | +0.0004 | +0.017 | +0.066 | +2.27 | 0/0 | 0.51 |
| **ship_agree** | **2** | **1** | **0** | **1** | 1.000 | **−0.030** | **−6.25** | +0.0010 | +0.227 | +0.066 | +12.50 | **0/0** | **0.09** |
| span_gated | 34 | 9 | 9 | 16 | 1.000 | −0.015 | −0.21 | −0.0053 | −0.079 | −0.197 | −2.59 | 0/0 | 1.56 |
| span_ungated | 138 | 19 | 36 | 83 | 0.030 | +0.247 | +0.85 | −0.0251 | −0.091 | −0.581 | −1.90 | 0/3 | 6.35 |

\* Baseline WER > 100 % is expected under this anchoring: refs are single corrected script *turns* while hyp segments carry cross-turn bleed, so insertions dominate (June per-turn conversation WER was 86–92 % on the same footage). All Δ columns are unaffected — both texts face the same ref.

The 2 ship substitutions (both on `s1_tomer_yoad_1`, the #3-ranked camera scene):
1. `figured` → `forgot` — ref *"Technically I **forgot** where I put my passport."* → **fixed** (beam mass 12.4 %, Llama Δ=+12.4 nats).
2. `on` → `of` (*"getting out on it"* → *"getting out of it"*) — the region is an insertion vs this turn's ref (*"I'm the reason you're getting on the right plane."*) → **neutral**; the later, correct *"on the right plane"* was untouched. The idiom repair is harmless and arguably more fluent; note the aligner grades it against the turn ref only.

## Arms — shaam (330 segs = 175 img_* iPhone + 155 shaam_* screen-rec; 1,693 words; baseline WER 157.1 %*, recall 16.4 %)

| arm | n subs | fixed | broke | neutral | sign p | ΔWER overall (pp) | ΔWER touched (pp) | ΔIS overall | ΔIS touched | ΔRecall overall (pp) | ΔRecall touched (pp) | num/ent intro | sub rate % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noop | 0 | 0 | 0 | 0 | — | +0.000 | +0.00 | +0.0000 | +0.000 | +0.000 | +0.00 | 0/0 | 0.00 |
| naive_max_mass | 19 | 1 | 11 | 7 | 0.006 | +0.609 | +12.44 | −0.0145 | −0.342 | −0.318 | −5.95 | 0/0 | 1.12 |
| claude_only | 0 | 0 | 0 | 0 | — | +0.000 | +0.00 | +0.0000 | +0.000 | +0.000 | +0.00 | 0/0 | 0.00 |
| llama_only | 2 | 0 | 1 | 1 | 1.000 | +0.039 | +5.56 | −0.0021 | −0.349 | −0.095 | −12.50 | 0/0 | 0.12 |
| **ship_agree** | **0** | 0 | 0 | 0 | — | 0 | 0 | 0 | 0 | 0 | 0 | **0/0** | **0.00** |
| span_gated | 12 | 1 | 7 | 4 | 0.070 | +0.470 | +11.21 | −0.0086 | −0.237 | −0.127 | −2.78 | 0/0 | 0.71 |
| span_ungated | 70 | 11 | 18 | 41 | 0.265 | +0.992 | +4.81 | −0.0120 | −0.062 | +0.159 | +0.73 | 0/0 | 4.13 |

Shaam is the weak-footage run: Claude kept all 19 judgeable flags, and validation says it was right — Llama's 2 solo proposals graded 0 fixed / 1 broke (`plane`→`train` against ref *"…getting on the right **plane**."*). The ship arm being empty here **is** the mechanism working.

## Arms — english_1497 (wild YouTube; 23,510 words; baseline WER 63.84 % — reproduces the known MBR 63.8 %; recall 44.3 %)

| arm | n subs | fixed | broke | neutral | sign p | ΔWER overall (pp) | ΔWER touched (pp) | ΔIS overall | ΔIS touched | ΔRecall overall (pp) | ΔRecall touched (pp) | num/ent intro | sub rate % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| noop | 0 | 0 | 0 | 0 | — | +0.000 | +0.00 | +0.0000 | +0.000 | +0.000 | +0.00 | 0/0 | 0.00 |
| naive_max_mass | 1075 | 178 | 395 | 502 | 6.5e-20 | +0.934 | +2.07 | −0.0274 | −0.061 | −0.821 | −1.82 | 0/12 | 4.57 |
| claude_only (sample) | 12 | 4 | 3 | 5 | 1.000 | −0.009 | −1.13 | +0.0004 | +0.049 | +0.005 | +0.65 | 0/0 | 0.05 |
| llama_only | 230 | 70 | 57 | 103 | 0.287 | −0.033 | −0.24 | +0.0053 | +0.039 | +0.025 | +0.18 | 0/1 | 0.98 |
| ship_agree (in-sample) | 7 | 3 | 2 | 2 | 1.000 | −0.007 | −1.60 | +0.0002 | +0.052 | +0.003 | +0.53 | 0/0 | 0.03 |
| span_gated | 731 | 149 | 303 | 279 | 3.7e-13 | +0.548 | +1.46 | −0.0143 | −0.038 | −0.218 | −0.58 | 0/11 | 3.11 |
| span_ungated | 1070 | 193 | 404 | 473 | 3.7e-18 | +0.683 | +1.20 | −0.0167 | −0.029 | −0.223 | −0.39 | 0/19 | 4.55 |
| l4_liberal | 235 | 73 | 57 | 105 | 0.188 | −0.051 | −0.36 | +0.0061 | +0.044 | +0.049 | +0.35 | 0/1 | 1.00 |

Notes: `claude_only` and `ship_agree` exist only within Claude's 300-key stratified sample (full-set agreement is not computable — Claude did not judge the other 1,038 keys). `llama_only`'s single flagged "entity introduction" is `another`→`third` (spaCy ORDINAL): a real gap — ordinal words pass the module's `is_numeric`; Claude's veto kept it out of the ship arm, and adding ordinals to the numeric gate is a one-line module fix worth making before any wider rollout.

### What the tables say

1. **Engine arbitration is the whole game.** Naive max-mass — the exact same flags, candidates, and gates, minus the context engine — breaks 2.2× more than it fixes on 1497 (395 vs 178, p≈7e-20) and is worse on every metric on all three datasets. The plan's prior ("beam mass alone does NOT separate fixes from breaks") is now measured.
2. **Both engines solo are ~1.2–1.3× fix:break in the wild** (Claude 4F/3B on its sample; Llama 70F/57B full) — net-positive on ΔWER/ΔIS/recall but far from 3×. Agreement (3F/2B in-sample) filters both solo error modes yet stays below 3× on wild data at current calibration.
3. **Quality splits (llama_only, 1497)**: NIV-Y 36F/26B, P 31F/29B, N 3F/2B; by MBR segment confidence: ≥0.85 band 24F/14B, 0.75–0.85 27F/24B, 0.65–0.75 19F/19B. Precision rises with segment quality — the "Trust-tier enhancer, not a rescue tool" doctrine holds for the engine-gated arm. The mechanical arms invert it catastrophically: naive on NIV-Y segments is 74F/**233B** — mass-swapping is *most* destructive exactly where the text is already good.
4. **ΔIS and Δrecall are honest but tiny** at ~1 % sub rate: llama_only moves whole-set IS by +0.005 (touched +0.039); the ship arm by +0.0002. Nobody should sell this as a WER/IS feature; its value is transparent per-word correction with an audit trail.

## Engine agreement — the dual-engine payoff, quantified

| dataset | joint keys | both keep | both replace (same word) | both replace (diff word) | Llama-only replace | Claude-only replace | raw agree | Cohen's κ |
|---|---|---|---|---|---|---|---|---|
| scene12 | 72 | 61 | 2 | 0 | 9 | 0 | 87.5 % | 0.274 |
| shaam | 19 | 17 | 0 | 0 | 2 | 0 | 89.5 % | 0.0 |
| english_1497 (Claude's sample) | 300 | 243 | 7 | 0 | 45 | 5 | 83.3 % | 0.164 |

κ is low everywhere: past the shared keep-bias, the engines rarely agree on *acting* — Llama proposes ~4× more replacements than Claude (fp16 teacher-forced margins are trigger-happy; Claude's "when in doubt keep" rubric is conservative). Notably they **never both-replace with different words** (0 across 391 joint keys) — when they do act together, they act identically.

**Who was right where they disagreed** (validation verdict on each one-sided proposal, 1497 sample):

| disagreement | n | replacer right | keeper right | neither (both wrong) |
|---|---|---|---|---|
| Llama replace / Claude keep | 45 | 8 | **14** | 23 |
| Claude replace / Llama keep | 5 | 1 | 1 | 3 |
| *(scene12, Llama replace / Claude keep)* | *9* | *1* | *2* | *6* |

Claude's veto prevented **14 breaks at the cost of 8 missed fixes** on the 1497 sample (1.75 : 1 protective; e.g. blocked `another`→`third`, `our`→`my`, `how`→`of`); Llama's veto ran 1:1 but blocked the genuine `until`→`at` break that Claude alone would have shipped. Both directions earn their keep; agreement mode is the highest-precision configuration available at m=2.0 — the missed fixes are the price, e.g. `phones`→`phone` on scene12 (ref *"Look at your phone."*), which Llama proposed (Δ=+5.9 nats) and Claude vetoed as "plural is as plausible".

## Threshold sensitivity — the Llama margin sweep (real, through the apply gates)

Llama's decisions record `delta_nats` + `best_candidate` for every judged flag, so re-thresholding the margin and re-running the **actual apply pipeline** is exact (no re-scoring). 1497, solo Llama:

| margin (nats) | subs | fixed | broke | fix:break | sign p | ΔWER overall (pp) | ΔRecall overall (pp) |
|---|---|---|---|---|---|---|---|
| 1.0 | 303 | 79 | 90 | 0.88 | n.s. | +0.067 | −0.064 |
| **2.0 (shipped)** | 231* | 70 | 57 | 1.23 | 0.287 | −0.033 | +0.025 |
| 3.0 | 178 | 59 | 35 | 1.69 | 0.017 | −0.087 | +0.065 |
| **4.0** | 115 | 45 | 15 | **3.00** | 1.3e-4 | **−0.113** | **+0.134** |
| 6.0 | 58 | 28 | 5 | **5.60** | 5.4e-5 | −0.068 | +0.103 |

\* 231 vs the shipped 230: one flag sits at Δ=2.00 exactly with verdict `somewhat_better` (engine boundary is strict); the sweep's ≥ includes it — a live illustration of the fp16 ±0.03-nat caveat.

**The margin is the knob.** Fix:break crosses the 3× ship gate at **m=4.0**, which also minimizes ΔWER and maximizes recall gain — and a solo Llama at m=4.0 (45F/15B, p=1.3e-4) outperforms cross-engine agreement at m=2.0 (3F/2B in-sample). The 2.0-nat calibration was fitted on scene1 only (tiny, scripted); wild data wants a stricter engine, not a second vetoer. Raising the margin *inside* the agreement intersection doesn't help (the 7 in-sample agreement subs at m≥4 become 2F/1B/2N — the intersection is already margin-heavy).

**Not swept** (each requires regenerating `candidates.json` — cheap CPU — but *re-judging both engines*, which is the expensive part: ~43 in-session Claude batches + ~1 h GPU Llama per configuration): `MIN_BEAM_MASS` (0.05 → 0.10/0.15), `SEG_MEANPROB_FLOOR` (0.65 → 0.75), `PHON_ADMIT_NORM` (0.5 → 0.35), `SPAN_SIM_MIN` (0.78 → 0.85). Margin dominates observed behavior (it directly scales precision monotonically); these four shape the candidate pool and are second-order at current settings. Sweep them only if the m=4.0 rollout still under-delivers.

## Span-level arm (cross-word re-segmentation)

Span-level fixed/broke (substituted span strictly closer/farther from the aligned ref span): scene12 gated **9F/9B**, ungated 19F/36B; shaam gated 1F/7B; 1497 gated **149F/303B** (p≈4e-13 in the wrong direction), ungated 193F/404B.

- The arm **does** capture genuine re-segmentation wins the word arm can't reach — scene12 examples: `came to your` → `keep your` (ref *"That's why I **keep you** around."*), `so what is next` → `so what's next` (exact), `media their life` → `media life` (ref *"…military life…"*) — exactly the failure mode the handoff said needed real n-best alternatives.
- But **unarbitrated it breaks 2× more than it fixes on wild data**, and even on scripted footage it only breaks even. The segment gate helps (ungated is worse everywhere, and ungated introduced `love france` — a country name — into a weak shaam segment) but is not sufficient.
- **Verdict: NO-GO for shipping spans**; the P1 contract's exemption (spans generated but display_only on weak segments, never run-selected) stands. If revisited, spans need the same engine arbitration words get — none of the span candidates here were engine-judged.

## L4 overlap-neighbor layer (1497 only)

`l4_liberal` (overlap-eligible candidates + Llama-L4 decisions, `--overlap-eligible`) vs `llama_only`: **+6 pure-overlap subs, −1 displaced beam sub** (`carbon`→`carpenter` replaced by the neighbor's `carbon`→`the`). Net arm delta: +3 fixed / +0 broke / +2 neutral; the 6 overlap-evidenced subs all carried `beam_mass = 0.0` in the primary segment (pure neighbor words, overlap weight 0.94–1.0). Aggregate: 73F/57B, best ΔWER of any engine arm (−0.051pp overall).

Tiny n, but it lands exactly where [overlap_consistency_analysis.md](../../beam-search/overlap_consistency_analysis.md) predicted (green-gated neighbor precision ~50 %, ceiling ~43 words on this set; engine arbitration on top): **GO (narrow, unchanged)** — keep L4 as a green-gated *candidate layer* behind `--overlap-eligible`, engine-arbitrated, never auto-applied. Forward value is coverage on production-split long client videos (every interior segment gets two overlap windows), not this set's 0.02pp.

## Oracle upper-bound context (handoff experiment — different unit, do not read as the same metric)

The July-15 handoff's oracle viseme-snapping ([viseme_snapping_experiment.md](../../nbest_viseme_handoff/viseme_snapping_experiment.md), `snap_results.json`; OCR-extracted turns, phrase bank built **from the real scripts**, sim ≥ 0.78; scores are a threshold-binarized per-turn content-recall **proxy for judged Y+P**, MAE 7.6pp vs the documented judge): mean delta **+0.6pp**, improved 5/21 videos, regressed 1/21; best videos img_6825 **+4.0pp** (14 subs), img_6822 +3.1pp, s2_yoad_tomer_1 +3.0pp; ~40 % genuine fix / ~30 % lateral / ~30 % fabrication concentrated on weak footage.

That is the ceiling with **reference-derived** candidates: +1–4pp proxy on the strongest videos, ~0 mean. Our reference-free arms should be read against it: the ship arm's ΔRecall +0.066pp (egla) / +0.003pp (1497) and llama-m4's +0.134pp are small *because the ceiling is low* — the deliverable's value is transparent, validated correction with an audit trail, not headline movement. (Our recall numbers are raw mean per-segment content recall on real per-turn artifacts; the oracle's are OCR-turn Y+P proxy percentages — same hit machinery, different unit and text source.)

## GO/NO-GO — binding call

**Gate arithmetic on the client-package arm** (egla ship arm = scene12 + shaam, agree-mode=all):

| clause | value | pass |
|---|---|---|
| fixed ≥ 3× broke | 1 fixed / **0 broke** (scene12 2 subs; shaam 0 subs) | ✅ (trivially — no breaks) |
| ΔWER ≤ 0 overall | scene12 −0.030pp; shaam ±0.000pp | ✅ |
| ΔWER ≤ 0 touched | scene12 −6.25pp; shaam n/a | ✅ |
| zero entity/number introductions | 0/0 (independent audit) | ✅ |
| sub rate ≤ 5 % of words | 2 / 3,866 = **0.05 %** | ✅ |

**Verdict: GO.** Ship `substitutions.json` (the agreement arm) in the egla guessing-game package with the **subtle marking** already applied (U+00B0 degree sign on substituted words in V's subtitles, dotted underline + "° phonetic auto-correction" legend line in T's transcripts, README legend sentence). Both substitutions sit on `s1_tomer_yoad_1` (camera scene, #3 of the camera ranking) — if Agent F's final selection takes only the top-2 camera scenes, the package ships with zero applied substitutions and the capability is still visible through T's flagged-word hover alternatives, which ship regardless (display-only, `MASS_FLOOR_DISPLAY` cutoff).

**Honesty about n**: the gate passes on 2 substitutions. That is statistically weightless on its own; the decision leans on the mechanism evidence: (a) the agreement arm never introduced an entity/number anywhere (0 across all datasets, independent audit); (b) on 1,497 wild segments the same configuration is net-positive on every aggregate metric (ΔWER −0.007pp, ΔIS +0.0002, Δrecall +0.003pp in-sample) with 3F/2B/2N; (c) the two engines' vetoes are measurably protective (14 breaks prevented per 8 fixes lost, Claude side; the `until`→`at` break blocked, Llama side); (d) the arm is 26× below the sub-rate ceiling. What the wild set does **not** support is calling the *mechanism* 3×-safe at current calibration — 1.5× in-sample is the honest number, and scripted-dialogue context (egla) is easier for context engines than wild YouTube.

**Do NOT ship** (all NO-GO for auto-substitution, all stay available as display-only candidates): naive max-mass (breaks 2.2–11× its fixes — this arm existing in the eval is what proves the engines matter), span-level (2× breaks in the wild; needs engine arbitration before re-testing), L4-liberal auto-apply beyond its candidate-layer role, and the heuristic engine (never fires).

**Production-default recommendation (beyond this package)**: keep post-hoc substitution OFF by default on wild/unscripted content at m=2.0. The validated path to a production default is **Llama margin 4.0 nats** (3.0× fix:break, ΔWER −0.113pp, p=1.3e-4, ~115 subs/1497 ≈ 0.5 % of words) — optionally still intersected with Claude where sessions allow, and with ordinals added to the numeric gate first. Re-validate on one more wild batch before flipping any default (this sweep reuses the same 1,338 judged flags — it is threshold selection on the evaluation set; treat m=4.0 as a strong hypothesis, not a certified operating point).

## Verification

- **Baseline WER reproduction**: evaluator's 1497 MBR baseline = **63.84 %** vs the Mission-6 published 63.8 % (report.csv `wer_hyp_mbr_%` mean) — the full scoring path (texts, tokenizer, macro-mean) reproduces the known number.
- **Hand-checked classifications**: all 2 scene12 ship subs and all 7 1497 agreement subs verified against printed ref/hyp lines (this doc quotes them); 3 naive breaks and 3 span fixes spot-checked. One conservative-aligner case found and documented: `less`→`unless` (ref *"…vice versa **unless they** have been requested…"*, hyp *"…or less they've…"*) grades **neutral** because the 2:1 token merge pulls the alignment off by one — a human grades it fixed. The strict aligner under-credits fixes near contractions; it never over-credits, so gate math is safe.
- **m=2.0 sweep row == shipped llama_only** modulo the single Δ=2.00-exactly boundary flag (231 vs 230 subs; 70F/57B identical).
- **Idempotence/consistency**: every arm's `text_original` verified byte-identical to `candidates.json` `display_text`; rebuilt substituted texts cross-checked against marking-stripped `text_substituted` (assertion in the loader, zero mismatches).

## Caveats

- **Tiny egla n**: 2 subs (scene12) / 0 (shaam). The gate is applied literally as specified; the mechanism claim rests on the 1,497 evidence, not on egla counts.
- **1497 agreement is sample-limited**: Claude judged a 300-key stratified sample (of 1,338), so `ship_agree`/`claude_only` rows are within-sample; llama_only and the sweep are full-set. Full-set agreement is not computable without ~35 more in-session judging batches.
- **Llama fp16 nondeterminism**: teacher-forced deltas reproduce to ±0.03 nats run-to-run; decisions within that band of the margin can flip (one observed at Δ=2.00). Immaterial at m=4.0 for the 45F/15B conclusion (flips at the boundary are ~1–2 subs).
- **Sweep is post-hoc on the eval set** — m=4.0 is selected *using* the references; certify on fresh data before production.
- **NIV tier stratifier is top-1-anchored** (report.csv `is_score`); fine as a difficulty proxy, not an MBR-exact tier.
- **Egla absolute WER >100 %** is an anchoring artifact (turn refs vs bleed-carrying segments), affects no Δ column.
- **Oracle row unit mismatch** (OCR turns, Y+P proxy, script-derived bank) — context only, upper bound only.
- **Aligner conservatism** under-counts fixes near contractions/merges (≥1 observed of 9 agreement subs); breaks are not affected (a break requires original == aligned ref word, which merges don't fabricate).

## Reproduce

```bash
/home/ubuntu/vsp-llm-yoad-venv/bin/python scripts/pipeline/egla_kafe_substitution_eval.py \
    --datasets scene12,shaam,english_1497        # full run ≈ 15 min (IS on GPU)
# per-dataset outputs: .../substitution/<run>/eval_results.json (+ eval_arms/ artifacts)
```

Cross-references: candidate/gate contract in [phonetic_substitute.py](../../../scripts/pipeline/phonetic_substitute.py) (module docstring); engines `egla_kafe_substitution_judge.py` / `substitution_engine_llama.py`; overlap L4 rationale in [overlap_consistency_analysis.md](../../beam-search/overlap_consistency_analysis.md); n-best context in [n_best_implementation.md](../../beam-search/n_best_implementation.md); oracle bundle in [docs/nbest_viseme_handoff/](../../nbest_viseme_handoff/).

## Addendum (July 19 2026) — judge robustness battery: engine swap, test-retest, determinism

Three questions, one battery: (1) what changes if the agreement arm pairs **two Claude models
(Fable ∧ Opus)** instead of Claude ∧ Llama — same rubric, same batches, same mechanical collect
gates, no Llama; (2) is the in-session judge **repeatable** — same query, same model, different
sessions; (3) is the Llama engine **deterministic** on re-run. All runs reuse the unchanged
prepare batches and `collect` validation; decisions files sit next to the originals
(`decisions_claude_r2.json`, `decisions_claude_opus{,_r2}.json`, `decisions_llama_r2.json`;
1497: `judge/decisions_claude_opus.json`, arms + stats in `eval_arms/fable_opus_analysis.json`,
runner [analyze_fable_opus_1497.py](../../_research-tools/generators/analyze_fable_opus_1497.py)).

### Test-retest (egla, 91 judgeable flags, fresh session per run)

| pair | decision agreement | replaces (r1 vs r2) | verdict-label agreement |
|---|---|---|---|
| Fable r1 vs Fable r2 | **91/91 (100 %)** | 2 vs 2 — same words, same positions | 80/91 (87.9 %) |
| Opus r1 vs Opus r2 | **91/91 (100 %)** | 0 vs 0 | 80/91 (87.9 %) |

The replace/keep layer is perfectly stable across sessions for both models; variance lives only in
verdict *labels* on kept flags (equal ↔ worse ↔ somewhat_better relabeling). 87.9 % label
test-retest matches the March judge gold standard's 86.7 % intra-rater exact rate — that is the
noise floor of LLM verdict labeling, which the `clearly_better`-only replace gate sits above.

### Engine swap — egla (91 flags)

| pair | decision agreement | replaces | verdict labels |
|---|---|---|---|
| Fable r1 vs Opus r1 | 89/91 (97.8 %) | 2 vs 0 | 68/91 (74.7 %) |
| Fable r1 vs Llama | 80/91 (87.9 %) | 2 vs 13 | — |
| Opus r1 vs Llama | 78/91 (85.7 %) | 0 vs 13 | — |

The only two Fable–Opus disagreements are **exactly the two shipped substitutions**
(`figured→forgot`, `on→of`, both s1_tomer_yoad_1): Opus sees the same direction but rates them
`somewhat_better` / `keep` — below its "clearly better" bar (κ degenerate at 0 because Opus never
replaces on egla). **Fable ∧ Opus arm on egla = 0 substitutions** — the shipped package would have
contained no corrections. Conservatism ordering on identical evidence: **Opus (0) < Fable (2) <
Llama (13)** — the models differ in where "clearly better" begins, not in reading.

### Engine swap — wild set (1497 sample, 300 joint keys)

Opus judged the same 300-flag stratified sample Fable judged (fresh session; collect passed
300/300, 0 drops, 6 replaces vs Fable's 12).

| pair | raw agreement | κ | replaces | verdict labels |
|---|---|---|---|---|
| Fable vs Opus | 292/300 (97.3 %) | **0.543** | 12 vs 6 (5 same-word overlap) | 81.7 % |
| Opus vs Llama | 83.3 % | 0.106 | 6 vs 52 | 45.0 % |
| Fable vs Llama (§Engine agreement) | 83.3 % | 0.164 | 12 vs 52 | — |

Same-family κ=0.54 vs cross-family κ≈0.11–0.16: the two Claude models are correlated raters;
Llama is the independent one. Arms through the real apply gates (sample-only engines — compare
within this table, not to full-set rows):

| arm | subs | fixed | broke | neutral | ΔWER pp | num/ent intro |
|---|---|---|---|---|---|---|
| fable_only (`claude_only`) | 12 | 4 | 3 | 5 | −0.009 | 0/0 |
| ship (Fable ∧ Llama) | 7 | 3 | 2 | 2 | −0.007 | 0/0 |
| opus_only | 6 | 2 | 1 | 3 | −0.003 | 0/0 |
| **fable_opus_agree** | **5** | **2** | **1** | **2** | −0.003 | 0/0 |

Fable ∧ Opus is not a better arm, just a smaller one: 2F/1B vs the ship arm's 3F/2B —
indistinguishable at this n. Its 2 fixes are genuine phonetic bridges (`that→then`,
`information→inflammation`); its 1 break (`life→lifestyle`) was endorsed by **both** Claude
models — intersecting same-family judges does not filter shared failure modes, it mostly takes
the stricter model's set (5 of Opus's 6 survive). The cross-family Llama veto, by contrast,
blocked breaks Claude would have shipped (§Engine agreement). The one Opus-only replace Fable
vetoed (`to→notice`) was neutral (both wrong).

### Determinism (Llama engine)

Re-running `substitution_engine_llama.py` on the identical egla candidates file (same 4-bit NF4
quantization, same flag order, greedy teacher-forcing) reproduces **bit-identical output**: 91/91
decisions unchanged, 0 chosen-word flips, max |Δ| drift **0.0000 nats**. The ±0.03-nat caveat in
§Caveats applies across *changed invocation contexts* (the calibration-vs-eval observation), not
to like-for-like re-runs — under a pinned invocation the engine is exactly reproducible, so
`decisions_llama.json` is a stable artifact, not a sample.

### Takeaway

Repeatability is a non-issue at the decision layer (100 % test-retest for both Claude models;
Llama exact under pinned invocation). The consequential knob is **which model defines "clearly
better"**: swapping the second engine from Llama to Opus switches the egla arm off entirely
(0 subs vs the 2 shipped) and shrinks the wild-set arm 7→5 subs at the same ~1.5–2:1 fix:break
precision — strictly less output, no precision gain, because same-family judges share failure
modes (κ=0.54) while the cross-family pair is near-independent (κ≈0.11–0.16). The dual-family
agreement arm (Claude ∧ Llama) remains the shipped design.
