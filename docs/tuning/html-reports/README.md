# Experiment HTML Reports

Quick-view HTML reports for each decode tuning experiment. Open any `.html` file to see per-segment results, WER metrics, and comparison tables.

**Baseline**: exp_A (default params from the VSP-LLM paper)

| Report | Parameter Overrides |
|--------|-------------------|
| [exp_A_baseline.html](exp_A_baseline.html) | baseline (default params) |
| [exp_B_no_rep_pen.html](exp_B_no_rep_pen.html) | generation.repetition_penalty=1.0 |
| [exp_C_lenpen_pos1.html](exp_C_lenpen_pos1.html) | generation.lenpen=1.0 |
| [exp_D_lenpen_neg05.html](exp_D_lenpen_neg05.html) | generation.lenpen=-0.5 |
| [exp_E_sampling_low_temp.html](exp_E_sampling_low_temp.html) | generation.do_sample=true, temperature=0.5, top_p=0.9 |
| [exp_F_sampling_original.html](exp_F_sampling_original.html) | generation.do_sample=true, temperature=1.0, top_p=0.9 |
| [exp_G_greedy.html](exp_G_greedy.html) | generation.beam=1 |
| [exp_H_lenpen_pos2.html](exp_H_lenpen_pos2.html) | generation.lenpen=2.0 |
| [exp_I_lenpen1_sample.html](exp_I_lenpen1_sample.html) | generation.lenpen=1.0, do_sample=true, temperature=1.0 |
| [exp_J_lenpen1_temp05.html](exp_J_lenpen1_temp05.html) | generation.lenpen=1.0, do_sample=true, temperature=0.5 |
| [exp_K_sampling_temp15.html](exp_K_sampling_temp15.html) | generation.do_sample=true, temperature=1.5 |
| [exp_L_sampling_temp03.html](exp_L_sampling_temp03.html) | generation.do_sample=true, temperature=0.3 |
| [exp_M_lenpen1_temp03.html](exp_M_lenpen1_temp03.html) | generation.lenpen=1.0, do_sample=true, temperature=0.3 |

Full experiment data (config, decode output, detailed reports) is in `../experiments/`.
