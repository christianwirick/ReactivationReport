@echo off
REM Launch the Hosted Players Report GUI after setup_and_run_gui.bat has run.
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1

set "VENV_ROOT=%LOCALAPPDATA%\HostedPlayersReport"
if "%LOCALAPPDATA%"=="" set "VENV_ROOT=%USERPROFILE%\AppData\Local\HostedPlayersReport"
set "VENV_DIR=%VENV_ROOT%\.venv"

if exist "%VENV_DIR%\Scripts\pythonw.exe" (
    start "" "%VENV_DIR%\Scripts\pythonw.exe" gui.py
) else if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" gui.py
) else (
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
    if defined PYTHON_LAUNCHER (
        "%PYTHON_LAUNCHER%" gui.py
    ) else (
        echo No local Python environment or supported fallback Python was found.
        echo Run setup_and_run_gui.bat or set HOSTED_PLAYERS_PYTHON to a Python 3.11+ executable.
        pause
        exit /b 1
    )
)
