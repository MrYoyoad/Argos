# Argos VSP `AFTER_AMOSI_May2026.pptx` — Must-Fix Numbers (Pre-Commit)

_Generated 2026-05-06. Rank-ordered: title-shape > hot-slide body > body > notes._


All fixes flip a *top-1* number to the *MBR-default* number from `after_amosi_audit.json`.


## High-Priority Fixes (body / hot slides)

### 1. Slide 10 — `shape[4]/para[2]`

- **Current text**: `• Result: 64.1% WER — 2.5× worse`
- **Token**: `64.1%` (shadows `wer_top1`)
- **Replace with**: `63.84%` — _MBR mean_wer = 63.84% (top-1 was 64.05%)_

### 2. Slide 11 — `shape[2]/para[0]`

- **Current text**: `64.1%`
- **Token**: `64.1%` (shadows `wer_top1`)
- **Replace with**: `63.84%` — _MBR mean_wer = 63.84% (top-1 was 64.05%)_

### 3. Slide 70 — `shape[7]/para[0]`

- **Current text**: `• 61.6% useful output (IS ≥ 2.00)`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_

### 4. Slide 70 — `shape[9]/para[0]`

- **Current text**: `The gap is real — but WER dramatically overstates failure. 61.6% useful by IS (Y+P), 64.9% confirmed by Opus-as-a-Judge.`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_

### 5. Slide 72 — `shape[6]/para[0]`

- **Current text**: `IS 2.52  •  61.6% useful (Y+P)`
- **Token**: `2.52` (shadows `is_mean_top1`)
- **Replace with**: `2.547` — _MBR is_mean = 2.547 (top-1 was 2.532)_

### 6. Slide 72 — `shape[6]/para[0]`

- **Current text**: `IS 2.52  •  61.6% useful (Y+P)`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_

### 7. Slide 72 — `shape[19]/para[0]`

- **Current text**: `Conversion: ~0.033 IS per pp WER (empirical: 2.52@64% → ~3.81@25.4%).`
- **Token**: `2.52` (shadows `is_mean_top1`)
- **Replace with**: `2.547` — _MBR is_mean = 2.547 (top-1 was 2.532)_

### 8. Slide 79 — `shape[5]/para[0]`

- **Current text**: `Rigorous assessment: 2.5× WER gap on 1,497 segments. Novel IS metric reveals 61.6% useful output (NIV Y+P), confirmed by LLM judge at 64.9%. Full failure analysis with improvement suggestions.`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_

### 9. Slide 10 — `notes/para[0]`

- **Current text**: `The paper reports 25.4% WER on LRS3 — a curated TED talks dataset with ideal conditions. Our 1,497 YouTube segments are fundamentally harder: diverse speakers, topics, lighting, angles. Result: 64.1% WER, 2.5x worse. The dataset is differen`
- **Token**: `64.1%` (shadows `wer_top1`)
- **Replace with**: `63.84%` — _MBR mean_wer = 63.84% (top-1 was 64.05%)_
- **Acceptable alternative**: keep `64.1%` and add `(top-1 baseline)` qualifier in surrounding text

### 10. Slide 11 — `notes/para[0]`

- **Current text**: `1,497 diverse YouTube segments. 64.1% mean WER — 2.5x worse than the paper's 25.4%. Only 25.5% useful by WER (≤34%). And 20.6% are hallucinations — fluent text that's completely fabricated. This is the most dangerous failure mode. But WER i`
- **Token**: `64.1%` (shadows `wer_top1`)
- **Replace with**: `63.84%` — _MBR mean_wer = 63.84% (top-1 was 64.05%)_
- **Acceptable alternative**: keep `64.1%` and add `(top-1 baseline)` qualifier in surrounding text

### 11. Slide 70 — `notes/para[0]`

- **Current text**: `This is the turning point. WER says 25.5% useful. Our Intelligibility Score says 61.6% useful output (NIV Y+P) — 2.4x more. WER correlates with IS but not perfectly — it misses phonetic and semantic preservation, so it is not good enough as`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_
- **Acceptable alternative**: keep `61.6%` and add `(top-1 baseline)` qualifier in surrounding text

### 12. Slide 72 — `notes/para[1]`

- **Current text**: `Current IS 2.52 (61.6% useful, NIV Y+P).`
- **Token**: `2.52` (shadows `is_mean_top1`)
- **Replace with**: `2.547` — _MBR is_mean = 2.547 (top-1 was 2.532)_
- **Acceptable alternative**: keep `2.52` and add `(top-1 baseline)` qualifier in surrounding text

### 13. Slide 72 — `notes/para[1]`

- **Current text**: `Current IS 2.52 (61.6% useful, NIV Y+P).`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_
- **Acceptable alternative**: keep `61.6%` and add `(top-1 baseline)` qualifier in surrounding text

