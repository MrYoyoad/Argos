# Competitive Landscape — Commercial Visual Speech Recognition

Last updated: 2026-05-03
Source: web search audit during Argos VSP v10 client-meeting prep.
Companion to [QA_CHEAT_SHEET.md](QA_CHEAT_SHEET.md). Pull-only material — do
not volunteer in-meeting; deploy if a competitor or "why not just use X" question is asked.

## TL;DR

Two consumer-facing SaaS products explicitly market the surveillance/forensic
lip-reading use case. Neither is a serious enterprise competitor. Both exhibit
the exact failure mode (fluent hallucination without confidence signal) that
Argos's Strip tier and per-word trust layer are designed to flag. The
forensic-services industry openly states current AI lip-reading isn't
court-defensible because it can't surface uncertainty — this is the market gap
Argos closes.

---

## Direct competitors (consumer SaaS)

### Symphonic Labs — "Read Their Lips" (readtheirlips.com)

- **Company size:** 2 employees, founded 2024, Waterloo Canada (PitchBook,
  Crunchbase).
- **Actual flagship product:** MAMO — a Mac OS app for silent voice commands
  to your computer. The lip-reading website is a marketing showcase, not a
  forensic product.
- **Hard limit:** 3-minute clip cap. Disqualifies for surveillance/archive use
  cases.
- **Founder framing:** "to build an interface that felt telepathic, without the
  need for an implant or bulky hardware" (Newsweek, 2024). They are not
  building for our use case.
- **Public test results (HN thread, Sept 2024, two independent users):**
  - Two-person YouTube clip → fluent hallucination, infinite token loop
    ("thats my gosh thats my gosh thats my gosh...").
  - HAL 9000 dialogue from 2001 (clean frontal, single speaker, easy case)
    → semantic drift, repetitive loop ("youre going to get the best youre
    going to get the best..."), no flag, no signal to user.
- **Newsweek test (Sept 2024):** 23-second 1925 silent newsreel — system
  "guesses ... approximating" output, no reference verification, no
  confidence layer.

### LipReadPro (lipreadpro.com)

- **Company opacity:** No Crunchbase, no PitchBook, no verifiable team. The
  dang.ai aggregator listing notes the company **refused verification** of
  their listing.
- **Marketing claim:** "up to 95% accuracy" on real-world footage.
- **Reality check:** Published SOTA on the LRS3 benchmark (controlled,
  curated, frontal-face footage) is ~27% WER (AV-HuBERT, Meta, 2022). Human
  expert lip-readers manage 30–60% accuracy. A 95% accuracy claim on
  real-world surveillance footage is marketing fiction, not measurement.
- **Distribution:** Web upload, free demo + paid tiers. Files to their
  servers — not on-prem.
- **Listed personas:** content creators, journalists, security personnel,
  forensic analysts. Range too wide to be a serious specialist tool.

---

## Adjacent — not direct competitors

### Big-tech speech APIs (Google STT, AWS Transcribe, Azure Speech, OpenAI Whisper)

Audio-only. Return nothing or hallucinate from noise when audio is missing
or unreliable. **Different problem entirely** — useful framing if asked
"why don't you just use Whisper."

### Accessibility-focused VSR tools (Liopa SRAVI)

- Built for deaf-communication: single speaker, close-up, controlled
  lighting, often constrained vocabulary (a few dozen phrases at ~90%
  accuracy).
- Does not generalize to observer-distance surveillance footage.
- No per-word trust signal — accessibility users want fluent output,
  not flagged uncertainty. Different design goals entirely.

### Research demos / open source

- **LipNet** (Oxford, 2016) — 93% on the GRID corpus (64,000 sentences,
  controlled lighting, frontal face, tiny vocabulary). Not productized.
- **AV-HuBERT** (Meta, 2022) — 26.9% WER on LRS3, the largest public
  benchmark. SOTA at time of publication. Open-source weights.
- **VSP-LLM** (2024) — combines AV-HuBERT visual encoder with LLaMA
  decoder for context. Open-source.
- These are **GitHub repos, not products.** Productionizing one of these
  is six months of engineering work (see Argos timeline slide). The IP
  is public; the productionization isn't, and that's most of the work.

### Manual expert lip-readers (forensic services)

- **Examples:** 121 Captions (UK), Silent Eye Lip Reading Translator (US),
  Jeremy Freeman (UCL-certified expert witness, UK).
- **Accuracy:** ~45–52% on real-world footage (Bear & Harvey 2017,
  Assael et al. 2016).
- **Cost structure:** hours of expert time per clip, hard to audit, not
  scalable.
- **Industry stance — most strategically useful finding:**

  > "Technology doesn't 'do' the lip reading. It merely provides a clearer
  > canvas for the human expert to work on. ... For forensic applications,
  > human oversight and expertise are still paramount due to the need for
  > nuanced interpretation and legal defensibility." — 121 Captions, 2026

  **This is the gap.** The professional forensic-services industry rejects
  AI lip-reading not because the recognition is bad but because **it can't
  tell you when to trust it.** That's the seam Argos's confidence layer
  fills.

---

## Why the gap exists (audience-facing framing)

The use case is narrow enough that it doesn't fit consumer or accessibility
playbooks the big labs optimize for, and broad enough that it's not a
single-customer custom build. It sits between research and product. Research
has been published for years; what's missing is the engineering and the trust
layer. That's the work Argos has done.

---

## Argos's actual differentiation (what to defend)

1. **Calibrated trust signal.** Per-word and per-segment confidence,
   validated against an independent blind evaluator. No competitor surfaces
   this. Marketing claims of accuracy are unfalsifiable; calibrated
   confidence is testable on every clip.

2. **Failure-mode taxonomy.** Argos classifies its own outputs into Trust /
   Salvage / Strip tiers and detects fluent hallucination explicitly.
   Competitors' fluent-halluci<!-- [source paste truncated mid-word here; recover original if more was intended] -->
