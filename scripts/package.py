import pathlib
import shutil
import sys

platform = sys.argv[1]
root = pathlib.Path(__file__).resolve().parents[1]
stage = root / 'build' / ('Send-to-device-' + platform)
stage.mkdir(parents=True, exist_ok=True)
if platform.startswith('macos'):
    bundle = root / 'dist/Send to Device.app'
    # Keep the internal executable name consistent with the installer.
    import plistlib
    executable = bundle / 'Contents/MacOS/Send to Device'
    executable.rename(executable.with_name('SendToDevice'))
    plist = bundle / 'Contents/Info.plist'
    with plist.open('rb') as stream: info = plistlib.load(stream)
    info['CFBundleExecutable'] = 'SendToDevice'
    with plist.open('wb') as stream: plistlib.dump(info, stream)
    # Re-sign ad-hoc after renaming the executable / editing Info.plist.
    import subprocess
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(bundle)], check=True)
    shutil.copytree(bundle, stage / bundle.name, dirs_exist_ok=True, symlinks=True)
    launcher = 'install-macos.command'
else:
    shutil.copytree(root / 'dist/SendToDevice', stage / 'SendToDevice', dirs_exist_ok=True)
    launcher = 'install-windows.cmd' if platform.startswith('windows') else 'install-linux.sh'
for name in (launcher, 'README.md'):
    shutil.copy2(root / name, stage / name)
archive = str(root / 'dist' / stage.name)
if platform.startswith('macos'):
    # ditto preserves framework symlinks, resource forks and executable bits.
    subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(stage), archive + '.zip'], check=True)
else:
    shutil.make_archive(archive, 'zip', stage.parent, stage.name)
print(archive + '.zip')
