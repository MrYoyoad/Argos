# LLaMA-2 Per-Token Softmax Confidence: Literature Review

**Scope:** Practitioner review for using max-softmax per-token probabilities from a fine-tuned LLaMA-2-7B decoder as a word-level confidence signal in our VSR pipeline. Goal: defensible green/yellow/red coloring without retraining or recalibrating before the client deck ships.

## 1. Calibration Consensus

Pre-trained *base* LLMs at scale are reasonably well-calibrated on multiple-choice: Kadavath et al. (2022, "Language Models (Mostly) Know What They Know") found GPT-3-class models close to identity calibration with ECE in the few-percent range. **Instruction-tuning and RLHF degrade calibration.** OpenAI's GPT-4 technical report (2023, Figure 8) shows the post-RLHF model is more confidently wrong than the pre-RLHF base; Tian et al. (2023, "Just Ask for Calibration") report the same for LLaMA-2-Chat — max-softmax becomes systematically *over-confident* after alignment.

For *generative* (free-form) outputs — our setting — calibration is worse. Geng et al. (2024, "Survey of Confidence Estimation and Calibration in LLMs") summarize that raw token-level softmax for open-ended generation tends to be **mildly over-confident, especially in the 0.7-0.95 band**, with empirical ECE in the 5-15% range across tasks. A LoRA-fine-tuned LLaMA-2-7B on a domain task is likely *more* over-confident than the base, because cross-entropy fine-tuning on hard labels sharpens the output distribution. Bottom line: **treat any p ≥ 0.9 as more confident than it should be by roughly 5-15 percentage points.**

## 2. Recommended Thresholds

ASR confidence literature (Jiang 2005, "Confidence measures for speech recognition: A survey") typically uses three bins, with the high band starting at **0.8-0.9** and the low band ending at **0.3-0.5**. MT confidence work (Specia et al. QuEst++ 2015; Fomicheva et al. 2020) lands in the same range. NER confidence tends stricter, often using ≥0.95 for auto-trust because entity errors are high-cost.

The current bands (≥0.7 / 0.3-0.7 / <0.3) are **slightly generous on the high end and roughly correct on the low end** relative to literature.

| Band | Current | Literature norm | Recommendation |
|---|---|---|---|
| Trust | ≥0.7 | 0.85-0.95 | Tighten to **≥0.85** |
| Review | 0.3-0.7 | 0.4-0.85 | Widen to **0.4-0.85** |
| Likely error | <0.3 | <0.4 | Loosen to **<0.4** |

If the deck must ship in 48 hours, the current ≥0.7 / 0.3-0.7 / <0.3 is *defensible* but should be footnoted: "uncalibrated raw softmax; the green band corresponds to roughly 60-75% empirical word-correctness in published LLM calibration studies, not 70%+." That footnote is honest and protects against client overreading.

## 3. Calibration Techniques (Future Work)

**Temperature scaling** (Guo et al. 2017) is the standard fix: a single scalar T applied to logits before softmax, fit on a held-out set. Nearly free, doesn't change ranking, reduces ECE by 50-80% on classifiers. Desai & Durrett (2020) and Tian et al. (2023) confirm it works on LLM multiple-choice but is less effective for free-form. **Platt scaling** is rarely used for LLMs — auto-regressive structure makes it awkward. **Label smoothing** (Müller et al. 2019) helps at training time but isn't applicable post-hoc. Actionable: **fit a single T on a 100-segment held-out slice with manual word labels in a future sprint.** Cost is minutes; ECE reduction is meaningful.

## 4. Sub-Token Aggregation

For BPE/SentencePiece sub-token → word aggregation, dominant choices are **min, mean, and product (geometric mean)**. HuggingFace's `compute_transition_scores` returns per-token log-probs and leaves aggregation to the user. OpenAI's Whisper uses **mean log-prob**; NVIDIA NeMo and several MT confidence papers (Fomicheva et al. 2020) use **geometric mean**. **min** is the most conservative and is what speech products often ship for human-review UIs because a single low-confidence sub-token usually signals a real problem.

