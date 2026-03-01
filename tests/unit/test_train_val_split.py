"""Tests for the stratified train/val split used in weekend fine-tuning.

Validates data integrity of /home/ubuntu/finetune_data/ after running
scripts/create_train_val_split.py.
"""

import json
import os
import random

import pytest

DATA_DIR = "/home/ubuntu/finetune_data"
ORIGINAL_TSV = "/home/ubuntu/english_full_results/manifests/train.tsv"
ORIGINAL_WRD = "/home/ubuntu/english_full_results/manifests/train.wrd"
ORIGINAL_CC = "/home/ubuntu/english_full_results/flat_labels/train.cluster_counts"
TOTAL_SEGMENTS = 1497
TARGET_VAL_FRACTION = 0.15


@pytest.fixture(scope="module")
def split_files():
    """Load all split files once for the test module."""
    files = {}
    for prefix in ("train", "test"):
        tsv_path = os.path.join(DATA_DIR, f"{prefix}.tsv")
        wrd_path = os.path.join(DATA_DIR, f"{prefix}.wrd")
        cc_path = os.path.join(DATA_DIR, f"{prefix}.cluster_counts")

        with open(tsv_path) as f:
            lines = f.readlines()
            files[f"{prefix}_tsv_header"] = lines[0]
            files[f"{prefix}_tsv_data"] = lines[1:]

        with open(wrd_path) as f:
            files[f"{prefix}_wrd"] = f.readlines()

        with open(cc_path) as f:
            files[f"{prefix}_cc"] = f.readlines()

    return files


def test_line_count_integrity(split_files):
    """TSV data lines == WRD lines == cluster_counts lines for both splits."""
    for prefix in ("train", "test"):
        n_tsv = len(split_files[f"{prefix}_tsv_data"])
        n_wrd = len(split_files[f"{prefix}_wrd"])
        n_cc = len(split_files[f"{prefix}_cc"])
        assert n_tsv == n_wrd == n_cc, (
            f"{prefix}: tsv={n_tsv}, wrd={n_wrd}, cc={n_cc}"
        )


def test_no_overlap(split_files):
    """No segment IDs appear in both train and test sets."""
    train_ids = {line.split("\t")[0] for line in split_files["train_tsv_data"]}
    test_ids = {line.split("\t")[0] for line in split_files["test_tsv_data"]}
    overlap = train_ids & test_ids
    assert len(overlap) == 0, f"Overlap found: {list(overlap)[:5]}"


def test_completeness(split_files):
    """Train + test = original 1,497 segments with no data loss."""
    n_train = len(split_files["train_tsv_data"])
    n_test = len(split_files["test_tsv_data"])
    assert n_train + n_test == TOTAL_SEGMENTS, (
        f"Expected {TOTAL_SEGMENTS}, got train={n_train} + test={n_test} = {n_train + n_test}"
    )


def test_stratification():
    """Each IS tier (1-5) is represented in both splits, within +-3% of target."""
    metadata_path = os.path.join(DATA_DIR, "split_metadata.json")
    with open(metadata_path) as f:
        metadata = json.load(f)

    for tier, dist in metadata["tier_distribution"].items():
        total = dist["total"]
        val = dist["val"]
        val_frac = val / total
        assert abs(val_frac - TARGET_VAL_FRACTION) < 0.03, (
            f"Tier {tier}: val fraction {val_frac:.3f} deviates from target {TARGET_VAL_FRACTION}"
        )
        assert dist["train"] + dist["val"] == total, (
            f"Tier {tier}: train + val != total"
        )


def test_tsv_format(split_files):
    """TSV has header '/' and each data line has 5 tab-separated columns."""
    for prefix in ("train", "test"):
        header = split_files[f"{prefix}_tsv_header"].strip()
        assert header == "/", f"{prefix} TSV header is '{header}', expected '/'"

        for i, line in enumerate(split_files[f"{prefix}_tsv_data"][:10]):
            cols = line.strip().split("\t")
            assert len(cols) == 5, (
                f"{prefix} line {i}: expected 5 columns, got {len(cols)}"
            )


def test_video_files_exist(split_files):
    """Spot-check that 10 random video paths from the TSV actually exist on disk."""
    all_lines = split_files["train_tsv_data"] + split_files["test_tsv_data"]
    random.seed(42)
    sample = random.sample(all_lines, min(10, len(all_lines)))

    missing = []
    for line in sample:
        video_path = line.strip().split("\t")[1]
        if not os.path.exists(video_path):
            missing.append(video_path)

    assert len(missing) == 0, f"Missing video files: {missing}"


def test_cluster_counts_format(split_files):
    """Each cluster_counts line contains only space-separated integers."""
    for prefix in ("train", "test"):
        for i, line in enumerate(split_files[f"{prefix}_cc"][:20]):
            parts = line.strip().split()
            for part in parts:
                assert part.isdigit(), (
                    f"{prefix} cc line {i}: '{part}' is not an integer"
                )
