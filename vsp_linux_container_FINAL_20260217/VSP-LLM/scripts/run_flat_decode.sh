#!/usr/bin/env bash
set -euo pipefail

########################
# Config (override via env)
########################

# Which split to decode: train / valid / test
SPLIT="${SPLIT:-train}"

# Language + task
LANG="${LANG:-en}"
TASK="vsr"   # visual speech recognition

# Repo root
ROOT=$(dirname "$(dirname "$(readlink -fm "$0")")")

# Auto-detect galaxy_export root
GALAXY_ROOT="$(cd "${ROOT}/.." && pwd)"

# Paths consistent with your previous steps
LRS3_ROOT="${LRS3_ROOT:-${GALAXY_ROOT}/auto_avsr/preprocessed_flat_seg4}"
TSV_ROOT="${TSV_ROOT:-${LRS3_ROOT}/433h_data}"
LAB_DIR="${LAB_DIR:-${ROOT}/flat_labels}"             # where *.cluster_counts live
WRD_ROOT="${WRD_ROOT:-${ROOT}/labels/vsr/${LANG}}"    # where *.wrd live

MODEL_SRC="${ROOT}/src"
DATA_ROOT="${MODEL_SRC}/dataset"

LLM_PATH="${LLM_PATH:-${ROOT}/checkpoints/Llama-2-7b-hf}"
MODEL_PATH="${MODEL_PATH:-${ROOT}/checkpoints/checkpoint_finetune.pt}"

# This is the *base* decode folder; we'll write per-task/lang inside it
DECODE_ROOT="${OUT_PATH:-${ROOT}/decode}"
RESULT_DIR="${DECODE_ROOT}/${TASK}/${LANG}"

# Target dataset dir in the format VSP-LLM expects
TGT_DIR="${DATA_ROOT}/${TASK}/${LANG}"

########################
# Print config
########################

echo ">>> Using:"
echo "  ROOT       = ${ROOT}"
echo "  SPLIT      = ${SPLIT}"
echo "  LANG       = ${LANG}"
echo "  TASK       = ${TASK}"
echo "  TSV_ROOT   = ${TSV_ROOT}"
echo "  LAB_DIR    = ${LAB_DIR}"
echo "  WRD_ROOT   = ${WRD_ROOT}"
echo "  TGT_DIR    = ${TGT_DIR}"
echo "  LLM_PATH   = ${LLM_PATH}"
echo "  MODEL_PATH = ${MODEL_PATH}"
echo "  DECODE_ROOT= ${DECODE_ROOT}"
echo "  RESULT_DIR = ${RESULT_DIR}"

########################
# Prepare dataset layout (symlinks)
########################

mkdir -p "${TGT_DIR}"

split="${SPLIT}"

src_tsv="${TSV_ROOT}/${split}.tsv"
src_cc="${LAB_DIR}/${split}.cluster_counts"
src_wrd="${WRD_ROOT}/${split}.wrd"

dst_tsv="${TGT_DIR}/${split}.tsv"
dst_cc="${TGT_DIR}/${split}.cluster_counts"
dst_wrd="${TGT_DIR}/${split}.wrd"

echo
echo ">>> Symlinking files for split: ${split}"

# sanity checks
for f in "${src_tsv}" "${src_cc}" "${src_wrd}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing source file: $f" >&2
    exit 1
  fi
done

link_force() {
  local src="$1"
  local dst="$2"
  if [[ -L "$dst" || -f "$dst" ]]; then
    rm -f "$dst"
  fi
  ln -s "$src" "$dst"
}

link_force "${src_tsv}" "${dst_tsv}"
link_force "${src_cc}" "${dst_cc}"
link_force "${src_wrd}" "${dst_wrd}"

echo "  -> ${dst_tsv} -> ${src_tsv}"
echo "  -> ${dst_cc}  -> ${src_cc}"
echo "  -> ${dst_wrd} -> ${src_wrd}"

# --- AUTO-INSERTED BLOCK FOR test.* SYMLINKS ---
if [[ "${SPLIT}" == "train" ]]; then
  echo
  echo ">>> Creating test.* symlinks pointing to train.* (for gen_subset=test)"

  test_tsv="${TGT_DIR}/test.tsv"
  test_cc="${TGT_DIR}/test.cluster_counts"
  test_wrd="${TGT_DIR}/test.wrd"

  link_force "${dst_tsv}" "${test_tsv}"
  link_force "${dst_cc}" "${test_cc}"
  link_force "${dst_wrd}" "${test_wrd}"

  echo "  -> ${test_tsv} -> ${dst_tsv}"
  echo "  -> ${test_cc}  -> ${dst_cc}"
  echo "  -> ${test_wrd} -> ${dst_wrd}"
fi
# --- END AUTO BLOCK ---


########################
# Patch scripts/decode.sh (as README says)
########################

DECODE_SH="${ROOT}/scripts/decode.sh"

echo
echo ">>> Patching decode.sh"
echo "    LANG       = ${LANG}"
echo "    MODEL_PATH = ${MODEL_PATH}"
echo "    OUT_PATH   = ${RESULT_DIR}"

# keep a backup once (if not already)
if [[ ! -f "${DECODE_SH}.bak" ]]; then
  cp "${DECODE_SH}" "${DECODE_SH}.bak"
fi

# Replace only the variable assignment lines at the top
# Assumes decode.sh contains plain lines like:
#   LANG=...
#   MODEL_PATH=...
#   OUT_PATH=...
sed -i "s|^LANG=.*$|LANG=${LANG}|"             "${DECODE_SH}"
sed -i "s|^MODEL_PATH=.*$|MODEL_PATH=${MODEL_PATH}|" "${DECODE_SH}"
sed -i "s|^OUT_PATH=.*$|OUT_PATH=${RESULT_DIR}|"     "${DECODE_SH}"

echo ">>> New settings in decode.sh:"
grep -E '^(LANG|MODEL_PATH|OUT_PATH)=' "${DECODE_SH}"

########################
# Call scripts/decode.sh
########################

echo
echo ">>> Starting decode via scripts/decode.sh"
(
  cd "${ROOT}"
  bash scripts/decode.sh
)

echo
echo ">>> Done run_flat_decode.sh for split=${SPLIT}"
echo "    Results should be under: ${RESULT_DIR}"