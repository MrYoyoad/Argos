# Encoder vs. LLM: Where Is the Real Bottleneck in Visual Speech Recognition?

**Author:** Yoad Oxman · **Date:** 2026-05-10 · **Context:** Decision rationale for the Llama 2 → Llama 3.1 swap planned in [come-up-with-a-distributed-bunny.md](../../.claude/plans/come-up-with-a-distributed-bunny.md)

---

## TL;DR

Replacing the LLM decoder in our VSP-LLM pipeline (Llama 2 → Llama 3.1) is **worth doing** for ecosystem and minor accuracy reasons, but the realistic ceiling is **only ~1.5% absolute WER**. Published 2025 evidence on LRS3 shows that all reasonable LLM choices fall within a 1.5% WER band, and that the **visual encoder dominates system quality**. After the Llama 3.1 baseline lands, the highest-leverage follow-up work is encoder-side: unfreezing AV-HuBERT during fine-tuning, audio fusion (Whisper + AV-HuBERT), two-stage phoneme-centric decoding, and more training data. Qwen 3 is **ruled out** because its dialogue/multilingual pretraining bias actively *hurts* VSR — Qwen-2.5-14B is the worst of the four LLMs benchmarked on LRS3 in the recent literature.

---

## 1. Why lips are an information-poor signal

Visual speech recognition is hard because lips are physically incapable of distinguishing many English phonemes.

### Homophenes and visemes

Phonemes that look identical on the lips are called **homophenes**, and the visual unit that maps to multiple phonemes is called a **viseme**. Examples:

| Viseme | Phonemes that share it | Why they look alike |
|---|---|---|
| Bilabial closure | `/p/`, `/b/`, `/m/` | Lips press together, then release. Voicing (vocal cord vibration) and nasality are invisible. |
| Labiodental | `/f/`, `/v/` | Lower lip touches upper teeth identically; only voicing differs. |
| Lingual/alveolar | `/t/`, `/d/`, `/n/`, `/s/`, `/z/`, `/l/` | All happen behind the teeth; lips barely move. |
| Velar | `/k/`, `/g/`, `/ŋ/` | Articulation happens at the soft palate, invisible from outside. |

Linguistic studies estimate that **40-60% of English phonemic contrasts are not visible on the lips alone**. Even a perfect human lip-reader achieves only ~30-50% word accuracy on unconstrained speech, and trained deaf lip-readers report relying heavily on context, gesture, and topic priming.

### Implication for our system

The visual encoder (AV-HuBERT in our pipeline) is solving a problem where the **input is intrinsically ambiguous**. Whatever ambiguity it cannot resolve, no downstream language model can fully recover. This is the classic information-theoretic limit: the LLM cannot fabricate information that the visual signal never carried.

---

## 2. What the LLM actually contributes

When the encoder produces ambiguous features, the LLM falls back on its **language prior** — its learned distribution over English text. It picks the most-likely word given the context, independent of the visual signal.

### Where the language prior helps

- **Disambiguating homophenes via word-level context.** Given visual features compatible with both `/b/` and `/p/`, the LLM knows "the boy" is far more likely than "the poy". This is real, useful signal.
- **Maintaining grammatical coherence.** Even with noisy features, the output reads like fluent English.
- **Recovering function words.** Articles, prepositions, and auxiliaries are short, often visually unclear, but predictable from context.

### Where the language prior hurts

- **Hallucinations.** When visual features are very weak, the LLM stops being grounded by the input and starts generating plausible-sounding English from pure context. Our pipeline's **20.5% hallucinated segments** (WER ≥ 100%) are exactly this failure mode. A better LLM does not fix this — in fact, a more fluent LLM can hallucinate *more confidently*, producing fluent text disconnected from the actual speech.
- **Domain bias.** An LLM heavily pretrained on internet text will prefer common phrases ("the United States", "I think that") over domain-specific vocabulary. Our [llm_salvage analysis](../evaluation/llm_salvage/llm_salvage_analysis.md) found 165 of 900 metric-failed segments retain useful meaning the LLM partially decoded; another large fraction is invented entirely.

### Why a "stronger" LLM gives diminishing returns

The language prior is already near-saturated for English text at the 7-8B scale. Llama-2 7B already produces fluent English. The marginal benefit of Llama 3.1 8B is sharper disambiguation in a small fraction of cases where Llama 2's prior was suboptimal — not a wholesale capability upgrade.

---

## 3. The empirical evidence: LLM choice barely matters on LRS3

