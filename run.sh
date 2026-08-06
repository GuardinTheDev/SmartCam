#!/usr/bin/env bash

# SmartCam IoT Platformu — Başlatıcı Script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Aktif olan başka sanal ortam veya PYTHONPATH çakışmalarını temizle
unset VIRTUAL_ENV
unset PYTHONPATH
unset PYTHONHOME

if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/run.py" "$@"
else
    exec python3 "$SCRIPT_DIR/run.py" "$@"
fi
