#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -d './Send to Device.app' ]; then
    exec './Send to Device.app/Contents/MacOS/SendToDevice' --install "$@"
fi
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import tkinter' 2>/dev/null; then
    echo 'Install Python 3.10+ for macOS from https://www.python.org/downloads/macos/ (includes Tk).' >&2
    exit 1
fi
exec python3 installer.py --install "$@"