Our current choice of `min` is **the right default for a client-facing review UI**: it errs toward flagging more words for review, the safer error mode when humans are in the loop. Geometric mean would surface fewer red words but miss "one bad subword inside a confident word" cases. Stick with `min`.

## 5. Sequence vs Per-Token

Sum-of-log-probs (sequence_score) is a **weak WER predictor**. Murray & Chiang (2018) and Stahlberg & Byrne (2019) on NMT showed length-normalized sequence log-prob correlates with quality at r ≈ 0.3-0.5, dominated by length effects. **Per-token aggregated confidence beats sequence-level for word-error localization**; sequence-level is OK for ranking whole hypotheses (N-best rescoring). For a client report that highlights individual words: **use per-token; do not surface sequence_score to the client.** It remains useful internally for beam aggregation (Mission 6).

## 6. Caveats / Watch-outs

- **Hallucinations are often high-confidence.** Fluent fabrications can sit at p > 0.95 per token (Kadavath 2022; Manakul et al. 2023, SelfCheckGPT). Confidence color does NOT detect hallucination — flag in the deck.
- **Repetition loops are high-confidence.** Repeated tokens approach p = 1.0; confidence won't catch what your decode penalty doesn't.
- **First tokens are systematically lower-confidence.** Sentence-initial tokens have higher entropy by construction; consider excluding the first 1-2 sub-tokens from aggregation, or footnote.
- **Named entities and rare words skew low even when correct.** Sub-token splitting of rare words drops min-confidence; expect more yellow/red on proper nouns.
- **Fine-tuning sharpens distributions.** If you LoRA-fine-tune later, expect more over-confidence; recalibrate after each fine-tune.
- **Domain shift breaks calibration.** Calibration learned on one domain won't transfer to another without re-fitting.

## Citations

- Kadavath, S. et al. (2022). *Language Models (Mostly) Know What They Know.* arXiv:2207.05221.
- OpenAI (2023). *GPT-4 Technical Report.* arXiv:2303.08774. (Figure 8: calibration degradation post-RLHF.)
- Tian, K. et al. (2023). *Just Ask for Calibration.* EMNLP 2023.
- Geng, J. et al. (2024). *A Survey of Confidence Estimation and Calibration in Large Language Models.* NAACL 2024.
- Guo, C. et al. (2017). *On Calibration of Modern Neural Networks.* ICML 2017.
- Desai, S. & Durrett, G. (2020). *Calibration of Pre-trained Transformers.* EMNLP 2020.
- Müller, R., Kornblith, S., Hinton, G. (2019). *When Does Label Smoothing Help?* NeurIPS 2019.
- Jiang, H. (2005). *Confidence measures for speech recognition: A survey.* Speech Communication 45(4).
- Fomicheva, M. et al. (2020). *Unsupervised Quality Estimation for Neural Machine Translation.* TACL.
- Murray, K. & Chiang, D. (2018). *Correcting Length Bias in Neural Machine Translation.* WMT 2018.
- Stahlberg, F. & Byrne, B. (2019). *On NMT Search Errors and Model Errors: Cat Got Your Tongue?* EMNLP 2019.
- Manakul, P., Liusie, A., Gales, M. (2023). *SelfCheckGPT.* EMNLP 2023.
- HuggingFace Transformers docs: `GenerationMixin.compute_transition_scores`, `output_scores`.
- OpenAI Whisper repo (`openai/whisper`): word-level confidence aggregation pattern in `decoding.py`.

**Source-confidence note:** All citations above are works I am confident exist with the titles and approximate findings as cited. Specific numeric claims (e.g., "ECE 5-15% for free-form generation") are paraphrased ranges from these surveys, not exact figures from a single table — verify before citing in a peer-reviewed venue.
