"""Build on Windows CI only; no developer machine dependency installation."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import importlib.metadata

root=Path(__file__).resolve().parents[1]
NAME='SendToDevice'
ENTRY='app.py'
VERSION='1.0.1'

def build(name,entry,windowed):
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--noupx','--name',name,'--icon','assets/app.ico','--version-file','packaging/version_info.txt','--add-data','assets;assets']
    command+=['--windowed' if windowed else '--console']
    if NAME=='GETEdit':
        command+=['--copy-metadata','PyMuPDF','--copy-metadata','PySide6','--copy-metadata','shiboken6']
    subprocess.run(command+[entry],cwd=root,check=True)

if sys.platform!='win32':raise SystemExit('Run this build on Windows CI')
version_tuple=tuple(int(x) for x in VERSION.split('.'))+(0,)
(root/'packaging/version_info.txt').write_text("VSVersionInfo(ffi=FixedFileInfo(filevers="+repr(version_tuple)+", prodvers="+repr(version_tuple)+", mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0,0)), kids=[StringFileInfo([StringTable('040904B0', [StringStruct('CompanyName','n0ngXarm'), StringStruct('FileDescription',"+repr(NAME)+"), StringStruct('FileVersion',"+repr(VERSION)+"), StringStruct('ProductName',"+repr(NAME)+"), StringStruct('ProductVersion',"+repr(VERSION)+")])]), VarFileInfo([VarStruct('Translation',[1033,1200])])])")
build(NAME,ENTRY,True)
stage=root/'dist'/NAME
if NAME=='GETEdit':
    build('GETEditWorker','import_worker.py',False)
    shutil.copytree(root/'dist/GETEditWorker',stage,dirs_exist_ok=True)
for document in ('LICENSE','README.md','THIRD_PARTY.md','NOTICE'):
    if (root/document).exists():shutil.copy2(root/document,stage/document)
# Bundle exact application source and generated notices alongside binaries.
source=root/'dist/corresponding-source.zip'
subprocess.run(['git','archive','--format=zip','--output',str(source),'HEAD'],cwd=root,check=True)
shutil.copy2(source,stage/'corresponding-source.zip')
notices=['Unsigned build. Windows SmartScreen reputation is not guaranteed.', 'No firewall rules, antivirus exclusions or background services are installed.', 'Python: '+sys.version, 'Application source: corresponding-source.zip']
if NAME=='GETEdit':
    notices+=['PyMuPDF: AGPL-3.0; https://pypi.org/project/PyMuPDF/','PySide6/Qt and shiboken6: LGPL-3.0/GPL; https://code.qt.io/cgit/pyside/pyside-setup.git/','Qt source: https://download.qt.io/archive/qt/','The shared Qt libraries in _internal may be replaced with compatible modified versions.']
    for package in ('PyMuPDF','PySide6','shiboken6'):
        dist=importlib.metadata.distribution(package)
        notices.append(package+' '+dist.version)
        for f in dist.files or []:
            if any(word in str(f).lower() for word in ('license','copying','notice')):
                src=Path(dist.locate_file(f))
                if src.is_file():
                    dest=stage/'licenses'/package/str(f).replace('..','_')
                    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
(stage/'BUILD-NOTICES.txt').write_text('\n'.join(notices),encoding='utf-8')
compiler=Path(r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe')
if not compiler.exists():raise SystemExit('Inno Setup 6 unavailable on CI runner')
subprocess.run([str(compiler),str(root/'packaging/windows.iss')],cwd=root,check=True)
