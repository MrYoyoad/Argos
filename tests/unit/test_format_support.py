"""Every video-discovery site must accept every format the UI promises.

vsp-ui/app/config.py::SUPPORTED_EXTENSIONS is the single source of truth
(11 containers as of May 27 2026). The UI accept-list, the pipeline's copy
loops, and every downstream scanner must agree — the historical failure
mode is "we never accepted it": the May-27 five-format commit updated the
UI and normalization globs but missed fast_segment.py (stage 0.1), the
ASR scanner, enhance_videos.py, and one pipeline glob, so a raw .MTS died
with "No videos found" (caught by the build-004 .mts E2E fixture,
Aug 2026). This test pins all known scanner sites to the config set.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(REPO / "vsp-ui"))
from app.config import SUPPORTED_EXTENSIONS  # noqa: E402

# Bare extensions without the dot, lowercase: {"mp4", "mkv", ...}
CANON = {e.lstrip(".").lower() for e in SUPPORTED_EXTENSIONS}


def test_canonical_set_is_the_full_may2026_roster():
    assert CANON == {
        "mp4", "mkv", "webm", "mov", "m4v", "avi",
        "mts", "m2ts", "ts", "wmv", "flv",
    }


def _extensions_in_python_literal(path: Path, var_names: tuple) -> set:
    """Extract string elements of a list/set literal assigned to var_names."""
    tree = ast.parse(path.read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in var_names for t in targets):
                for elt in ast.walk(node.value):
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        found.add(elt.value.lstrip(".").lower())
    return found


def test_fast_segment_scanner_covers_all_formats():
    exts = _extensions_in_python_literal(
        REPO / "auto_avsr" / "preparation" / "fast_segment.py", ("exts",))
    assert CANON <= exts, f"fast_segment.py missing: {CANON - exts}"


def test_asr_scanner_covers_all_formats():
    exts = _extensions_in_python_literal(
        REPO / "auto_avsr" / "asr_to_words_notime.py", ("VIDEO_EXTS",))
    assert CANON <= exts, f"asr_to_words_notime.py missing: {CANON - exts}"


def test_enhance_videos_scanner_covers_all_formats():
    exts = _extensions_in_python_literal(
        REPO / "scripts" / "pipeline" / "enhance_videos.py", ("exts",))
    assert CANON <= exts, f"enhance_videos.py missing: {CANON - exts}"


def _pipeline_glob_lines(path: Path) -> list:
    text = path.read_text()
    return [ln for ln in text.splitlines()
            if re.search(r'for video_file in .*\*\.', ln)]


def test_pipeline_copy_loops_cover_all_formats():
    """Both `for video_file in ...*.ext` loops in the master pipeline script
    must list every canonical extension (lowercase; uppercase mirrors too
    for the brace-glob loops)."""
    for script in (REPO / "run_flat_english_pipeline.sh",
                   REPO / "vsp_linux_container_FINAL_20260217" / "run_flat_english_pipeline.sh",
                   REPO / "vsp_docker" / "container_payload_20260507" / "run_flat_english_pipeline.sh"):
        text = script.read_text()
        # The RAW_DIR loop spans continuation lines; check the whole file for
        # each extension appearing as a glob token.
        for ext in CANON:
            assert re.search(rf'\*\.{ext}\b|[{{,]{ext}[,}}]', text), (
                f"{script}: no glob for .{ext}")


def test_normalization_find_covers_all_formats():
    for script in (REPO / "lib" / "normalization.sh",
                   REPO / "vsp_linux_container_FINAL_20260217" / "lib" / "normalization.sh",
                   REPO / "vsp_docker" / "container_payload_20260507" / "lib" / "normalization.sh"):
        text = script.read_text()
        for ext in CANON:
            assert re.search(rf'\*\.{ext}\b', text), (
                f"{script}: find/glob missing .{ext}")


def test_deploy_tree_scanners_match_ec2():
    """The synced copies must be byte-identical to EC2 (they are direct-copy
    files, not container-adapted)."""
    for rel in ("auto_avsr/preparation/fast_segment.py",
                "auto_avsr/asr_to_words_notime.py",
                "scripts/pipeline/enhance_videos.py"):
        src = (REPO / rel).read_bytes()
        for tree in ("vsp_linux_container_FINAL_20260217",
                     "vsp_docker/container_payload_20260507"):
            assert (REPO / tree / rel).read_bytes() == src, (
                f"{tree}/{rel} differs from EC2 copy")
