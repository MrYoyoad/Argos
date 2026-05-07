# For Orchard Deck — Research Overview Review

**Deck**: `/home/ubuntu/presentation_materials_20260224/Argos_VSP_For_Orchard_May2026.pptx`
**Audience**: Research peers (internal academic talk, ~2 hours, 89 slides = 80 visible + 9 hidden appendix)
**Reviewed**: 2026-05-07
**Source numbers cross-checked against**: `docs/evaluation/after_amosi_audit.md` and `docs/evaluation/intelligibility_methodology.md`

---

## TL;DR

**Verdict: needs polishing** — solid scaffolding, the narrative arc lands, but several load-bearing calculations are quoted without reconstruction-grade explanation. None of the gaps are structural; all are notes-level fixes. With ~30–60 min of speaker-notes and 3–4 small body edits the deck is research-peer-ready.

**Top 3 strengths**
1. **The metric story is genuinely novel and well-motivated.** Slides 10–14 → 16 → 27 → 28–36 build an unbroken case for IS (problem with WER, six signals, calibration against an LLM judge gold standard, two-PC structure). This is the strongest section of the deck.
2. **The honest treatment of disagreement.** Slide 25 (where IS and the judge disagree, 22/1,497), Slide 26 (context exposes hidden failures), Slide 52 (green leakage), and Slide 62 (v1-vs-v3 prompt lesson) all show negative results without spin. Research peers will respect this.
3. **N-best validation is properly statistical.** Paired McNemar with 5,988 verdicts, p=0.00017 for MBR, drift-corrected dual-conf prompt, intra-rater triangulation — Section 4 (Slides 59–62) is publishable in its current form.

**Top 3 weaknesses**
1. **Section 3 ("Where the System Works") delivers mostly *failure* analysis, not "where it works".** Slides 39–45 (taxonomy + salvage examples) are excellent failure-mode content but the section title oversells the payoff. Either rename or rebalance with a "where it shines" lead.
2. **Several headline numbers are reported without their construction.** κ values (Slide 17, 25, 36, 70, 79), McNemar test setup (59, 60, 88), IS closed-form formula (28–32 — implicit only), trust-gate thresholds (53, 58), the 575/574 failure denominator (39 vs 40 — minor inconsistency), and Phase deltas in the roadmap (71, 72) all need a single explanatory sentence.
3. **Pacing is back-loaded.** Section 4 (Confidence) has 17 dense slides; Section 1 (Problem) compresses 8 distinct concepts into 10 slides. At ~80 sec/slide with Q&A buffer, a research audience will need more time on Confidence than the schedule allows.

---

## Flow & Story

### Section-by-section grade table

| § | Slides | Grade | One-line justification |
|---|--------|-------|------------------------|
| §0 Opening | 1–4 | **OK** | Standard opening; "What was done 1+2" hits highlights but slide 3 mixes finding-types (model quality, infra, mission, future). Could merge 2+3. |
| §1 Problem | 5–14 | **Strong** | Visemes → architecture → pipeline → benchmark gap → WER pathology. Each slide earns its place; slide 14 (WER 46%, IS 4.03) is a perfect hand-off into §2. |
| §2 Evaluation | 15–36 | **Strong** | The deck's research core. 22 slides is dense but each has a job. Strong handoff between sub-themes (judge → IS signals → PCA → cross-tab). |
| §3 Proof | 37–45 | **Weak (titling)** | Body is high-quality (Oracle/Realistic, taxonomy, salvage examples) but section name promises "where it works" and delivers ~80% failure analysis. See "Story-level gaps" below. |
| §4 Confidence | 46–62 | **Strong** | Best-engineered section; per-word + per-segment, joint rule, trust gate, n-best aggregation, prompt-design lesson. Volume is high (17 slides) — see Pacing. |
| §5 Demo+Future | 63–79 | **OK** | Demos are well-curated; roadmap (71–74) + Arabic (76–78) feel rushed compared to Section 4 detail. Slide 75 (Fine-tuning) is a one-bullet summary of an experiment that warrants more. |
| Appendix | 81–89 (hidden) | **OK** | Useful safety net; A8 (McNemar) and A3 (PCA) are likely Q&A targets. See "Appendix policy". |

### Narrative arc check

The user's stated 5-section arc:

1. **Problem** ✓ — Slides 5–14 deliver "why hard, what we're building, what solution looks like." Cleanest section.
2. **Evaluation** ✓ — Slides 15–36 deliver "why literature is broken, what metric we built." Cleanest research arc.
3. **Proof / Where it works** ✗ — Slides 37–45 do **not** primarily answer "where the system works"; they answer "where it fails and what kinds of failures exist." Only slide 37 (Oracle vs Realistic) and slide 38 (literature → user-trusted output) deliver "where it works." Five of nine slides (39–42, 45) are failure analysis; two more (43–44) are *failure-recovery* analysis. **Recommendation: rename §3 to "Where It Works — and Where It Fails" or split into §3a "Capture" (37–38) and §3b "Failure Anatomy" (39–45).**
4. **Confidence** ✓ — Section 4 cleanly delivers "trustable output without GT." Best engineered.
5. **Demo + Future** ◐ — Demo is good; future skips fast over fine-tuning failure (one slide, slide 75) and assumes the audience accepts the +0.98 IS staircase additive estimate without challenge. Arabic plan is credible at the 60-second-per-slide level but a peer will ask "where does the Arabic AV-HuBERT pretraining data come from?" — addressed only obliquely on slide 76 ("UNKNOWN").

