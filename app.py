#!/usr/bin/env python3
import os
import sys

if __name__ == '__main__':
    if '--smoke-test' in sys.argv:
        import tempfile
        import tkinter as tk
        from pathlib import Path
        from send_to_device import core
        from send_to_device.gui import App
        with tempfile.TemporaryDirectory() as directory:
            root = tk.Tk()
            App(root, state=core.State(Path(directory)), autoload=False)
            root.after(300, root.destroy)
            root.mainloop()
        sys.exit(0)
    if '--install' in sys.argv or '--uninstall' in sys.argv:
        from installer import main
        main()
    else:
        from send_to_device.gui import main
        paths = sys.argv[1:] or [p for p in os.environ.get('NAUTILUS_SCRIPT_SELECTED_FILE_PATHS', '').splitlines() if p]
        # Finder may pass a process-serial-number argument on older macOS.
        main([p for p in paths if not p.startswith('-psn_')])
