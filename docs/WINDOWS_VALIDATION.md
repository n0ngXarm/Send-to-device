# Windows installer validation: Send-to-device 1.0.1

Build commit: 55d943282e30de56ad43c3fcd9bc55cd30c50bca
Windows CI: https://github.com/n0ngXarm/Send-to-device/actions/runs/42185417297
Result: SUCCESS

Verified: regression suite; per-user installer; install path with Thai characters and spaces; installed GUI launch; reinstall/update; Start Menu shortcut; HKCU uninstall registration; uninstallation; separate user fixture retained.

10 regression tests. Installed GUI opens with discovery disabled. Start Menu and Send To shortcuts are checked through install, reinstall and uninstall. Tailscale is a separate prerequisite. No live transfers or peer discovery were performed.

Microsoft Defender custom scan completed on the CI runner (see SECURITY-REPORT.txt). Binaries are unsigned; SmartScreen reputation and every antivirus cannot be guaranteed. CI uses windows-latest, not a human-operated Windows 10/11 device. No firewall changes, security exclusions, services or startup tasks are installed.
