# LLM Salvage: Curated Example Gallery

**Parent document:** [llm_salvage_analysis.md](llm_salvage_analysis.md) (executive summary, methodology, implications)
**Dataset:** 165 divergent segments (LLM prob >= 0.5, IS < 3.0) from 1,497 baseline

5 examples per category, organized by recovery type.

---

## Hidden Gems: High Confidence Despite Bad Metrics

*Claude assigns probability >= 0.80 that a viewer with context could recover meaning, yet IS < 3.0 and WER >= 50%. These segments demonstrate where traditional metrics systematically undervalue lip-reading output.*

**54 segments** in this category.

#### Example 1: `Q8aPjew1aUU_5__621126f2`

| Metric | Value |
|--------|-------|
| **Reference** | when life itself doesn't have essential worth our opinions about reason and logic and all these other concepts don't have any more value than we give them |
| **Hypothesis** | a lot of these things haven't existed in our world until our opinion is about reasoning and logic and all these other concepts you don't have any more faith than you want to give up |
| WER | 74.1% |
| IS | 2.918 (Fair) |
| Semantic Sim | 0.6657 |
| LLM Context Prob | **0.900** |

#### Example 2: `JWhR-GLoVgk_7__5ef19db5`

| Metric | Value |
|--------|-------|
| **Reference** | so we're going to get on into some maybe more important things so in 1 5 we're going to start with some design of experiments type things and then i'm going to show you because we talked about it |
| **Hypothesis** | you can get on and do some maybe more important things so like one point five we're going to show students this kind of experiment same things and then i'm gonna show you things that we talked about maybe that we |
| WER | 59.0% |
| IS | 2.901 (Fair) |
| Semantic Sim | 0.7010 |
| LLM Context Prob | **0.900** |

#### Example 3: `loebelfG9T4_10__76adce28 - Part 1`

| Metric | Value |
|--------|-------|
| **Reference** | make yourself at home make yourself at home si ntase como en casa so repeat |
| **Hypothesis** | make yourself i still home make yourself at home take things in your own hands don't repeat make your |
| WER | 73.3% |
| IS | 2.416 (Fair) |
| Semantic Sim | 0.6315 |
| LLM Context Prob | **0.900** |

#### Example 4: `8lRWXCrYauk_26__bb277d54`

| Metric | Value |
|--------|-------|
| **Reference** | calcium is made up of galactomyloids a substance similar to the carbohydrate starch or to cellulose |
| **Hypothesis** | is made up of collected waste substances that are similar to the carbohydrates starch and cellulose the chemical |
| WER | 68.8% |
| IS | 2.991 (Fair) |
| Semantic Sim | 0.6463 |
| LLM Context Prob | **0.900** |

#### Example 5: `oQEVi0gxmoE_16__3949b7ce`

| Metric | Value |
|--------|-------|
| **Reference** | dollars of damages americans want football they love football they want to go protest on their own time no one cares |
| **Hypothesis** | years of taekwondo is american kids want football they love football they want to go protest in the streets |
| WER | 57.1% |
| IS | 2.818 (Fair) |
| Semantic Sim | 0.6721 |
| LLM Context Prob | **0.900** |

---

## Semantic Preservation: Same Meaning, Different Words

*Semantic similarity >= 0.50 confirms the hypothesis conveys the same meaning as the reference, yet WER >= 50% rates these as failures.*

**57 segments** in this category.

#### Example 1: `WTSIAfzvYUU_0__0f6af48b`

| Metric | Value |
|--------|-------|
| **Reference** | india china afghanistan all these different places that are so foreign to us so both sides would benefit |
| **Hypothesis** | middle east and afghanistan there are all these different warring places and there's no fertile soil so both sides will benefit |
| WER | 72.2% |
| IS | 2.863 (Fair) |
| Semantic Sim | 0.7155 |
| LLM Context Prob | **0.900** |

#### Example 2: `qUxQbCxP3Kg_7__8e48ee47 - Part 2`

