"""Install, open and uninstall an actual built bundle from a path with spaces."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
if sys.platform=='darwin': binary=root/'dist/Send to Device.app/Contents/MacOS/SendToDevice'
elif sys.platform=='win32': binary=root/'dist/SendToDevice/SendToDevice.exe'
else: binary=root/'dist/SendToDevice/SendToDevice'
with tempfile.TemporaryDirectory() as d:
    target=Path(d)/'app with spaces'
    subprocess.run([str(binary),'--install','--prefix',str(target),'--no-shortcuts','--quiet'],check=True,timeout=120)
    # Installing twice verifies upgrades, including macOS framework symlinks.
    subprocess.run([str(binary),'--install','--prefix',str(target),'--no-shortcuts','--quiet'],check=True,timeout=120)
    data=json.loads((target/'install-manifest.json').read_text())
    env=dict(os.environ,PYINSTALLER_RESET_ENVIRONMENT='1')
    subprocess.run(data['command']+['--smoke-test'],check=True,timeout=30,env=env)
    subprocess.run([str(binary),'--uninstall','--prefix',str(target),'--quiet'],check=True,timeout=30)
    assert not target.exists()
print('Bundled install, GUI launch and uninstall passed')
