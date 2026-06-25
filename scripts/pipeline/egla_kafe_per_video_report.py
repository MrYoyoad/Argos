#!/usr/bin/env python3
"""Per-video 'what is understood' report — one row per conversation.

Assembles, per video: source (iPhone-4K vs client-camera), script (Emma/Jake vs Military),
speakers (face-ID), camera angle, model metrics (IS, useful%), the context-judge gist, and the
recovered facts. Writes a ranked markdown table + detail.
"""
import csv, glob, json, os, re

BASE = "/home/ubuntu/datasets/clients/egla_kafe/work/eval"
SCRIPT_NAME = {"scene1": "Emma/Jake (airport)", "scene2": "Military (planning)"}


def stem_of(utt):
    m = re.match(r"^(.*)_(\d{2})_(\d{6})_(\d{6})$", utt)
    return m.group(1) if m else utt.rsplit("_", 3)[0]


def main():
    idx = {e["stem"]: e for e in json.load(open(f"{BASE}/index.json"))["entries"]}
    fid = json.load(open(f"{BASE}/face_id.json")).get("per_crop", {})
    # per-stem metrics from both reports
    metrics = {}
    for rep in (f"{BASE}/run_scene12_all/report/report.csv", f"{BASE}/run_shaam_all/report/report.csv"):
        if not os.path.exists(rep):
            continue
        for r in csv.DictReader(open(rep)):
            st = stem_of(r["utt_id"])
            try: is_ = float(r["is_score"])
            except: continue
            metrics.setdefault(st, []).append(is_)
    judg = {}
    for jp in glob.glob(f"{BASE}/judge/judgments/*.json"):
        j = json.load(open(jp)); judg[j["stem"]] = j

    rows = []
    for stem, j in judg.items():
        e = idx.get(stem, {})
        src = "iPhone-4K" if e.get("source_type") == "master" else "camera-screenrec"
        persons = sorted({fid.get(f"{stem}__left", {}).get("person") if isinstance(fid.get(f"{stem}__left"), dict) else fid.get(f"{stem}__left"),
                          fid.get(f"{stem}__right", {}).get("person") if isinstance(fid.get(f"{stem}__right"), dict) else fid.get(f"{stem}__right")} - {None})
        if not persons:
            persons = e.get("speakers_in_name", [])
        iss = metrics.get(stem, [])
        rows.append({
            "stem": stem, "source": src, "script": SCRIPT_NAME.get(j.get("scene"), j.get("scene")),
            "speakers": "+".join(persons) if persons else "?", "angle": e.get("angle", "?"),
            "n": len(iss), "IS": round(sum(iss)/len(iss), 2) if iss else None,
            "useful_pct": round(100*sum(1 for v in iss if v >= 2)/len(iss), 0) if iss else None,
            "ctx_yp": j["overall"]["yp_pct"], "gist": j["gist"], "facts": j.get("recoverable_facts", []),
        })
    rows.sort(key=lambda r: -(r["ctx_yp"] or 0))

    L = ["# Egla-Kafe — per-video: what is understood",
         "",
         "Ranked best→worst by context-aware recovery (Y+P = fraction of turns a context-aware viewer grasps).",
         "Source: iPhone-4K = native 4K masters; camera-screenrec = client 380–440px screen recordings.",
         "",
         "| # | video | source | script | speakers | angle | IS | useful% | **context Y+P** | what is understood |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        L.append(f"| {i} | {r['stem']} | {r['source']} | {r['script']} | {r['speakers']} | {r['angle']} | "
                 f"{r['IS']} | {r['useful_pct']}% | **{r['ctx_yp']}%** | {r['gist']} |")
    L += ["", "## Recovered facts per video (what you can actually take away)", ""]
    for r in rows:
        facts = ", ".join(r["facts"]) if r["facts"] else "— (nothing reliably recovered)"
        L.append(f"- **{r['stem']}** ({r['source']}, {r['script']}, Y+P {r['ctx_yp']}%): {facts}")
    out = "/home/ubuntu/docs/evaluation/egla_kafe/per_video_understanding.md"
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