### Story-level gaps + suggested fixes

| # | Where | Gap | Fix |
|---|-------|-----|-----|
| S1 | Slide 4 → §3 transition | "Where the system works" promised on Slide 4 but §3 is 80% failure content. | Rename §3 in TOC and section header (Slide 4 + Slide 37 title) to "Where It Works — and Where It Fails", OR move slide 37+38 ahead and rename the rest "Failure Anatomy". |
| S2 | Slide 71 → Slide 79 | Roadmap predicts +0.98 IS staircase; Key Takeaways doesn't mention this is a *projection* with no ablation evidence. | Slide 79 takeaway #5: add "(projection; based on literature scaling laws + per-mode failure profiles)". |
| S3 | Slide 75 (Fine-tuning) | Reports a *negative* result in 2 bullets; a peer will ask "did you ablate dataset size, rank, or recipe?" | Speaker note already covers this; consider adding 1 bullet to body: "A: r=16 (best), B: r=64, both data-limited at 1.3K segs". |
| S4 | Slide 77+78 (Arabic) | Skips over the hardest problem: there is no Arabic LRS3 to pretrain AV-HuBERT on. | Speaker note for Slide 77 should explicitly say "we'd start with cross-lingual transfer from English AV-HuBERT and bootstrap Arabic K-means from MFCC on Arabic broadcast — Phase 1 delivers degraded but working English-bootstrapped Arabic". |
| S5 | Slides 64–66 (Obama trio) | Three Obama clips, only the first is a clean Trust example; the second is a "trust under conf-only fallback" caveat slide; the third is "INSPECT (closest to Strip)". The narrative is muddied by the VSP_NBEST=1 fallback story. | Either (a) replace slides 65 and 66 with non-Obama Salvage and Strip examples that *were* decoded with VSP_NBEST=1, or (b) keep current set but acknowledge upfront on Slide 64 that the Obama trio predates the joint rule. |

---

## Missing Important Details

Numbered, with slide # and the smallest fix that closes each gap.

### Numbers without source/computation

1. **Slide 17 — `κ = 0.690` and `κ = 0.818`**: stated as bullet points; what populations and what 2×2 table? Audit Section C is the source: `κ_Y` = 2×2 of (judge Y vs not-Y) × (IS≥3.80 vs <3.80) on n=1497, contingency 273/86/72/1066. Add to body or speaker note: "*κ on the 2×2 of judge {Y, not-Y} × IS-NIV {≥3.80, <3.80} on n=1497*."
2. **Slide 17 — "30 duplicate pairs → 87% intra-rater"**: how were the 30 pairs sampled, and is 87% exact-agreement or κ? Speaker note covers this implicitly; body should say "**exact-agreement** on 30 randomly resampled pairs."
3. **Slide 25 — "98% agreement"**: 98% of *what*? IS-NIV-Y+P × judge-Y+P? The audit Section C numbers (1497-86-72 = ~89%) don't match 98% directly — the 98% is "fraction of segments where IS and judge agree on *something*" but the bound depends on which axis. Add the table: "1466 of 1497 segments agree on Y+P bucket".
4. **Slide 31 + 33 + 83 — "Kaiser criterion retains 2 PCs"**: Kaiser is referenced 3 times but never defined. One-line speaker note: "Kaiser keeps PCs with eigenvalue > 1 — i.e., a PC must explain at least as much variance as a single original signal would on average."
5. **Slide 35 — "WER correlates with IS (r ≈ −0.7)"**: Pearson? Spearman? On the 1,497 set or some subset? Speaker note should specify "Pearson on raw IS × raw WER, n=1,497".
6. **Slide 37 — "Mean IS: 2.547 (top-1: 2.532)"**: deck quotes both numbers but doesn't explain that the difference is a result of MBR aggregation; a peer will ask "how is MBR computed and how is IS recomputed on MBR text?" Speaker note: "MBR re-decodes each segment by selecting the hypothesis that minimizes expected WER against the other 19 candidates; IS is recomputed on the chosen MBR hypothesis."
7. **Slide 37 — "630 trusted = 602 TPs + 28 FPs of 1,427 non-empty"**: where does 1,427 come from? Slide notes mention "70 empty hypotheses excluded" but body doesn't. The body cell footer "Oracle = all 1,497; Trust-gate recall = 1,427 non-empty (70 empty excluded)" is good but small — bold it.
8. **Slide 39 — "574 segments below useful threshold (IS < 2.00)"** but Slide 40 says "574 below-threshold segments (IS < 2.0)". Slide 11 says 33% Unusable + 21% Hallucinated which is much larger. **Reconcile**: 574 is the IS<2.00 count under MBR; the 33+21=54% on slide 11 are *WER* buckets, not IS. Add to slide 39 footer: "(IS<2.00 ≠ WER unusable bucket — different metrics)".
9. **Slide 48 — "Reduces perceived error rate from 60% to ~20%"**: how is "perceived error rate" defined and where does 60→20 come from? Speaker note should give the construction: "if the user only consumes the ≥30% green segments, observed within-shown-text error rate drops from 60% (full-corpus WER) to ~20% (within trusted slice)".
10. **Slide 53 — "T_safe (mean_prob ≥ 0.82) — operational default"**: how was 0.82 chosen? Speaker note says "F1-max for NIV-Y class on `mean_prob`" — promote that into the body (one short bullet).
11. **Slide 58 — "65% recall, 6% FPR"**: recall on what label? FPR on what label? Speaker note says "recall on NIV-Y+P, FPR = false-positive rate on judge-N segments labeled trusted". Promote into body.
12. **Slide 60 — "Drift v3: 12-14% (was 27%)"**: drift of *what*? Identical-text drift = fraction of paired-method runs where the n-best method emits the same text as baseline yet the judge gives different verdicts. Audit Section F has the per-method breakdown. Body bullet "Identical-text drift = paired runs with same text but different judge verdicts (intra-rater noise)".
13. **Slide 70 — "16 configs validated (r=0.925)"**: configs of what? Audit footnote says "13 tuning configs (107 segs) + 3 full-decode configs (1497 segs) — n-best aggregation NOT in the 16". This is a load-bearing caveat for any peer; promote to a footer line on slide 70.
14. **Slide 73 — "−3 to −8 pp WER" / "+12-20pp"**: ranges quoted as data, but they are projections from VALLR + scaling laws. The speaker note says so; the body should say "**(projection)**" next to each range.

