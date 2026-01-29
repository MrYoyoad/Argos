#!/bin/bash
# Script to prepare requirements files for USB transfer

echo "Creating requirements files for transfer..."

# 1. Auto-AVSR preprocessing requirements
source ~/auto_avsr/pre-process-venv/bin/activate
pip freeze > ~/auto_avsr/requirements_preprocessing.txt
deactivate

# 2. VSP-LLM requirements
source ~/vsp-llm-yoad-venv/bin/activate
pip freeze > ~/VSP-LLM/requirements_vspllm.txt
deactivate

# 3. VSP-UI requirements (if exists)
if [ -d ~/vsp-ui/venv ]; then
    source ~/vsp-ui/venv/bin/activate
    pip freeze > ~/vsp-ui/requirements.txt
    deactivate
fi

echo "Requirements files created successfully!"
echo "Files created:"
echo "  - ~/auto_avsr/requirements_preprocessing.txt"
echo "  - ~/VSP-LLM/requirements_vspllm.txt"
echo "  - ~/vsp-ui/requirements.txt (if applicable)"
