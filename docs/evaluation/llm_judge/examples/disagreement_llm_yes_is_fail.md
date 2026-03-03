# LLM Judge Says YES, but IS < 3.0

These segments convey the reference meaning despite poor metric scores.
They validate the 'LLM salvage' hypothesis.

### Example 1
- **REF:** one really nice thing about this is
- **HYP:** what a brilliant idea this is
- **LLM Judge:** Y
- **IS:** 1.841 (Poor)
- **llm_context_prob:** 0.300 (marginal)
- **WER:** 71.4%
### Example 2
- **REF:** about the being the living in space part that
- **HYP:** we're basically about the business of sending kids to live in space
- **LLM Judge:** Y
- **IS:** 1.984 (Poor)
- **llm_context_prob:** 0.800 (semantic_plus_phonetic)
- **WER:** 111.1%
### Example 3
- **REF:** real human application that we can pull from that
- **HYP:** what are the human implications of that but because
- **LLM Judge:** Y
- **IS:** 2.059 (Fair)
- **llm_context_prob:** 0.300 (marginal)
- **WER:** 100.0%
### Example 4
- **REF:** rotates all the way around once the dial that looks like a clock it means that you've used 7 48
- **HYP:** process all the way around once you get to the end of the clock it means that you viewed seven or seven point four a
- **LLM Judge:** Y
- **IS:** 2.256 (Fair)
- **llm_context_prob:** 0.900 (high_semantic_good_overlap)
- **WER:** 80.0%
### Example 5
- **REF:** to the next level
- **HYP:** to the next level and they have tried
- **LLM Judge:** Y
- **IS:** 2.318 (Fair)
- **llm_context_prob:** 0.600 (moderate_structure_coherent)
- **WER:** 100.0%
### Example 6
- **REF:** there's that i know that looks really bad but if you do take time it'll look a lot better
- **HYP:** and there's nothing i can do about that i know that this is going to be a painful experience but it will look a lot better
- **LLM Judge:** Y
- **IS:** 2.445 (Fair)
- **llm_context_prob:** 0.750 (good_overlap_coherent)
- **WER:** 89.5%
### Example 7
- **REF:** so instead of being 150 155 i was almost approaching 160 and i could have
- **HYP:** instead of being 50 55 i was almost approaching 60 and i
- **LLM Judge:** Y
- **IS:** 2.446 (Fair)
- **llm_context_prob:** 0.750 (good_overlap_coherent)
- **WER:** 40.0%
### Example 8
- **REF:** where is the car wo ist das auto
- **HYP:** where is the car full is dusty outdoors
- **LLM Judge:** Y
- **IS:** 2.448 (Fair)
- **llm_context_prob:** 0.550 (phonetic_bridge_semantic)
- **WER:** 50.0%
### Example 9
- **REF:** hey what's up it's donna today we're gonna be talking about gruselcoin and i'm gonna break the video down into parts and timestamps can be found down below
- **HYP:** we're going to be talking about crucial coins and i'm going to break the video down into parts and time stamps can be found down below
- **LLM Judge:** Y
- **IS:** 2.454 (Fair)
- **llm_context_prob:** 0.750 (good_overlap_coherent)
- **WER:** 50.0%
### Example 10
- **REF:** is also very heavy and is seven and a half pounds over 11 and a half inches
- **HYP:** also very heavy at 7 5 pounds and over 11 5 inches
- **LLM Judge:** Y
- **IS:** 2.600 (Fair)
- **llm_context_prob:** 0.900 (high_semantic_good_overlap)
- **WER:** 64.7%
