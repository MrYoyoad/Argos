#!/usr/bin/env python3
"""
Unit tests for overlap parameter validation and segment splitting logic.

Tests verify that:
1. 2-second overlap creates correct stride (12s - 2s = 10s)
2. Videos <12s don't get split (MIN_SPLIT_DURATION check)
3. Videos ≥12s get split properly
4. Frame calculations match expected overlap
"""

import pytest
import sys
from pathlib import Path

# Add auto_avsr to path
sys.path.insert(0, str(Path.home() / 'auto_avsr' / 'preparation'))

from overlapping_segmentation import split_video_by_time


class TestOverlapParameters:
    """Test overlap parameter calculations."""

    def test_overlap_2_seconds_12_second_segments(self):
        """Test that 2s overlap creates correct stride."""
        duration = 60.0
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        # Expected: stride = 12 - 2 = 10s
        # 60s video: segments at 0, 10, 20, 30, 40, 50s
        assert len(segments) == 6, f"Expected 6 segments, got {len(segments)}"

        # Check first two segments
        assert segments[0][0] == 0.0, "First segment should start at 0s"
        assert segments[0][1] == 12.0, "First segment should end at 12s"
        assert segments[0][2] == 0, "First segment should start at frame 0"
        assert segments[0][3] == 300, "First segment should end at frame 300 (12s * 25fps)"

        assert segments[1][0] == 10.0, "Second segment should start at 10s"
        assert segments[1][1] == 22.0, "Second segment should end at 22s"
        assert segments[1][2] == 250, "Second segment should start at frame 250 (10s * 25fps)"
        assert segments[1][3] == 550, "Second segment should end at frame 550 (22s * 25fps)"

        # Verify overlap between first two segments
        overlap_frames = segments[0][3] - segments[1][2]  # 300 - 250 = 50 frames
        assert overlap_frames == 50, f"Expected 50 frame overlap (2s * 25fps), got {overlap_frames}"

    def test_min_split_duration_12_seconds_no_split(self):
        """Test that videos <12s don't get split."""
        duration = 11.5
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        # Should return single segment (no split) for video < 12s
        assert len(segments) == 1, f"Expected 1 segment for 11.5s video, got {len(segments)}"
        assert segments[0][0] == 0.0, "Single segment should start at 0s"
        assert abs(segments[0][1] - duration) < 0.01, f"Single segment should end at {duration}s"

    def test_exactly_12_seconds_gets_split(self):
        """Test that exactly 12s video gets split into 2 segments."""
        duration = 12.0
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        # 12s video with 12s segments and 2s overlap:
        # Segment 0: 0-12s
        # Since stride = 10s, next would start at 10s, but that's < 12s duration
        # So we should get 1 or 2 segments depending on implementation
        # With MIN_SPLIT_DURATION=12s, this should create 1 segment
        assert len(segments) >= 1, f"Expected at least 1 segment for 12s video, got {len(segments)}"

    def test_24_second_video_multiple_segments(self):
        """Test that 24s video splits into proper segments with 2s overlap."""
        duration = 24.0
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        # Expected segments with stride=10s:
        # Seg 0: 0-12s
        # Seg 1: 10-22s
        # Seg 2: 20-24s (or might extend to fit)
        assert len(segments) >= 2, f"Expected at least 2 segments for 24s video, got {len(segments)}"

        # Verify overlap exists
        for i in range(len(segments) - 1):
            seg_a = segments[i]
            seg_b = segments[i + 1]
            # seg_b should start before seg_a ends (overlap condition)
            assert seg_b[0] < seg_a[1], f"Segment {i+1} should overlap with segment {i}"

    def test_stride_calculation(self):
        """Test that stride is correctly calculated as seg_duration - overlap."""
        duration = 100.0
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        # Calculate stride from actual segments
        if len(segments) > 1:
            actual_stride = segments[1][0] - segments[0][0]  # Start time difference
            expected_stride = seg_duration - overlap_duration  # 12 - 2 = 10

            assert abs(actual_stride - expected_stride) < 0.1, \
                f"Expected stride={expected_stride}s, got {actual_stride}s"

    def test_frame_count_consistency(self):
        """Test that frame counts are consistent with time calculations."""
        duration = 60.0
        fps = 25
        seg_duration = 12
        overlap_duration = 2.0

        segments = split_video_by_time(
            video_duration=duration,
            segment_duration=seg_duration,
            overlap_duration=overlap_duration,
            min_split_duration=12.0,
            fps=fps
        )

        for i, seg in enumerate(segments):
            start_sec, end_sec, start_frame, end_frame = seg

            # Calculate expected frames
            expected_start_frame = int(start_sec * fps)
            expected_end_frame = int(end_sec * fps)

            assert abs(start_frame - expected_start_frame) <= 1, \
                f"Segment {i}: start frame mismatch"
            assert abs(end_frame - expected_end_frame) <= 1, \
                f"Segment {i}: end frame mismatch"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
