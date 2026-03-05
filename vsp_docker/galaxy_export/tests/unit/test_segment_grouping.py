#!/usr/bin/env python3
"""
Unit tests for segment ID parsing and grouping logic.

Tests verify that:
1. Segment IDs with hash are parsed correctly
2. Segment IDs without hash (like Obama video) are parsed correctly
3. Old format segment IDs are handled
4. Segments are correctly grouped by original video
"""

import pytest
import sys
from pathlib import Path

# Add VSP-LLM scripts to path
sys.path.insert(0, str(Path.home() / 'VSP-LLM' / 'scripts'))

from calculate_per_video_wer import parse_segment_id, group_segments_by_video


class TestSegmentIdParsing:
    """Test segment ID parsing functions."""

    def test_parse_segment_filename_with_hash(self):
        """Test parsing segments with hash."""
        result = parse_segment_id("VideoA__abc12345_00_000000_000300")

        assert result['video_id'] == "VideoA"
        assert result['hash'] == "abc12345"
        assert result['seg_idx'] == 0
        assert result['full_id'] == "VideoA__abc12345"

    def test_parse_segment_filename_without_hash(self):
        """Test parsing segments without hash (like Obama video)."""
        result = parse_segment_id("050111_OsamaBinLadenStatement_00_000000_000300")

        assert result['video_id'] == "050111_OsamaBinLadenStatement"
        assert result['hash'] is None
        assert result['seg_idx'] == 0
        assert result['full_id'] == "050111_OsamaBinLadenStatement"

    def test_parse_segment_with_extension(self):
        """Test parsing segment IDs that include file extensions."""
        result = parse_segment_id("VideoA__abc12345_01_000250_000550.mp4")

        assert result['video_id'] == "VideoA"
        assert result['hash'] == "abc12345"
        assert result['seg_idx'] == 1
        assert result['full_id'] == "VideoA__abc12345"

    def test_parse_old_format_with_hash(self):
        """Test parsing old format segment IDs (no frame info)."""
        result = parse_segment_id("VideoB__def67890")

        assert result['video_id'] == "VideoB"
        assert result['hash'] == "def67890"
        assert result['seg_idx'] == 0
        assert result['full_id'] == "VideoB__def67890"

    def test_parse_simple_filename(self):
        """Test parsing simple filenames without patterns."""
        result = parse_segment_id("simple_video")

        assert result['video_id'] == "simple_video"
        assert result['hash'] is None
        assert result['seg_idx'] == 0
        assert result['full_id'] == "simple_video"

    def test_parse_multiple_segments_same_video(self):
        """Test parsing multiple segments from same video maintains same full_id."""
        seg0 = parse_segment_id("Obama_00_000000_000300")
        seg1 = parse_segment_id("Obama_01_000250_000550")
        seg2 = parse_segment_id("Obama_02_000500_000800")

        # All should have same full_id
        assert seg0['full_id'] == seg1['full_id'] == seg2['full_id']
        assert seg0['full_id'] == "Obama"

        # But different segment indices
        assert seg0['seg_idx'] == 0
        assert seg1['seg_idx'] == 1
        assert seg2['seg_idx'] == 2


class TestSegmentGrouping:
    """Test segment grouping by video."""

    def test_group_single_video_multiple_segments(self):
        """Test grouping segments from a single video."""
        decode_data = {
            'utt_id': [
                'Obama_00_000000_000300',
                'Obama_01_000250_000550',
                'Obama_02_000500_000800'
            ],
            'hypo': ['text 0', 'text 1', 'text 2'],
            'ref': ['ref 0', 'ref 1', 'ref 2']
        }

        groups = group_segments_by_video(decode_data)

        assert len(groups) == 1, "Should have 1 video group"
        assert 'Obama' in groups, "Should have Obama video"
        assert len(groups['Obama']) == 3, "Obama should have 3 segments"

        # Verify segments are sorted by index
        assert groups['Obama'][0]['seg_idx'] == 0
        assert groups['Obama'][1]['seg_idx'] == 1
        assert groups['Obama'][2]['seg_idx'] == 2

    def test_group_multiple_videos(self):
        """Test grouping segments from multiple videos."""
        decode_data = {
            'utt_id': [
                'VideoA__abc12345_00_000000_000300',
                'VideoA__abc12345_01_000250_000550',
                'VideoB__def67890_00_000000_000300'
            ],
            'hypo': ['text A0', 'text A1', 'text B0'],
            'ref': ['ref A0', 'ref A1', 'ref B0']
        }

        groups = group_segments_by_video(decode_data)

        assert len(groups) == 2, "Should have 2 video groups"
        assert 'VideoA__abc12345' in groups
        assert 'VideoB__def67890' in groups
        assert len(groups['VideoA__abc12345']) == 2
        assert len(groups['VideoB__def67890']) == 1

    def test_group_out_of_order_segments(self):
        """Test that segments are sorted even if provided out of order."""
        decode_data = {
            'utt_id': [
                'Obama_02_000500_000800',  # Out of order
                'Obama_00_000000_000300',
                'Obama_01_000250_000550'
            ],
            'hypo': ['text 2', 'text 0', 'text 1'],
            'ref': ['ref 2', 'ref 0', 'ref 1']
        }

        groups = group_segments_by_video(decode_data)

        # Should be sorted by seg_idx
        assert groups['Obama'][0]['seg_idx'] == 0
        assert groups['Obama'][1]['seg_idx'] == 1
        assert groups['Obama'][2]['seg_idx'] == 2

        # But text should match original order
        assert groups['Obama'][0]['hyp'] == 'text 0'
        assert groups['Obama'][1]['hyp'] == 'text 1'
        assert groups['Obama'][2]['hyp'] == 'text 2'

    def test_group_mismatched_lengths_raises_error(self):
        """Test that mismatched array lengths raise an error."""
        decode_data = {
            'utt_id': ['seg1', 'seg2'],
            'hypo': ['text1'],  # Mismatched length
            'ref': ['ref1', 'ref2']
        }

        with pytest.raises(ValueError, match="Mismatched lengths"):
            group_segments_by_video(decode_data)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
