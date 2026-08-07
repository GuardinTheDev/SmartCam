#!/usr/bin/env bash

# SmartCam IoT Platformu — Başlatıcı Script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Aktif olan başka PYTHONHOME çakışmalarını temizle
unset PYTHONHOME

# PYTHONPATH'i venv site-packages klasörüne yönlendirerek çakışmaları ve modül bulunamadı hatalarını önle
if [ -d "$SCRIPT_DIR/venv/lib" ]; then
    for py_dir in "$SCRIPT_DIR"/venv/lib/python*; do
        if [ -d "$py_dir/site-packages" ]; then
            export PYTHONPATH="$py_dir/site-packages:$PYTHONPATH"
            break
        fi
    done
fi

export VIRTUAL_ENV="$SCRIPT_DIR/venv"

if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/run.py" "$@"
else
    exec python3 "$SCRIPT_DIR/run.py" "$@"
fi
