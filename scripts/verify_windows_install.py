"""Exercise the installed binaries, update, registry, shortcuts and uninstall."""
import os
import subprocess
import tempfile
import winreg
from pathlib import Path

NAME='SendToDevice'
LABEL='Send-to-device'
root=Path(__file__).resolve().parents[1]
setup=next((root/'dist/installer').glob('*setup.exe'))

def run(args, timeout=180):
    diagnostics=root/'build/windows-runtime-error.txt'
    diagnostics.parent.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,WINDOWS_APP_DIAGNOSTICS=str(diagnostics))
    try:subprocess.run(list(map(str,args)),check=True,timeout=timeout,env=env)
    except Exception:
        if diagnostics.exists():print(diagnostics.read_text(encoding='utf-8'),flush=True)
        raise

with tempfile.TemporaryDirectory(prefix='windows-install-') as d:
    folder=Path(d);target=folder/'โปรแกรม with spaces';fixture=folder/'test data';fixture.mkdir()
    sentinel=fixture/'keep.txt';sentinel.write_text('user data')
    shortcut=Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs'/LABEL/(LABEL+'.lnk')
    key='Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\n0ngXarm.'+NAME+'_is1'
    for phase in ('fresh','update'):
        run([setup,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/DIR='+str(target),'/LOG='+str(folder/(phase+'.log'))])
        exe=target/(NAME+'.exe');assert exe.is_file()
        assert shortcut.is_file(),shortcut
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as registry:
            location=winreg.QueryValueEx(registry,'InstallLocation')[0]
            assert Path(location)==target
        if NAME=='SendToDevice':run([exe,'--smoke-test'],60)
        else:
            marker=fixture/'verified.txt';marker.unlink(missing_ok=True)
            run([exe,'--verify-install',fixture],90)
            assert marker.read_text()=='ok'
        assert sentinel.read_text()=='user data'
    run([target/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'])
    assert not (target/(NAME+'.exe')).exists()
    assert not shortcut.exists()
    try:winreg.OpenKey(winreg.HKEY_CURRENT_USER,key)
    except FileNotFoundError:pass
    else:raise AssertionError('Uninstall registry entry remains')
    assert sentinel.read_text()=='user data'
print('PASS: installed GUI/runtime, update, shortcuts, registry, uninstall; user fixture retained')
