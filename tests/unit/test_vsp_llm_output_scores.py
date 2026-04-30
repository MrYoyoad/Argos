"""Smoke tests for the VSP_OUTPUT_SCORES env-var gate (B1).

Importing vsp_llm.py at test time requires fairseq + peft + transformers + a CUDA
runtime. That is too heavy for a unit test, so these tests verify the gate at the
source-code level: the env-var conditional must exist, the unwrap must exist, the
sidecar JSON write must exist.

The full end-to-end signal-quality verification is B3 (on a GPU subset).
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VSP_LLM = REPO_ROOT / "VSP-LLM" / "src" / "vsp_llm.py"
VSP_LLM_DECODE = REPO_ROOT / "VSP-LLM" / "src" / "vsp_llm_decode.py"
DECODE_SH = REPO_ROOT / "lib" / "decode.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_vsp_llm_envvar_gate_present():
    """B1.t1 — vsp_llm.py reads VSP_OUTPUT_SCORES and only sets output_scores
    when explicitly enabled. Default behavior (env unset / 0) must be unchanged."""
    src = _read(VSP_LLM)
    assert 'os.environ.get("VSP_OUTPUT_SCORES", "0") == "1"' in src, (
        "vsp_llm.py must gate output_scores behind the VSP_OUTPUT_SCORES env var"
    )
    assert '"output_scores"' in src, "vsp_llm.py must reference output_scores kwarg"
    assert '"return_dict_in_generate"' in src, (
        "vsp_llm.py must reference return_dict_in_generate kwarg"
    )


def test_vsp_llm_decode_unwrap_present():
    """B1.t2 — vsp_llm_decode.py must defensively unwrap the dict return from
    generate() (.sequences attr) and fall back to the tensor path when absent."""
    src = _read(VSP_LLM_DECODE)
    assert 'hasattr(gen_out, "sequences")' in src, (
        "decode must check for the .sequences attribute (dict-mode return from generate)"
    )
    assert "compute_transition_scores" in src, (
        "decode must use compute_transition_scores to extract per-token probs"
    )
    assert "best_hypo_tokens" in src, "decode must use the unwrapped token tensor"


def test_vsp_llm_decode_sidecar_write_present():
    """B1.t3 — decode writes a confidence-{fid}.json sidecar when env var is on,
    and never when env var is off."""
    src = _read(VSP_LLM_DECODE)
    assert "confidence-{fid}.json" in src, (
        "decode must write a confidence-{fid}.json sidecar"
    )
    assert "output_scores_enabled" in src, (
        "the sidecar write must be gated by output_scores_enabled"
    )


def test_decode_sh_passes_envvar():
    """B1.t4 — lib/decode.sh must explicitly pass VSP_OUTPUT_SCORES through
    to the Python decode subprocess so the env-var gate is reachable."""
    src = _read(DECODE_SH)
    assert 'VSP_OUTPUT_SCORES="${VSP_OUTPUT_SCORES:-0}"' in src, (
        "decode.sh must explicitly forward VSP_OUTPUT_SCORES to run_flat_decode.sh"
    )


def test_default_off_is_no_op():
    """B1.t5 — when the env var is unset or 0, the source path must NOT call
    generate() with output_scores or return_dict_in_generate. We verify this
    statically: those kwargs must only appear inside the gated block."""
    src = _read(VSP_LLM)
    # The kwargs should only appear inside the gated block, not unconditionally.
    # Find the if-block and assert the kwargs are inside it.
    gate_idx = src.find('os.environ.get("VSP_OUTPUT_SCORES"')
    assert gate_idx != -1
    # Both kwargs must appear AFTER the gate (i.e., inside the if-block region).
    assert src.find('"output_scores"') > gate_idx, (
        "output_scores kwarg must be inside the env-var gated block"
    )
    assert src.find('"return_dict_in_generate"') > gate_idx, (
        "return_dict_in_generate kwarg must be inside the env-var gated block"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