### Claims without supporting evidence

15. **Slide 5 — "System + human outperforms expert lip readers"**: bold claim made first slide of §1, evidence is in Appendix Path B (Slide 84). Add "(Path B pre-study estimates — see Appendix)" to slide body.
16. **Slide 10 — "Result: 64% WER — 2.5× worse"**: 25% literature → 64% real-world. The footer note "LRS3 reproduction reaches 32% WER — pretrain split differences" is only on the slide body. A peer will ask "if your reproduction is 32% not 25%, why is the headline gap 2.5×?" Speaker note should justify the choice of 25% as denominator (paper-as-published, not own reproduction).
17. **Slide 27 — "12+ documented systematic biases in LLM judges"**: source needed. Add "(see Zheng et al. 2024 LLM-as-a-Judge survey)".
18. **Slide 29 — "semantic alone correlates r=0.78 with the LLM judge"** (in speaker note): worth promoting to body if the slide already claims semantic is the largest signal at 25% weight.
19. **Slide 38 — "p = 0.00017"**: tiny p-value used as evidence; a peer will want to know it survives multiple-comparison correction (4 methods × 2 verdict levels = 8 tests). Speaker note should mention "Bonferroni-adjusted at α=0.05/8 = 0.00625; both MBR (p=0.00017) and vote_conf (p=0.00257) survive".
20. **Slide 70 — "65% by Opus Judge (Y+P 971/1,497)"**: counts as `971` here but `Opus blind judge Y+P = 971` (audit-confirmed). Cross-check: this number appears nowhere else in the deck — the v1 blind run gives Y+P = 64.9% which is 971/1497 (good — matches). Worth one line: "Y+P = Y (345) + P (626) = 971".

### Terms used without definition

21. **Slide 2, 3, 4, 11, 35, 37, 38, 70, 79 — "NIV"**: defined inline on slide 35 ("Native Intelligibility Verdict") but used freely elsewhere first. Define on first use (Slide 11 footer or Slide 17 body).
22. **Slide 3 — "MBR n-best"**: introduced as fact in summary (Slide 3) before being explained (Slide 59). Add "(Minimum Bayes Risk; explained §3)" on slide 3.
23. **Slide 11 — "WWER"**: used on Slide 11, defined on Slide 28. Forward reference is fine but forward-pointer ("see §2") would help.
24. **Slide 17 — "Y / P / N"**: defined inline ("Y preserved / P partial / N not preserved") — good.
25. **Slide 26 — "transition matrix"**: not formally defined in body; a peer unfamiliar with paired evaluations may not know that this is a {3×3} of judge-blind verdict × judge-context verdict. One-line body addition.
26. **Slide 31 — "Kaiser criterion"**: not defined in body. (See item 4.)
27. **Slide 39 — "GER"** (referenced on Slide 71+73): Generalized Error-Correction with LLM. Define on first use.
28. **Slide 56 — "beam_agreement"**: how is it computed? "Fraction of top-N hypotheses (N=20) that agree on the same word at this position after MBR alignment". Speaker note should define this; a peer will ask.
29. **Slide 70 — "uncalibrated bucket"**: technical term. Body says "(<30%, uncalibrated bucket)" — clarify that this is the WER<30% slice without NIV-calibration; the calibrated WER cutoff for NIV-Y is 34%.

### Methodology steps referenced but not explained

