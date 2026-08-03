# Viseme-snapping oracle experiment — all 21 Egla-Kafe videos

Question: if we flag hypothesis words that do not make sense (outside the scene lexicon) and replace them with viseme-close phrases from a domain phrase bank (oracle: built from the scene scripts), does judged understanding improve?

Method: hyp/ref extracted per turn from the burned-in subtitles (OCR); snapping gated on nonsense spans only; sim = viseme-string ratio >= 0.78; scoring = per-turn content-word recall proxy calibrated to the documented context-judge Y+P (MAE 7.6pp).

| video | turns | doc Y+P | proxy before | proxy after | delta | subs |
|---|---|---|---|---|---|---|
| img_6825 | 25 | 72.7 | 52.0 | 56.0 | 4.0 | 14 |
| img_6824 | 29 | 66.7 | 62.1 | 62.1 | 0.0 | 10 |
| s2_tomer_ido_1 | 25 | 62.5 | 64.0 | 64.0 | 0.0 | 8 |
| s2_yoad_tal_1 | 30 | 46.4 | 33.3 | 33.3 | 0.0 | 2 |
| s1_tomer_yoad_1 | 40 | 45.8 | 55.0 | 57.5 | 2.5 | 7 |
| s2_yoad_tomer_2 | 36 | 44.8 | 44.4 | 44.4 | 0.0 | 7 |
| shaam_amosi_ido_2 | 9 | 42.9 | 22.2 | 22.2 | 0.0 | 1 |
| s2_yoad_tomer_1 | 33 | 39.4 | 45.5 | 48.5 | 3.0 | 5 |
| s1_tomer_yoad_2 | 42 | 35.7 | 26.2 | 23.8 | -2.4 | 1 |
| img_6822 | 32 | 35.3 | 25.0 | 28.1 | 3.1 | 4 |
| s1_tomer_ido_1 | 30 | 33.3 | 26.7 | 26.7 | 0.0 | 4 |
| s1_yoad_tal_z30_1 | 31 | 30.4 | 25.8 | 25.8 | 0.0 | 1 |
| s2_yoad_tal_2 | 38 | 29.0 | 28.9 | 28.9 | 0.0 | 5 |
| s1_yoad_tal_1 | 38 | 27.6 | 21.1 | 21.1 | 0.0 | 4 |
| img_6821 | 25 | 19.0 | 8.0 | 8.0 | 0.0 | 0 |
| shaam_yoad_amosi_2 | 33 | 17.2 | 12.1 | 12.1 | 0.0 | 5 |
| img_6823 | 26 | 14.8 | 7.7 | 7.7 | 0.0 | 5 |
| shaam_yoad_amosi_3 | 35 | 14.8 | 5.7 | 5.7 | 0.0 | 2 |
| shaam_amosi_ido_1 | 30 | 12.0 | 6.7 | 10.0 | 3.3 | 6 |
| s1_yoad_tal_z45_1 | 28 | 11.5 | 7.1 | 7.1 | 0.0 | 6 |
| shaam_yoad_amosi_1 | 16 | 10.0 | 6.2 | 6.2 | 0.0 | 5 |

Mean delta: **+0.6pp**. Improved: 5/21. Regressed: 1/21 (s1_tomer_yoad_2, -2.4).

## Substitution quality (sampled)

Genuine fixes (~40%): you're showing it->you're joking; we write for->we wait for; the profile->approval; many languages->military language; is actually movies->is action movies; everyone now->everyone arrived.

Lateral (~30%): a dozen or->at nine at; body knows->buses (target was nobody notices; needs cross-word re-segmentation).

Fabrication risk (~30%): doesn't mean that->nine at night; even life->never seen a — noise converted to on-topic plausible-wrong text.

## Conclusion

Post-hoc nonsense-gated snapping, even with an oracle phrase bank, adds ~1-4pp on the strongest videos and ~0 on average. The near-miss turns that motivate the idea (body knows this planet -> nobody notices planning) need word-boundary re-segmentation over the viseme stream, which short-span snapping only partially achieves — and a third of substitutions convert honest noise into plausible-wrong content. If pursued: show snaps as marked suggestions only, or retain the decoder N-best/lattice (a decoder-output change, not a prompting change) so re-segmentation has real alternatives to work with.

Caveats: hyp/ref via OCR of burned subtitles (some junk tokens inflate sub counts); proxy judge is per-turn (no cross-turn context credit), calibrated to but not identical with the original Claude Opus context judge.