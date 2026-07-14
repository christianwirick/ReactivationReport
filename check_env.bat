@echo off
REM Check the Hosted Players Report runtime environment without changing it.
setlocal
cd /d "%~dp0"

set "BOOTSTRAP_PY="
if defined HOSTED_PLAYERS_PYTHON (
    if exist "%HOSTED_PLAYERS_PYTHON%" set "BOOTSTRAP_PY="%HOSTED_PLAYERS_PYTHON%""
)
if not defined BOOTSTRAP_PY (
    where py >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PY=py -3"
)
if not defined BOOTSTRAP_PY (
    where python >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PY=python"
)
if not defined BOOTSTRAP_PY (
    where python3 >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PY=python3"
)

set "PYTHON_LAUNCHER="
if defined BOOTSTRAP_PY (
    for /f "usebackq delims=" %%P in (`%BOOTSTRAP_PY% "%~dp0check_env.py" --print-python-executable 2^>nul`) do set "PYTHON_LAUNCHER=%%P"
)

if not defined PYTHON_LAUNCHER (
    echo A supported Python 3.11 or newer was not found.
    echo Set HOSTED_PLAYERS_PYTHON to a full python.exe path or install Python 3.11+.
    pause
    exit /b 1
)

"%PYTHON_LAUNCHER%" check_env.py %*
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
