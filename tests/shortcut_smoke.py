"""CI-only: check native shortcut creation in an ephemeral runner account."""
from pathlib import Path
import json
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import installer
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / 'installed app'
    try:
        installer.install(target)
        manifest=json.loads((target/'install-manifest.json').read_text())
        assert manifest['shortcuts']
        for item in manifest['shortcuts']: assert Path(item).exists(), item
    finally:
        if (target/'install-manifest.json').exists(): installer.uninstall(target)
    for item in manifest['shortcuts']: assert not Path(item).exists(), item
print('Native shortcuts created and removed successfully')
