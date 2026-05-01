#!/usr/bin/env bash
# Phase 0 pre-flight tests for the do_sample ablation.
#
# Runs 6 decodes on the 107-segment tuning subset with controlled overrides,
# then evaluates four tests by diffing hypothesis JSONs:
#
#   T1 Deterministic reproducibility:  do_sample=false run twice must match
#   T2 Same-seed sampling reproducible: do_sample=true same seed twice must match
#   T3 Seed varies sampler:             do_sample=true seed 1 vs 2 must differ on >=50%
#   T4 YAML default claim:              no overrides must match explicit do_sample=false
#
# Gate: the main ablation does not start until T1, T2, T3 pass and T4 validates the
# do_sample=false YAML default.
#
# Usage:
#   bash scripts/tests/test_do_sample_determinism.sh [--skip-decode]
#
# Artifacts land in /home/ubuntu/tuning_results/phase0_*/ (cleanup at your discretion;
# these are test scratch, not experiment records). Summary written to
# /home/ubuntu/tuning_results/phase0_report.json.

set -euo pipefail

SKIP_DECODE=0
if [[ "${1:-}" == "--skip-decode" ]]; then
    SKIP_DECODE=1
fi

RUN_SCRIPT="/home/ubuntu/docs/_research-tools/scripts/run_experiment.sh"
TUNING_RESULTS="/home/ubuntu/tuning_results"
REPORT_JSON="${TUNING_RESULTS}/phase0_report.json"

# The original preprocessed_flat_seg12/{audio,video} dirs got rotated away since
# the Feb 19 tuning experiments (the symlink now points elsewhere). We use a
# Phase 0 fork of the dataset whose TSVs point into the Mar 5 archive where
# the 107 videos + audio are still intact. This keeps the ablation's data
# strictly equivalent to what exp_A actually saw.
export TUNING_DATA_OVERRIDE="/home/ubuntu/tuning_results/decode_dataset_phase0"

# Run name -> override string. run_experiment.sh already forces beam=20 lenpen=0
# on the command line, so we only need to set seed and the sampling knobs here.
declare -A RUN_OVERRIDES=(
    [phase0_det_a]="common.seed=1 generation.do_sample=false generation.temperature=1.0 generation.top_p=0.9"
    [phase0_det_b]="common.seed=1 generation.do_sample=false generation.temperature=1.0 generation.top_p=0.9"
    [phase0_samp_s1_a]="common.seed=1 generation.do_sample=true generation.temperature=1.0 generation.top_p=0.9"
    [phase0_samp_s1_b]="common.seed=1 generation.do_sample=true generation.temperature=1.0 generation.top_p=0.9"
    [phase0_samp_s2]="common.seed=2 generation.do_sample=true generation.temperature=1.0 generation.top_p=0.9"
    # T4: empty overrides. Consumes whatever is in s2s_decode.yaml today.
    # We still pass seed=1 so batch iteration ordering matches the other runs
    # (do_sample itself is left to the YAML default — that's what we're testing).
    [phase0_empty]="common.seed=1"
)

RUN_ORDER=(phase0_det_a phase0_det_b phase0_samp_s1_a phase0_samp_s1_b phase0_samp_s2 phase0_empty)

if [[ $SKIP_DECODE -eq 0 ]]; then
    echo "=============================================="
    echo "  Phase 0 pre-flight: 6 decode runs"
    echo "=============================================="
    for name in "${RUN_ORDER[@]}"; do
        overrides="${RUN_OVERRIDES[$name]}"
        echo
        echo "---- [$(date -Iseconds)] Starting $name"
        echo "     overrides: $overrides"
        # shellcheck disable=SC2086
        bash "$RUN_SCRIPT" "$name" $overrides
    done
else
    echo "--skip-decode set: reusing existing run outputs"
fi

echo
echo "=============================================="
echo "  Evaluating T1-T4"
echo "=============================================="

python3 - <<'PYEOF'
import glob, json, os, sys

