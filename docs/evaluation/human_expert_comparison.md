# Model + Human vs. Expert Lip Reader: Comparative Analysis

**Argos — The Orchard**
**Date:** 2026-03-07
**Author:** Yoad Oxman

---

## 1. The Fundamental Constraint

Only ~30% of English phonemes are visually distinguishable. The 44 English phonemes collapse into ~14-15 visemes (visual units). Pairs like /b/, /p/, /m/ are identical on the lips. This information-theoretic ceiling applies to both humans and machines.

---

## 2. Human Lip-Reading Performance (Academic Baselines)

| Population | Word Accuracy | Key Source |
|-----------|--------------|-----------|
| Average hearing adult | ~10-12% | Auer & Bernstein 2007 (PMC3155585) |
| Average deaf adult | ~44% | Forensic speechreading literature |
| Professional forensic lip reader | ~45-52% | Oxford/DeepMind 2016, LipNet 2017 |
| Exceptional expert (5-sigma outlier) | ~45% | Auer & Bernstein 2007 — 5 SDs above mean |
| Trained modern speechreader (real-time) | 30-35% max | ASHA lipreading review 2021 |

### Key Findings from the Literature

- **No verified expert reliably exceeds ~52% word accuracy** on unconstrained speech.
- **Forensic lip reading has no standardized benchmarks.** Courts in the UK, Australia, and US accept speechreading evidence but require special judicial warnings about its unreliability (R. v Luttrell, 2004).
- **One prominent UK forensic lip reader's reports were withdrawn** from evidential use — their work is no longer used for evidential purposes.
- **The popular image of lip readers decoding full conversations is largely fiction.** Even trained speechreaders under optimal conditions capture only 30-35% of spoken English in real-time.

---

## 3. Machine Performance

### VSP-LLM (Our Model)

| Condition | WER | Word Accuracy |
|-----------|-----|---------------|
| LRS3 benchmark (clean, trained domain) | 25.4% | **74.6%** |
| Real-world YouTube (1,497 segments) | 64.1% | **35.9%** |

| Metric | Value |
|--------|-------|
| LLM Judge Y+P (any useful meaning) | 64.9% |
| NIV Y+P (useful, IS ≥ 2.00) | 61.6% |
| Hallucination rate | 20.5% |
| *Legacy: IS ≥ 3.0 + salvage* | *51.1% (superseded by NIV)* |

### State-of-the-Art Comparison (LRS3 Benchmark)

| Model | WER | Year |
|-------|-----|------|
| VSP-LLM (unfrozen encoder) | 25.4% | 2024 |
| VALLR (Llama 3.2-3B) | 22.1% | 2025 |
| VALLR (phoneme-to-word, best) | 18.7% | 2025 |
| LipNet (constrained grammar) | 6.6% | 2017 |

On clean, trained-domain data, all modern models already far exceed any human expert.

---

## 4. The Combined System: Model + Context-Aware Human

**Scenario:** A human who can see the video (no audio), knows the basic topic/context, and has the model's output to review.

### Why the Combination is Powerful

**1. Verification is easier than generation.**
The model produces fluent candidate text. The human doesn't need to lip-read from scratch — they check whether proposed words match the lip movements they see. A human who couldn't generate "cortisol" from lip movements alone can verify "yes, those lip shapes are consistent with 'cortisol'" when the model suggests it.

**2. Hallucination filtering.**
The model's worst failure mode — 20.5% fluent hallucinations — is exactly where a human adds the most value. A human watching a cooking video who reads "the quantum field collapses" immediately knows it's wrong. Our context-aware LLM Judge evaluation showed 230 judgment downgrades when context was available, proving context knowledge is a powerful filter.

**3. The salvage effect is real.**
Our LLM salvage analysis found 165 metric-failed segments were actually recoverable — phonetic bridges, entity preservation, structural matches. A human naturally performs this salvage. Under NIV thresholds (IS ≥ 2.00), 922/1,497 segments (61.6%) already qualify as useful; a human reviewer would push this higher still.

**4. Topic context eliminates homophene ambiguity.**
Our LLM Judge found ~284 segments (19%) where domain vocabulary confusion was the primary failure. If a human knows "this is a medical lecture," they resolve "bear/bare/bar" type ambiguities that the model can't. Research confirms that topic knowledge and context are as important as visual information for speechreading accuracy (ASHA 2021).

---

## 5. Comparative Assessment

| Dimension | Expert Lip Reader | Model Alone (wild) | Model + Human w/ Context |
|-----------|------------------|-------------------|------------------------|
| **Raw word accuracy** | ~45-52% | ~36% | Est. **55-70%** |
| **Meaning capture** | High (when correct) | 64.9% Y+P | Est. **75-85%** |
| **Hallucination risk** | Low (marks uncertainty) | 20.5% | **<5%** (human filters) |
| **Domain vocabulary** | Limited by personal knowledge | Limited by training data | **Strong** (complementary) |
| **Speed** | Very slow (forensic: hours/min) | Seconds | Minutes (human review) |
| **Consistency** | Variable, no standards | Deterministic | High |
| **Scalability** | One person, one video | Unlimited | Bottlenecked by human |

