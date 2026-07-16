#!/usr/bin/env bash
# run_resolution_conditions.sh — serial runner for the resolution ablation (Workstream R).
#
# For each condition res4k_ctrl -> res2k -> res1080 (trees built beforehand by
# scripts/pipeline/egla_kafe_resolution_prep.py):
#   1. orchestrator --stages segments            (CPU: cut 175 clips from the condition crops)
#   2. GATE 1: clip count == segments.json-derived count (175), seg_id parity vs the original
#      4K baseline run (in_shaam_all img_* names), ffprobe dims/pix_fmt of 3 sample clips
#      against the prep manifest + per-condition resolution class (~1300 / ~866 / ~650)
#   3. orchestrator --stages decode,align,score  (GPU decode ~70-80 min, then align+report)
#   4. GATE 2: report.csv utt_ids == the same 175 seg_ids, fresh hypo (mtime > condition
#      start), fresh archive with client_outputs, cross-check vs last_decode.json, stats dir
#      non-empty; then record hypo filename + archive path into the condition's
#      prep_manifest.json (key "run") and keep a copy of the raw hypo json in work/eval/.
# Any gate failure ABORTS the whole run with a clear message (nonzero exit).
#
# !!! SEQUENCING HAZARD — STRICTLY SERIAL DECODES ONLY !!!
# The orchestrator's align stage resolves the NEWEST hypo-*.json under
# /home/ubuntu/VSP-LLM/decode/vsr/en/ (same fid each run -> each decode OVERWRITES the previous
# hypo), and stage_decode records the NEWEST /home/ubuntu/flat_runs_archive/*/client_outputs.
# If ANYTHING else decodes concurrently (another pipeline run, another orchestrator session),
# a condition can silently pick up the wrong hypo/archive. Do not run anything else that
# invokes run_flat_english_pipeline.sh while this script is running. A pgrep guard below
# refuses to start a condition while another pipeline instance is alive, and Gate 2's
# mtime checks catch stale-hypo pickup after the fact.
#
# Usage:
#   bash scripts/pipeline/run_resolution_conditions.sh                # full serial run (GPU)
#   bash scripts/pipeline/run_resolution_conditions.sh --dry-gate res4k_ctrl
#       runs ONLY the segments stage + Gate 1 for one condition (no decode/align/score);
#       used for prep validation. Safe to re-run: cut_segments overwrites clips with -y.
set -euo pipefail

BASE="/home/ubuntu/datasets/clients/egla_kafe_resolution"
ORCH="/home/ubuntu/scripts/pipeline/client_lipread_eval.py"
HYPO_DIR="/home/ubuntu/VSP-LLM/decode/vsr/en"
ARCH_ROOT="/home/ubuntu/flat_runs_archive"
ORIG_IN="/home/ubuntu/datasets/clients/egla_kafe/work/decode/in_shaam_all"
CONDITIONS=(res4k_ctrl res2k res1080)

die() { echo "" >&2; echo "ABORT: $*" >&2; exit 1; }

no_other_pipeline() {
  if pgrep -f "run_flat_english_pipeline.sh" >/dev/null 2>&1; then
    die "another run_flat_english_pipeline.sh is running — newest-hypo/newest-archive resolution requires strictly serial decodes (see hazard comment)"
  fi
  if pgrep -f "client_lipread_eval.py" >/dev/null 2>&1; then
    die "another client_lipread_eval.py is running — refusing to interleave decodes"
  fi
}

