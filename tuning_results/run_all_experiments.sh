#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${SCRIPT_DIR}/run_experiment.sh"

echo "=============================================="
echo "  VSP-LLM Decode Parameter Tuning"
echo "  100-video sample (107 segments)"
echo "  $(date)"
echo "=============================================="
echo

# Experiment A: Current baseline (do_sample=false, beam=20, lenpen=0, rep_pen=1.2)
echo ">>> [A] Baseline (do_sample=false, beam=20, lenpen=0, rep_pen=1.2)"
bash "$RUNNER" exp_A_baseline
echo

# Experiment B: No repetition penalty
echo ">>> [B] No repetition penalty (rep_pen=1.0)"
bash "$RUNNER" exp_B_no_rep_pen \
    generation.repetition_penalty=1.0
echo

# Experiment C: Length penalty +1.0 (favor longer outputs)
echo ">>> [C] Length penalty +1.0 (favor longer)"
bash "$RUNNER" exp_C_lenpen_pos1 \
    generation.lenpen=1.0
echo

# Experiment D: Length penalty -0.5 (favor shorter, more confident)
echo ">>> [D] Length penalty -0.5 (favor shorter)"
bash "$RUNNER" exp_D_lenpen_neg05 \
    generation.lenpen=-0.5
echo

# Experiment E: Stochastic sampling with low temperature
echo ">>> [E] Sampling: do_sample=true, temp=0.5, top_p=0.9"
bash "$RUNNER" exp_E_sampling_low_temp \
    generation.do_sample=true \
    generation.temperature=0.5 \
    generation.top_p=0.9
echo

# Experiment F: Stochastic sampling with original settings (baseline style)
echo ">>> [F] Sampling: do_sample=true, temp=1.0 (baseline style)"
bash "$RUNNER" exp_F_sampling_original \
    generation.do_sample=true \
    generation.temperature=1.0 \
    generation.top_p=0.9
echo

# Experiment G: Greedy decode (beam=1)
echo ">>> [G] Greedy decode (beam=1)"
bash "$RUNNER" exp_G_greedy \
    generation.beam=1
echo

echo "=============================================="
echo "  All experiments complete!"
echo "=============================================="
echo

# Build comparison table
echo ">>> Building comparison table..."
python3 << 'PYEOF'
import csv, os, json, glob

results = []
exp_dir = "/home/ubuntu/tuning_results"

for exp in sorted(glob.glob(f"{exp_dir}/exp_*/report/report.csv")):
    exp_name = exp.split("/")[-3]

    # Load config
    config_path = os.path.join(exp_dir, exp_name, "config.json")
    overrides = ""
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
            overrides = " ".join(cfg.get("overrides", []))

    with open(exp) as f:
        rows = list(csv.DictReader(f))

    wwers = [float(r['wwer_%']) for r in rows if r.get('wwer_%')]
    nea_r = [float(r['nea_recall_%']) for r in rows if r.get('nea_recall_%')]
    nea_f1 = [float(r['nea_f1_%']) for r in rows if r.get('nea_f1_%')]
    empty = sum(1 for r in rows if not r.get('hyp', '').strip())

    results.append({
        'exp': exp_name,
        'overrides': overrides,
        'n': len(rows),
        'empty': empty,
        'empty_pct': f"{100*empty/len(rows):.1f}",
        'mean_wwer': f"{sum(wwers)/len(wwers):.1f}" if wwers else "N/A",
        'med_wwer': f"{sorted(wwers)[len(wwers)//2]:.1f}" if wwers else "N/A",
        'mean_nea_r': f"{sum(nea_r)/len(nea_r):.1f}" if nea_r else "N/A",
        'mean_nea_f1': f"{sum(nea_f1)/len(nea_f1):.1f}" if nea_f1 else "N/A",
    })

# Print table
print()
print(f"{'Experiment':<30} {'Overrides':<55} {'Segs':>4} {'Empty':>6} {'WWER':>7} {'Med':>7} {'NEA-R':>7} {'NEA-F1':>7}")
print("-" * 130)
for r in results:
    print(f"{r['exp']:<30} {r['overrides']:<55} {r['n']:>4} {r['empty_pct']:>5}% {r['mean_wwer']:>6}% {r['med_wwer']:>6}% {r['mean_nea_r']:>6}% {r['mean_nea_f1']:>6}%")

# Save as CSV
with open(f"{exp_dir}/comparison.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print()
print(f"Comparison saved to {exp_dir}/comparison.csv")
PYEOF

# Experiment H: Higher length penalty (lenpen=2.0)
echo ">>> [H] Length penalty +2.0 (favor even longer)"
bash "$RUNNER" exp_H_lenpen_pos2 \
    generation.lenpen=2.0
echo

# Experiment I: Best combo — lenpen=1.0 + sampling temp=1.0
echo ">>> [I] Combo: lenpen=1.0 + do_sample=true + temp=1.0"
bash "$RUNNER" exp_I_lenpen1_sample \
    generation.lenpen=1.0 \
    generation.do_sample=true \
    generation.temperature=1.0
echo

# Experiment J: lenpen=1.0 + sampling temp=0.5
echo ">>> [J] Combo: lenpen=1.0 + do_sample=true + temp=0.5"
bash "$RUNNER" exp_J_lenpen1_temp05 \
    generation.lenpen=1.0 \
    generation.do_sample=true \
    generation.temperature=0.5
echo

# Experiment K: Sampling with higher temp (1.5)
echo ">>> [K] Sampling: do_sample=true, temp=1.5"
bash "$RUNNER" exp_K_sampling_temp15 \
    generation.do_sample=true \
    generation.temperature=1.5
echo

# Experiment L: Sampling with lower temp (0.3)
echo ">>> [L] Sampling: do_sample=true, temp=0.3"
bash "$RUNNER" exp_L_sampling_temp03 \
    generation.do_sample=true \
    generation.temperature=0.3
echo

# Experiment M: lenpen=1.0 + sampling temp=0.3 (combo with lowest temp)
echo ">>> [M] Combo: lenpen=1.0 + do_sample=true + temp=0.3"
bash "$RUNNER" exp_M_lenpen1_temp03 \
    generation.lenpen=1.0 \
    generation.do_sample=true \
    generation.temperature=0.3
echo
