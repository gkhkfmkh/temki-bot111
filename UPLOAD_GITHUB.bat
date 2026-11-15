@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Git is not installed or not found in PATH.
  echo Install Git for Windows: https://git-scm.com/download/win
  echo Then run this file again.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0UPLOAD_GITHUB.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo Upload completed. Check your GitHub repository.
) else (
  echo Upload failed. See the error above.
)
pause
exit /b %RESULT%
