# Send-to-device working instructions

Read PROJECT_PROGRESS.md before changes. Use `.agents/skills/send-to-device-maintenance/SKILL.md` for this project.
Keep existing installations and unrelated worktrees intact. Run focused regression tests before and after bug fixes, then `python -m unittest discover -s tests -v`.
Windows packaging: `scripts/build_windows.py`, `packaging/windows.iss`, `.github/workflows/windows-installer.yml`. Build dependencies are approved only on ephemeral CI, not on a developer host.
Do not disable security controls, add firewall exceptions or claim unsigned binaries avoid SmartScreen. Distinguish CI checks from real-device acceptance. Preserve licenses and update PROJECT_PROGRESS.md with actual exit codes and limitations.
