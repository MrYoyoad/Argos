#!/usr/bin/env python3
"""Context-aware, sequence-level LLM-as-a-Judge for Egla-Kafe conversations.

Per-segment WER/IS scores each turn in isolation and harshly. A real viewer, however, reads the
WHOLE lip-read conversation knowing the general context (e.g. "Emma & Jake, at an airport, about
a flight") and exploits cross-turn redundancy. This judge measures THAT: given the ordered model
hypotheses + a viewer-level context blurb, how much of the conversation is understandable?

Mechanism: there is no Anthropic API key on this box, so judging is done IN-SESSION by Claude
(the repo's existing prepare->judge->collect pattern). This script:
  - `prepare`: build per-conversation judge payloads (context + ordered hyps + refs) -> judge_batch.json
  - `analyze`: ingest the filled verdicts -> context-aware Y / Y+P per conversation, compared to the
    per-segment IS-NIV captured rate (the "context lift").

Verdict schema (one object per conversation), produced in-session and saved under judgments/<stem>.json:
  {stem, scene, gist: "<one-paragraph reconstruction a context-aware viewer gets>",
   recoverable_facts: ["..."], turns: [{idx, verdict: "Y"|"P"|"N"}],
   overall: {y, p, n, y_pct, yp_pct}}
"""
import argparse
import glob
import json
import os

# viewer-level context (general setup the audience knows — NOT the exact lines)
SCENE_CONTEXT = {
    "scene1": ("Two friends, EMMA and JAKE, at an airport before Jake's flight. Emma is checking "
               "he is ready to travel and teases him about being disorganized."),
    "scene2": ("Two military officers, TOM and DAN, late at night planning the logistics of a "
               "unit's departure (transportation, schedule changes)."),
}


def build_payloads(align_glob):
    payloads = []
    for ap in sorted(glob.glob(align_glob)):
        d = json.load(open(ap, encoding="utf-8"))
        scene = d.get("scene")
        turns = [{"idx": i, "char": s["char"], "hyp": s["hyp"], "ref": s["ref"]}
                 for i, s in enumerate(d["segments"])]
        payloads.append({"stem": d.get("stem") or os.path.basename(os.path.dirname(ap)),
                         "scene": scene, "context": SCENE_CONTEXT.get(scene, ""),
                         "side_to_char": d.get("side_to_char", {}), "turns": turns})
    return payloads


def render_prompt(p):
    """Human/Claude-readable judge prompt for one conversation (used in-session)."""
    lines = [
        "You are judging a silent lip-reading system. A viewer watches a silent video of a "
        "conversation and reads the model's transcription, knowing only this general context:",
        f"  CONTEXT: {p['context']}",
        "The conversation strictly alternates between the two speakers. For EACH turn decide, "
        "using the surrounding turns + context (NOT word-for-word), whether a context-aware viewer "
        "would understand the intended meaning: Y=clearly, P=partial/gist, N=not at all. Then give "
        "the overall gist a viewer reconstructs and the key recoverable facts.",
        "",
        "Turns (CHAR: model_hypothesis  ||  reference_intended):",
    ]
    for t in p["turns"]:
        lines.append(f"  {t['idx']:>2} {t['char'].upper():>5}: {t['hyp']!r}  ||  {t['ref']!r}")
    return "\n".join(lines)


def analyze(judgments_dir, reports_glob, out_path):
    rows = []
    for jp in sorted(glob.glob(os.path.join(judgments_dir, "*.json"))):
        j = json.load(open(jp, encoding="utf-8"))
        ov = j.get("overall", {})
        rows.append({"stem": j["stem"], "scene": j.get("scene"),
                     "n_turns": len(j.get("turns", [])),
                     "y": ov.get("y"), "p": ov.get("p"), "n": ov.get("n"),
                     "y_pct": ov.get("y_pct"), "yp_pct": ov.get("yp_pct")})
    agg = {}
    if rows:
        import numpy as np
        agg = {"n_conversations": len(rows),
               "mean_context_y_pct": round(float(np.mean([r["y_pct"] for r in rows if r["y_pct"] is not None])), 1),
               "mean_context_yp_pct": round(float(np.mean([r["yp_pct"] for r in rows if r["yp_pct"] is not None])), 1)}
    out = {"aggregate": agg, "conversations": rows}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[context-judge] {len(rows)} conversations; aggregate={agg} -> {out_path}")
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("prepare")
    pp.add_argument("--align-glob",
                    default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/**/align/*/alignment.json")
    pp.add_argument("--out", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/judge/judge_batch.json")
    pp.add_argument("--print-prompts", action="store_true")
    aa = sub.add_parser("analyze")
    aa.add_argument("--judgments", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/judge/judgments")
    aa.add_argument("--reports", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/**/report/report.csv")
    aa.add_argument("--out", default="/home/ubuntu/datasets/clients/egla_kafe/work/eval/judge/context_judge_summary.json")
    args = ap.parse_args()

    if args.cmd == "prepare":
        payloads = build_payloads(args.align_glob)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump({"n": len(payloads), "payloads": payloads}, open(args.out, "w"),
                  ensure_ascii=False, indent=2)
        print(f"[context-judge] prepared {len(payloads)} conversation payloads -> {args.out}")
        if args.print_prompts:
            for p in payloads:
                print("\n" + "=" * 90 + f"\n# {p['stem']} ({p['scene']})\n" + render_prompt(p))
    else:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        analyze(args.judgments, args.reports, args.out)


if __name__ == "__main__":
    main()
