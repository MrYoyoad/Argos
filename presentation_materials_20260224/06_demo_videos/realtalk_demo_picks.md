# RealTalk Demo Picks — Curated Set

_Source: 25-candidate run on RealTalk English (auto-triaged from 34 unscripted YouTube two-person conversations)._
_Pipeline: `flat_runs_archive/20260503_000805` (VSP_NBEST=1, hyp_mbr displayed, joint conf+agreement bands)._

## Aggregate (all 25 candidates)

| Outcome | Count | % | Threshold |
|---|---|---|---|
| **Clearly Conveyed** | 5 | 20% | IS ≥ 3.80 |
| **Salvage** | 9 | 36% | 2.00 ≤ IS < 3.80 |
| **Failed** | 11 | 44% | IS < 2.00 |
| Mean WER (top1=MBR) | 64.8% | — | — |
| Mean IS | 2.29 | — | — |

The Clearly-Conveyed rate (20%) **beats the project's 1,497-segment baseline (15%)**. Triage's named-entity-density + speaker-dominance scoring did select harder-than-typical material that the model still got right when the visual conditions were clean.

---

## A. Headline Wins (Clearly Conveyed) — `IS ≥ 3.80`

These are the primary "model ↔ ground truth" demos. All 5 have partner-speaker streams available for Mode-B side-by-side composites.

### 1. `12XM5_1lyrc__p0` @ 240s — **PERFECT (IS 5.00, WER 0%)**
- **REF**: "in the united states i just think that you're taking it like a trooper that you are i think"
- **HYP (MBR)**: identical
- **sentence_conf**: 0.756 (Salvage tier — bands flag some words as non-green even though all are correct, illustrating that confidence ≠ correctness perfectly)
- **Visual**: clean frontal, glasses don't matter, lips fully visible
- **Deck role**: existence proof — "the system can perfectly transcribe lip movement, on real conversational data, including a named entity ("united states")"

### 2. `7LcWBEVtGwA__p1` @ 520s — IS 4.72, WER 15%
- **REF**: "...you're the one that introduced me to god i wouldn't have a context of who god was if it wasn't for you and for that faith you have but i just want to say thank you for"
- **HYP (MBR)**: "...when you're the one that introduced me to god like i wouldn't have a context of who god was if it wasn't for you for that faith cradle but like i just want to say thank you for"
- Tiny visemic substitutions: "and"→"when", "you have"→"cradle"; structure preserved
- **Deck role**: salvage-aware production output — long sentence, semantic meaning fully preserved, confidence layer correctly downgrades the wrong tokens

### 3. `V1tcw5SLwmM__p1` @ 360s — IS 4.58, WER 20%
- **REF**: "...this is gonna be my trap him method i'll have all of his children and it'll be perfect and we'll be together forever and so on and so forth..."
- **HYP**: "...this is going to be my trappy method i'll have all of these children and it will be perfect and we'll be together forever and so on and so forth..."
- "trap him"→"trappy", "his"→"these" — phonetically very close; long fluent recovery

### 4. `RfhG9O99MIY__p1` @ 230s — IS 4.38, WER 28%
- **REF / HYP**: see analysis json
- Same speaker as worst failure (`RfhG9O99MIY__p0 @ 210s`, IS=0) — direct contrast: the OTHER person in this conversation, 20 seconds later, is a clear win. **Single conversation, both extremes.** Strong narrative for the deck.

### 5. `nvqZ0zrca4I__p1` @ 40s — IS 4.36, WER 31%
- Earliest in its video; comfortable clean frontal frame.

---

## B. Salvage Cases — `2.00 ≤ IS < 3.80`

9 segments where partial meaning survives. Recommended deck pick: `5M9kx6mrXrA__p0 @ 70s` ("Long Island / FaceTiming") — the textbook visemic-confusion example: "long island" → "long eyelashes", "phone or" → "floor", but the surrounding 70% of words and the conversational frame are intact. This is the deck's "the meaning is there even when WER looks bad" slide.

Full list in `realtalk_analysis.md`.

---

## C. Failure-Mode Catalog (for Limitations slide)

11 segments at IS < 2.00. Visible failure modes from frame inspection:

1. **Non-speech mouth motion** — `RfhG9O99MIY__p0 @ 210s`: speaker laughing with eyes closed, lips moving but not phonating speech → empty HYP. **Visual: laughing close-up.**
2. **Off-axis pose** — `Z2vxS15RWMU__p0 @ 90s,320s`: speaker looking far right, lips partially occluded → empty HYP.
3. **Low speech density** — `_0VwR9WPS-k__p0 @ 30s`: visually clean but the window has long pauses → empty HYP.
4. **Confident hallucination** — `v43L_FaHz28__p1 @ 440s`: REF "probably the biggest deal i didn't think we'd be back here anytime soon..." → HYP "well you have seen anything" — short, confident, completely wrong. **Confidence layer (sentence_conf 0.42, Strip tier) catches it.** Strong "automatic flagging" demo.

