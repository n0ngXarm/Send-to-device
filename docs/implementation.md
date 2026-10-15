# Portable Send to Device

Goal: package the approved personal-device Taildrop workflow for Linux, Windows and macOS.

Architecture: Python standard-library transfer core, Tk desktop UI, background worker with queued UI events. Platform adapters locate Tailscale, store per-user data and terminate transfers. Installers only write user-owned application and shortcut locations.

Implementation sequence:
- Extract and test target discovery, validation, ZIP packaging, cancellation and state persistence.
- Build the shared desktop UI: files/folders, visible IP, status, refresh, settings, history and transfer cancellation/retry.
- Provide source installers and bundled executables built natively on GitHub Actions.
- Test core on all OS runners; smoke-test Tk on Linux with a virtual display. Test isolated installs and uninstall.
- Document prerequisites, receiving files and unsigned release limitations; push reviewed source and build release artifacts.

Acceptance: no hardcoded personal device names, IPs, paths or history; no automatic transfer on startup; no SSH/friend-sharing features; Tailscale must already be installed and logged in. The existing local installation is retained until the portable app is validated.
