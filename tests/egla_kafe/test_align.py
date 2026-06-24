"""Unit tests for align_script_to_segments.py — pure-logic, no video/GPU."""
import os
import tempfile

import align_script_to_segments as A


def make_script():
    raw = [
        ("emma", "the quick brown fox runs"),
        ("jake", "jumps over a very lazy dog"),
        ("emma", "pack my box with five dozen jugs"),
        ("jake", "the wizards quickly jumped sideways"),
        ("emma", "bright vixens jump for candy quickly"),
        ("jake", "sphinx of black quartz judge my vow"),
    ]
    turns = [{"idx": i, "speaker": sp, "raw": t, "tokens": A.toks(t)}
             for i, (sp, t) in enumerate(raw)]
    return {"scene": "scene1", "speakers": ["emma", "jake"], "first_speaker": "emma",
            "n_turns": len(turns), "turns": turns}


def seg(i, side, hyp, t0):
    return {"seg_id": f"s_{i:02d}_{t0:06d}_{t0+50:06d}", "side": side, "t0": t0, "hyp": hyp}


def test_clean_alignment_maps_each_segment_to_its_turn():
    script = make_script()
    s2c = {"left": "emma", "right": "jake"}
    seg_records = []
    for i, t in enumerate(script["turns"]):
        side = "left" if t["speaker"] == "emma" else "right"
        seg_records.append(seg(i, side, t["raw"], i * 100))
    recs = A.build_references(seg_records, script, s2c)
    assert [r["ref_turn_idxs"][0] for r in recs] == list(range(6))
    assert all(r["align_conf"] > 0.9 for r in recs)


def test_dropped_words_and_repeats_still_map_correctly():
    script = make_script()
    s2c = {"left": "emma", "right": "jake"}
    # drop/duplicate some words but keep gist + order
    noisy = ["the brown fox runs runs", "jumps over lazy dog", "pack box with five jugs",
             "the wizards jumped sideways", "bright vixens jump candy", "sphinx black quartz judge vow"]
    seg_records = []
    for i, (t, h) in enumerate(zip(script["turns"], noisy)):
        side = "left" if t["speaker"] == "emma" else "right"
        seg_records.append(seg(i, side, h, i * 100))
    recs = A.build_references(seg_records, script, s2c)
    assert [r["ref_turn_idxs"][0] for r in recs] == list(range(6))


def test_alignment_is_monotonic():
    script = make_script()
    s2c = {"left": "emma", "right": "jake"}
    # one segment's hyp better matches a LATER turn; monotonicity must still hold
    seg_records = [
        seg(0, "left", "the quick brown fox runs", 0),
        seg(1, "right", "sphinx of black quartz judge my vow", 100),  # looks like turn 5
        seg(2, "left", "pack my box with five dozen jugs", 200),
    ]
    recs = A.build_references(seg_records, script, s2c)
    idxs = [r["ref_turn_idxs"][0] for r in recs if r["ref_turn_idxs"]]
    assert idxs == sorted(idxs), f"non-monotonic: {idxs}"


def test_all_wrong_hypothesis_flags_low_conf_and_falls_back_to_structure():
    """Garbage model output -> every row flagged conf~0, but the strict-alternation prior
    still yields the best-possible (structural diagonal) reference for manual review."""
    script = make_script()
    s2c = {"left": "emma", "right": "jake"}
    seg_records = [seg(i, "left" if i % 2 == 0 else "right", "zzz qqq xkcd wob", i * 100)
                   for i in range(6)]
    recs = A.build_references(seg_records, script, s2c)
    # all flagged low-confidence
    assert all(r["align_conf"] < 0.25 for r in recs)
    # graceful structural fallback: assignments are the monotonic diagonal on the right character
    idxs = [r["ref_turn_idxs"][0] for r in recs if r["ref_turn_idxs"]]
    assert idxs == sorted(idxs)
    assert all(s2c[r["side"]] == r["char"] for r in recs if r["ref_turn_idxs"])


def test_infer_side_to_char():
    script = make_script()
    s2c = A.infer_side_to_char([{"side": "right", "seg_id": "x_00_0_1"}], script)
    assert s2c == {"right": "emma", "left": "jake"}


def test_wrd_files_one_word_per_line():
    script = make_script()
    s2c = {"left": "emma", "right": "jake"}
    seg_records = [seg(0, "left", script["turns"][0]["raw"], 0)]
    recs = A.build_references(seg_records, script, s2c)
    with tempfile.TemporaryDirectory() as d:
        A.write_wrd_files(recs, d)
        p = os.path.join(d, recs[0]["seg_id"] + ".wrd")
        assert os.path.exists(p)
        lines = open(p).read().split()
        words = open(p).read().splitlines()
        assert words == A.toks(recs[0]["ref"])
        assert all(" " not in w for w in words)


def test_token_sim_bounds():
    assert A.token_sim([], []) == 1.0
    assert A.token_sim(["a"], []) == 0.0
    assert A.token_sim(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    assert 0.0 < A.token_sim(["a", "b", "c"], ["a", "b", "x"]) < 1.0
