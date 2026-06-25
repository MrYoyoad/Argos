#!/usr/bin/env python3
"""What can you actually understand after confidence-gating? — per word-category trust profile.

After dropping low-confidence content, characterize the SURVIVING words by linguistic category and
answer two questions:
  PRECISION (trust): when you see a GREEN word of category X, how often is it correct?
  RECALL  (coverage): of the reference words of category X, how many are correctly recovered (in green)?

Categories: NUMBER/DATE, ENTITY (names/places/orgs), NOUN, VERB, ADJ/ADV, FUNCTION.
Inputs: word_confidence.json (per-word prob + conf_class + is_numeric) and the aligned references
(alignment.json per segment). Per-word correctness = difflib alignment of hyp words to ref words.
"""
import argparse
import glob
import json
import os
import re
from difflib import SequenceMatcher

TOK = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
def toks(s): return TOK.findall((s or "").lower())

ENT_NUM = {"DATE", "TIME", "CARDINAL", "ORDINAL", "QUANTITY", "MONEY", "PERCENT"}
ENT_NAME = {"PERSON", "GPE", "LOC", "ORG", "FAC", "NORP", "EVENT", "PRODUCT", "WORK_OF_ART"}
BANDS = {"conf-high": "green", "conf-med": "yellow", "conf-low": "red"}
CATS = ["NUMBER", "ENTITY", "NOUN", "VERB", "ADJ_ADV", "FUNCTION"]


def categorize(word, is_numeric, tokens):
    """tokens: list of spaCy tokens covering this hyp word. Priority-based bucket."""
    if is_numeric or any(getattr(t, "like_num", False) or t.ent_type_ in ENT_NUM for t in tokens):
        return "NUMBER"
    if any(t.pos_ == "PROPN" or t.ent_type_ in ENT_NAME for t in tokens):
        return "ENTITY"
    pos = [t.pos_ for t in tokens]
    if "NOUN" in pos: return "NOUN"
    if "VERB" in pos: return "VERB"
    if any(p in ("ADJ", "ADV") for p in pos): return "ADJ_ADV"
    return "FUNCTION"