| Metric | Value |
|--------|-------|
| **Reference** | to put around it and kind of we're all getting a lot more knowledge about kind of where we came from |
| **Hypothesis** | like to poke around and get to know more about where we came from |
| WER | 61.9% |
| IS | 2.618 (Fair) |
| Semantic Sim | 0.6992 |
| LLM Context Prob | **0.900** |

#### Example 3: `zvCa9Y9eklk_1__87543719`

| Metric | Value |
|--------|-------|
| **Reference** | if you're not even anxious about your own death and demise and it gets into some philosophical and religious concepts it becomes very difficult to talk about because some people say well i'm going to heaven i don't care what happens now |
| **Hypothesis** | very anxious about her own death and i think this is a philosophical religious concept that became very difficult to talk about because some people didn't want me going down that road what happened to that |
| WER | 61.9% |
| IS | 2.522 (Fair) |
| Semantic Sim | 0.6809 |
| LLM Context Prob | **0.900** |

#### Example 4: `y0iPkZ3L6Fw_7__2b16dd83`

| Metric | Value |
|--------|-------|
| **Reference** | one is as you're moving conceptual surface data over to engineering solutions and tools you want to make sure that you have good clean |
| **Hypothesis** | has actually moved the conceptual rules over to engineering tools so what i want you to have good at is |
| WER | 75.0% |
| IS | 2.179 (Fair) |
| Semantic Sim | 0.6317 |
| LLM Context Prob | **0.900** |

#### Example 5: `S0ID6pdAvvY_7__e2281119`

| Metric | Value |
|--------|-------|
| **Reference** | with how to reverse it okay what are the handful of things i'm gonna show you some things that might help you here in just a minute |
| **Hypothesis** | just reverse it like what is the handful of things i'm going to show you some things like my belt loop or something like that but |
| WER | 59.3% |
| IS | 2.479 (Fair) |
| Semantic Sim | 0.6704 |
| LLM Context Prob | **0.900** |

---

## Phonetic Bridge: Natural Lip-Reading Confusions

*Phonetic similarity >= 0.60 shows errors are caused by visually similar mouth shapes (homophenes), not hallucination.*

**93 segments** in this category.

#### Example 1: `cT6aHJmM4cA_2__a0c6120f`

| Metric | Value |
|--------|-------|
| **Reference** | expresses in concrete and symbolic and beautifully real deep |
| **Hypothesis** | suppresses the concrete and the symbolic and the beautiful and the real |
| WER | 88.9% |
| IS | 2.750 (Fair) |
| Phonetic Sim | 0.6667 |
| LLM Context Prob | **0.900** |

#### Example 2: `b2K8u6wfPhU_0__e8c6e06b`

| Metric | Value |
|--------|-------|
| **Reference** | if i have him in my arms and i just want him to go to sleep but he's not but i know lullabies help him i can say hey google turn on lullaby music for baby |
| **Hypothesis** | if i have him in my arms then i just want him to go to sleep peacefully on my own on the back couch i take kids a turn on the lap of a baby |
| WER | 50.0% |
| IS | 2.965 (Fair) |
| Phonetic Sim | 0.6111 |
| LLM Context Prob | **0.900** |

#### Example 3: `xsK5nVERhnE_11__757cd73f`

| Metric | Value |
|--------|-------|
| **Reference** | the folders notification center multitasking and that's pretty much it some little updates of the stock apps but not really much at all so finally we are getting what |
| **Hypothesis** | the faults and notifications there are mostly texting and that's pretty much the sum total of the stock ups but not really much and also finding we are getting what |
| WER | 55.2% |
| IS | 2.771 (Fair) |
| Phonetic Sim | 0.7069 |
| LLM Context Prob | **0.800** |

#### Example 4: `RYHeYQI8Ozg_4__cb42b815`

| Metric | Value |
|--------|-------|
| **Reference** | that means the fear of allah is completely gone the only fear you have is that of the seen there's no more fear of the unseen what a horrible spiritual |
| **Hypothesis** | is the fear of the loss complete the only fear you have outside of death is no more fear of loss what a horrible spiritual |
| WER | 43.3% |
| IS | 2.754 (Fair) |
| Phonetic Sim | 0.6500 |
| LLM Context Prob | **0.900** |

