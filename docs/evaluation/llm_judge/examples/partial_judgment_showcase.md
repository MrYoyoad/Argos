# Partial Judgment Showcase

These segments partially convey meaning. Annotations show what's preserved vs lost.

### Example 1
- **REF:** i just learned something recently because i'm a lover of
- **HYP:** i just learned something recently because i'm not a lover of
- **LLM Judge:** P:struct+key/sem
- **IS:** 4.750 (Excellent)
- **llm_context_prob:** 1.000 (near_perfect)
- **WER:** 10.0%
### Example 2
- **REF:** 101 harper street
- **HYP:** one o one arm twist
- **LLM Judge:** P:phon/sem
- **IS:** 0.327 (Failed)
- **llm_context_prob:** 0.050 (hallucination)
- **WER:** 166.7%
### Example 3
- **REF:** how would you unite your empire well i can tell you what constantine wanted he wanted to unite the roman empire
- **HYP:** how would you unite your empire well i can tell you we lost he wanted he wanted to unite the roman empire
- **LLM Judge:** P:sem+struct+key/names
- **IS:** 4.603 (Excellent)
- **llm_context_prob:** 1.000 (near_perfect)
- **WER:** 14.3%
### Example 4
- **REF:** unfair advantage to a lot of artists that have talent but don't necessarily have the money
- **HYP:** a fair advantage to a lot of artists that have talent but don't necessarily have the money
- **LLM Judge:** P:sem+struct+key/detail
- **IS:** 4.603 (Excellent)
- **llm_context_prob:** 1.000 (near_perfect)
- **WER:** 12.5%
### Example 5
- **REF:** so for example let's go back and look at how we build syllables you may remember from our episode about syllable structure that the beginning and ending consonants of syllables work differently depending on the language the beginning
- **HYP:** for example let's go back and look at how we build sentences you may remember from our episode about sentence structure that the beginning and ending consonants of sentences work differently depending on the language the beginning
- **LLM Judge:** P:struct+key/sem
- **IS:** 4.571 (Excellent)
- **llm_context_prob:** 1.000 (near_perfect)
- **WER:** 10.5%
### Example 6
- **REF:** home is what you will become and home is what you will
- **HYP:** home is when you will become a home is where you will
- **LLM Judge:** P:sem+struct+key/detail
- **IS:** 4.569 (Excellent)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 25.0%
### Example 7
- **REF:** about how what we're learning about the neurobiology of social emotions that is emotions that we feel about other people and the emotions
- **HYP:** about how what we're learning about the biology of social emotions and emotions that we feel about other people and the emotions
- **LLM Judge:** P:sem+struct+key/detail
- **IS:** 4.561 (Excellent)
- **llm_context_prob:** 1.000 (near_perfect)
- **WER:** 13.0%
### Example 8
- **REF:** popular with republican presidential candidates
- **HYP:** unpopular with republican presidential candidates
- **LLM Judge:** P:key+struct/sem
- **IS:** 4.540 (Excellent)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 20.0%
### Example 9
- **REF:** trying to start my business i didn't have control i really would take
- **HYP:** trying to start my business i can have control i really want to take
- **LLM Judge:** P:struct+key/sem
- **IS:** 4.525 (Excellent)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 23.1%
### Example 10
- **REF:** month of the year now i have made
- **HYP:** month of the year now i have my role
- **LLM Judge:** P:struct+key/detail
- **IS:** 4.508 (Excellent)
- **llm_context_prob:** 0.950 (strong_structure_match)
- **WER:** 25.0%