def map_words_to_tokens(hyp_words, doc):
    """Greedy: assign spaCy tokens to hyp words by consuming until the concatenated text matches."""
    out = [[] for _ in hyp_words]
    ti = 0
    toks_sp = [t for t in doc if not t.is_space]
    for wi, w in enumerate(hyp_words):
        target = re.sub(r"[^a-z0-9]", "", w.lower())
        acc = ""
        while ti < len(toks_sp) and acc != target:
            out[wi].append(toks_sp[ti])
            acc += re.sub(r"[^a-z0-9]", "", toks_sp[ti].text.lower())
            ti += 1
            if target and acc and not target.startswith(acc) and not acc.startswith(target):
                break  # drift; stop consuming for this word
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--word-conf", required=True)
    ap.add_argument("--align-glob", required=True, help="alignment.json files for per-seg refs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="scene1+2")
    args = ap.parse_args()

    import spacy
    nlp = spacy.load("en_core_web_sm")
    wc = {}
    for wcf in args.word_conf.split(","):
        wc.update(json.load(open(wcf)))
    # aligned refs per seg (merge across runs)
    ref = {}
    for g in args.align_glob.split(","):
        for ap_ in glob.glob(g):
            d = json.load(open(ap_))
            for s in d["segments"]:
                ref[s["seg_id"]] = s["ref"]

    # precision tallies: [band][cat] -> [correct, total]; recall: [cat] -> [recovered, recovered_green, total]
    prec = {b: {c: [0, 0] for c in CATS} for b in ("green", "yellow", "red")}
    rec = {c: [0, 0, 0] for c in CATS}
    leak_examples = []  # green-but-wrong, esp NUMBER/ENTITY

    for seg_id, e in wc.items():
        if seg_id not in ref:
            continue
        words = e.get("words", [])
        hyp_words = [w["word"] for w in words]
        ref_words = toks(ref[seg_id])
        if not hyp_words:
            continue
        # per-hyp-word correctness via alignment to ref
        sm = SequenceMatcher(None, [w.lower() for w in hyp_words], ref_words)
        correct = [False] * len(hyp_words)
        ref_recovered = [False] * len(ref_words)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i1, i2): correct[k] = True
                for k in range(j1, j2): ref_recovered[k] = True
        # POS tag hyp
        doc = nlp(" ".join(hyp_words))
        wtoks = map_words_to_tokens(hyp_words, doc)
        for wi, w in enumerate(words):
            band = BANDS.get(w.get("conf_class"), "red")
            cat = categorize(w["word"], w.get("is_numeric", False), wtoks[wi])
            prec[band][cat][1] += 1
            if correct[wi]:
                prec[band][cat][0] += 1
            elif band == "green" and cat in ("NUMBER", "ENTITY"):
                leak_examples.append({"seg": seg_id, "word": w["word"], "cat": cat,
                                      "prob": round(w["prob"], 3)})
        # recall: tag ref words, mark recovered + whether the matching hyp word was green
        rdoc = nlp(" ".join(ref_words))
        rtoks = map_words_to_tokens(ref_words, rdoc)
        # map ref index -> was the equal-matched hyp word green?
        green_ref = [False] * len(ref_words)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for off in range(i2 - i1):
                    hi = i1 + off; rj = j1 + off
                    if BANDS.get(words[hi].get("conf_class")) == "green":
                        green_ref[rj] = True
        for rj, rw in enumerate(ref_words):
            cat = categorize(rw, False, rtoks[rj])
            rec[cat][2] += 1
            if ref_recovered[rj]:
                rec[cat][0] += 1
                if green_ref[rj]:
                    rec[cat][1] += 1

    def pct(a, b): return round(100 * a / b, 1) if b else None
    result = {"label": args.label,
              "precision_trust": {b: {c: {"p_correct": pct(prec[b][c][0], prec[b][c][1]),
                                          "n": prec[b][c][1]} for c in CATS}
                                  for b in ("green", "yellow", "red")},
              "recall_coverage": {c: {"recovered_%": pct(rec[c][0], rec[c][2]),
                                       "recovered_green_%": pct(rec[c][1], rec[c][2]),
                                       "n_ref": rec[c][2]} for c in CATS},
              "green_leak_examples": leak_examples[:40]}
    json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=2)

    # pretty print
    print(f"\n===== {args.label}: WHAT YOU CAN TRUST after gating to GREEN words =====")
    print(f"{'category':>10} | {'GREEN P(correct)':>16} {'n':>5} | {'YELLOW':>8} | {'RED':>8}")
    for c in CATS:
        g = pct(prec['green'][c][0], prec['green'][c][1]); gn = prec['green'][c][1]
        y = pct(prec['yellow'][c][0], prec['yellow'][c][1]); r = pct(prec['red'][c][0], prec['red'][c][1])
        print(f"{c:>10} | {str(g)+'%':>15} {gn:>5} | {str(y)+'%':>7} | {str(r)+'%':>7}")
    print(f"\n===== COVERAGE: of reference words, how many recovered (and in green) =====")
    print(f"{'category':>10} | {'recovered%':>10} {'green-recovered%':>16} {'n_ref':>6}")
    for c in CATS:
        print(f"{c:>10} | {str(pct(rec[c][0],rec[c][2]))+'%':>10} "
              f"{str(pct(rec[c][1],rec[c][2]))+'%':>16} {rec[c][2]:>6}")
    print(f"\ngreen-but-WRONG NUMBER/ENTITY examples (the dangerous leak): {len(leak_examples)}")
    for ex in leak_examples[:12]:
        print(f"   '{ex['word']}' ({ex['cat']}, prob {ex['prob']}) in {ex['seg']}")
    print(f"\n-> {args.out}")


if __name__ == "__main__":
    main()
