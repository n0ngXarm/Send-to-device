# Project progress

2026-11-06: User authorized isolated review, portable agent skill, unique device-themed logo and stable Windows installer tested on CI. Build tools approved for CI only. Existing installations retained; no real file transfers or security-control changes. Work in release/windows-suite-20261106. Windows installer and validation pending.

2026-11-06: User prioritized Windows installation stability; npm deferred. Prepared per-user Inno installer and CI verification of installed runtime, reinstall/update, shortcuts, uninstall registry and user fixture retention. No host dependencies or security settings changed. CI results pending; unsigned, no real Windows desktop acceptance yet.

Local regression: `python3 -m unittest discover -s tests -v` passed (exit 0): 10 tests. GETEdit worker command test first failed; Allzip overwrite-failure and empty-folder tests first failed before fixes. Windows built-binary validation pending.

Installed binary test reproduced a startup timeout on Windows CI, before app-level diagnostics. Added CI-only runtime-hook traceback collection; no release published from the failed runs.

Root cause reproduced in CI: PyInstaller 6.20 Tcl runtime hook requires _tcl_data, but current Windows Python 3.14.10 embeds Tcl/Tk 9 scripts in DLL zipfs. Added repo-local runtime hook through documented hook-directory mapping; validates embedded Tcl interpreter instead of requiring nonexistent external data. No build tool/runtime downgrade or security bypass. Full installed GUI test remains required.

CI 42184982908 passed installed runtime, update, shortcuts, HKCU uninstall and data retention after Tcl9 packaging fix. Restored Send To shortcut parity with the existing installer and added install/uninstall checks for it; rerun required.

2026-11-06 — Windows installer verification complete for v1.0.1, build 55d943282e30de56ad43c3fcd9bc55cd30c50bca. Windows CI 42185417297: SUCCESS, 10 collected regression tests (platform-specific skip where applicable), real installed-runtime exercise, reinstall/update, shortcuts/HKCU uninstall and uninstall/data retention. Microsoft Defender custom scan completed. Source and checksum verified from downloaded artifact. GETEdit uses native Windows Qt for installed smoke; Send-to-device includes Send To shortcut and disables discovery in smoke; Allzip verifies a generated ZIP and native Tk launch. No real-device Windows acceptance, real transfers, Office frozen acceptance or guarantee of SmartScreen reputation. Build is unsigned. Portable project skill validated. npm remains deferred by user priority. Release https://github.com/n0ngXarm/Send-to-device/releases/tag/v1.0.1; publication status must be verified externally before reporting delivery.
