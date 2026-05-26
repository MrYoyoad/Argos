"""Tests for the audio-aligned transcription injection CLI.

Whisper itself is not exercised (heavy model, GPU dependency). What we
verify is the math + plumbing around it:
  1. segment-id parsing + frame→sec at 25 fps.
  2. clip-window calculation for the two-offset alignment scheme.
  3. past-end-of-audio segments are skipped.
  4. metadata writer produces `type='audio-injected'` + source_audio.
  5. --dry-run emits the plan and does NOT touch the filesystem.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make scripts/pipeline importable as a flat module.
sys.path.insert(0, str(Path("/home/ubuntu/scripts/pipeline")))

import inject_transcription_from_audio as inj  # noqa: E402


def test_parse_segment_id_frame_window():
    """frames at 25 fps: Obama_00_000150_000450 → [6.0, 18.0]."""
    base, seg_idx, sf, ef = inj.parse_segment_id("Obama_00_000150_000450")
    assert base == "Obama"
    assert seg_idx == 0
    assert sf == 150
    assert ef == 450
    start, end = inj._seg_time_window("Obama_00_000150_000450")
    assert start == pytest.approx(6.0)
    assert end == pytest.approx(18.0)


def test_clip_window_math_with_offsets(tmp_path):
    """Audio leads video by 5s: segment [12, 24] → clip [17, 29] in audio."""
    # Build a minimal plan-input scenario by stubbing the segment discovery
    # to a synthetic file (we only care about the math). build_plan needs
    # ffprobe_duration to return a large enough number so the clip falls
    # within bounds.
    parent = tmp_path / "Obama.mp4"
    parent.write_bytes(b"x")
    seg_dir = tmp_path / "fast_segments"
    seg_dir.mkdir()
    (seg_dir / "Obama_00_000300_000599").write_bytes(b"")  # we just need the name
    # The discover_segments scan keys on .mp4/etc; rename appropriately.
    seg_file = seg_dir / "Obama_00_000300_000599.mp4"
    seg_file.write_bytes(b"")
    audio = tmp_path / "rec.wav"
    audio.write_bytes(b"")

    with patch.object(inj, "ffprobe_duration", return_value=120.0):
        plan = inj.build_plan(parent, audio, audio_start=5.0,
                              video_start=0.0, search_dirs=[seg_dir])
    assert len(plan) == 1
    entry = plan[0]
    assert entry["skip"] is None
    assert entry["v0"] == pytest.approx(12.0)
    assert entry["v1"] == pytest.approx(23.96)
    assert entry["clip0"] == pytest.approx(17.0)
    assert entry["clip1"] == pytest.approx(28.96)


def test_clip_outside_audio_is_skipped(tmp_path):
    """A segment whose mapped clip starts past audio duration is skipped."""
    parent = tmp_path / "Obama.mp4"
    parent.write_bytes(b"x")
    seg_dir = tmp_path / "fast_segments"
    seg_dir.mkdir()
    # Frame indices 25000–25300 → seconds [1000, 1012].
    (seg_dir / "Obama_00_025000_025300.mp4").write_bytes(b"")
    audio = tmp_path / "rec.wav"
    audio.write_bytes(b"")
    with patch.object(inj, "ffprobe_duration", return_value=60.0):
        plan = inj.build_plan(parent, audio, audio_start=0.0,
                              video_start=0.0, search_dirs=[seg_dir])
    assert len(plan) == 1
    assert plan[0]["skip"] == "outside-audio"


def test_normalize_words_matches_transcription_manager():
    """Same normalization rules: lowercase, alphanum + apostrophes, drop rest."""
    assert inj.normalize_words("Hello, World!") == ["hello", "world"]
    assert inj.normalize_words("Don't drop me.") == ["don't", "drop", "me"]
    assert inj.normalize_words("$50") == ["50"]   # $ is dropped, digits kept
    assert inj.normalize_words("") == []
    assert inj.normalize_words("   ") == []


def test_update_metadata_writes_audio_injected_type(tmp_path):
    """The metadata writer produces the new 'audio-injected' type + source fields."""
    meta = tmp_path / "metadata.json"
    inj.update_metadata(
        meta, "Obama_00_000150_000450.mp4",
        word_count=12, source_audio="rec.wav", audio_offset=5.0,
    )
    data = json.loads(meta.read_text())
    entry = data["transcriptions"]["Obama_00_000150_000450.mp4"]
    assert entry["type"] == "audio-injected"
    assert entry["source_audio"] == "rec.wav"
    assert entry["audio_offset"] == pytest.approx(5.0)
    assert entry["word_count"] == 12
    assert entry["created_at"]  # non-empty ISO timestamp

    # A second update bumps edited_at without losing the original created_at.
    inj.update_metadata(
        meta, "Obama_00_000150_000450.mp4",
        word_count=15, source_audio="rec.wav", audio_offset=5.0,
    )
    data2 = json.loads(meta.read_text())
    entry2 = data2["transcriptions"]["Obama_00_000150_000450.mp4"]
    assert entry2["created_at"] == entry["created_at"]
    assert entry2["edited_at"] is not None
    assert entry2["word_count"] == 15


def test_dry_run_does_not_touch_filesystem(tmp_path, capsys):
    """--dry-run prints the plan and writes nothing under .transcriptions/."""
    parent = tmp_path / "Obama.mp4"
    parent.write_bytes(b"x")
    seg_dir = tmp_path / "auto_avsr" / "preprocessed_flat_seg12" / "fast_segments"
    seg_dir.mkdir(parents=True)
    (seg_dir / "Obama_00_000000_000299.mp4").write_bytes(b"")
    audio = tmp_path / "rec.wav"
    audio.write_bytes(b"")
    tx_dir = tmp_path / ".transcriptions"
    # Run with a synthetic HOME so default_segment_search_dirs finds the seg.
    with patch.object(inj, "ffprobe_duration", return_value=120.0), \
         patch.dict(os.environ, {"HOME": str(tmp_path), "SEGMENT_DURATION": "12"}):
        rc = inj.main([
            "--video", str(parent),
            "--audio", str(audio),
            "--input-dir", str(tmp_path),
            "--audio-start", "0",
            "--video-start", "0",
            "--dry-run",
        ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "Obama_00_000000_000299" in out
    # No .wrd files should have been produced.
    assert not tx_dir.exists() or not list(tx_dir.glob("*.wrd"))