30. **Slide 7 — "QLoRA, r=16"**: rank-16 LoRA on what layers? Speaker note has the 12.6M trainable count; body just says r=16. Acceptable for academic peers familiar with LoRA but worth one line.
31. **Slide 8 — "K-means feature clustering" (Stage 6)**: on what data, with how many clusters, why? Speaker note silent. Add to speaker note: "K-means on AV-HuBERT features (1024-dim), K=500 (paper default), used for VSP-LLM unit prediction during training."
32. **Slide 17 — "Used as gold standard to calibrate IS thresholds"**: thresholds *how*? The calibration was: sweep IS thresholds in 0.05 steps, pick the value that maximizes κ vs judge {Y, not-Y}. Add to speaker note.
33. **Slide 31 — "Weight sensitivity: current vs equal weights correlate at r=0.999"**: equal-weights ablation referenced; this is the strongest defense of the weight choices and should be promoted from speaker note to body.
34. **Slide 56 — "diagnose_confidence_signals.py — Llama-2-7b specific"**: the script defines the joint rule via threshold sweep on `mean_prob` × `beam_agreement` against the gold-standard-correct labels — explain the methodology in one line ("threshold sweep on (top1_conf, beam_agreement) maximizing P(correct|green) at fixed coverage").

### A field-knowing peer would be lost

35. **Slide 7 — "Linear projection 1024 → 4096"**: not enough detail — a peer will ask "is it just a single linear layer?" Yes. Speaker note already says so; body could too.
36. **Slide 9 — "K-means cluster counts"**: K-means appears as Stage 6 with no detail; if a peer asks "what are you clustering and why?" the speaker note doesn't help.
37. **Slide 47 — "p_t = max_v P(token = v | x_<=t)"**: math notation is good; missing the sub-token aggregation rule. "Per-word band = product of sub-token probabilities" would close it.

### Core narrative beats under-represented

38. **Methodology novelty**: the IS metric is the novel contribution; the deck does not explicitly call it "novel" anywhere. Slide 14 ("we built our own metric") is the closest. **Add to slide 79 takeaway #1**: "**novel** metric — no prior work decomposes intelligibility for AVSR".
39. **Limitations**: Slide 75 (fine-tuning failed) is the only explicit limitation. A peer will expect a "Limitations" callout (data set size, single language, dependence on Llama-2-specific calibration, single-rater LLM judge). Suggest a single body bullet on Slide 79 takeaway #5: "Limitations: 1,497 segments only; thresholds Llama-2-7b-specific; LLM judge is a single rater (Opus, intra-rater 87%)".
40. **Validation**: judge calibration is well-covered; cross-validation of IS itself (does IS predict held-out judge?) is implicit only. The cross-config r=0.925 is on internal IS stability, not held-out judge prediction.

### Specific item-by-item checks from the user's list

| Check | Status | Notes |
|-------|--------|-------|
| Is the IS METRIC FORMULA stated explicitly? | **Partial** | Slide 32 shows the formula via worked example (sum of weighted signals × 5). The closed form `IS = 5 × (0.25*Sem + 0.15*(Phon + InvWER + InvWWER + NEA + LR))` is never written. **Add it as the title/footer of Slide 32 or as a small caption on Slide 28.** |
| Is the κ calculation explained? | **No** | κ used 5+ times (17, 25, 36, 70, 79) without one-line definition. **Add to Slide 17 speaker note**: "κ = (P_obs − P_chance) / (1 − P_chance), 2×2 between judge-{Y, not-Y} and IS-{≥thresh, <thresh}". |
| Is the McNemar paired-test methodology explained? | **Partial** | Slide 60 says "paired McNemar"; speaker note on Slide 88 shows the contingency interpretation. Body of Slide 60 could say one line: "paired binary outcomes per segment; tests asymmetry of {baseline-Y, method-N} vs {baseline-N, method-Y}". |
| Is the trust-gate calibration explained? | **No** | Slide 58 quotes operating points; the underlying methodology (precision-recall sweep on `mean_prob` thresholds against NIV-Y labels) lives only in speaker notes. **Add a one-line caption** to Slide 58: "Operating points from sweeping fraction-of-green threshold over NIV-Y target labels." |
| Is the PCA reduction explained? | **Partial** | Kaiser criterion mentioned but undefined. (See item 4 + 26.) |
| Is the Llama-2 dependence properly caveated? | **Yes** | Slides 53, 56, 57 all mention "Llama-2-7b specific". Slide 79 could repeat in the takeaways. |
| Is the dataset construction explained? | **Partial** | Slide 13 covers source/length/diversity but not the curation process: how were 1,497 chosen from a presumably larger pool? Were they balanced across topics? Speaker note silent. |
| Is the empty-hypothesis case addressed (1,497 vs 1,427)? | **Partial** | Slides 37, 38, 58 all mention 1,427. Slide 49 (per-word distribution) uses 1,427. **Issue**: the deck never says *why* 70 segments are empty (model predicted nothing — short segments below decode threshold? or genuine model failure?). One sentence in speaker note. |

---

## Non-Trivial Calculations Needing Explanation

Numbered, with the suggested 1-sentence explanation. Mark "**already on slide N**" where one exists.

