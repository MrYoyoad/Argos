#!/bin/bash
# Helper script to push tags via VS Code's credential helper

cd /home/ubuntu

echo "Configuring git to use VS Code credential helper..."
git config --local credential.helper ""
git config --local credential.helper "!f() { /usr/share/code-server/bin/code-server credential-helper; }; f"

echo "Pushing tags to GitHub..."
git push origin --tags

echo "Done! Check https://github.com/MrYoyoad/Argos/tags"
