# Topic Label Injection Experiment

**Date:** 2026-03-05
**Status:** Complete (all 284 segments decoded, final results)

## Hypothesis

284 segments (19% of 1,497) show domain vocabulary confusion where the LLM decoder produces fluent text from the wrong topic domain. Injecting a topic label into the instruction prompt at decode time should bias the Llama-2-7B decoder toward domain-appropriate vocabulary and reduce WER on these segments.

## Origin of the 284 Segments

The LLM-as-a-Judge evaluation (March 2026) classified failure modes for all 1,497 segments:
- **143 segments** tagged "Total Topic Drift" -- model produces fluent text about a completely wrong topic
- **141 segments** tagged "Phonetically Similar but Wrong Topic" -- model gets sounds right but resolves to wrong-domain vocabulary
- **143 + 141 = 284** segments with domain vocabulary confusion

## Technical Implementation

### How topic labels were injected

The VSP-LLM architecture prepends a text instruction to visual features before feeding them to Llama-2-7B. The token sequence is:

```
[instruction tokens] [visual encoder features] [label tokens]
```

**Baseline instruction** (line 401 of `vsp_llm_dataset.py`):
```
"Recognize this speech in English. Input : "
```

**Topic-labeled instruction** (new, line 403-404):
```
"The speaker is discussing {Topic}. Recognize this speech in English. Input : "
```

The topic label is prepended at the BEGINNING of the instruction, before "Recognize...". This means it is the very first thing the LLM processes, setting context before seeing any visual data.

### Implementation details

1. **Environment variable `VSP_TOPIC_FILE`**: Points to a file with one topic label per line (matching TSV row order)
2. **Loading**: Topics loaded in `__init__` of `VSP_LLM_dataset`, filtered to same indices as loaded data
3. **Injection**: In `__getitem__`, topic label prepended to instruction string before tokenization
4. **No model changes**: Only the instruction text changes; visual encoder, k-means, and model weights remain identical

### Topic distribution (284 segments)

| Topic | Count |
|-------|-------|
| Other | 182 |
| Technology | 22 |
| Cooking/Food | 20 |
| Education/Academic | 17 |
| Entertainment | 12 |
| Medical/Health | 10 |
| Sports/Fitness | 5 |
| Business/Finance | 4 |
| Politics/News | 4 |
| Religion/Spirituality | 4 |
| DIY/Home | 4 |

## Results (284/284 segments — final)

| Metric | Baseline | Topic-Labeled | Delta |
|--------|----------|---------------|-------|
| Mean WER | 86.6% | 87.6% | -0.9pp (worse) |
| Improved (>1pp) | -- | 47 (17%) | -- |
| Degraded (>1pp) | -- | 55 (19%) | -- |
| Unchanged | -- | 182 (64%) | -- |
| Echo instruction | 0 | 67 (24%) | new failure |
| Empty outputs | 0 | 2 | new failure |

### Per-topic breakdown

| Topic | N | Base WER | Topic WER | Delta |
|-------|---|----------|-----------|-------|
| Education/Academic | 17 | 84.7% | 82.9% | +1.8pp |
| Technology | 22 | 83.3% | 82.9% | +0.4pp |
| Politics/News | 4 | 76.9% | 76.7% | +0.2pp |
| Medical/Health | 10 | 87.8% | 87.7% | +0.1pp |
| DIY/Home | 4 | 89.9% | 89.9% | 0.0pp |
| Other | 182 | 86.5% | 86.7% | -0.3pp |
| Entertainment | 12 | 85.9% | 86.9% | -0.9pp |
| Religion/Spirituality | 4 | 100.0% | 102.3% | -2.3pp |
| Sports/Fitness | 5 | 89.8% | 92.3% | -2.5pp |
| Business/Finance | 4 | 94.3% | 99.9% | -5.5pp |
| Cooking/Food | 20 | 89.5% | 99.8% | -10.3pp |

### Key finding: Topic labels do NOT help

**Naive topic label injection is a wash.** The model was not trained with topic-prefixed instructions, so:

1. **Instruction echoing** (67/284 = 24%): The model literally outputs "the speaker is discussing technology" instead of recognizing speech. The extra tokens in the instruction leak into the output.

2. **Position shift**: The additional topic tokens push visual features to different token positions, misaligning the learned instruction-to-visual mapping. The model was trained with a fixed instruction length.

3. **"Other" is uninformative**: 64% of segments (182/284) have topic "Other", which adds noise without useful context.

4. **More degradation than improvement**: 55 degraded vs 47 improved shows no systematic benefit.

5. **Cooking/Food actively hurt** (-10.3pp): Many segments labeled "Cooking" are actually about other topics (weather, coding), so the wrong topic label confuses the model further.

## Control Group Results (100 good segments)

To test whether topic labels hurt already-good segments, we decoded 100 segments with IS >= 3.0 (baseline WER ~29%) using topic-labeled instructions.

| Metric | Experiment (284 bad) | Control (100 good) |
|--------|---------------------|-------------------|
| Baseline WER | 86.6% | 29.3% |
| Topic WER | 87.6% | 30.0% |
| Delta | -0.9pp | -0.6pp |
| Improved (>1pp) | 47 (17%) | 9 (9%) |
| Degraded (>1pp) | 55 (19%) | 18 (18%) |
| Unchanged | 182 (64%) | 73 (73%) |
| Echo instruction | 67 (24%) | 0 (0%) |

### Key control group finding

**Zero instruction echoing on good segments.** When the visual signal is strong enough, the model successfully ignores the extra topic tokens and transcribes normally. Instruction echoing only occurs when the visual features are weak/ambiguous (the bad segments).

However, topic labels still cause net degradation (-0.6pp) even on good segments -- 18 degraded vs 9 improved. The position shift still hurts, just less catastrophically. One perfect segment (0% WER, Politics/News) degraded to 14.3% just from the topic label.

## Why This Was Expected (in hindsight)

The VSP-LLM model was trained with a fixed instruction format: `"Recognize this speech in {language}. Input : "`. The visual encoder features are concatenated after this instruction embedding at a specific position. Changing the instruction length:

- Shifts where visual features start in the combined sequence
- Changes the attention patterns the model learned during training
- The Llama-2-7B decoder treats the extra topic tokens as part of the "prompt to complete" rather than as context for the visual features

This is analogous to prompt engineering on a model not trained for it -- the model has learned rigid positional expectations.

## What Would Actually Work

For topic labels to help, the model would need to be **fine-tuned with topic-prefixed instructions** in the training data. This means:

1. **Training data augmentation**: Include `"The speaker is discussing {topic}. Recognize..."` as an instruction variant during LoRA training
2. **Topic classifier**: Train a lightweight topic classifier (CLIP-based frame classification or LLM inference on first-pass decode)
3. **Positional adaptation**: The model needs to learn that visual features can start at different positions depending on instruction length

This experiment provides empirical evidence that prompt engineering alone cannot solve the domain vocabulary confusion problem. It requires architectural or training changes.

## Files

- `tuning_results/topic_label_experiment/topic_map.json` -- 284 segment-to-topic mapping
- `tuning_results/topic_label_experiment/train.topics` -- topic labels (one per line)
- `tuning_results/topic_label_experiment/run_decode.sh` -- decode script (baseline/topic modes)
- `tuning_results/topic_label_experiment/topic.log` -- full decode log
- `tuning_results/topic_label_experiment/interim_results.json` -- analysis results
- `VSP-LLM/src/vsp_llm_dataset.py` -- modified with topic injection code (guarded by VSP_TOPIC_FILE env var)
