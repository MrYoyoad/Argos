#!/usr/bin/env python3
"""Engine (a) prepare/collect for the phonetic-substitution module (in-session Claude judging).

Pattern (mirrors egla_kafe_context_judge.py): `prepare` renders one prompt file per source
video from candidates.json (phonetic_substitute.py output); a Claude session judges each
batch and writes judgments/<video>.json; `collect` validates every judgment mechanically
(engine output is untrusted input) and emits decisions.json for `phonetic_substitute.py apply`.

The judge NEVER sees references — batches are built from the hypothesis side only.

Usage:
  prepare --candidates C.json --out-dir <dir> [--videos a,b] [--sample-flags N --seed S]
  collect --candidates C.json --judgments-dir <dir>/judgments --out decisions.json
"""
import argparse
import json
import os
import random
import sys

MIN_BEAM_MASS = 0.05          # mirrored in the rubric text below
VALID_DECISIONS = {"replace", "keep"}
VALID_VERDICTS = {"clearly_better", "somewhat_better", "equal", "worse"}

RUBRIC = """You are reviewing a silent lip-reading system's transcript for ONE video.
You see the full ordered hypothesis transcript (imperfect; it may contain recognition
errors). You never see the true reference. For each FLAGGED word, phonetically similar
candidate words are listed with the share of beam-search probability mass supporting them
(evidence from the recognizer itself, shown as NN%).

For each flag decide:
  keep    - the original word is plausible in context, OR no candidate is clearly better.
  replace - EXACTLY ONE candidate is (1) clearly more plausible in the sentence and the
            surrounding turns (verdict clearly_better - not merely equal or slightly
            better), AND (2) marked [SUB-OK] below (beam evidence with mass >= 5%).
Rules: never introduce a proper name, place, brand, or number; when in doubt, keep;
at most 2 replacements per segment; judge plausibility from the transcript context only -
do not invent what "should" have been said. Candidates NOT marked [SUB-OK] are context
for you (display-only); you may never choose them for replace.

Return STRICT JSON (a single array, no prose):
[{"utt_id": "...", "pos": <int>, "decision": "replace"|"keep",
  "chosen": "<candidate word or empty when keep>",
  "verdict": "clearly_better"|"somewhat_better"|"equal"|"worse",
  "rationale": "<one sentence>"}]
Include one entry for EVERY flag listed below (keep entries too).
"""


def load_candidates(path):
    with open(path) as f:
        return json.load(f)


def judgeable_flags(seg):
    """Flags an engine should rule on: not display_only and >=1 substitutable candidate."""
    out = []
    for fl in seg.get("flags", []):
        if fl.get("display_only"):
            continue
        if any(c.get("eligible_for_sub") for c in fl.get("candidates", [])):
            out.append(fl)
    return out


def fmt_flag(utt_id, fl):
    cands = []
    for c in fl.get("candidates", []):
        if not c.get("admissible"):
            continue
        tag = " [SUB-OK]" if c.get("eligible_for_sub") else ""
        cands.append(f"{c['word']} {c.get('beam_mass_pct', 0):.0f}%"
                     f" (phon {1 - c.get('phon_dist_norm', 1):.2f}){tag}")
    return (f"  utt {utt_id} pos {fl['position']}: '{fl['word']}'"
            f" (orig {100 * fl.get('original_mass', 0):.0f}% mass, p={fl['prob']:.2f})"
            f" -> candidates: {'; '.join(cands) if cands else '(none)'}")