RUNS = {
    "det_a":      "/home/ubuntu/tuning_results/phase0_det_a/decode_output",
    "det_b":      "/home/ubuntu/tuning_results/phase0_det_b/decode_output",
    "samp_s1_a":  "/home/ubuntu/tuning_results/phase0_samp_s1_a/decode_output",
    "samp_s1_b":  "/home/ubuntu/tuning_results/phase0_samp_s1_b/decode_output",
    "samp_s2":    "/home/ubuntu/tuning_results/phase0_samp_s2/decode_output",
    "empty":      "/home/ubuntu/tuning_results/phase0_empty/decode_output",
}

def load_hypo(run_dir):
    candidates = sorted(glob.glob(os.path.join(run_dir, "hypo-*.json")))
    if not candidates:
        raise FileNotFoundError(f"No hypo-*.json under {run_dir}")
    # Most recent
    path = candidates[-1]
    with open(path) as f:
        d = json.load(f)
    # Canonicalize: map utt_id -> hypo, sorted
    items = dict(zip(d["utt_id"], d["hypo"]))
    return path, items

loaded = {}
for k, v in RUNS.items():
    path, items = load_hypo(v)
    loaded[k] = items
    print(f"  {k:12s} {len(items):3d} segs  ({os.path.basename(path)})")

def compare(a_name, b_name):
    a, b = loaded[a_name], loaded[b_name]
    all_keys = sorted(set(a) | set(b))
    diffs = [k for k in all_keys if a.get(k) != b.get(k)]
    return len(all_keys), len(diffs)

results = {}

# T1: det_a vs det_b -- must match (0 diffs)
n, d = compare("det_a", "det_b")
t1_pass = (d == 0)
results["T1_deterministic_reproducibility"] = {
    "runs": ["det_a", "det_b"], "total": n, "diff": d,
    "pass": t1_pass,
    "criterion": "diff == 0",
}

# T2: samp_s1_a vs samp_s1_b -- must match (0 diffs)
n, d = compare("samp_s1_a", "samp_s1_b")
t2_pass = (d == 0)
results["T2_same_seed_sampling_reproducible"] = {
    "runs": ["samp_s1_a", "samp_s1_b"], "total": n, "diff": d,
    "pass": t2_pass,
    "criterion": "diff == 0",
}

# T3: samp_s1_a vs samp_s2 -- must differ on >= 50%
n, d = compare("samp_s1_a", "samp_s2")
t3_pass = (d / n >= 0.5) if n else False
results["T3_different_seeds_diverge"] = {
    "runs": ["samp_s1_a", "samp_s2"], "total": n, "diff": d,
    "diff_frac": round(d / n, 3) if n else None,
    "pass": t3_pass,
    "criterion": "diff_frac >= 0.5",
}

# T4: empty vs det_a -- must match (proves YAML default is do_sample=false)
n, d = compare("empty", "det_a")
t4_pass = (d == 0)
results["T4_yaml_default_is_do_sample_false"] = {
    "runs": ["empty", "det_a"], "total": n, "diff": d,
    "pass": t4_pass,
    "criterion": "diff == 0 -- empty overrides must match explicit do_sample=false",
}

print()
print("-" * 70)
for name, r in results.items():
    status = "PASS" if r["pass"] else "FAIL"
    print(f"  [{status}] {name}")
    print(f"         runs={r['runs']} total={r['total']} diff={r['diff']}")
    if "diff_frac" in r:
        print(f"         diff_frac={r['diff_frac']}")
    print(f"         criterion: {r['criterion']}")

out = {
    "results": results,
    "all_pass": all(r["pass"] for r in results.values()),
}
with open("/home/ubuntu/tuning_results/phase0_report.json", "w") as f:
    json.dump(out, f, indent=2)

print()
print(f"  Report: /home/ubuntu/tuning_results/phase0_report.json")
print(f"  all_pass: {out['all_pass']}")
sys.exit(0 if out["all_pass"] else 1)
PYEOF
