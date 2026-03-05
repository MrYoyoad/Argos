# Checkpoint-vs-IS Correlation Analysis

## Question

Does the checkpoint with the highest **validation token accuracy** (fairseq's
`best_checkpoint_metric: accuracy`) also produce the highest **Intelligibility Score**?

If not, we may be evaluating the wrong checkpoint from our fine-tuning experiments.

## Exp A (r=16)

| Update | Val Acc (%) | Train Acc (%) | Mean IS | Captured (%) | Empty Hyp |
|--------|:---:|:---:|:---:|:---:|:---:|
| 320 (best acc) | 62.94 | 65.00 | 2.312 | 38.8 | 26 |
| 1000 (best IS) | 60.14 | 86.03 | 2.424 | 33.5 | 1 |
| 1500 | 59.07 | 93.22 | 2.355 | 32.1 | 1 |
| 2000 | 59.12 | 94.72 | 2.389 | 33.5 | 0 |
| 3000 | 58.98 | 95.52 | 2.391 | 35.7 | 0 |

**IS Tier Distribution by Checkpoint:**

| Update | Excellent | Good | Fair | Poor | Failed |
|--------|:---:|:---:|:---:|:---:|:---:|
| 320 | 17.9% | 21.0% | 17.0% | 18.3% | 25.9% |
| 1000 | 14.3% | 19.2% | 26.3% | 24.1% | 16.1% |
| 1500 | 13.8% | 18.3% | 24.6% | 25.4% | 17.9% |
| 2000 | 15.2% | 18.3% | 23.7% | 27.2% | 15.6% |
| 3000 | 12.5% | 23.2% | 21.9% | 26.8% | 15.6% |

**Correlation (Val Accuracy vs Mean IS):**

- Pearson r = -0.657
- Spearman r = -0.300
- N = 5 checkpoints

Interpretation: **moderate negative correlation** between validation accuracy and IS.

**FINDING**: Best accuracy checkpoint (update 320, acc=62.94%, IS=2.312) is NOT the best IS checkpoint!

Best IS checkpoint is update 1000 (acc=60.14%, IS=2.424).
IS difference: 0.112

This suggests that `checkpoint_best.pt` may not be optimal for downstream IS evaluation.

---

## Exp B (r=64)

| Update | Val Acc (%) | Train Acc (%) | Mean IS | Captured (%) | Empty Hyp |
|--------|:---:|:---:|:---:|:---:|:---:|
| 320 (best acc) | 59.80 | 60.56 | 2.023 | 33.0 | 57 |
| 1000 | 57.24 | 81.60 | 2.159 | 28.1 | 12 |
| 1500 | 55.97 | 92.42 | 2.189 | 26.3 | 3 |
| 2000 | 56.85 | 94.82 | 2.182 | 28.6 | 2 |
| 3000 (best IS) | 56.61 | 95.57 | 2.206 | 29.9 | 1 |

**IS Tier Distribution by Checkpoint:**

| Update | Excellent | Good | Fair | Poor | Failed |
|--------|:---:|:---:|:---:|:---:|:---:|
| 320 | 15.2% | 17.9% | 17.4% | 13.8% | 35.7% |
| 1000 | 13.8% | 14.3% | 21.9% | 26.3% | 23.7% |
| 1500 | 12.5% | 13.8% | 21.0% | 30.8% | 21.9% |
| 2000 | 13.8% | 14.7% | 18.3% | 33.5% | 19.6% |
| 3000 | 12.9% | 17.0% | 18.3% | 29.0% | 22.8% |

**Correlation (Val Accuracy vs Mean IS):**

- Pearson r = -0.969
- Spearman r = -0.900
- N = 5 checkpoints

Interpretation: **very strong negative correlation** between validation accuracy and IS.

**FINDING**: Best accuracy checkpoint (update 320, acc=59.80%, IS=2.023) is NOT the best IS checkpoint!

Best IS checkpoint is update 3000 (acc=56.61%, IS=2.206).
IS difference: 0.183

This suggests that `checkpoint_best.pt` may not be optimal for downstream IS evaluation.

---

## Overall Conclusions

In 2 experiment(s) (Exp A (r=16), Exp B (r=64)), the best-accuracy
checkpoint did NOT produce the highest IS. This means **token accuracy is not a
reliable proxy for IS**, and future experiments should evaluate IS directly when
selecting the best checkpoint.

**Correlation Summary:**

| Experiment | Pearson r | Spearman r | Agreement? |
|-----------|:---:|:---:|:---:|
| Exp A (r=16) | -0.657 | -0.300 | **No** |
| Exp B (r=64) | -0.969 | -0.900 | **No** |
