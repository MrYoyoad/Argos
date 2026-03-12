# Arabic VSP Adaptation — What's Needed vs English

## Key Question: Is AV-HuBERT Language-Specific?

AV-HuBERT is a **self-supervised visual feature extractor** — it learns to map lip movements to cluster pseudo-labels derived from audio. It was pretrained on LRS3 (English TED talks).

- **Low-level features are mostly universal**: lip shape, mouth opening, jaw movement transfer across languages
- **Language bias is subtle**: the model learned which visual distinctions *matter for English* — e.g., it never learned to distinguish Arabic emphatics (ص vs س) which involve visible pharyngeal constriction
- **Not a hard blocker**: frozen English AV-HuBERT + Arabic-retrained downstream components is a viable first attempt

## VSP-LLM Pipeline: English vs Arabic

| Component | English (what authors had) | Arabic (what's needed) |
|-----------|---------------------------|------------------------|
| AV-HuBERT encoder | LRS3-pretrained, used as-is | Can reuse frozen; fine-tune later as optimization |
| K-means clustering | Pretrained on LRS3 audio | **Retrain** on Arabic audio features (already trains on the fly in our pipeline) |
| LLM backbone | Llama 2 7B (English-native) | **Replace** with Arabic-capable LLM (Jais, AceGPT, multilingual Llama 3) |
| Q-Former bridge | Trained on LRS3 pairs | **Retrain** on Arabic video-transcript pairs |
| LoRA adapter | Trained on LRS3 pairs | **Retrain** on Arabic data |
| Training data | LRS3 (400h, freely available) | Arabic lip-reading corpus (scarce — may need collection) |

## The Real Difference: One Step vs Four

The VSP-LLM authors' **only novel contribution** was training the Q-Former + LoRA — everything else (AV-HuBERT, k-means, Llama 2, LRS3 data) was off-the-shelf English infrastructure.

For Arabic, you need to adapt or replace **almost every downstream component**. The visual encoder is the most transferable part.

## Suggested Phased Approach

1. **Phase 1 — Minimum viable**: Frozen AV-HuBERT + Arabic k-means + Arabic LLM + retrain Q-Former/LoRA on Arabic data
2. **Phase 2 — Optimize**: Fine-tune AV-HuBERT on Arabic video to capture language-specific visual distinctions
3. **Phase 3 — Scale**: Collect more Arabic training data, upgrade LLM backbone

## Data Challenge

The biggest practical bottleneck is **training data**. There is no Arabic equivalent of LRS3 at scale. Options:
- ArabicVisual dataset (if available/sufficient)
- Custom collection from Arabic broadcast/YouTube (requires alignment pipeline)
- Cross-lingual pretraining strategies to reduce data requirements

## Key Talking Points for Slides

- AV-HuBERT visual features are ~80% language-agnostic (mouth geometry is universal)
- The language specificity lives in the **downstream components**, not the visual encoder
- K-means already retrains per-dataset in our pipeline — Arabic clusters are "free"
- The LLM swap is the most impactful single change
- Data scarcity is the real bottleneck, not model architecture