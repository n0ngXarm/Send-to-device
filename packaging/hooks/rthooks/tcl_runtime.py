"""Support ordinary Tcl data folders and Windows Tcl 9 DLL-embedded zipfs.

PyInstaller 6.20 assumes external data folders. New Windows Python embeds
Tcl/Tk 9 scripts in DLLs. Validate the actual Tcl interpreter's library before
accepting missing folders; keep the old failure for genuinely incomplete data.
"""
import os
import sys
from pathlib import Path
import _tkinter

root=Path(sys._MEIPASS)
tcl=root/'_tcl_data';tk=root/'_tk_data'
if tcl.is_dir():
    os.environ['TCL_LIBRARY']=str(tcl)
else:
    interpreter=_tkinter.create(None,'frozen','Tk',False,True,False,False,None)
    library=interpreter.eval('info library')
    if not library.startswith('//zipfs:'):
        raise FileNotFoundError('Bundled Tcl scripts missing: '+library)
    del interpreter
if tk.is_dir():
    os.environ['TK_LIBRARY']=str(tk)
elif tcl.is_dir():
    raise FileNotFoundError('Bundled Tk scripts missing')
