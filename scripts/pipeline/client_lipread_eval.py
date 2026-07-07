#!/usr/bin/env python3
"""client_lipread_eval.py — one-command visual-speech evaluation pipeline for ANY client dataset.

Generalizes the Egla-Kafe work into a repeatable, config-driven orchestrator. Given a dataset that
has been indexed into the canonical index.json contract (see below), it runs the full chain and
produces the same deliverables every time:

    index → crops → streams → segments → decode → align → score → per-video report
          → said-vs-heard subtitle videos → sample clips → stats plots → (client deck)

Every stage is an existing, tested tool; this driver wires them with config-derived paths and
resolves the VSP decode archive dynamically. Stages are individually selectable/resumable.

CANONICAL INPUT — <work>/eval/index.json:
  {"entries":[{"stem": ascii-safe id, "orig_path": abs path to source video,
     "source_type": "scene_recording"|"master"|..., "scene": "scene1"|...|null,
     "script": "script1"|null, "angle": str, "speakers_in_name": [..],
     "existing_crops": {"left": path|null, "right": path|null}}]}
  Produce it with a dataset-specific indexer (egla_kafe_index.py is the reference) or by hand.
  Scripts: parsed dialogue JSONs (parse_dialogue_script.py) named script_<sceneid>.json under <work>/eval.

CONFIG (JSON), passed via --config:
  {"name","dataset_root","work_root","deliverables_root",
   "scripts": {"scene1": "<txt>", ...} | null,      # raw dialogue txts to parse (optional)
   "indexer": "<cmd>" | null,                        # command to (re)build index.json (optional)
   "golden_kmeans": "<path>", "venv_prep","venv_full","vsp_dir",
   "stages": [ ... subset of the pipeline ... ]}
"""
import argparse, glob, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = "/home/ubuntu/docs/_research-tools/generators"
DEFAULTS = {
    "venv_prep": "/home/ubuntu/auto_avsr/pre-process-venv/bin/python",
    "venv_full": "/home/ubuntu/vsp-llm-yoad-venv/bin/python",
    "vsp_dir": "/home/ubuntu/VSP-LLM",
    "golden_kmeans": "/home/ubuntu/golden_weights/baseline_20260218/flat_kmeans_200.bin",
    "pipeline": "/home/ubuntu/run_flat_english_pipeline.sh",
}
ALL_STAGES = ["index", "scripts", "crops", "faceid", "streams", "segments", "decode", "align",
              "score", "pervideo", "subtitles", "clips", "plots"]


def sh(cmd, env=None, check=True, cwd="/home/ubuntu"):
    print(f"  $ {' '.join(str(c) for c in cmd)}", file=sys.stderr)
    e = dict(os.environ); e.update(env or {})
    r = subprocess.run([str(c) for c in cmd], env=e, cwd=cwd)
    if check and r.returncode != 0:
        raise SystemExit(f"stage command failed ({r.returncode})")
    return r.returncode


def latest_archive():
    """Path to the most recent VSP run's client_outputs (holds word_confidence.json etc.)."""
    cands = glob.glob("/home/ubuntu/flat_runs_archive/*/client_outputs")
    return max(cands, key=os.path.getmtime) if cands else None


