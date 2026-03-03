# LLM Judge Says NO, but IS >= 3.0

These segments have good metric scores but fail to convey meaning.
They represent IS false positives.

### Example 1
- **REF:** all you have to do is unscrew
- **HYP:** all you have to do is not to
- **LLM Judge:** N
- **IS:** 3.419 (Good)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 28.6%
### Example 2
- **REF:** blood extraction first before going to x ray because i wish i did that
- **HYP:** cut your hair first before going to ashram because i wish i did that
- **LLM Judge:** N
- **IS:** 3.142 (Good)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 35.7%
### Example 3
- **REF:** one twitch is all you do
- **HYP:** one to rich is all the
- **LLM Judge:** N
- **IS:** 3.011 (Good)
- **llm_context_prob:** 0.300 (marginal)
- **WER:** 66.7%
