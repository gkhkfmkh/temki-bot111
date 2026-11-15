@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -m pip install -r requirements.txt
    goto finish
)
python -m pip install -r requirements.txt
:finish
set "code=%errorlevel%"
pause
exit /b %code%
