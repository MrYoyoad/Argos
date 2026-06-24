#!/usr/bin/env python3
"""Parse a two-character dialogue script (``Speaker: line``) into structured JSON.

The tokenizer mirrors VSP-LLM/scripts/make_report.py ``toks()`` exactly so that the
references we emit later score identically to the model's hypotheses:

    re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.strip().lower())

Output schema (one file per scene), consumed by align_script_to_segments.py:

    {
      "scene": "scene1",
      "title": "...",                      # optional, from --title
      "speakers": ["emma", "jake"],        # in first-appearance order
      "first_speaker": "emma",
      "n_turns": 47,
      "turns": [
        {"idx": 0, "speaker": "emma", "raw": "...", "tokens": ["you","look",...]},
        ...
      ],
      "tokens_flat": ["you","look",...],   # all turn tokens concatenated, in order
      "token_turn_idx": [0,0,0,...]        # parallel to tokens_flat: owning turn idx
    }
"""
import argparse
import json
import re
import sys

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def toks(s: str):
    return TOKEN_RE.findall((s or "").strip().lower())


def parse_script(text: str, scene: str, title: str = "") -> dict:
    turns = []
    speakers = []
    tokens_flat = []
    token_turn_idx = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        speaker, _, said = line.partition(":")
        speaker = speaker.strip().lower()
        said = said.strip()
        if not speaker:
            continue
        if speaker not in speakers:
            speakers.append(speaker)
        idx = len(turns)
        tk = toks(said)
        turns.append({"idx": idx, "speaker": speaker, "raw": said, "tokens": tk})
        for t in tk:
            tokens_flat.append(t)
            token_turn_idx.append(idx)
    return {
        "scene": scene,
        "title": title,
        "speakers": speakers,
        "first_speaker": speakers[0] if speakers else None,
        "n_turns": len(turns),
        "turns": turns,
        "tokens_flat": tokens_flat,
        "token_turn_idx": token_turn_idx,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="raw dialogue txt (Speaker: line)")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--scene", required=True, help="scene id, e.g. scene1")
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    with open(args.inp, encoding="utf-8") as f:
        text = f.read()
    parsed = parse_script(text, args.scene, args.title)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print(f"[parse] {args.scene}: {parsed['n_turns']} turns, "
          f"{len(parsed['tokens_flat'])} tokens, speakers={parsed['speakers']} -> {args.out}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