# ---------- GATE 1: after the segments stage ----------
gate_segments() {
  local cond="$1"
  python3 - "$BASE/$cond" "$ORIG_IN" <<'PY' || die "Gate 1 (segments) failed for condition $cond"
import glob, json, os, subprocess, sys
cond_root, orig_in = sys.argv[1], sys.argv[2]
cond = os.path.basename(cond_root)
din = os.path.join(cond_root, "work/decode/in_all")
MIN_DUR = 0.6  # mirrors egla_kafe_cut_segments.py default

def fail(msg):
    print(f"[gate1:{cond}] FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

exp = set()
for p in glob.glob(os.path.join(cond_root, "work/streams/*/*__segments.json")):
    for s in json.load(open(p))["segments"]:
        if s["t1"] - s["t0"] >= MIN_DUR:
            exp.add(s["seg_id"])
if not exp:
    fail("no segments.json found under work/streams/")
if not os.path.isdir(din):
    fail(f"missing decode input dir {din}")
clips = sorted(os.path.splitext(b)[0] for b in os.listdir(din) if b.endswith(".mp4"))
if len(clips) != len(exp) or set(clips) != exp:
    fail(f"clip set != segments.json-derived seg_ids: {len(clips)} clips vs {len(exp)} expected; "
         f"diff sample {sorted(set(clips) ^ exp)[:5]}")
orig = {os.path.splitext(b)[0] for b in os.listdir(orig_in)
        if b.startswith("img_") and b.endswith(".mp4")}
if set(clips) != orig:
    fail(f"seg_id parity vs 4K baseline ({orig_in}) failed: "
         f"diff sample {sorted(set(clips) ^ orig)[:5]}")
meta_p = os.path.join(din, "seg_meta.json")
if not os.path.exists(meta_p):
    fail("missing seg_meta.json in decode input dir")
meta = json.load(open(meta_p))
if set(meta) != exp:
    fail(f"seg_meta.json keys ({len(meta)}) != expected seg_ids ({len(exp)})")
man = json.load(open(os.path.join(cond_root, "prep_manifest.json")))
dims = {(c["stem"], c["side"]): (c["dst_probe"]["w"], c["dst_probe"]["h"]) for c in man["crops"]}
CLASS = {"res4k_ctrl": {1300, 1200}, "res2k": {866, 800}, "res1080": {650, 600}}
for sid in (clips[0], clips[len(clips) // 2], clips[-1]):
    m = meta[sid]
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,pix_fmt", "-of", "csv=p=0",
                        os.path.join(din, sid + ".mp4")], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"ffprobe failed on {sid}: {r.stderr[-200:]}")
    w, h, pix = r.stdout.strip().split(",")
    w, h = int(w), int(h)
    want = dims[(m["stem"], m["side"])]
    if (w, h) != want:
        fail(f"{sid}: dims {w}x{h} != condition crop dims {want[0]}x{want[1]}")
    if pix != "yuv420p":
        fail(f"{sid}: pix_fmt {pix} != yuv420p")
    if w not in CLASS[cond]:
        fail(f"{sid}: width {w} outside expected class {sorted(CLASS[cond])} for {cond} "
             f"(wrong-condition tree mixup?)")
    print(f"[gate1:{cond}] sample {sid}: {w}x{h} {pix} OK", file=sys.stderr)
print(f"[gate1:{cond}] PASS: {len(clips)} clips == segments.json count, seg_id parity vs 4K "
      f"baseline, seg_meta consistent, sample dims verified", file=sys.stderr)
PY
}

# ---------- GATE 2: after decode,align,score ----------
gate_post() {
  local cond="$1" t_start="$2"
  python3 - "$BASE/$cond" "$t_start" "$HYPO_DIR" "$ARCH_ROOT" <<'PY' || die "Gate 2 (post-decode) failed for condition $cond"
import csv, glob, json, os, shutil, sys, time
cond_root, t_start, hypo_dir, arch_root = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
cond = os.path.basename(cond_root)

def fail(msg):
    print(f"[gate2:{cond}] FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

exp = set()
for p in glob.glob(os.path.join(cond_root, "work/streams/*/*__segments.json")):
    for s in json.load(open(p))["segments"]:
        if s["t1"] - s["t0"] >= 0.6:
            exp.add(s["seg_id"])

rp = os.path.join(cond_root, "work/eval/run_all/report/report.csv")
if not os.path.exists(rp):
    fail(f"missing {rp}")
rows = list(csv.DictReader(open(rp, encoding="utf-8")))
ids = {r["utt_id"] for r in rows}
if len(rows) != len(exp) or ids != exp:
    fail(f"report.csv rows ({len(rows)}) != segment count ({len(exp)}); "
         f"missing {sorted(exp - ids)[:5]}, extra {sorted(ids - exp)[:5]}")

cands = [c for c in glob.glob(os.path.join(hypo_dir, "hypo-*.json")) if "merged" not in c]
if not cands:
    fail(f"no hypo-*.json under {hypo_dir}")
hypo = max(cands, key=os.path.getmtime)
hypo_mtime = os.path.getmtime(hypo)
if hypo_mtime <= t_start:
    fail(f"newest hypo {hypo} (mtime {time.ctime(hypo_mtime)}) predates condition start "
         f"({time.ctime(t_start)}) — decode produced no fresh hypo / concurrent-run interference")
hd = json.load(open(hypo, encoding="utf-8"))
if set(hd["utt_id"]) != exp:
    fail(f"hypo utt_ids ({len(hd['utt_id'])}) != this condition's seg_ids ({len(exp)}) — "
         f"picked up a foreign decode?")

arch_cands = [d for d in glob.glob(os.path.join(arch_root, "*")) if os.path.isdir(d)]
if not arch_cands:
    fail(f"no archives under {arch_root}")
arch = max(arch_cands, key=os.path.getmtime)
co = os.path.join(arch, "client_outputs")
if not os.path.isdir(co):
    fail(f"newest archive {arch} has no client_outputs/")
if os.path.getmtime(co) <= t_start:
    fail(f"newest archive client_outputs predates condition start — stale archive")
ld_p = os.path.join(cond_root, "work/eval/last_decode.json")
if os.path.exists(ld_p):
    ld = json.load(open(ld_p))
    if os.path.realpath(ld.get("archive") or "") != os.path.realpath(co):
        fail(f"last_decode.json archive {ld.get('archive')} != newest archive {co}")
else:
    fail("missing work/eval/last_decode.json (decode stage did not record its archive)")

stats_dir = os.path.join(cond_root, "work/eval/run_all/stats")
if not (os.path.isdir(stats_dir) and os.listdir(stats_dir)):
    fail(f"score stage output missing/empty: {stats_dir}")

# keep a copy of the raw hypo (+ decode params) — the next condition's decode overwrites them
eval_dir = os.path.join(cond_root, "work/eval")
hypo_copy = os.path.join(eval_dir, os.path.basename(hypo))
shutil.copy2(hypo, hypo_copy)
fid = os.path.basename(hypo).replace("hypo-", "").replace(".json", "")
params = os.path.join(hypo_dir, f"decode_params-{fid}.json")
if os.path.exists(params):
    shutil.copy2(params, os.path.join(eval_dir, os.path.basename(params)))

mp = os.path.join(cond_root, "prep_manifest.json")
man = json.load(open(mp, encoding="utf-8"))
man["run"] = {
    "started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_start)),
    "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
    "hypo": hypo,
    "hypo_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(hypo_mtime)),
    "hypo_copy": hypo_copy,
    "archive": arch,
    "client_outputs": co,
    "report_csv": rp,
    "report_rows": len(rows),
}
with open(mp, "w", encoding="utf-8") as f:
    json.dump(man, f, ensure_ascii=False, indent=2)
print(f"[gate2:{cond}] PASS: report rows {len(rows)} == {len(exp)} seg_ids; hypo {os.path.basename(hypo)} "
      f"fresh; archive {arch}; manifest updated", file=sys.stderr)
PY
}

run_condition() {
  local cond="$1"
  local cfg="$BASE/$cond/eval_config.json"
  [[ -f "$cfg" ]] || die "missing $cfg — run scripts/pipeline/egla_kafe_resolution_prep.py first"
  no_other_pipeline
  local t_start
  t_start=$(date +%s)
  echo ""
  echo "########## CONDITION: $cond  (start: $(date '+%F %T')) ##########"
  python3 "$ORCH" --config "$cfg" --stages segments \
    || die "orchestrator segments stage failed for $cond"
  gate_segments "$cond"
  python3 "$ORCH" --config "$cfg" --stages decode,align,score \
    || die "orchestrator decode/align/score failed for $cond"
  gate_post "$cond" "$t_start"
  echo "########## CONDITION $cond COMPLETE  ($(date '+%F %T')) ##########"
}

# ---------- entry ----------
if [[ "${1:-}" == "--dry-gate" ]]; then
  cond="${2:?usage: $0 --dry-gate CONDITION}"
  cfg="$BASE/$cond/eval_config.json"
  [[ -f "$cfg" ]] || die "missing $cfg — run scripts/pipeline/egla_kafe_resolution_prep.py first"
  echo "[dry-gate] $cond: running segments stage + Gate 1 only (no GPU work)"
  python3 "$ORCH" --config "$cfg" --stages segments \
    || die "orchestrator segments stage failed for $cond"
  gate_segments "$cond"
  echo "[dry-gate] $cond PASS — decode/align/score untouched"
  exit 0
fi

for cond in "${CONDITIONS[@]}"; do
  run_condition "$cond"
done
echo ""
echo "ALL ${#CONDITIONS[@]} CONDITIONS PASSED — per-condition hypo/archive recorded in prep_manifest.json"