---

## D. Recommended Deck Set (10 clips)

| Slot | Clip | IS | WER | Deck role |
|---|---|---|---|---|
| 1 | `12XM5_1lyrc__p0 @ 240s` | 5.00 | 0% | Existence proof — perfect MBR |
| 2 | `12XM5_1lyrc` Mode-B @ 240s | — | — | Conversation-context view (perfect speaker + partner, side-by-side) |
| 3 | `7LcWBEVtGwA__p1 @ 520s` | 4.72 | 15% | Long sentence, structure preserved |
| 4 | `V1tcw5SLwmM__p1 @ 360s` | 4.58 | 20% | Visemic-near substitutions only |
| 5 | `RfhG9O99MIY__p1 @ 230s` | 4.38 | 28% | "Single conversation, both extremes" pair |
| 6 | `RfhG9O99MIY__p0 @ 210s` | 0.00 | 100% | Same convo, the failure side |
| 7 | `5M9kx6mrXrA__p0 @ 70s` | 2.80 | 44% | Salvage / visemic confusion ("Long Island") |
| 8 | `Z2vxS15RWMU__p0 @ 90s` | 0.00 | 100% | Failure mode: off-axis pose |
| 9 | `RfhG9O99MIY__p0 @ 210s` (smiling) | 0.00 | 100% | Failure mode: non-speech mouth motion |
| 10 | `v43L_FaHz28__p1 @ 440s` | 0.30 | 97% | Confidence layer auto-flags hallucination |

(Slots 5+6 form the "single conversation, both extremes" pair — same source video, ~20 s apart.)

---

## E. Mode-B Side-by-Side Composites — DONE

5 composites produced at `presentation_materials_20260224/06_demo_videos/realtalk/{source}__win{NNNN}__sidebyside.mp4` using `compose_side_by_side.py` with original two-shot audio re-attached.

Partner-speaker decode results (the *listener* side at the same 12s window — partner pipeline run `flat_runs_archive/20260503_004919`):

| Source | Active speaker (left/right) | Active hyp | Partner (listener) hyp | Listener WER | Insight |
|---|---|---|---|---|---|
| `12XM5_1lyrc @ 240s` | p0, **WER 0%** | "in the united states i just think that you're taking it like a trooper that you are i think" | _(empty)_ | 100% | Partner is silent / listening; system correctly emits nothing. **Strongest contrast — works as headline slide.** |
| `7LcWBEVtGwA @ 520s` | p1, WER 15% | "...you're the one that introduced me to god..." | "when i was a little girl i always wanted to be a princess" (hallucination) | 90% | Listener has minor mouth movement; LLM hallucinates a fluent-but-wrong sentence. **Confidence layer flags it (WER 90%, IS 0.62, sentence_conf low).** |
| `V1tcw5SLwmM @ 360s` | p1, WER 20% | "...this is going to be my trappy method i'll have all of these children..." | "you've got to be kidding me" | 98% | Listener emits a plausible reaction phrase — could be a real micro-utterance or a hallucination; trust layer downgrades. |
| `RfhG9O99MIY @ 230s` | p1, WER 28% | (see report) | _(empty)_ | 100% | Same conversation as our worst failure (`p0 @ 210s`). Listener empty. |
| `nvqZ0zrca4I @ 40s` | p1, WER 31% | (see report) | "i don't know what i'm going to be when i grow up but i know i wan" | 88% | Listener gets a hallucinated coherent fragment. |

**Bigger insight for the deck:** Mode-B side-by-side **spatially distinguishes the active speaker** without explicit speaker selection. Viewer sees one half with confident colored text matching the audio, other half with empty/red/grayed-out hyp — system never had to decide *who's talking*, the visual signal makes it self-evident. This is a free win the deck didn't previously have.

The empty/wrong listener-side hyps also showcase the **automatic hallucination flagging** at work: the model produces fluent text from non-speech mouth movement, but the trust bands + sentence_conf catch it. That's the "confidence layer earns its keep" story on real data.

---

## Files

- Decoded report: `flat_runs_archive/20260503_000805/client_outputs/report/report.csv`
- 25 burned face clips: `presentation_materials_20260224/06_demo_videos/realtalk/{per_speaker_id}__win{NNNN}__burned.mp4`
- Per-candidate analysis with frames: `presentation_materials_20260224/06_demo_videos/realtalk/realtalk_analysis.md`
- Aggregate JSON: `presentation_materials_20260224/06_demo_videos/realtalk/realtalk_analysis.json`