#### Example 5: `JTnwhXvcX9I_0__b67ad686`

| Metric | Value |
|--------|-------|
| **Reference** | let the suit fool you i'm the founder and cto currently of a company called aerospike i founded this company to bring fast |
| **Hypothesis** | true founder and ceo of a company called aereo i founded this company to bring fast |
| WER | 43.5% |
| IS | 2.697 (Fair) |
| Phonetic Sim | 0.6087 |
| LLM Context Prob | **0.900** |

---

## Entity-Preserved: Key Information Survives

*Named Entity F1 >= 50% shows that the most important information (names, numbers, places) is captured correctly.*

**44 segments** in this category.

#### Example 1: `tkblkDZq5oA_12__a389f3ee`

| Metric | Value |
|--------|-------|
| **Reference** | that you tell them what is the way it is and what they should do the way it should be |
| **Hypothesis** | to tell them what the next step is what they should do or what they |
| WER | 55.0% |
| IS | 2.929 (Fair) |
| NEA F1 | 57.1% |
| LLM Context Prob | **0.900** |

#### Example 2: `cECxDMkqVcs_0__91f4d916`

| Metric | Value |
|--------|-------|
| **Reference** | the truth how facebook is a media company or is not what's about twitter |
| **Hypothesis** | use how facebook is a media company on switzerland |
| WER | 57.1% |
| IS | 2.861 (Fair) |
| NEA F1 | 54.5% |
| LLM Context Prob | **0.900** |

#### Example 3: `KBplcu6C5Gs_3__583c583c`

| Metric | Value |
|--------|-------|
| **Reference** | it's a panasonic camera really awesome camera |
| **Hypothesis** | to pan down on camera a really awesome camera i |
| WER | 85.7% |
| IS | 2.698 (Fair) |
| NEA F1 | 75.0% |
| LLM Context Prob | **0.800** |

#### Example 4: `yIcwLBt4S64_7__97673c99`

| Metric | Value |
|--------|-------|
| **Reference** | flat against your breastbone how do i know what size bra to buy that's our next step we're going to do some measurements that will help us figure out how to make the best bra |
| **Hypothesis** | landing next to your bone how do i know what size boot to buy that's our next step we're going to use a 3d scanner to figure |
| WER | 54.3% |
| IS | 2.749 (Fair) |
| NEA F1 | 50.0% |
| LLM Context Prob | **0.750** |

#### Example 5: `qHImZGBRto8_5__fa62c87d`

| Metric | Value |
|--------|-------|
| **Reference** | point being is if we had like if my k 52s started doing that i there's something's wrong it's going back to |
| **Hypothesis** | beings if we had like my kfv2 i started doing that and something's wrong it's holding me back into |
| WER | 50.0% |
| IS | 2.877 (Fair) |
| NEA F1 | 52.6% |
| LLM Context Prob | **0.750** |

---

## Structure Match: Word Order Preserved

*The hypothesis follows the same grammatical structure as the reference. Content words appear in the same sequence.*

**74 segments** in this category.

#### Example 1: `KcDqXon7I3c_0__757ee72e`

| Metric | Value |
|--------|-------|
| **Reference** | to the next level |
| **Hypothesis** | to the next level and they have tried |
| WER | 100.0% |
| IS | 2.318 (Fair) |
| Semantic Sim | 0.6580 |
| LLM Context Prob | **0.600** |

#### Example 2: `IZcKDz911X8_0__21f03eb3`

| Metric | Value |
|--------|-------|
| **Reference** | neptune gives us a long time to learn and experience the energies and wisdom it has to bring you will find over the next few weeks |
| **Hypothesis** | you give it a long time to learn and experience the energies and wisdom that it brings you will find over the |
| WER | 38.5% |
| IS | 2.938 (Fair) |
| Semantic Sim | 0.6495 |
| LLM Context Prob | **0.950** |