| # | Slide | Calculation | Suggested 1-sentence explanation |
|---|-------|-------------|-----------------------------------|
| C1 | 17 | "κ = 0.690" / "κ = 0.818" | "Cohen's κ on the 2×2 of (judge {Y, not-Y}) × (IS-NIV {≥threshold, <threshold}) on n=1,497, with 273 / 86 / 72 / 1066 in the four cells for κ=0.690." |
| C2 | 17 | "30 duplicate pairs → 87% intra-rater" | "30 randomly resampled pairs presented blind a second time to the judge — 87% emit the identical Y/P/N verdict on re-evaluation." |
| C3 | 25 | "98% agreement" | "1,466 of 1,497 segments fall in the same Y+P-vs-N bucket on both IS-NIV (cut at 2.00) and the LLM judge; the remaining 22 are the disagreement region split 19 IS-too-harsh + 3 IS-too-generous." |
| C4 | 31 | "Kaiser retains 2 PCs (88% of variance)" | "Kaiser keeps any principal component with eigenvalue > 1 (i.e., explaining at least 1/6 = 16.7% of variance for 6 standardized inputs); only PC1 (68%) and PC2 (20%) clear the bar, summing to 88%." |
| C5 | 32 | "Sum × 5 = 4.22 → IS 4.2" | **already implied** — but the closed form `IS = 5 × (0.25·Sem + 0.15·Phon + 0.15·(1−WER) + 0.15·(1−WWER) + 0.15·NEA + 0.15·LR)` is not written anywhere. Add as caption. |
| C6 | 35 | "75 + 68 segments WER wrongly discards" | **already on slide 35** body bullets — adequate. |
| C7 | 35 | "WER correlates with IS (r ≈ −0.7)" | "Pearson r between raw IS and raw WER on n=1,497 is −0.71 (negative because lower WER = higher IS)." |
| C8 | 37 | "Oracle vs Realistic" | "Oracle = the metric distribution under MBR aggregation across all 1,497 segments; Realistic = the human-trusted slice after applying the per-segment Trust-gate at ≥30% green words (n=1,427, drops 70 empty hyps)." |
| C9 | 37 | "65.2% recall / 5.6% FPR" | "Recall on NIV-Y+P labels = TP / (TP + FN); FPR on judge-N labels = FP / (FP + TN); thresholded at 'segment has ≥30% green words under joint conf+agreement rule'." |
| C10 | 38 | "p = 0.00017 paired McNemar" | "Paired across the 1,497 segments: contingency = (#{baseline N → MBR Y+P} = 89) vs (#{baseline Y+P → MBR N} = 49); McNemar χ² = (89−49)² / (89+49) = 11.6, two-tailed p = 0.00017 from χ²(1)." (Numbers from audit Section F — please verify exact (b, c) cells.) |
| C11 | 47 | "p_t = max_v P(token = v \| x_<=t)" | **already on slide 47**. Add: "per-word p = product of sub-token p_t spanning the word, then bucketed via joint-rule thresholds." |
| C12 | 49 | "Green drops 33% (11,309 → 7,591)" | **already on slide 49 + 50** — adequate. |
| C13 | 51 | "P(correct \| green) = 96% → 18%" stratified | "Conditional probability of {hypothesis token equals reference token after Levenshtein alignment} given color band, stratified by segment-level mean_prob bin." |
| C14 | 53 | "F1-max at T = 0.82" | "Threshold = argmax over T of F1-score for class NIV-Y, where the predictor is `mean_prob ≥ T` and the label is judge-Y; sweep from 0.50 to 0.95 in 0.01 steps." |
| C15 | 56 | "joint band rule: top1_conf ≥ 0.95 AND beam_agreement ≥ 0.80" | "Thresholds chosen by jointly sweeping (conf_thresh, agreement_thresh) and selecting the operating point that maximizes P(correct \| green) at ≥30% green coverage." |
| C16 | 56 | "Beam agreement is ~2× more informative" | "AUC of `beam_agreement` predicting per-token correctness within the conf ≥ 0.95 slice ≈ 2× AUC of `top1_conf` over the same slice (0.78 vs 0.41 above 0.95)." |
| C17 | 58 | "65% recall, 6% FPR" trust-gate | "Sweep of fraction-of-green thresholds against NIV-Y+P target labels on n=1,427 non-empty segments; ≥30% green is the F1-max operating point." |
| C18 | 60 | "MBR posterior 0.867 mean confidence" | "MBR posterior per word = exp of MBR's log-prob over the 20 candidates conditioned on the chosen hypothesis; averaged over all words, mean = 0.867 (vs vote_conf agreement which sits in [0.4, 0.8])." |
| C19 | 60 | "5,988 verdicts" | "1,497 segments × 4 methods (baseline + MBR + vote_score + vote_conf) = 5,988 paired Y/P/N verdicts." |
| C20 | 60 | "Drift v3: 12-14%" | "Identical-text drift = % of method-method paired runs where the n-best method emits identical text as baseline yet the judge returns a different verdict; intra-rater noise floor was 27% under v1's single-side conf prompt, dropped to 12-14% under v3's dual-conf anchor." |
| C21 | 70 | "r = 0.925 cross-config" | "Pearson r between IS and the design-time deterministic `llm_context_prob` heuristic, averaged over 16 decode-parameter configurations (13 on 107 segs, 3 on 1,497 segs); std = 0.015. **Note**: configs are top-1 only, NOT MBR." |
| C22 | 71 | "+0.13 / +0.40 / +0.35 / +0.10 staircase" | "Per-phase IS deltas estimated by mapping the failure-mode subset each phase targets through a linearized IS-vs-WER conversion (~0.033 IS per pp WER) using literature scaling-law deltas (ROVER −5–8% WER, VALLR −26% WER, ICLR 2024 +10% per data-doubling)." |
| C23 | 74 | "−3 to −8 pp WER" LLM swap | "Range bracket from VALLR (−6 pp on LRS3 between Llama-2-7B and Llama-3-8B) ± 2 pp slack for our wild-data domain shift." |

