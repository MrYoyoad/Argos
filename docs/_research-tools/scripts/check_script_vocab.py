#!/usr/bin/env python3
"""Check a conversation-script markdown against the LRS3 safe vocabulary.

The VSP-LLM decoder was trained on LRS3 (TED-style spoken English). Scripts
written for lip-reading demos decode best when they stay inside vocabulary the
model has actually seen and historically gets right. This tool scans the spoken
lines of a script and flags every token that falls into a risk category:

  OUT_OF_VOCAB   not in the LRS3 safe-vocab CSV and not in the small embedded
                 common-English allowlist
  ENTITY         capitalized mid-sentence (not sentence-initial) or in the
                 names gazetteer — named entities are missed in ~85% of
                 benchmark segments (NE F1 = 38.9%)
  NUMBER         contains digits, or is a number word above ten
  LOW_ACCURACY   in vocab but historically decoded badly: hist_acc < 0.35
                 with hist_n >= 5 (B3 per-word diagnostic, 23,261 words)

Dialogue convention: lines formatted as `**SPEAKER:** text ...` are treated as
spoken. If a file contains no such lines, plain paragraphs are used as a
fallback (headings, lists, block quotes, code fences, and parenthesized stage
directions are skipped).

Usage:
    python3 check_script_vocab.py <script.md> [--vocab <csv>] [--json]

Exit code 0 if no flags were raised, 1 otherwise.
Default vocab: ../datasets/lrs3_safe_vocab.csv relative to this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

DEFAULT_VOCAB = Path(__file__).resolve().parent.parent / "datasets" / "lrs3_safe_vocab.csv"

LOW_ACC_THRESHOLD = 0.35
LOW_ACC_MIN_N = 5

# Small common-English allowlist: glue words and everyday spoken words that are
# safe regardless of whether they cleared the frequency bar in the 197-transcript
# LRS3 sample. Content-word coverage lives in the CSV, not here.
COMMON_ALLOWLIST = set("""
a i an of to in it is as at be by or so do if on up us am no me my we he she
the and but for not you are was were they them their his her him its our your
yours mine ours out who how all can may has had have this that these those
what when where why with from into onto over under about after before again
then than there here just only also very too more most some any each both few
own same such nor once did does done being been will would should could shall
must might let get got go goes going come came make made say said see saw
know knew think thought want yes okay please thanks thank hello hi bye
good bad big small new old right wrong long short high low one two three four
five six seven eight nine ten day days time times way ways thing things
people person man woman men women child children friend friends home house
work works word words talk talks look looks feel feels really always never
sometimes maybe well much many little lot bit still even ever every because
oh yeah hey now today tomorrow yesterday morning night around back down off
give take put keep help start stop open close find need use tell ask try
""".split())

# Names/places gazetteer — flagged as ENTITY even when sentence-initial.
NAMES_GAZETTEER = set("""
america american england britain france germany china japan india russia
israel africa europe asia australia canada mexico london paris york boston
chicago texas california washington vegas hollywood google facebook twitter
youtube amazon apple microsoft tesla nasa january february march april june
july august september october november december monday tuesday wednesday
thursday friday saturday sunday christmas easter thanksgiving john james
robert michael william david richard joseph thomas charles chris daniel paul
mark donald george kenneth steven edward brian ronald anthony kevin jason
matt jeff mary patricia jennifer linda elizabeth barbara susan jessica sarah
karen nancy lisa betty margaret sandra ashley kimberly emily donna michelle
carol amanda emma jake jesus obama trump biden clinton bush reagan lincoln
einstein newton darwin shakespeare
""".split())

NUMBER_WORDS_ABOVE_TEN = set("""
eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen
twenty thirty forty fifty sixty seventy eighty ninety hundred thousand
million billion trillion dozen twentieth thirtieth fortieth fiftieth
hundredth thousandth millionth
""".split())

DIALOGUE_RE = re.compile(r"^\s*\*\*([^*]+?):?\*\*:?\s*(.+)$")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z']*|\d[\d,.:]*")
SENT_SPLIT_RE = re.compile(r"[.!?]+")


def extract_spoken_lines(text: str) -> list[tuple[int, str]]:
    """Return (line_number, spoken_text) pairs.

    Prefers `**SPEAKER:** text` dialogue lines; falls back to plain paragraphs
    when the file contains no dialogue-formatted lines.
    """
    dialogue: list[tuple[int, str]] = []
    plain: list[tuple[int, str]] = []
    in_fence = False
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        m = DIALOGUE_RE.match(line)
        if m:
            dialogue.append((i, m.group(2)))
            continue
        # plain-paragraph fallback candidates: skip markdown structure and
        # parenthesized/italicized stage directions
        if line.startswith(("#", ">", "-", "*", "|", "(", "[", "_")):
            continue
        plain.append((i, line))
    return dialogue if dialogue else plain


def strip_directions(text: str) -> str:
    """Remove parenthesized/bracketed stage directions and italics markers."""
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    return text.replace("*", " ").replace("_", " ")


def load_vocab(path: Path) -> tuple[set[str], dict[str, tuple[int, float]]]:
    """Return (vocab_words, {word: (hist_n, hist_acc)}). Skips '#' comment lines."""
    vocab: set[str] = set()
    hist: dict[str, tuple[int, float]] = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(row for row in f if not row.startswith("#"))
        for row in reader:
            w = row["word"].lower()
            vocab.add(w)
            if row.get("hist_n") and row.get("hist_acc"):
                hist[w] = (int(row["hist_n"]), float(row["hist_acc"]))
    return vocab, hist


def check_line(line_no: int, text: str, vocab: set[str],
               hist: dict[str, tuple[int, float]], flags: dict[str, list[dict]]) -> None:
    text = strip_directions(text)
    for sentence in SENT_SPLIT_RE.split(text):
        tokens = list(TOKEN_RE.finditer(sentence))
        for idx, m in enumerate(tokens):
            tok = m.group(0)
            low = tok.lower().strip("'")
            if not low or low == "i" or low.startswith("i'"):
                continue
            base = low.rstrip("'").replace("'s", "") if low.endswith("'s") else low

            # NUMBER: digits or number words above ten
            if any(c.isdigit() for c in tok) or base in NUMBER_WORDS_ABOVE_TEN:
                flags["NUMBER"].append({"word": tok, "line": line_no})
                continue
            # ENTITY: gazetteer hit, or capitalized mid-sentence
            if base in NAMES_GAZETTEER or (idx > 0 and tok[0].isupper()):
                flags["ENTITY"].append({"word": tok, "line": line_no})
                continue
            # LOW_ACCURACY: in vocab but historically decoded badly
            h = hist.get(low) or hist.get(base)
            if h and h[0] >= LOW_ACC_MIN_N and h[1] < LOW_ACC_THRESHOLD:
                flags["LOW_ACCURACY"].append(
                    {"word": tok, "line": line_no, "hist_n": h[0], "hist_acc": h[1]})
                continue
            # OUT_OF_VOCAB: neither in the CSV nor the common allowlist.
            # A simple depluralized form of an in-vocab word also passes.
            candidates = {low, base}
            for c in (low, base):
                if c.endswith("es"):
                    candidates.add(c[:-2])
                if c.endswith("s"):
                    candidates.add(c[:-1])
            if not any(c in vocab or c in COMMON_ALLOWLIST for c in candidates):
                flags["OUT_OF_VOCAB"].append({"word": tok, "line": line_no})


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check a script markdown against the LRS3 safe vocabulary.")
    ap.add_argument("script", type=Path, help="script markdown file to check")
    ap.add_argument("--vocab", type=Path, default=DEFAULT_VOCAB,
                    help=f"safe-vocab CSV (default: {DEFAULT_VOCAB})")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit machine-readable JSON instead of text report")
    args = ap.parse_args()

    if not args.script.is_file():
        print(f"error: script not found: {args.script}", file=sys.stderr)
        return 2
    if not args.vocab.is_file():
        print(f"error: vocab CSV not found: {args.vocab}", file=sys.stderr)
        return 2

    vocab, hist = load_vocab(args.vocab)
    lines = extract_spoken_lines(args.script.read_text(errors="replace"))
    flags: dict[str, list[dict]] = {
        "OUT_OF_VOCAB": [], "ENTITY": [], "NUMBER": [], "LOW_ACCURACY": []}
    for line_no, text in lines:
        check_line(line_no, text, vocab, hist, flags)

    n_flags = sum(len(v) for v in flags.values())
    if args.as_json:
        print(json.dumps({
            "script": str(args.script), "vocab": str(args.vocab),
            "spoken_lines": len(lines), "total_flags": n_flags,
            "flags": flags, "ok": n_flags == 0,
        }, indent=2))
    else:
        print(f"Checked {args.script} ({len(lines)} spoken lines, "
              f"vocab: {len(vocab)} words)")
        for cat in ("OUT_OF_VOCAB", "ENTITY", "NUMBER", "LOW_ACCURACY"):
            hits = flags[cat]
            print(f"\n{cat}: {len(hits)}")
            for h in hits:
                extra = (f"  (hist_acc={h['hist_acc']:.2f}, n={h['hist_n']})"
                         if cat == "LOW_ACCURACY" else "")
                print(f"  line {h['line']:>4}: {h['word']}{extra}")
        verdict = "OK — script stays inside the safe vocabulary." if n_flags == 0 \
            else f"{n_flags} flag(s) — consider rewording before filming."
        print(f"\n{verdict}")
    return 0 if n_flags == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
