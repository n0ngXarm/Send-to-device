# Windows installer verification

The Windows installer workflow builds an unsigned x64 onedir application with PyInstaller and a per-user Inno Setup installer. It installs no firewall rules, services, startup tasks or antivirus exclusions. Target: Windows 10/11 x64; CI uses windows-latest and does not prove every Windows release or real hardware.

CI executes unit tests; installs to a path with Thai characters and spaces; checks Start Menu shortcut and HKCU uninstall registration; launches the installed executable; repeats installation; verifies a separate user-data fixture survives; then uninstalls and checks registration/shortcut removal. GETEdit additionally imports a generated PDF through the bundled worker and exports/reopens it. Allzip creates and reads back a generated ZIP. Send-to-device opens its GUI with network discovery disabled; no real transfer is tested.

All binaries are unsigned. Defender scan availability and actual completion are recorded in SECURITY-REPORT.txt. A completed scan does not guarantee acceptance by every antivirus or SmartScreen reputation.

Build tools are CI-only. `python scripts/build_windows.py` requires Windows and the approved dependencies; `python scripts/verify_windows_install.py` installs/uninstalls the built application and should run only on an isolated CI runner. Source and license notices ship alongside the installed executable.
