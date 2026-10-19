"""Per-user install/uninstall. No administrator access and no network downloads."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import subprocess
import sys
import tempfile

from send_to_device import runtime

NAME = 'Send to Device'


def install_root():
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'Programs/SendToDevice'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/SendToDevice/app'
    return Path.home() / '.local/share/send-to-device'


def executable(path):
    path.chmod(path.stat().st_mode | 0o111)


def shell_launcher(path, command):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('#!/bin/sh\nexec ' + ' '.join(shlex.quote(str(p)) for p in command) + ' "$@"\n', encoding='utf-8')
    executable(path)


def desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def replace_tree(source, target):
    """Stage bundles before replacing; preserves framework symlinks on updates."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.send-to-device-', dir=target.parent) as directory:
        stage = Path(directory)
        payload, backup = stage / 'payload', stage / 'previous'
        shutil.copytree(source, payload, symlinks=True)
        existed = target.exists()
        if existed:
            target.rename(backup)
        try:
            payload.rename(target)
        except OSError:
            if existed:
                backup.rename(target)
            raise


def install(destination=None, shortcuts=True):
    target = Path(destination or install_root()).absolute()
    source = Path(__file__).resolve().parent
    frozen = getattr(sys, 'frozen', False)
    if not frozen:
        import tkinter  # fail before writing an unusable installation
    if target == source or source in target.parents:
        raise ValueError('Install outside the source folder')
    target.mkdir(parents=True, exist_ok=True)
    installed = []
    if frozen:
        binary = Path(sys.executable)
        if sys.platform == 'darwin' and binary.parent.name == 'MacOS':
            app_source = binary.parents[2]
            app_target = target / 'Send to Device.app'
            replace_tree(app_source, app_target)
            command = [str(app_target / 'Contents/MacOS/SendToDevice')]
        else:
            app_source = binary.parent
            if app_source == target:
                raise ValueError('Close the installed app and run the new installer from another folder')
            replace_tree(app_source, target)
            command = [str(target / binary.name)]
    else:
        shutil.copytree(source / 'send_to_device', target / 'send_to_device', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__'))
        for name in ('app.py', 'installer.py'):
            shutil.copy2(source / name, target / name)
        python = Path(sys.executable)
        if sys.platform == 'win32' and python.with_name('pythonw.exe').exists():
            python = python.with_name('pythonw.exe')
        command = [str(python), str(target / 'app.py')]
    if shortcuts and sys.platform == 'win32':
        # COM creates true shortcuts, preserving spaces and Unicode in arguments.
        appdata = Path(os.environ['APPDATA'])
        links = [appdata / 'Microsoft/Windows/Start Menu/Programs/Send to Device.lnk',
                 appdata / 'Microsoft/Windows/SendTo/Send to Device.lnk']
        def ps(value): return "'" + str(value).replace("'", "''") + "'"
        for link in links:
            link.parent.mkdir(parents=True, exist_ok=True)
            arguments = subprocess.list2cmdline(command[1:])
            script = (f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut({ps(link)});'
                      f'$s.TargetPath={ps(command[0])};$s.Arguments={ps(arguments)};'
                      f'$s.WorkingDirectory={ps(target)};$s.Save()')
            runtime.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script], check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            installed.append(str(link))
    elif shortcuts and sys.platform == 'darwin':
        bundle = Path.home() / 'Applications/Send to Device.app'
        if frozen:
            replace_tree(target / 'Send to Device.app', bundle)
        else:
            macos = bundle / 'Contents/MacOS'; macos.mkdir(parents=True, exist_ok=True)
            # Standalone Python .app launcher receives CLI paths; select files in UI from Finder.
            shell_launcher(macos / 'SendToDevice', command)
            with (bundle / 'Contents/Info.plist').open('wb') as stream:
                plistlib.dump(dict(CFBundleName=NAME, CFBundleDisplayName=NAME,
                    CFBundleIdentifier='io.github.n0ngxarm.sendtodevice', CFBundleExecutable='SendToDevice',
                    CFBundlePackageType='APPL', CFBundleShortVersionString='1.0.0', NSHighResolutionCapable=True), stream)
        installed.append(str(bundle))
    elif shortcuts:
        launcher = Path.home() / '.local/bin/send-to-device'
        shell_launcher(launcher, command); installed.append(str(launcher))
        legacy = Path.home() / '.local/share/nautilus/scripts/Send-to-Android'
        if legacy.exists() or legacy.is_symlink():
            try:
                legacy.unlink()
            except OSError:
                pass
        script = Path.home() / '.local/share/nautilus/scripts/Send-to-Device'
        shell_launcher(script, command); installed.append(str(script))
        desktop = Path.home() / '.local/share/applications/send-to-device.desktop'
        desktop.parent.mkdir(parents=True, exist_ok=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=Send to Device\n'
                           'Comment=Send files to your devices with Tailscale\n'
                           'Exec=' + ' '.join(desktop_quote(c) for c in command) + ' %F\n'
                           'Icon=folder-remote\nTerminal=false\nCategories=Network;FileTransfer;\n', encoding='utf-8')
        installed.append(str(desktop))
    (target / 'install-manifest.json').write_text(json.dumps(dict(shortcuts=installed, command=command)), encoding='utf-8')
    return target


def uninstall(destination=None):
    target = Path(destination or install_root()).absolute()
    manifest = target / 'install-manifest.json'
    if not manifest.is_file():
        raise ValueError('Installation manifest not found; nothing was removed')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    for item in data['shortcuts']:
        path = Path(item)
        if path.is_dir(): shutil.rmtree(path)
        elif path.exists(): path.unlink()
    shutil.rmtree(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=NAME + ' user installer')
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--prefix', type=Path)
    parser.add_argument('--no-shortcuts', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    try:
        target = uninstall(args.prefix) if args.uninstall else install(args.prefix, not args.no_shortcuts)
        text = ('Uninstalled: ' if args.uninstall else 'Installed: ') + str(target)
        print(text)
        if getattr(sys, 'frozen', False) and not args.quiet:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw(); messagebox.showinfo(NAME, text); root.destroy()
    except Exception as error:
        if getattr(sys, 'frozen', False) and not args.quiet:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw(); messagebox.showerror(NAME, str(error)); root.destroy()
        else:
            print('Installation failed: ' + str(error), file=sys.stderr)
        raise SystemExit(1)

if __name__ == '__main__': main()