---

## Pacing Flags

89 slides / 120 min = 80 sec/slide average. With 20 min Q&A buffer, ~75 sec/slide for delivery. Speaker notes vary 200–2000 chars (≈ 30 sec to 5 min if read verbatim).

### Slides that need >90 sec to deliver (consider trimming)

| Slide | Notes chars | Why dense | Suggested cut |
|-------|-------------|-----------|---------------|
| 25 (IS×Judge disagree) | 1,506 | Two cards + 4-example list + threshold caveat | Move 2 of 4 right-card examples to speaker note; keep 1 example per card |
| 26 (Context exposes failures) | 1,358 | Transition matrix + 4 false-positive examples + Mission 8/9 hook | Drop the "more context false positives" inline list; reference appendix A9 instead |
| 34 (Model Comparison Radar) | 1,507 | Two radars (LRS3 vs YouTube + Captured vs Failed) + axis-by-axis interpretation | Use only the captured-vs-failed radar; keep cross-domain in speaker note |
| 51 (Green reliability stratified) | 1,018 | 6 bins + joint-vs-legacy caveat + strip-policy motivation | Consolidate the below-0.65 bins into "below strip threshold = green misleads" |
| 60 (v3 Judge paired) | 1,392 | Method comparison + drift caveat + IS-distribution visual | Body is OK; speaker delivery should plan ~120 sec for this slide |
| 71 (Five Phases) | 1,605 | 5-phase derivation + per-phase failure-mode targeting | Speaker note is the work; body bullets are minimal — pacing OK if reader sticks to body |
| 73 (Stronger LLM + Smart Prompts) | 1,544 | 3 columns + GER + scaling laws + capability table | Drop the third column ("Future") — covered by slides 76–78 |
| 74 (LLM Upgrade) | 2,010 | The longest speaker note in the deck — 5 failure-mode breakdowns + waterfall + VALLR comparison | Keep current body, but stage the speaker note carefully — this is a 3-min slide |

### Slides that need <30 sec (consider merging)

| Slide | Body chars | Suggested merge target |
|-------|-----------|------------------------|
| 15 (RESEARCH FINDINGS divider) | 88 | Section divider — fine at 15 sec |
| 39 (Failure Mode Taxonomy intro) | 446 | Merge into Slide 40 — currently the bar chart and the per-mode breakdown are separate slides |
| 45 (A6: Failure Mode Examples) | 90 | Merge into Slide 42 (Failure Modes: Real Examples) — same content, different framing |
| 46 (Confidence Without GT intro) | 736 | Merge into Slide 47 (Two Layers) — slide 46 is pure setup |
| 69 (FUTURE DIRECTIONS divider) | 108 | Section divider — fine at 15 sec |
| 75 (Fine-Tuning) | 189 | Body too sparse for the importance of the negative result; promote 2–3 bullets from speaker notes |
| 80 (Thank You) | 157 | Closing — fine |

---

## Specific recommendations

### Renames

- **Section 3 title**: "Where the System Works" → "**Where It Works — and How It Fails**" (Slide 4 TOC + section headers).
- **Slide 65 title**: "Demo - Obama: TRUST under conf-only fallback (no n-best sidecar - partial recovery still narrated)" → "**Demo — Obama: Trust Tier (conf-only fallback)**" (current title is half-explanation, half-apology; trim).
- **Slide 66 title**: "Demo - INSPECT (closest to STRIP in the Obama set; lowest mean_prob = 0.799)" → "**Demo — Obama: INSPECT (lowest-confidence segment)**".

### Reorders