class Pipeline:
    def __init__(self, cfg):
        self.c = {**DEFAULTS, **cfg}
        self.work = self.c["work_root"]
        self.eval = os.path.join(self.work, "eval")
        self.deliv = self.c["deliverables_root"]
        for d in (self.eval, self.deliv, os.path.join(self.work, "streams"),
                  os.path.join(self.work, "decode")):
            os.makedirs(d, exist_ok=True)
        self.index = os.path.join(self.eval, "index.json")

    # ---- stages ----
    def stage_index(self):
        if self.c.get("indexer"):
            sh(self.c["indexer"].split())
        if not os.path.exists(self.index):
            raise SystemExit(f"no index.json at {self.index} — provide an indexer or build it by hand")

    def stage_scripts(self):
        for scene, txt in (self.c.get("scripts") or {}).items():
            out = os.path.join(self.eval, f"script_{scene}.json")
            sh([self.c["venv_full"], f"{HERE}/parse_dialogue_script.py",
                "--in", txt, "--out", out, "--scene", scene])

    def stage_crops(self):
        # generate crops only for indexed videos lacking existing_crops
        idx = json.load(open(self.index))
        for e in idx["entries"]:
            if e["existing_crops"].get("left") and e["existing_crops"].get("right"):
                continue
            outd = os.path.join(self.work, "crops", e["stem"])
            sh([self.c["venv_prep"], f"{HERE}/make_speaker_crops.py",
                "--video", e["orig_path"], "--out-dir", outd, "--stem", e["stem"]])

    def stage_faceid(self):
        # cross-video face clustering + constraint naming -> face_id.json (per-person attribution)
        sh([self.c["venv_prep"], f"{HERE}/egla_kafe_face_id.py",
            "--index", self.index, "--out", os.path.join(self.eval, "face_id.json"),
            "--scenes", "all"], check=False)

    def stage_streams(self):
        sh([self.c["venv_prep"], f"{HERE}/egla_kafe_build_streams.py",
            "--index", self.index, "--streams-dir", os.path.join(self.work, "streams"),
            "--scenes", "all", "--method", "lipvar", "--overlay"])

    def stage_segments(self):
        din = os.path.join(self.work, "decode", "in_all")
        sh([self.c["venv_prep"], f"{HERE}/egla_kafe_cut_segments.py",
            "--index", self.index, "--streams-dir", os.path.join(self.work, "streams"),
            "--out-dir", din])

    def stage_decode(self):
        din = os.path.join(self.work, "decode", "in_all")
        env = {"SEGMENTATION_ENABLED": "0", "VSP_NBEST": "1",
               "GOLDEN_KMEANS": self.c["golden_kmeans"]}
        sh(["bash", self.c["pipeline"], din], env=env)
        # record which archive this run produced (for downstream confidence sidecars)
        arch = latest_archive()
        json.dump({"archive": arch, "ts": time.strftime("%Y%m%d_%H%M%S")},
                  open(os.path.join(self.eval, "last_decode.json"), "w"))
        print(f"  decode archive: {arch}", file=sys.stderr)

    def _hypo(self):
        cands = glob.glob(f"{self.c['vsp_dir']}/decode/vsr/en/hypo-*.json")
        cands = [c for c in cands if "merged" not in c]
        return max(cands, key=os.path.getmtime)

    def stage_align(self):
        din = os.path.join(self.work, "decode", "in_all")
        sh([self.c["venv_prep"], f"{HERE}/egla_kafe_align_and_score.py",
            "--hypo", self._hypo(), "--seg-meta", f"{din}/seg_meta.json",
            "--scripts-dir", self.eval, "--out-dir", os.path.join(self.eval, "run_all"),
            "--face-id", os.path.join(self.eval, "face_id.json"), "--run-report"])

    def stage_score(self):
        R = os.path.join(self.eval, "run_all")
        sh([self.c["venv_full"], f"{GEN}/analyze_egla_kafe.py",
            "--report", f"{R}/report/report.csv", "--provenance", f"{R}/provenance.json",
            "--out-dir", f"{R}/stats"])

    def _archive(self):
        p = os.path.join(self.eval, "last_decode.json")
        return json.load(open(p))["archive"] if os.path.exists(p) else latest_archive()

    def _write_runs_json(self):
        """runs.json maps a run key -> {seg_meta, align, wconf} for the subtitle/QA tools."""
        arch = self._archive()
        runs = {"run_all": {
            "seg_meta": os.path.join(self.work, "decode", "in_all", "seg_meta.json"),
            "align": os.path.join(self.eval, "run_all", "align"),
            "wconf": os.path.join(arch, "report", "word_confidence.json") if arch else ""}}
        p = os.path.join(self.eval, "runs.json")
        json.dump(runs, open(p, "w"), indent=2)
        return p

    def stage_pervideo(self):
        R = os.path.join(self.eval, "run_all")
        sh([self.c["venv_full"], f"{HERE}/egla_kafe_per_video_report.py",
            "--eval-dir", self.eval, "--reports", f"{R}/report/report.csv",
            "--out", os.path.join(self.deliv, "per_video_understanding.md")])

    def stage_subtitles(self):
        runs = self._write_runs_json()
        sh([self.c["venv_full"], f"{HERE}/egla_kafe_conversation_subtitle_video.py",
            "--stems", "all", "--runs-json", runs, "--index", self.index,
            "--out-dir", os.path.join(self.deliv, "conversation_videos")])

    def stage_clips(self):
        sh([self.c["venv_prep"], f"{HERE}/egla_kafe_make_demo_clips.py"], check=False)

    def stage_plots(self):
        sh([self.c["venv_full"], f"{GEN}/egla_kafe_significance.py"], check=False)
        sh([self.c["venv_full"], f"{GEN}/egla_kafe_deck_plots.py"], check=False)

    def run(self, stages):
        for s in stages:
            print(f"\n===== STAGE: {s} =====", file=sys.stderr)
            getattr(self, f"stage_{s}")()
        print(f"\n[done] stages: {stages}\n  deliverables: {self.deliv}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="dataset JSON config")
    ap.add_argument("--stages", default=None, help="comma subset (default: config stages or all)")
    ap.add_argument("--from-stage", default=None, help="run from this stage to the end")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    stages = (args.stages.split(",") if args.stages else cfg.get("stages") or ALL_STAGES)
    if args.from_stage:
        stages = ALL_STAGES[ALL_STAGES.index(args.from_stage):]
    Pipeline(cfg).run(stages)


if __name__ == "__main__":
    main()
