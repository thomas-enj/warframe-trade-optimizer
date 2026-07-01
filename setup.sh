#!/usr/bin/env bash
set -e

if [ -d "./venv" ]; then
    echo "====== [1/4] Venv already exists ======"
else
    echo "====== [1/4] Creating venv ======"
    if command -v python3 >/dev/null 2>&1; then python3 -m venv venv
    elif command -v python >/dev/null 2>&1; then python -m venv venv
    else
        echo "ERROR: Python 3 is not installed."
        exit 1
    fi
fi

echo -e "\n====== [2/4] Checking/Installing requirements ======"
if [ -f "./requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

echo -e "\n====== [3/4] Ensuring Playwright (Chromium) is installed ======"
./venv/bin/playwright install chromium

echo -e "\n====== [4/4] Setup complete ! ======"
echo "To start developing, activate your venv with:"
echo -e "\033[35msource ./venv/bin/activate\033[0m"