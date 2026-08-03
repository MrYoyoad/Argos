#!/usr/bin/env bash
# test_docs_package.sh — validate the August-2026 docs handover package.
#
# Checks:
#   a) LINK CHECK      — relative markdown link targets resolve, for the four
#                        package docs (WARN-skip if a doc is absent)
#   b) GENERATOR SMOKE — generate_teammate_briefing.py builds a docx > 20 KB
#   c) NUMBER SPOT-CHECK — headline figures present in the briefing md
#   d) SCRIPT VOCAB    — conversation scripts pass check_script_vocab.py
#                        (WARN-skip while the scripts are being written)
#
# Exit: non-zero if any check FAILs. WARNs do not fail the run.

set -uo pipefail

REPO="/home/ubuntu"
BRIEFING="$REPO/docs/guides/teammate-briefing-aug2026.md"
GENERATOR="$REPO/docs/_research-tools/generators/generate_teammate_briefing.py"
VOCAB_CHECKER="$REPO/docs/_research-tools/scripts/check_script_vocab.py"
SCRATCH="/tmp/claude-1000/-home-ubuntu/d31d89ce-6d69-492e-a33b-da9c152323ea/scratchpad"

PASS=0
FAIL=0
WARN=0

pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }
warn() { echo "WARN: $*"; WARN=$((WARN + 1)); }

# ─────────────────────────────────────────────
# a) LINK CHECK
# ─────────────────────────────────────────────
echo "── a) LINK CHECK ──"

check_links() {
    local file="$1"
    if [ ! -f "$file" ]; then
        warn "link check skipped — file absent: $file"
        return 0
    fi
    local dir broken=0 total=0 target resolved
    dir="$(dirname "$file")"
    # Relative markdown link targets: ](...) minus http/https/mailto/#anchors
    while IFS= read -r target; do
        total=$((total + 1))
        resolved="${target%%#*}"          # strip #fragment
        [ -z "$resolved" ] && continue     # pure anchor (already filtered)
        if [ ! -e "$dir/$resolved" ]; then
            broken=$((broken + 1))
            echo "  BROKEN LINK: $target  (in $file)"
        fi
    done < <(grep -oE '\]\([^)]+\)' "$file" 2>/dev/null \
             | sed -e 's/^](//' -e 's/)$//' \
             | grep -vE '^(https?:|mailto:|#)' || true)
    if [ "$broken" -eq 0 ]; then
        pass "links OK ($total relative targets checked): ${file#"$REPO"/}"
    else
        fail "$broken broken link(s) in ${file#"$REPO"/}"
    fi
}

check_links "$BRIEFING"
check_links "$REPO/docs/guides/project-handover-july2026.md"
check_links "$REPO/docs/sessions/HANDOVER.md"
check_links "$REPO/docs/guides/conversation-filming-protocol.md"

# ─────────────────────────────────────────────
# b) GENERATOR SMOKE
# ─────────────────────────────────────────────
echo "── b) GENERATOR SMOKE ──"

if [ ! -f "$GENERATOR" ]; then
    fail "generator not found: $GENERATOR"
else
    mkdir -p "$SCRATCH"
    TMP_DOCX="$SCRATCH/test_docs_package_briefing_$$.docx"
    if python3 "$GENERATOR" --out "$TMP_DOCX" > /dev/null 2>&1; then
        if [ -f "$TMP_DOCX" ]; then
            size=$(stat -c%s "$TMP_DOCX" 2>/dev/null || echo 0)
            if [ "$size" -gt 20480 ]; then
                pass "generator smoke — docx built, ${size} bytes (> 20 KB)"
            else
                fail "generator smoke — docx too small: ${size} bytes (<= 20 KB)"
            fi
        else
            fail "generator smoke — exited 0 but no output file"
        fi
    else
        fail "generator smoke — generate_teammate_briefing.py exited non-zero"
    fi
    rm -f "$TMP_DOCX"
fi

# ─────────────────────────────────────────────
# c) NUMBER SPOT-CHECK
# ─────────────────────────────────────────────
echo "── c) NUMBER SPOT-CHECK ──"

if [ ! -f "$BRIEFING" ]; then
    fail "briefing md absent — cannot spot-check numbers: $BRIEFING"
else
    for num in 63.8 2.547 61.9 71.1; do
        if grep -qF -- "$num" "$BRIEFING"; then
            pass "headline figure present: $num"
        else
            fail "headline figure MISSING from briefing: $num"
        fi
    done
fi

# ─────────────────────────────────────────────
# d) SCRIPT VOCAB
# ─────────────────────────────────────────────
echo "── d) SCRIPT VOCAB ──"

for script in "$REPO/docs/guides/conversation_scripts/script_orchard.md" \
              "$REPO/docs/guides/conversation_scripts/script_everyday.md"; do
    if [ ! -f "$script" ]; then
        warn "vocab check skipped — script absent (being written in parallel): ${script#"$REPO"/}"
        continue
    fi
    if [ ! -f "$VOCAB_CHECKER" ]; then
        fail "vocab checker not found: $VOCAB_CHECKER"
        continue
    fi
    if python3 "$VOCAB_CHECKER" "$script" > /dev/null 2>&1; then
        pass "vocab clean: ${script#"$REPO"/}"
    else
        fail "vocab flags raised (or checker error) on: ${script#"$REPO"/}"
    fi
done

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
echo "─────────────────────────────────────────────"
echo "SUMMARY: $PASS passed, $FAIL failed, $WARN warned"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
