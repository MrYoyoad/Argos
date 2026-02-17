#!/usr/bin/env python3
"""
Patch fairseq GenerationConfig to add 'max_len' field.

Required because VSP-LLM's s2s_decode.yaml sets generation.max_len=2048,
but the stock fairseq GenerationConfig dataclass doesn't have this field,
causing Hydra schema validation to fail.

This script finds fairseq's configs.py, checks if max_len already exists,
and adds it between max_len_b and min_len if missing.

Safe to run multiple times (idempotent).
"""
import sys
import importlib

def patch():
    try:
        import fairseq.dataclass.configs as c
    except ImportError:
        print("ERROR: fairseq not installed - cannot patch")
        return False

    src = c.__file__
    print(f"Found fairseq configs at: {src}")

    with open(src, 'r') as f:
        content = f.read()

    # Check if already patched (look for standalone max_len field, not max_len_a/max_len_b)
    # We need to find "max_len:" that is NOT "max_len_a:" or "max_len_b:"
    lines = content.split('\n')
    has_max_len = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('max_len:') or stripped.startswith('max_len :'):
            has_max_len = True
            break

    if has_max_len:
        print("Already patched - max_len field exists")
        return True

    # Insert max_len field after max_len_b block, before min_len
    target = "    min_len: int"
    replacement = """    max_len: int = field(
        default=0,
        metadata={
            "help": "maximum length of generated sequence (hard cap), 0 = use model default"
        },
    )
    min_len: int"""

    if target not in content:
        print("ERROR: Could not find 'min_len: int' in configs.py - unexpected format")
        print("You may need to manually add the max_len field to GenerationConfig")
        return False

    content = content.replace(target, replacement)

    with open(src, 'w') as f:
        f.write(content)

    # Verify the patch worked
    importlib.reload(c)
    if hasattr(c.GenerationConfig, 'max_len'):
        print(f"SUCCESS: Patched {src}")
        print("  Added: max_len: int = field(default=0)")
        return True
    else:
        print("ERROR: Patch applied but field not detected after reload")
        return False

if __name__ == '__main__':
    success = patch()
    sys.exit(0 if success else 1)