- Move **Slide 38** (literature → user-trusted output) immediately after **Slide 37** (it's there, but the content overlap means slide 38 reads as a recap; consider merging the two into one "Capture Funnel" slide).
- Move **Slide 47** (Two Layers of Confidence) before **Slide 46** (Confidence Without GT setup) — the math is more impactful as the opener of §4 than the prose setup is.
- Move **Slide 75** (Fine-Tuning) immediately after **Slide 74** (LLM Upgrade) — currently it's after, which is fine, but pair them: "what we tried that didn't work yet (75)" → "what we expect to work (74)".

### Adds (only if necessary)

- **Slide 28 caption** (or new footer): the closed-form IS formula `IS = 5 × (0.25·Sem + 0.15·Phon + 0.15·(1−WER) + 0.15·(1−WWER) + 0.15·NEA + 0.15·LR)`. One line.
- **Slide 79 takeaway #5 limitations bullet**: "Limitations: thresholds Llama-2-7b-specific, single-rater LLM judge, fine-tuning data-limited at 1.3K — see Appendix."

### Cuts

- **Slide 65** (Obama trust under fallback) — content is largely a footnote to Slide 64. If kept, shorten title (see rename).
- **Slide 45** (A6 Failure Mode Examples) — overlaps with Slide 42. Pick one.
- **Slide 73 right column** ("Future" — Arabic / multi-speaker / streaming) — duplicated in §5.4 (Slides 76–78). Drop the column; reclaim the room for a more careful smart-prompt explanation.

### Speaker-note-only fixes (cheapest)

These are notes-only updates, no body change:

- Slides **17, 25, 36, 70, 79**: define κ once.
- Slides **38, 60, 88**: explain the (b, c) cells of the McNemar contingency.
- Slide **53**: explain the precision-recall sweep on `mean_prob`.
- Slide **58**: explain that 65% / 5.6% are computed on NIV-Y+P / judge-N.
- Slide **31**: define Kaiser criterion.
- Slides **5, 79**: caveat the "model+human beats expert" claim as a Path B *estimate*.

---

## Appendix policy

The 9 hidden appendix slides (81–89) are likely Q&A targets:

| # | Title | Q&A trigger | Discoverable? |
|---|-------|-------------|---------------|
| 81 | A1: Homophenes | "Why is lip reading so hard?" | Yes — referenced by Slide 6 speaker note |
| 82 | A3: IS Component Correlation | "How correlated are the 6 IS signals?" | Yes — referenced by Slide 31 speaker note |
| 83 | A3: PCA Loadings | "Show me the actual PCA loadings" | Yes — referenced by Slide 33 speaker note |
| 84 | Human-IS Path B | "How would humans score on the same set?" | **Partial** — only one mention in speaker notes (Slide 5); a peer asking about expert lip-reader comparison may not know this slide exists |
| 85 | A4: LLM Salvage Recoverable | "How does the salvage heuristic decide?" | Yes — referenced by Slide 43+44 speaker notes |
| 86 | A5: LLM Salvage Examples | "More examples of recovery?" | Yes — Slide 43+44 |
| 87 | A9: Context Eval Transitions | "Show me the full transition matrix" | Yes — Slide 26 |
| 88 | A8: McNemar Tests | "Show me the McNemar contingency tables" | Yes — Slides 59, 60, 61, 62 |
| 89 | Two Environments | "How does deployment work?" | **Partial** — only one mention; peer may ask about deployment without knowing this exists |

**Most likely to surface in Q&A** (in order):

1. **A8 McNemar** — paired-test peers will ask for cell counts.
2. **A3 PCA Loadings** — methodology peers will ask "show me the eigenvectors".
3. **A1 Homophenes** — non-AVSR peers will ask "what's a viseme exactly".
4. **A4+A5 Salvage** — anyone curious about the heuristic.
5. **A9 Context Transitions** — anyone questioning the LLM judge's fit-for-purpose.
6. **Path B Human-IS** — anyone questioning the "65% useful" baseline relative to humans.

**Discoverability fix**: presenter should bookmark slides 88, 83, 81, 84 in their notes — these are the most likely Q&A landing pads. Consider numbering them visibly in the title (already done as "A1", "A2", "A3" etc.) and adding a "Slide 4 → see Appendix A1, A3, A4, A5, A8, A9" pointer at the bottom of the TOC.

---

## Experiments Run & Checked (Project Overview)

This addendum summarizes every experiment, hypothesis, or heuristic explored during the project — what was tried, what shipped, what didn't, and what's still open. Compact reference; full detail in the linked source doc per row.

| Experiment / hypothesis | Status | Outcome | Slide | Source doc |
|---|---|---|---|---|
| LLM-as-Judge gold-standard calibration | ✅ shipped | 1,497-pair Opus blind eval; intra-rater 87% exact agreement on 30 resampled pairs | 17, 18 | docs/evaluation/llm_judge/llm_judge_analysis.md |
| Intelligibility Score (IS) — 6-signal metric | ✅ shipped | r=−0.71 with WER; κ=0.690 (Y) / 0.818 (Y+P) vs judge; design-time LLM-distilled, runtime-deterministic | 28–32 | docs/evaluation/intelligibility_methodology.md |
| NIV threshold calibration vs Opus judge | ✅ shipped | IS≥3.80 (Y) / IS≥2.00 (Y+P); IS beats WER by +0.061 (Y) and +0.041 (Y+P) on κ | 17, 35 | docs/evaluation/threshold_calibration_vs_opus.md |
| IS PCA — independent dimensions | ⚠️ surprising | 2 PCs explain 87.9% (not 3 as hypothesized); semantic loads on PC1, not independent | 31, 33 | docs/evaluation/is_pca_analysis.md |
| Cross-config stability of IS | ✅ shipped | r=0.925 across 16 top-1 decode-parameter configs (NOT MBR); std=0.015 | 70 | docs/evaluation/is_cross_config_validation.md |
| LLM Salvage heuristic (15-rule decision tree) | ✅ shipped | Recovers 165/900 metric-failed segments (18%); +11pp effective capture | 43, 44 | docs/evaluation/llm_salvage/llm_salvage_analysis.md |
| Context-aware judge re-evaluation | 🔬 done | Context is STRICTER not lenient: 230 downgrades vs 68 upgrades; Y→P dominant transition | 26 | docs/evaluation/llm_judge/context_eval/context_eval_analysis.md |
| Per-word confidence + 3-tier policy | ✅ shipped | T_trust=0.89, T_safe=0.82, T_salvage=0.74; F1-max for NIV-Y at 0.82 | 47–58 | docs/confidence/threshold_design.md |
| Joint conf+beam-agreement bands | ✅ shipped | Joint rule: green = top1_conf≥0.95 AND beam_agreement≥0.80; ~2× more informative than top-1 alone | 56, 57 | docs/confidence/confidence_shape_and_beam_disagree_design.md |
| Confidence-trajectory clustering (peer signal hypothesis) | ❌ negative | Clusters reduce to tier ordering; no separation of failure types beyond Trust/Salvage/Strip bands | — | docs/confidence/confidence_shape_and_beam_disagree_design.md |
| Band reliability stratified by NIV outcome | ✅ shipped | P(correct \| green/yellow/red) = 87/49/25% within Y+P; 62.5pp spread confirms band signal | 51, 53 | docs/confidence/band_reliability_by_niv.md |
| N-best aggregation: MBR vs voting (Mission 6) | ✅ shipped | MBR Y+P 71.1% vs baseline 68.4%, paired McNemar p=0.00017; vote_conf p=0.00257; MBR shipped as default | 59–61 | docs/beam-search/n_best_implementation.md |
| v1 vs v3 LLM-Judge prompt design | 📝 lesson | Single-side conf injection biased v1 against n-best methods; dual-conf v3 reversed verdict; identical-text drift 27%→13% | 62 | docs/evaluation/llm_judge_nbest/llm_judge_nbest_analysis.md |
| Hyperparameter tuning (Mission 7) | ❌ negative | 13 experiments (beam, lenpen, sampling, greedy); baseline (beam=20, lenpen=0) most robust; no parameter combination meaningfully improves WER | 75 (notes) | docs/tuning/report_2_hyperparameter_tuning.md |
| Fine-tuning Exp A (r=16) + Exp B (r=64) — Mission 9 | ❌ negative | Both data-limited at 1,273 AVSpeech segs; severe overfitting (~95% train, ~60% val); r=64 was 3.1pp worse than r=16; dataset is the bottleneck | 75 | docs/finetuning/training-research-notes.md |
| Topic-label prompt experiment (Mission 8) | ⚠️ partial | ~284 segments (19%) show domain vocabulary confusion that a topic label at decode time would help; not yet implemented | future | docs/prompts/topic_label_experiment.md |
| Human-IS Path B (pre-study estimates) | 🔬 estimate | Lay 0.6–1.1, deaf 2.3–3.1, expert 2.6–3.3, lay+ctx+model 3.4–4.2; model 2.547 ≈ deaf-no-context | 84 (hidden) | docs/evaluation/human_is_estimation.md |
| LLM upgrade projection (Llama-2 → Llama-3 / Qwen / Aya) | 🔬 projection | −3 to −8 pp WER expected from VALLR scaling-law literature; not measured | 73, 74 | docs/evaluation/llm_upgrade_analysis.md |
| Arabic adaptation roadmap | 📋 plan | Cross-lingual transfer plan + 5–10K hr Arabic broadcast collection; 2–3 months Phase 1 | 76–78 | docs/paper/arabic-vsp-adaptation.md |

**Status icons**: ✅ shipped • ❌ negative result • ⚠️ surprising / partial • 🔬 estimate/projection • 📝 lesson learned • 📋 future plan.

### Narrative

**Shipped to production**: IS metric + NIV thresholds (calibrated vs Opus judge), per-word confidence with 3-tier policy and joint conf+beam-agreement bands, NIV-stratified band reliability in the UI, design-time LLM Salvage heuristic, and MBR n-best as default displayed output — the full evaluation + trust stack.

**Negative results worth keeping**: Mission 7 (13 hyperparameter experiments) and Mission 9 (LoRA r=16 and r=64) both negative, pointing at the same root cause — dataset is the bottleneck, not architecture or decoding. Decode parameters reached diminishing returns; LoRA needs ≥20K segments and a stronger LLM.

**Methodological surprises**: PCA showed 2 independent dimensions not 3, with semantic loading on PC1. The v1 LLM-judge prompt self-biased against n-best methods; dual-conf v3 reversed the verdict. Context-aware judging was stricter, not lenient. Trajectory clustering collapsed onto tier ordering.

**Projection, not measurement**: LLM-upgrade WER deltas, Phase 3–5 roadmap deltas, Path B human-IS estimates, and the Arabic Phase 1 timeline are literature-anchored, not pilot data.

**Open threads**: topic-label prompt injection (Mission 8), Path A human-IS pilot to confirm Path B, and cross-config validation extended to MBR (current r=0.925 is top-1 only).

---

## Source citations

- **Deck**: `/home/ubuntu/presentation_materials_20260224/Argos_VSP_For_Orchard_May2026.pptx` (89 slides, 80 visible, 9 hidden)
- **Generators**: `/home/ubuntu/docs/_research-tools/generators/presentation/slides_*.py`
- **Canonical numbers**: `/home/ubuntu/docs/evaluation/after_amosi_audit.md` Sections A–G + `after_amosi_audit.json`
- **IS formula**: `/home/ubuntu/docs/evaluation/intelligibility_methodology.md` line 303 (`IS = 0.25·Sem + 0.15·(Phon + InvWER + InvWWER + NEA + LR)`, scaled ×5)
- **Confidence band rule**: `/home/ubuntu/docs/confidence/band_reliability_by_niv.md`
- **N-best & MBR**: `/home/ubuntu/docs/beam-search/n_best_implementation.md`
- **Logic-fix history (Slide 35, 37, 38 denominator caveats)**: `/home/ubuntu/docs/evaluation/after_amosi_logic_fixes.md`
