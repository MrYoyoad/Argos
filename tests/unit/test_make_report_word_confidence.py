"""Tests for make_report.py --word-confidence integration.

Covers:
  - CSV gains 3 trailing columns (sentence_confidence, min_word_conf, n_low_conf_words)
  - HTML gains conf-high / conf-med / conf-low CSS classes and a Sent Conf metric cell
  - HTML hypothesis cell renders both Accuracy: and Confidence: lines
  - Backward compat: without --word-confidence, output is unchanged in those respects
"""

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_REPORT = REPO_ROOT / "VSP-LLM" / "scripts" / "make_report.py"


def _write_inputs(tmp: Path):
    """Build a tiny decode JSON + word_confidence JSON pair for two segments."""
    decode = {
        "utt_id": ["s_alpha", "s_beta"],
        "ref":    ["hello world", "good morning team"],
        "hypo":   ["hello word",  "good morning team"],
    }
    decode_path = tmp / "hypo-12345.json"
    decode_path.write_text(json.dumps(decode), encoding="utf-8")

    word_conf = {
        "s_alpha": {
            "sequence_score": -0.5,
            "words": [
                {"word": "hello", "prob": 0.92, "conf_class": "conf-high", "n_subtokens": 1},
                {"word": "word",  "prob": 0.30, "conf_class": "conf-low",  "n_subtokens": 1},
            ],
            "summary": {
                "max_word_prob": 0.92, "min_word_prob": 0.30,
                "mean_word_prob": 0.61, "n_words": 2,
                "n_high": 1, "n_med": 0, "n_low": 1,
            },
        },
        "s_beta": {
            "sequence_score": -0.1,
            "words": [
                {"word": "good",    "prob": 0.95, "conf_class": "conf-high", "n_subtokens": 1},
                {"word": "morning", "prob": 0.88, "conf_class": "conf-high", "n_subtokens": 1},
                {"word": "team",    "prob": 0.55, "conf_class": "conf-med",  "n_subtokens": 1},
            ],
            "summary": {
                "max_word_prob": 0.95, "min_word_prob": 0.55,
                "mean_word_prob": 0.793, "n_words": 3,
                "n_high": 2, "n_med": 1, "n_low": 0,
            },
        },
    }
    wc_path = tmp / "word_confidence.json"
    wc_path.write_text(json.dumps(word_conf), encoding="utf-8")
    return decode_path, wc_path


def _run_make_report(decode_path: Path, out_dir: Path, wc_path: Optional[Path]):
    cmd = [
        sys.executable, str(MAKE_REPORT),
        "--jsonl", str(decode_path),
        "--out_dir", str(out_dir),
    ]
    if wc_path is not None:
        cmd += ["--word-confidence", str(wc_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"make_report.py failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    return proc


def test_csv_gains_confidence_columns(tmp_path):
    """CSV should have sentence_confidence, min_word_conf, n_low_conf_words trailing columns."""
    decode_path, wc_path = _write_inputs(tmp_path)
    out_dir = tmp_path / "out"
    _run_make_report(decode_path, out_dir, wc_path)

    csv_path = out_dir / "report.csv"
    assert csv_path.exists()
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Header includes new columns
    assert "sentence_confidence" in reader.fieldnames
    assert "min_word_conf" in reader.fieldnames
    assert "n_low_conf_words" in reader.fieldnames

    # Values populated for each segment
    by_id = {r["utt_id"]: r for r in rows}
    assert by_id["s_alpha"]["sentence_confidence"] == "0.610"
    assert by_id["s_alpha"]["min_word_conf"] == "0.300"
    assert by_id["s_alpha"]["n_low_conf_words"] == "1"
    assert by_id["s_beta"]["sentence_confidence"] == "0.793"
    assert by_id["s_beta"]["n_low_conf_words"] == "0"


def test_html_has_confidence_classes_and_metric(tmp_path):
    """HTML should contain conf-high/conf-med/conf-low spans, Sent Conf cell, and labeled lines."""
    decode_path, wc_path = _write_inputs(tmp_path)
    out_dir = tmp_path / "out"
    _run_make_report(decode_path, out_dir, wc_path)

    html = (out_dir / "report.html").read_text()

    # CSS classes used at least once each
    assert "conf-high" in html
    assert "conf-med" in html
    assert "conf-low" in html

    # Header cell + table label
    assert "Sent Conf" in html
    assert "Accuracy / Confidence" in html

    # Per-segment labels
    assert "Accuracy:" in html
    assert "Confidence:" in html

    # Confidence words actually wrapped in confidence spans
    assert '<span class="conf-high"' in html
    assert '<span class="conf-low"' in html


def test_no_confidence_flag_keeps_legacy_output(tmp_path):
    """Without --word-confidence, CSV header should not include confidence columns."""
    decode_path, _wc_path = _write_inputs(tmp_path)
    out_dir = tmp_path / "out_legacy"
    _run_make_report(decode_path, out_dir, wc_path=None)

    with (out_dir / "report.csv").open() as f:
        reader = csv.DictReader(f)
        _ = list(reader)
    assert "sentence_confidence" not in reader.fieldnames
    assert "min_word_conf" not in reader.fieldnames
    assert "n_low_conf_words" not in reader.fieldnames

    html = (out_dir / "report.html").read_text()
    assert "Sent Conf" not in html
    assert "Confidence:" not in html
