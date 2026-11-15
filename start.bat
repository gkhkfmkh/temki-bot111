@echo off
setlocal
cd /d "%~dp0"
set "PLAYEROK_AUTO_INSTALL=1"
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        py -3.12 server.py
        goto finish
    )
)
python server.py
:finish
set "code=%errorlevel%"
echo.
if not "%code%"=="0" echo Bot exited with code %code%. Check logs\latest.log.
pause
exit /b %code%
