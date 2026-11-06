# Project progress

2026-11-06: User authorized isolated review, portable agent skill, unique device-themed logo and stable Windows installer tested on CI. Build tools approved for CI only. Existing installations retained; no real file transfers or security-control changes. Work in release/windows-suite-20261106. Windows installer and validation pending.

2026-11-06: User prioritized Windows installation stability; npm deferred. Prepared per-user Inno installer and CI verification of installed runtime, reinstall/update, shortcuts, uninstall registry and user fixture retention. No host dependencies or security settings changed. CI results pending; unsigned, no real Windows desktop acceptance yet.

Local regression: `python3 -m unittest discover -s tests -v` passed (exit 0): 10 tests. GETEdit worker command test first failed; Allzip overwrite-failure and empty-folder tests first failed before fixes. Windows built-binary validation pending.

Installed binary test reproduced a startup timeout on Windows CI, before app-level diagnostics. Added CI-only runtime-hook traceback collection; no release published from the failed runs.

Root cause reproduced in CI: PyInstaller 6.20 Tcl runtime hook requires _tcl_data, but current Windows Python 3.14.10 embeds Tcl/Tk 9 scripts in DLL zipfs. Added repo-local runtime hook through documented hook-directory mapping; validates embedded Tcl interpreter instead of requiring nonexistent external data. No build tool/runtime downgrade or security bypass. Full installed GUI test remains required.

CI 42184982908 passed installed runtime, update, shortcuts, HKCU uninstall and data retention after Tcl9 packaging fix. Restored Send To shortcut parity with the existing installer and added install/uninstall checks for it; rerun required.
