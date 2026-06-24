"""Unit tests for build_active_speaker_stream.py pure logic."""
import re

import numpy as np
import build_active_speaker_stream as S


def test_seg_id_format():
    sid = S.seg_id("s1_tomer_yoad_1", 3, 4.0, 9.2, fps_model=25)
    assert sid == "s1_tomer_yoad_1_03_000100_000230"
    assert re.search(r"_\d{2}_\d{6}_\d{6}$", sid)


def test_timeline_switches_at_midpoint():
    fps = 30.0
    n = 300  # 10s
    eL = np.concatenate([np.ones(150) * 1.0, np.ones(150) * 0.05])
    eR = np.concatenate([np.ones(150) * 0.05, np.ones(150) * 1.0])
    active, turns = S.build_active_timeline(eL, eR, fps, smooth_win=0.2, min_dwell=0.3)
    assert len(turns) == 2
    assert turns[0][0] == "left" and turns[1][0] == "right"
    # switch near t=5s
    assert abs(turns[0][2] - 5.0) < 0.6


def test_hysteresis_collapses_chatter():
    fps = 30.0
    rng = np.random.RandomState(0)
    # left genuinely dominant but with noisy near-ties
    eL = 1.0 + rng.rand(300) * 0.3
    eR = 0.9 + rng.rand(300) * 0.3
    active, turns = S.build_active_timeline(eL, eR, fps, smooth_win=0.3, min_dwell=0.5)
    # with min_dwell 0.5s, we should not get hundreds of micro-turns
    assert len(turns) <= 4


def test_merge_never_crosses_side():
    # strictly alternating turns
    turns = [("left", 0, 2), ("right", 2, 4), ("left", 4, 6), ("right", 6, 8)]
    segs = S.merge_turns_to_segments(turns, "stem", merge_target=6.0, min_dwell=0.4)
    # each segment is single-side
    for seg in segs:
        involved = {turns[i][0] for i in seg["turn_idxs"]}
        assert involved == {seg["side"]}
    # seg ids well formed
    for seg in segs:
        assert re.search(r"_\d{2}_\d{6}_\d{6}$", seg["seg_id"])


def test_merge_same_side_within_target():
    # consecutive same-side turns should merge up to target
    turns = [("left", 0, 2), ("left", 2, 4), ("right", 4, 6)]
    segs = S.merge_turns_to_segments(turns, "stem", merge_target=6.0, min_dwell=0.4)
    assert len(segs) == 2
    assert segs[0]["side"] == "left" and segs[0]["turn_idxs"] == [0, 1]


def test_rolling_std_detects_oscillation():
    osc = np.tile([0.0, 0.2], 50)   # oscillating (speech-like)
    flat = np.ones(100) * 0.1       # sustained (smile-like)
    so = S._rolling_std(osc, 8)
    sf = S._rolling_std(flat, 8)
    assert so.mean() > sf.mean() * 5
