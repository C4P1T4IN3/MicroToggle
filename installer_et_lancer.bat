@echo off
cd /d "%~dp0"
py -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0microtoggle.py"
exit /b
:fail
echo Installation echouee. Verifiez que Python est installe avec le lanceur py.
pause