### 14. Slide 72 — `notes/para[5]`

- **Current text**: `Conversion: ~0.033 IS per pp WER (2.52@64% to ~3.81@25.4% paper).`
- **Token**: `2.52` (shadows `is_mean_top1`)
- **Replace with**: `2.547` — _MBR is_mean = 2.547 (top-1 was 2.532)_
- **Acceptable alternative**: keep `2.52` and add `(top-1 baseline)` qualifier in surrounding text


## Medium-Priority Fixes (other body content)

### 15. Slide 71 — `shape[13]/para[0]`

- **Current text**: `Combined target: IS 3.3–3.7 (~80–85% useful Y+P). Phase deltas sum to +0.98 from 2.52 baseline. Gains are multiplicative (ICLR 2024 scaling law).`
- **Token**: `2.52` (shadows `is_mean_top1`)
- **Replace with**: `2.547` — _MBR is_mean = 2.547 (top-1 was 2.532)_

### 16. Slide 85 — `shape[3]/cell[3,1]`

- **Current text**: `61.6%`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_

### 17. Slide 18 — `notes/para[0]`

- **Current text**: `30-sample overview: stratified sample from the 1,497-segment dataset. Distribution matches full dataset closely: Y=23%, P=40%, N=37%. Mean WER 61.4% vs 64.1% full. The interesting middle zone (IS 2-4) is where partial captures, phonetic bri`
- **Token**: `64.1%` (shadows `wer_top1`)
- **Replace with**: `63.84%` — _MBR mean_wer = 63.84% (top-1 was 64.05%)_
- **Acceptable alternative**: keep `64.1%` and add `(top-1 baseline)` qualifier in surrounding text

### 18. Slide 35 — `notes/para[0]`

- **Current text**: `Scatter plot of WER vs IS for all 1,497 segments with NIV thresholds. Green region: 42 segments clearly conveyed (IS >= 3.80) but WER > 34%. Amber region: 437 segments with useful meaning (IS >= 2.00) but WER > 40%. NIV thresholds calibrate`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_
- **Acceptable alternative**: keep `61.6%` and add `(top-1 baseline)` qualifier in surrounding text

### 19. Slide 85 — `notes/para[0]`

- **Current text**: `165 of 900 metric-failed segments are recoverable by the LLM heuristic. Useful output rate is 61.6% (NIV Y+P). 6 recovery categories (overlap, not disjoint). 58% have moderate WER (50-70%).`
- **Token**: `61.6%` (shadows `niv_yp_pct_top1`)
- **Replace with**: `61.92%` — _MBR niv_yp_pct = 61.92% (top-1 was 61.66%)_
- **Acceptable alternative**: keep `61.6%` and add `(top-1 baseline)` qualifier in surrounding text


## Low-Priority Fixes (speaker notes only)

### 20. Slide 5 — `notes/para[2]`

- **Current text**: `AFTER VIDEO: System + human reader outperforms expert lip readers. Expert lip readers achieve ~45-52% word accuracy on unconstrained speech (Auer & Bernstein 2007). Model + context-aware human: estimated 55-70% word accuracy, 75-85% meaning`
- **Token**: `20.5%` (shadows `hallucination_pct_top1`)
- **Replace with**: `20.71%` — _MBR hallucination_pct = 20.71% (top-1 was 20.51%)_
- **Acceptable alternative**: keep `20.5%` and add `(top-1 baseline)` qualifier in surrounding text


---

## Source-Code Citation Gaps (P2)

- `docs/_research-tools/generators/presentation/slides_opening.py` — 0 audit citations. Numbers `64.1`, `61.6`, `20.5`, `5.6` hard-coded inline. Add `# audit:wer_top1`, `# audit:niv_yp_pct_top1`, `# audit:hallu_pct_top1`, `# audit:trustgate_t30_fpr` next to each.

- `docs/_research-tools/generators/presentation/slides_future.py` — 0 audit citations. Numbers `61.6`, `2.52`, phase-delta IS values hard-coded. Add `# audit:niv_yp_pct_top1`, `# audit:is_mean_top1` (with note that they're top-1 baseline-anchored, not MBR), and document the rationale at the top of the file.


## Verification Checklist (post-fix)

- [ ] Re-run `python3 docs/_research-tools/generators/generate_after_amosi_presentation.py` to rebuild deck.

- [ ] Re-run `python3 /home/ubuntu/scripts/extract_pptx_numbers.py` (or the AMOSI variant) to extract numbers.

- [ ] Re-run consistency classifier; confirm STALE_LEAK count drops from 20 → 0.

- [ ] Confirm 11 positive checks still PASS.

- [ ] git commit with message: `presentation: replace top-1 numbers with MBR-default in slides 5/10/11/18/35/70/71/72/79/85`.