The most direct experiment available was published in September 2025 as ["From Hype to Insight: Rethinking Large Language Model Integration in Visual Speech Recognition"](https://arxiv.org/html/2509.14880v1) (arXiv 2509.14880). The authors held the visual encoder fixed and swapped four ~13B-scale LLMs on the LRS3 test set.

### Result table

| Decoder | LRS3 WER |
|---|---|
| **Llama-2-13B** | **25.7%** (best) |
| Phi-4 | 26.2% |
| Vicuna-13B-v1.5 | 26.5% |
| **Qwen-2.5-14B** | **27.2%** (worst) |

**Spread: 1.5% absolute WER across all four models.**

The paper's authors attribute Qwen's underperformance to its optimization for dialogue and multilingual tasks — characteristics that don't help (and may hurt) a monolingual VSR decoding task. **Qwen 3 doubles down on exactly these characteristics**: it adds a "thinking mode" toggle, expanded reasoning training, and 119-language pretraining. There is no published evidence that this helps VSR, and strong reason to believe it makes things worse.

### Corroborating evidence

- [MMS-LLaMA (arXiv 2503.11315)](https://arxiv.org/html/2503.11315v1) — 2025 SOTA on LRS3 — uses a 3B Llama 3.2 backbone, not Qwen. Their gains come from a **Q-Former multimodal bridge and Whisper+AV-HuBERT audio fusion**, not from a stronger LLM.
- [VALLR (arXiv 2503.21408)](https://arxiv.org/html/2503.21408v1) — 18.7% WER on LRS3 — uses Llama 3.2-3B. Their gains come from a **two-stage phoneme-centric decoder**, not from a stronger LLM.
- [Llama-AVSR (ACL Findings 2025)](https://aclanthology.org/2025.findings-acl.1065.pdf) — uses Llama-family backbones throughout.

The signal across all 2025 VSR papers is consistent: **Llama-family is the standard, encoder/fusion choices drive the headline gains**.

---

## 4. Where the gains actually come from — encoder-side levers

To meaningfully move beyond our current 64.1% WER baseline, the most impactful changes are on the encoder side. Concrete options, in priority order:

### 4.1 Unfreeze the visual encoder during fine-tuning

The original VSP-LLM paper reports two variants:
- **Frozen encoder**: 26.7% WER on LRS3 (matches the `vsp-llm-433h-freeze.yaml` config).
- **Unfrozen encoder after 18K steps**: 25.4% WER (matches `vsp-llm-433h-finetune.yaml`).

This is a 1.3% WER absolute improvement from a single config change. Our [docs/finetuning/training-research-notes.md](training-research-notes.md) flagged the same direction as Priority 2.

### 4.2 Audio fusion (Whisper + AV-HuBERT)

MMS-LLaMA reaches 0.74% WER on clean LRS3 by fusing audio (Whisper encoder) with visual features (AV-HuBERT) and routing them through a Q-Former to the LLM. The audio modality eliminates almost all visual ambiguity for clean recordings.

For our YouTube data, audio is present in most source videos. Adding an optional audio path through Whisper would likely cut our WER dramatically. Implementation cost: moderate — requires extending the dataset format and the projector module to accept two feature streams.

### 4.3 Two-stage phoneme-centric decoding

VALLR's recipe: a Video Transformer with a CTC head first predicts a phoneme sequence from the visual features; the LLM then reconstructs words from phonemes. Decoupling perception from language modeling gives the LLM a **discrete, structured input** rather than a 1024-dim continuous embedding it has to interpret.

Result: 18.7% WER on LRS3 with just Llama 3.2-3B.

### 4.4 Better preprocessing

- Higher-resolution mouth crops (we use 88×88 grayscale).
- Better face alignment and stabilization under head motion.
- Brightness enhancement — the CLAHE work shipped April 30, 2026 (commit `0dfa2d1`) already moves in this direction.

### 4.5 More training data

Our [finetune analysis](training-research-notes.md) found 1,273 segments was below the data-limited regime; LoRA generalization needs at least ~5-10K segments. LRS3's 433h / ~165K utterances is comfortably above that floor. Combining LRS3 + AVSpeech would push further.

### What's *not* the lever (for clarity)

- **LLM size scaling.** Going from 8B to 70B might move WER by 1-2% absolute at substantial compute cost. Bad ROI vs encoder-side work.
- **LLM family swap (Llama ↔ Qwen).** Capped at ~1.5% WER on LRS3 by the published ablation, and Qwen 3 specifically may regress.
- **More LoRA rank.** Our internal Exp B (r=64 vs r=16) made things worse, not better, in the data-limited regime.

---

## 5. Application to our specific system

### The gap that matters

| System | Test set | WER | Notes |
|---|---|---|---|
| Original VSP-LLM paper (frozen encoder) | LRS3 (clean, TED talks) | 26.7% | Llama-2 7B + AV-HuBERT, paper config |
| Original VSP-LLM paper (unfrozen) | LRS3 (clean, TED talks) | 25.4% | +encoder unfreezing |
| MMS-LLaMA | LRS3 (clean) | 0.74% | + audio fusion |
| VALLR | LRS3 (clean) | 18.7% | + two-stage phoneme decoding |
| **Our pipeline (top-1)** | **YouTube (1,497 segments)** | **64.1%** | **Same model, much harder test data** |
| Our pipeline (MBR-default) | YouTube (1,497 segments) | 63.8% | + N-best aggregation (May 2026) |

Two distinct gaps explain the 64% vs 25% comparison:
1. **Distribution shift** — LRS3 is curated TED talks (controlled lighting, frontal pose, clear speech). YouTube is wild: variable lighting, head motion, lower resolution, faster speech, broader vocabulary.
2. **Encoder bottleneck on harder distribution** — the encoder has to perceive a much noisier signal, so it produces much more ambiguous features. The LLM is being asked to disambiguate from less information.

The Llama 2 → Llama 3.1 swap moves the LLM line; it does not address the distribution shift or the harder-perception problem.

### What to expect from the Llama 3.1 swap

Based on the 1.5% WER ceiling reported by the published ablation, and accounting for the fact that LRS3-trained projector weights need to be relearned for the new LLM, the realistic outcomes are:

- **Best case (slight improvement)**: WER drops from 64.1% to ~62.5%, IS rises from 2.532 to ~2.60, hallucination rate (WER ≥ 100%) drops by 1-2 percentage points.
- **Likely case (match-or-tiny-gain)**: WER within ±1% of baseline, IS within ±0.05.
- **Worst case (small regression)**: WER up by 1-2% because projector training on noisy YouTube data underfits the new embedding geometry. This is recoverable with a second training run or by retraining on a larger dataset.

The swap is worth doing for these reasons:
- Modernizes the LLM dependency (Llama 2 is now 3+ years old).
- Better quantization tooling support for newer Llama versions.
- Cleaner ecosystem for downstream improvements (newer transformers, better PEFT integrations).
- Establishes the Llama 3.1 baseline as the foundation for follow-up encoder-side work.

The swap is **not** worth doing as a strategy to fundamentally improve VSR quality. That requires encoder-side work.

---

## 6. Recommended follow-up missions, in priority order

Once the Llama 3.1 baseline is locked in:

1. **Encoder unfreezing on LRS3** — re-run the paper's `vsp-llm-433h-finetune.yaml` config. Expect ~1.3% WER improvement on LRS3 test, modest gain on YouTube. Low engineering cost, single config change.
2. **Audio fusion (Whisper + AV-HuBERT)** — biggest single accuracy lever available. Implementation: extend the dataset format to carry audio, add a Whisper-encoder branch alongside AV-HuBERT, fuse via concatenation or cross-attention before the projector. Reference: MMS-LLaMA.
3. **Two-stage phoneme-centric decoding** — add a CTC phoneme prediction head on top of the visual encoder, then feed phonemes (as text tokens) into the LLM. Reference: VALLR. Higher engineering cost but well-validated approach.
4. **Combined LRS3 + AVSpeech training** — more data, broader distribution. Address the YouTube distribution shift directly.
5. **Higher-resolution mouth crops + better preprocessing** — incremental but compounds with the above.

Defer indefinitely (low expected ROI):
- Qwen 3 swap. Published evidence indicates regression risk.
- Llama 4 swap. MoE architecture is not a drop-in; high engineering risk for unclear gain.
- LoRA rank scaling. Already tested; counterproductive in data-limited regimes.
- Larger LLM scale (70B). Compute cost not justified by expected gain.

---

## 7. Bottom line

| Question | Answer |
|---|---|
| Is the Llama 3.1 swap worth doing? | Yes — for ecosystem and small accuracy lift. |
| Will it dramatically improve our system? | No — capped at ~1-2% WER absolute. |
| Should we use Qwen 3 instead? | No — published evidence shows Qwen regresses on VSR. |
| Where should we focus after the swap? | Encoder side: unfreezing, audio fusion, two-stage decoding. |
| What's the realistic ceiling for our pipeline? | With encoder-side work, target WER 30-40% on YouTube data — comparable to the LRS3 numbers in the literature, scaled for our harder distribution. |

---

## References

1. ["From Hype to Insight: Rethinking Large Language Model Integration in Visual Speech Recognition"](https://arxiv.org/html/2509.14880v1) — arXiv 2509.14880, September 2025. LRS3 LLM-ablation experiment.
2. ["MMS-LLaMA: Efficient LLM-based Audio-Visual Speech Recognition with Minimal Multimodal Speech Tokens"](https://arxiv.org/html/2503.11315v1) — arXiv 2503.11315, March 2025. SOTA audio-visual fusion on LRS3.
3. ["VALLR: Visual ASR Language Model for Lip Reading"](https://arxiv.org/html/2503.21408v1) — arXiv 2503.21408, March 2025. Two-stage phoneme-centric VSR.
4. ["Efficient LLM-based Audio-Visual Speech Recognition with Minimal Multimodal Speech Tokens"](https://aclanthology.org/2025.findings-acl.1065.pdf) — ACL Findings 2025. Llama-AVSR results.
5. ["VSP-LLM: Visual Speech Processing Incorporated with LLMs"](https://arxiv.org/html/2402.15151v1) — original paper our pipeline is based on. Frozen / unfrozen encoder variants.
6. [docs/finetuning/training-research-notes.md](training-research-notes.md) — internal fine-tuning experiments (Exp A r=16, Exp B r=64), data-limited regime analysis.
7. [docs/evaluation/llm_salvage/llm_salvage_analysis.md](../evaluation/llm_salvage/llm_salvage_analysis.md) — internal LLM hallucination and salvage analysis on the 1,497-segment baseline.