#### Example 3: `qUV14ZWiMH8_6__e4f3a3e0`

| Metric | Value |
|--------|-------|
| **Reference** | now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure |
| **Hypothesis** | now we are gaining a great civil war testing whether tyranny or anarchy should prevail in syria and donald trump |
| WER | 58.3% |
| IS | 2.783 (Fair) |
| Semantic Sim | 0.5832 |
| LLM Context Prob | **0.750** |

#### Example 4: `mgOhPGfqc2Q_7__2ab62cb5`

| Metric | Value |
|--------|-------|
| **Reference** | i'm sure somebody can explain how and why that happens i don't really care at the moment |
| **Hypothesis** | i'm sure somebody can explain how what happened and why at the moment or how we are |
| WER | 64.7% |
| IS | 2.677 (Fair) |
| Phonetic Sim | 0.6471 |
| LLM Context Prob | **0.750** |

#### Example 5: `DlFfRJ9zoAs_2__9050e8cd - Part 1`

| Metric | Value |
|--------|-------|
| **Reference** | so let me give you a stunning example of how nasa lies and why it is important why it's more than an academic exercise this is the current mission patch for sts 120 discovery |
| **Hypothesis** | so let me give you a second example of how this ties in and why it's important why is it more than an academic exercise this is our vision path for a city which we can never |
| WER | 52.9% |
| IS | 2.591 (Fair) |
| Phonetic Sim | 0.6912 |
| LLM Context Prob | **0.750** |

---

## WER Over-Punishment: Function Word Inflation

*WER is at least 10 percentage points higher than WWER, meaning most errors are in function words that don't affect meaning.*

**27 segments** in this category.

#### Example 1: `0FUlRjBcGGE_21__8fc418e2`

| Metric | Value |
|--------|-------|
| **Reference** | so um |
| **Hypothesis** | so i kind of |
| WER | 150.0% |
| WWER | 33.3% |
| IS | 2.059 (Fair) |
| Phonetic Sim | 0.7500 |
| LLM Context Prob | **0.650** |

#### Example 2: `XHCAXkDOMtI_4__6a3ac270 - Part 2`

| Metric | Value |
|--------|-------|
| **Reference** | when jesus rose again |
| **Hypothesis** | in one sense it's rose and kennedy |
| WER | 150.0% |
| WWER | 77.8% |
| IS | 1.291 (Poor) |
| Phonetic Sim | 0.6250 |
| LLM Context Prob | **0.550** |

#### Example 3: `a2CS82VZyO4_7__a6316c95`

| Metric | Value |
|--------|-------|
| **Reference** | and i have a tablespoon of jalapeno fresh jalapeno |
| **Hypothesis** | and i have a dietary smoothie i've got the banana called fresh banana |
| WER | 88.9% |
| WWER | 43.8% |
| IS | 2.074 (Fair) |
| Semantic Sim | 0.5005 |
| LLM Context Prob | **0.800** |

#### Example 4: `W25FLpQrqsg_0__0fc58273`

| Metric | Value |
|--------|-------|
| **Reference** | women who won't consider us today because we are not co educational and every person who wants to attend usj because |
| **Hypothesis** | women and queer youth of color because we're not going to go to college every person who wants to take the test can because |
| WER | 76.2% |
| WWER | 63.6% |
| IS | 2.256 (Fair) |
| Semantic Sim | 0.5231 |
| LLM Context Prob | **0.800** |

#### Example 5: `5mkJcxTK1sQ_6__b98995ef`

| Metric | Value |
|--------|-------|
| **Reference** | in various different compositions i'm not gonna talk about any other math for learning this kind of stuff from real world data but rest assured |
| **Hypothesis** | comics and fairy tales and different compositions i'm not going to talk about any of the math involved in this kind of stuff from renaissance |
| WER | 68.0% |
| WWER | 57.1% |
| IS | 2.804 (Fair) |
| Semantic Sim | 0.5029 |
| LLM Context Prob | **0.800** |
