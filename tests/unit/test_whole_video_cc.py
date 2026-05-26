"""Tests for the whole_video_cc.json sidecar + server-side resolution.

Covers:
  1. `build_whole_video_cc()` collapses segments into per-parent-video
     entries with correct frame→sec timing.
  2. Stripped flag round-trips through the payload.
  3. `_resolve_original_video()` resolution order: INPUT_DIR first,
     then INPUT_DIR/.excluded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make VSP-LLM scripts importable.
SCRIPTS_DIR = Path("/home/ubuntu/VSP-LLM/scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_client_demo_report as gen  # noqa: E402


def _fixture_record(utt_id, *, ref="", hyp="", words=None, sent_conf=0.9,
                    stripped=False):
    return {
        "utt_id": utt_id,
        "ref": ref,
        "hyp": hyp,
        "words": words or [],
        "sentence_confidence": sent_conf,
        "stripped": stripped,
    }


def test_build_whole_video_cc_collapses_segments_under_parent():
    """3 segments of the same parent video → one entry, sorted by start_sec."""
    recs = [
        _fixture_record("Obama_02_000450_000749",
                        words=[{"word": "c", "prob": 0.9, "conf_class": "conf-high"}]),
        _fixture_record("Obama_00_000000_000299",
                        words=[{"word": "a", "prob": 0.9, "conf_class": "conf-high"}]),
        _fixture_record("Obama_01_000150_000449",
                        words=[{"word": "b", "prob": 0.9, "conf_class": "conf-high"}]),
    ]
    payload = gen.build_whole_video_cc(recs)
    assert "videos" in payload
    assert list(payload["videos"].keys()) == ["Obama"]
    obama = payload["videos"]["Obama"]
    starts = [seg["start_sec"] for seg in obama["segments"]]
    assert starts == sorted(starts), f"segments must be sorted by start_sec: {starts}"
    # Frame→sec at PIPELINE_FPS (25 fps).
    assert obama["segments"][0]["start_sec"] == pytest.approx(0.0)
    assert obama["segments"][0]["end_sec"] == pytest.approx(11.96)
    assert obama["segments"][1]["start_sec"] == pytest.approx(6.0)
    assert obama["segments"][1]["end_sec"] == pytest.approx(17.96)
    assert obama["duration_sec"] == pytest.approx(29.96)


def test_stripped_flag_round_trips():
    """A stripped record produces stripped=True in the sidecar payload."""
    rec = _fixture_record(
        "Obama_00_000000_000299",
        words=[{"word": "x", "prob": 0.5, "conf_class": "conf-stripped"}],
        sent_conf=0.5, stripped=True,
    )
    payload = gen.build_whole_video_cc([rec])
    seg = payload["videos"]["Obama"]["segments"][0]
    assert seg["stripped"] is True
    assert seg["sentence_confidence"] == pytest.approx(0.5)


def test_frame_to_seconds_conversion():
    """Segment id Obama_00_000150_000450 → start_sec=6.0, end_sec=18.0 at 25 fps."""
    start, end = gen._segment_time_window("Obama_00_000150_000450")
    assert start == pytest.approx(6.0)
    assert end == pytest.approx(18.0)
    # Non-segmented id falls through to zeros.
    assert gen._segment_time_window("plain_id") == (0.0, 0.0)


def test_resolve_original_video_prefers_input_dir(tmp_path, monkeypatch):
    """When INPUT_DIR has the file, server returns that path (not archive)."""
    sys.path.insert(0, str(Path("/home/ubuntu/vsp-ui")))
    # Patch INPUT_DIR before importing the server module so module-level
    # `from .config import INPUT_DIR` lands on the patched value.
    fake_input = tmp_path / "vsp_input"
    fake_excl = fake_input / ".excluded"
    fake_input.mkdir(parents=True)
    fake_excl.mkdir(parents=True)
    live_video = fake_input / "Obama.mp4"
    excl_video = fake_excl / "Obama.mp4"
    live_video.write_bytes(b"x")
    excl_video.write_bytes(b"y")

    import importlib
    import app.server as server_mod
    monkeypatch.setattr(server_mod, "INPUT_DIR", fake_input)
    # Build a handler-like stub that exposes the resolver.
    handler = MagicMock(spec=server_mod.VSPRequestHandler)
    handler._resolve_original_video = server_mod.VSPRequestHandler._resolve_original_video.__get__(
        handler, server_mod.VSPRequestHandler
    )
    resolved = handler._resolve_original_video("Obama")
    assert resolved == live_video

    # Now remove the live file — fallback should land on the .excluded copy.
    live_video.unlink()
    resolved = handler._resolve_original_video("Obama")
    assert resolved == excl_video

    # Missing entirely → None.
    excl_video.unlink()
    assert handler._resolve_original_video("Obama") is None


def test_resolve_original_video_rejects_path_traversal(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path("/home/ubuntu/vsp-ui")))
    import app.server as server_mod
    monkeypatch.setattr(server_mod, "INPUT_DIR", tmp_path)
    handler = MagicMock(spec=server_mod.VSPRequestHandler)
    handler._resolve_original_video = server_mod.VSPRequestHandler._resolve_original_video.__get__(
        handler, server_mod.VSPRequestHandler
    )
    assert handler._resolve_original_video("../etc/passwd") is None
    assert handler._resolve_original_video("a/b") is None
