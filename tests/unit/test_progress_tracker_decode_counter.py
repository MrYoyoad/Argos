"""
Unit tests for the decode-phase per-segment counter in ProgressTracker.

The counter feeds the UI's "X / N segments decoded" line on the wait banner
during pipeline stage 7 (LLM decoding). Two signals drive it:

  - Total N: emitted by lib/decode.sh ("Decoding N segments...") and
    overridden by vsp_llm_decode.py ("Decode dataset loaded: N samples")
    once the dataset has actually loaded.
  - Per-segment increment: ^HYP: lines from vsp_llm_decode.py:409 give a
    smooth +1 per sample; "Incremental flush at N samples" (every 25
    samples) reconciles the absolute count, self-healing if any HYP is
    dropped under load.

A stage guard restricts increments to current_stage_id == "decode" so
out-of-order pipe writes can't bump the counter before stage 7 begins.
"""
import sys
from pathlib import Path

import pytest

# vsp-ui uses a relative import "from ..config import ...", so we need the
# `app` package on sys.path as a top-level package.
sys.path.insert(0, str(Path("/home/ubuntu/vsp-ui")))

from app.services.progress_tracker import ProgressTracker  # noqa: E402


@pytest.fixture
def tracker():
    t = ProgressTracker()
    t.reset(run_id="test")
    return t


def _enter_decode(tracker):
    """Drive the tracker into stage 7 by feeding the stage marker."""
    tracker.process_line(">>> [7] Running VSP-LLM decode")
    assert tracker.state.current_stage_id == "decode"


class TestDecodeTotal:
    def test_bash_total_parsed(self, tracker):
        tracker.process_line("INFO: Decoding 1497 segments...")
        assert tracker.state.decode_total == 1497

    def test_python_total_parsed(self, tracker):
        tracker.process_line("Decode dataset loaded: 1497 samples")
        assert tracker.state.decode_total == 1497

    def test_bash_total_does_not_decrement(self, tracker):
        # Two bash signals: max() wins.
        tracker.process_line("Decoding 1500 segments...")
        tracker.process_line("Decoding 1497 segments...")
        assert tracker.state.decode_total == 1500

    def test_python_total_overrides_bash(self, tracker):
        # Python is authoritative — overrides even if smaller than bash count.
        tracker.process_line("Decoding 1500 segments...")
        tracker.process_line("Decode dataset loaded: 1497 samples")
        assert tracker.state.decode_total == 1497

    def test_total_pattern_does_not_match_other_log_lines(self, tracker):
        tracker.process_line("Decoding the configuration file...")
        tracker.process_line("Some random log line about samples")
        assert tracker.state.decode_total == 0


class TestDecodeIncrement:
    def test_hyp_increments_in_decode_stage(self, tracker):
        _enter_decode(tracker)
        for _ in range(5):
            tracker.process_line("HYP:make yourself at home")
        assert tracker.state.decode_done == 5

    def test_hyp_outside_decode_stage_ignored(self, tracker):
        # Before any stage transition: HYP must not count.
        tracker.process_line("HYP:should not count")
        assert tracker.state.decode_done == 0

    def test_hyp_during_other_stage_ignored(self, tracker):
        tracker.process_line(">>> [3] Running ASR")
        tracker.process_line("HYP:should not count")
        assert tracker.state.decode_done == 0

    def test_hyp_only_matches_at_line_start(self, tracker):
        # Lines that happen to contain "HYP:" mid-string must not count.
        _enter_decode(tracker)
        tracker.process_line("Some output: HYP:embedded should not count")
        assert tracker.state.decode_done == 0


class TestFlushReconciliation:
    def test_flush_sets_absolute_count(self, tracker):
        _enter_decode(tracker)
        for _ in range(3):
            tracker.process_line("HYP:line")
        assert tracker.state.decode_done == 3
        tracker.process_line("Incremental flush at 25 samples → /tmp/hypo.json")
        assert tracker.state.decode_done == 25

    def test_flush_does_not_decrement(self, tracker):
        # If HYP-counting is ahead of the flush checkpoint, keep the higher value.
        _enter_decode(tracker)
        for _ in range(30):
            tracker.process_line("HYP:line")
        tracker.process_line("Incremental flush at 25 samples → /tmp/hypo.json")
        assert tracker.state.decode_done == 30

    def test_flush_outside_decode_stage_ignored(self, tracker):
        tracker.process_line("Incremental flush at 25 samples → /tmp/hypo.json")
        assert tracker.state.decode_done == 0


class TestStageReset:
    def test_reset_on_decode_entry(self, tracker):
        # Simulate stale counters (e.g., a re-run within the same UI session).
        tracker.state.decode_done = 10
        tracker.state.decode_total = 50
        _enter_decode(tracker)
        assert tracker.state.decode_done == 0
        assert tracker.state.decode_total == 0

    def test_no_reset_on_other_stage_entries(self, tracker):
        _enter_decode(tracker)
        tracker.process_line("HYP:line")
        tracker.process_line("HYP:line")
        # Transition to client_outputs (stage after decode) — counters preserved
        # so the final "N / N" can render briefly before the bar advances.
        tracker.process_line(">>> [8] Building client outputs")
        assert tracker.state.decode_done == 2


class TestSerialization:
    def test_to_dict_exposes_counters(self, tracker):
        _enter_decode(tracker)
        tracker.process_line("Decoding 100 segments...")
        tracker.process_line("HYP:line")
        d = tracker.state.to_dict()
        assert d["decode_total"] == 100
        assert d["decode_done"] == 1

    def test_to_dict_default_values(self, tracker):
        d = tracker.state.to_dict()
        assert d["decode_total"] == 0
        assert d["decode_done"] == 0


class TestEndToEndFlow:
    def test_full_decode_lifecycle(self, tracker):
        # Realistic order from lib/decode.sh + vsp_llm_decode.py:
        #   >>> [7] marker (log_stage "7")
        #   "Decoding N segments..." (bash)
        #   "Decode dataset loaded: N samples" (python, after model load)
        #   N × HYP lines, with "Incremental flush at K" every 25 samples
        tracker.process_line(">>> [7] Running VSP-LLM decode")
        assert tracker.state.current_stage_id == "decode"
        assert tracker.state.decode_done == 0
        assert tracker.state.decode_total == 0

        tracker.process_line("Decoding 50 segments...")
        assert tracker.state.decode_total == 50

        tracker.process_line("Decode dataset loaded: 50 samples")
        assert tracker.state.decode_total == 50

        for _ in range(25):
            tracker.process_line("HYP:line")
        tracker.process_line("Incremental flush at 25 samples → /tmp/hypo.json")
        assert tracker.state.decode_done == 25

        for _ in range(25):
            tracker.process_line("HYP:line")
        tracker.process_line("Incremental flush at 50 samples → /tmp/hypo.json")
        assert tracker.state.decode_done == 50
        assert tracker.state.decode_total == 50
