# Project progress

2026-11-06: User authorized isolated review, portable agent skill, unique device-themed logo and stable Windows installer tested on CI. Build tools approved for CI only. Existing installations retained; no real file transfers or security-control changes. Work in release/windows-suite-20261106. Windows installer and validation pending.

2026-11-06: User prioritized Windows installation stability; npm deferred. Prepared per-user Inno installer and CI verification of installed runtime, reinstall/update, shortcuts, uninstall registry and user fixture retention. No host dependencies or security settings changed. CI results pending; unsigned, no real Windows desktop acceptance yet.

Local regression: `python3 -m unittest discover -s tests -v` passed (exit 0): 10 tests. GETEdit worker command test first failed; Allzip overwrite-failure and empty-folder tests first failed before fixes. Windows built-binary validation pending.
