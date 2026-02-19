#!/usr/bin/env bash
set -euo pipefail
RUNNER="/home/ubuntu/tuning_results/run_experiment.sh"

echo ">>> [I] Combo: lenpen=1.0 + do_sample=true + temp=1.0"
bash "$RUNNER" exp_I_lenpen1_sample \
    generation.lenpen=1.0 generation.do_sample=true generation.temperature=1.0
echo

echo ">>> [J] Combo: lenpen=1.0 + do_sample=true + temp=0.5"
bash "$RUNNER" exp_J_lenpen1_temp05 \
    generation.lenpen=1.0 generation.do_sample=true generation.temperature=0.5
echo

echo ">>> [K] Sampling: do_sample=true, temp=1.5"
bash "$RUNNER" exp_K_sampling_temp15 \
    generation.do_sample=true generation.temperature=1.5
echo

echo ">>> [L] Sampling: do_sample=true, temp=0.3"
bash "$RUNNER" exp_L_sampling_temp03 \
    generation.do_sample=true generation.temperature=0.3
echo

echo ">>> [M] Combo: lenpen=1.0 + do_sample=true + temp=0.3"
bash "$RUNNER" exp_M_lenpen1_temp03 \
    generation.lenpen=1.0 generation.do_sample=true generation.temperature=0.3
echo

echo ">>> All remaining experiments complete!"