def cmd_prepare(args):
    data = load_candidates(args.candidates)
    segs = data["segments"]
    by_video = {}
    for utt_id, seg in segs.items():
        by_video.setdefault(seg.get("video", "unknown"), []).append((utt_id, seg))
    for v in by_video:
        by_video[v].sort(key=lambda kv: kv[1].get("order_key", 0))

    sample_keep = None
    if args.sample_flags:
        all_keys = [(v, utt_id, fl["position"])
                    for v, items in sorted(by_video.items())
                    for utt_id, seg in items
                    for fl in judgeable_flags(seg)]
        rng = random.Random(args.seed)
        rng.shuffle(all_keys)
        sample_keep = set(all_keys[: args.sample_flags])
        print(f"[prepare] sampled {len(sample_keep)}/{len(all_keys)} judgeable flags "
              f"(seed {args.seed})")

    only = set(args.videos.split(",")) if args.videos else None
    batch_dir = os.path.join(args.out_dir, "batches")
    os.makedirs(batch_dir, exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, "judgments"), exist_ok=True)

    index, n_flags_total = {}, 0
    for video, items in sorted(by_video.items()):
        if only and video not in only:
            continue
        flag_lines, n_flags = [], 0
        for utt_id, seg in items:
            for fl in judgeable_flags(seg):
                if sample_keep is not None and (video, utt_id, fl["position"]) not in sample_keep:
                    continue
                flag_lines.append(fmt_flag(utt_id, fl))
                n_flags += 1
        if not flag_lines:
            continue
        transcript = "\n".join(
            f"  [{utt_id}] {seg.get('display_text', '')}" for utt_id, seg in items
            if seg.get("display_text"))
        body = (RUBRIC + "\nTRANSCRIPT (segment order):\n" + transcript +
                "\n\nFLAGS:\n" + "\n".join(flag_lines) + "\n")
        with open(os.path.join(batch_dir, f"{video}.txt"), "w") as f:
            f.write(body)
        index[video] = {"n_flags": n_flags, "n_segments": len(items)}
        n_flags_total += n_flags

    with open(os.path.join(args.out_dir, "batches_index.json"), "w") as f:
        json.dump({"candidates": os.path.abspath(args.candidates),
                   "n_videos": len(index), "n_flags": n_flags_total,
                   "videos": index}, f, indent=1)
    print(f"[prepare] wrote {len(index)} batches, {n_flags_total} judgeable flags "
          f"-> {batch_dir}")


def cmd_collect(args):
    data = load_candidates(args.candidates)
    segs = data["segments"]
    flags_by_key = {}
    for utt_id, seg in segs.items():
        for fl in seg.get("flags", []):
            flags_by_key[(utt_id, fl["position"])] = fl

    decisions, dropped = [], []
    seen = set()
    for name in sorted(os.listdir(args.judgments_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(args.judgments_dir, name)
        try:
            entries = json.load(open(path))
            assert isinstance(entries, list)
        except Exception as e:  # noqa: BLE001 - untrusted input, log and move on
            dropped.append({"file": name, "reason": f"unparseable: {e}"})
            continue
        for e in entries:
            key = (e.get("utt_id"), e.get("pos"))
            reason = None
            fl = flags_by_key.get(key)
            if fl is None:
                reason = "unknown utt/pos"
            elif key in seen:
                reason = "duplicate entry"
            elif e.get("decision") not in VALID_DECISIONS:
                reason = f"bad decision {e.get('decision')!r}"
            elif e.get("verdict") not in VALID_VERDICTS:
                reason = f"bad verdict {e.get('verdict')!r}"
            elif fl.get("display_only"):
                reason = "flag is display_only"
            elif e["decision"] == "replace":
                cand = next((c for c in fl.get("candidates", [])
                             if c["word"] == (e.get("chosen") or "").strip().lower()), None)
                if cand is None:
                    reason = f"chosen {e.get('chosen')!r} not a listed candidate"
                elif not cand.get("eligible_for_sub"):
                    reason = f"chosen {e.get('chosen')!r} not substitution-eligible"
                elif cand.get("beam_mass", 0) < MIN_BEAM_MASS:
                    reason = "beam mass below floor"
                elif e.get("verdict") != "clearly_better":
                    reason = "replace requires verdict clearly_better"
            if reason:
                dropped.append({"file": name, "utt_id": e.get("utt_id"),
                                "pos": e.get("pos"), "reason": reason})
                continue
            seen.add(key)
            decisions.append({"utt_id": e["utt_id"], "pos": e["pos"],
                              "decision": e["decision"],
                              "chosen": (e.get("chosen") or "").strip().lower(),
                              "verdict": e["verdict"],
                              "rationale": e.get("rationale", "")})

    out = {"engine": "claude_session",
           "candidates": os.path.abspath(args.candidates),
           "n_decisions": len(decisions),
           "n_replace": sum(1 for d in decisions if d["decision"] == "replace"),
           "n_dropped": len(dropped), "dropped": dropped,
           "decisions": decisions}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"[collect] {len(decisions)} decisions ({out['n_replace']} replace), "
          f"{len(dropped)} dropped -> {args.out}")
    if dropped:
        for d in dropped[:10]:
            print(f"  dropped: {d}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--candidates", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--videos", default=None, help="comma list; default all")
    p.add_argument("--sample-flags", type=int, default=None,
                   help="randomly keep only N judgeable flags (1497 sampling)")
    p.add_argument("--seed", type=int, default=20260716)
    c = sub.add_parser("collect")
    c.add_argument("--candidates", required=True)
    c.add_argument("--judgments-dir", required=True)
    c.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.cmd == "prepare":
        cmd_prepare(args)
    else:
        cmd_collect(args)


if __name__ == "__main__":
    sys.exit(main())
