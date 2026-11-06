---
name: send-to-device-maintenance
description: Maintain, test and package Send-to-device; use for this repository's runtime, installer and release changes.
---

# Send-to-device

Read root AGENTS.md and PROJECT_PROGRESS.md first. This skill applies only to this repository.

Read send_to_device/core.py, gui.py, runtime.py and installer.py before edits. Tailscale is an external prerequisite. GUI smoke must use --smoke-test, disabling discovery. Never send real files or discover real peers as tests without explicit user authorization. Preserve retry/completion semantics, process environment cleanup and state retention.

Run `python -m unittest discover -s tests -v`. For installer changes, run the Windows installer workflow and inspect `scripts/verify_windows_install.py` results against the exact commit. Native setup should remain per-user and require no Python on the target machine. Preserve application licenses and corresponding source. Do not install dependencies, publish a release or change scope without authorization in the current task.

Record changed behavior, actual checks and remaining limitations in PROJECT_PROGRESS.md. Do not substitute Linux/source tests for installed Windows runtime acceptance.
