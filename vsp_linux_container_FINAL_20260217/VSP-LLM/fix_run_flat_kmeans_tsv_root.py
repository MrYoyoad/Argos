from pathlib import Path
import re
import sys

path = Path("scripts/run_flat_kmeans.sh")
text = path.read_text()

# Try to find the original TSV_ROOT line that points to 433h_data
old_line = None

# Case 1: colon-assign form from earlier: : "${TSV_ROOT:=${LRS3_ROOT}/433h_data}"
if ': "${TSV_ROOT:=${LRS3_ROOT}/433h_data}"' in text:
    old_line = ': "${TSV_ROOT:=${LRS3_ROOT}/433h_data}"'

# Case 2: more basic form like TSV_ROOT=${LRS3_ROOT}/433h_data
if old_line is None:
    m = re.search(r'^.*TSV_ROOT.*433h_data.*$', text, re.MULTILINE)
    if m:
        old_line = m.group(0)

if old_line is None:
    print("ERROR: Could not find TSV_ROOT line with 433h_data in scripts/run_flat_kmeans.sh")
    sys.exit(1)

new_block = """# Set TSV_ROOT depending on split:
#   - train/valid: use 433h_data
#   - test:        use 30h_data
# You can still override TSV_ROOT via environment if you want.
if [[ "${SPLIT}" == "test" ]]; then
    : "${TSV_ROOT:=${LRS3_ROOT}/30h_data}"
else
    : "${TSV_ROOT:=${LRS3_ROOT}/433h_data}"
fi
"""

print("Replacing line:\n  ", old_line)
print("With block:\n", new_block)

text = text.replace(old_line, new_block)
path.write_text(text)

print("Patched scripts/run_flat_kmeans.sh successfully.")