---

## 6. Conclusion

**The combined system (model + context-aware human) is comparable to or better than an expert lip reader**, with critical practical advantages:

1. **Expert lip readers are worse than people think.** No verified expert exceeds ~52% word accuracy on unconstrained speech. Forensic lip reading has no standardized benchmarks and requires judicial warnings about unreliability.

2. **The model provides what experts lack: candidate text.** The hardest part of lip reading is generation. The model does this. The human's job becomes curation and verification — a dramatically easier cognitive task.

3. **Context is the great equalizer.** Expert lip readers rely heavily on context but must build it themselves. The combined system provides context for free (the human sees the video, knows the topic). Our data shows context knowledge is worth roughly 10-20pp of disambiguation.

4. **The only edge experts retain** is on hallucination cases where the model produces confidently wrong output that a non-domain-expert human might not catch. But a human seeing the video has visual context (setting, objects, gestures) that helps detect these.

**Performance estimates:**
- Expert lip reader alone: ~45-52% word accuracy, ~60-70% meaning capture
- Model + context-aware human: ~55-70% word accuracy, ~75-85% meaning capture

On clean frontal speech (LRS3-like), the model alone at 74.6% accuracy already far surpasses any human. The gap narrows only on wild, degraded video where human contextual reasoning fills in.

---

## 7. References

### Human Lip-Reading Performance
- Auer, E.T. & Bernstein, L.E. (2007). "Some normative data on lip-reading skills." *JASA*. [PMC3155585](https://pmc.ncbi.nlm.nih.gov/articles/PMC3155585/)
- Wikipedia. "Forensic speechreading." [Link](https://en.wikipedia.org/wiki/Forensic_speechreading)
- Hill, C. (2023). "The reliability of speechreading as forensic evidence." University of Melbourne. [Link](https://blogs.unimelb.edu.au/language-forensics/2023/06/29/research-project-the-reliability-of-speechreading-as-forensic-evidence-by-catherine-hill/)
- Tye-Murray, N. (2021). "Lipreading: A Review of Its Continuing Importance." *American Journal of Audiology*. [ASHA](https://pubs.asha.org/doi/10.1044/2021_AJA-21-00112)

### Machine vs. Human Comparisons
- Chung, J.S. et al. (2017). "Lip Reading Sentences in the Wild." Oxford/DeepMind. [Oxford News](https://www.ox.ac.uk/news/2017-03-17-new-computer-software-programme-excels-lip-reading)
- Assael, Y.M. et al. (2016). "LipNet: End-to-End Sentence-level Lipreading." [NVIDIA Blog](https://developer.nvidia.com/blog/lip-reading-ai-more-accurate-than-humans/)
- MIT Technology Review (2016). "AI Has Beaten Humans at Lip-reading." [Link](https://www.technologyreview.com/2016/11/21/69566/ai-has-beaten-humans-at-lip-reading/)
- Quartz (2016). "Oxford's lip-reading AI is more accurate than humans." [Link](https://qz.com/829041/oxford-lip-reading-artificial-intelligence)

### VSP-LLM and State-of-the-Art Models
- Yeo, S.H. et al. (2024). "Where Visual Speech Meets Language: VSP-LLM." *EMNLP Findings*. [Paper](https://aclanthology.org/2024.findings-emnlp.666.pdf)
- Thomas, M. & Fish, E. (2025). "VALLR: Visual ASR Language Model for Lip Reading." *ICCV 2025*. [Paper](https://openaccess.thecvf.com/content/ICCV2025/papers/Thomas_VALLR_Visual_ASR_Language_Model_for_Lip_Reading_ICCV_2025_paper.pdf)

### Viseme/Homophene Ambiguity
- Wikipedia. "Viseme." [Link](https://en.wikipedia.org/wiki/Viseme)
- Bear, H.L. & Harvey, R. (2018). "Phoneme-to-viseme mappings: the good, the bad, and the ugly." *Speech Communication*. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167639317300286)
- Saxena, A. et al. (2020). "Disentangling Homophemes in Lip Reading Using Perplexity Analysis." [arXiv](https://arxiv.org/pdf/2012.07528)

### Our Internal Evaluations
- LLM-as-a-Judge analysis: `docs/evaluation/llm_judge/llm_judge_analysis.md`
- Context-aware evaluation: `docs/evaluation/llm_judge/context_eval/context_eval_analysis.md`
- LLM Salvage analysis: `docs/evaluation/llm_salvage/llm_salvage_analysis.md`
- IS Correlation analysis: `docs/evaluation/is_correlation_analysis.md`
- Intelligibility methodology: `docs/evaluation/intelligibility_methodology.md`