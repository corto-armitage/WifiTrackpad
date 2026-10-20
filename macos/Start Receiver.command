#!/bin/bash
set -e
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
    echo 'First run the setup commands in README.md to create .venv and install requirements.'
    read -r -p 'Press Enter to close.'
    exit 1
fi
.venv/bin/python receiver.py
