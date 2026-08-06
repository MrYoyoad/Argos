#!/bin/bash
# test_s3_claims.sh — verify the data-location claims made in
# docs/guides/teammate-briefing-aug2026.md §2 against live S3.
#
# Claims under test (as of 2026-08-03):
#   1. s3://conversation-datasets-733430125971/conversation_datasets/egla_kafe/
#      exists and holds the 5 raw iPhone masters (IMG_6821..IMG_6825).
#   2. The bucket contains NO keys matching avspeech / english_data / lrs3.
#      NOTE (2026-08-06): the briefing's "box-only" claim is SUPERSEDED —
#      these datasets were evacuated to
#      s3://yoad-vsp-transfer/vsp/box_evac_20260806/ (see
#      docs/guides/box-evacuation-aug2026.md). This bucket staying clean of
#      them is still expected (evacuation used the transfer bucket).
#   3. conversation_datasets/seamless_interaction/ is still a <1MB stub.
#      NOTE (2026-08-06): the real 1.9GB copy is no longer box-only — it is
#      in the box_evac prefix under datasets/datasets/seamless_interaction/.
#   4. The Aug-2026 evacuation keys exist in s3://yoad-vsp-transfer
#      (head-object on the critical checkpoint; the instance role has
#      GetObject but no ListBucket there).
#
# Read-only: uses `aws s3 ls` with the instance role. Skips (exit 0) when no
# credentials / no network, so it can live in the general test suite.

set -uo pipefail

BUCKET="s3://conversation-datasets-733430125971"
PREFIX="conversation_datasets"
PASS=0; FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

AWS_BIN="$(command -v aws || echo /opt/pytorch/bin/aws)"
if [[ ! -x "$AWS_BIN" ]]; then
    echo "SKIP: aws CLI not found — cannot verify S3 claims"
    exit 0
fi

echo "[1/4] egla_kafe raw-master backup present"
listing="$("$AWS_BIN" s3 ls "${BUCKET}/${PREFIX}/egla_kafe/" 2>&1)" || {
    echo "SKIP: cannot list ${BUCKET} (no credentials / no network / policy changed)"
    echo "      output: ${listing}"
    exit 0
}
n_masters=$(grep -cE "IMG_68[0-9]{2}\.mp4" <<< "$listing" || true)
if [[ "$n_masters" -ge 5 ]]; then
    pass "found ${n_masters} IMG_68xx.mp4 masters under ${PREFIX}/egla_kafe/"
else
    fail "expected >=5 IMG_68xx.mp4 masters, found ${n_masters}"
fi

echo "[2/4] no avspeech / english_data / lrs3 keys in bucket (evacuation used the transfer bucket)"
all_keys="$("$AWS_BIN" s3 ls --recursive "${BUCKET}/" 2>/dev/null || true)"
if [[ -z "$all_keys" ]]; then
    fail "recursive listing returned nothing (unexpected — bucket was listable in step 1)"
else
    hits=$(grep -icE "avspeech|english_data|lrs3" <<< "$all_keys" || true)
    if [[ "$hits" -eq 0 ]]; then
        pass "zero matching keys — evacuation correctly used the transfer bucket"
    else
        fail "${hits} key(s) now match avspeech|english_data|lrs3 — briefing §2 is STALE, update it:"
        grep -iE "avspeech|english_data|lrs3" <<< "$all_keys" | head -5 | sed 's/^/        /'
    fi
fi

echo "[3/4] seamless_interaction prefix still a stub (<1MB)"
si_bytes=$("$AWS_BIN" s3 ls --summarize --recursive \
    "${BUCKET}/${PREFIX}/seamless_interaction/" 2>/dev/null \
    | awk '/Total Size:/ {print $3}')
if [[ -z "${si_bytes:-}" ]]; then
    fail "could not read seamless_interaction prefix size"
elif [[ "$si_bytes" -lt 1000000 ]]; then
    pass "seamless_interaction is ${si_bytes} bytes — still a stub; authoritative copy now in box_evac (datasets/datasets/seamless_interaction/)"
else
    fail "seamless_interaction grew to ${si_bytes} bytes — a real upload happened; update briefing §2"
fi

echo "[4/4] Aug-2026 box evacuation present in yoad-vsp-transfer (head-object)"
evac_key="vsp/box_evac_20260806/models/vsp_checkpoints/checkpoint_finetune.pt"
evac_size=$("$AWS_BIN" s3api head-object --bucket yoad-vsp-transfer \
    --key "$evac_key" --query ContentLength --output text 2>/dev/null)
if [[ -z "${evac_size:-}" || "$evac_size" == "None" ]]; then
    fail "head-object failed for s3://yoad-vsp-transfer/${evac_key} — evacuation copy missing or role lost GetObject on vsp/*"
elif [[ "$evac_size" -gt 3000000000 ]]; then
    pass "critical checkpoint present in box_evac (${evac_size} bytes)"
else
    fail "critical checkpoint in box_evac is only ${evac_size} bytes — truncated upload?"
fi

echo
echo "S3 claims: ${PASS} passed, ${FAIL} failed"
[[ "$FAIL" -eq 0 ]]
