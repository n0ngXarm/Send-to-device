#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -x ./SendToDevice/SendToDevice ]; then
    exec ./SendToDevice/SendToDevice --install "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then
    echo 'Install Python 3.10+ and Tk first.' >&2
    exit 1
fi
if ! python3 -c 'import tkinter' 2>/dev/null; then
    echo 'Install Tk first: sudo apt install python3-tk OR sudo dnf install python3-tkinter' >&2
    exit 1
fi
exec python3 installer.py --install "$@"
