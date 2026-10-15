@echo off
setlocal
cd /d "%~dp0"
if exist "SendToDevice\SendToDevice.exe" (
    start /wait "" "SendToDevice\SendToDevice.exe" --install
    exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 installer.py --install
) else (
    python installer.py --install
)
if errorlevel 1 (
    echo Install Python 3.10+ from python.org with Tcl/Tk and the Python launcher enabled.
    pause
    exit /b 1
)
echo Installation complete. Open Send to Device from Start, or right-click a file and use Send to.
pause
