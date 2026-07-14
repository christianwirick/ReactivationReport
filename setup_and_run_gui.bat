@echo off
REM First-run helper for the source-code version of Hosted Players Report.
REM Creates a per-user local virtual environment, installs dependencies, then opens the GUI.
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1

set "VENV_ROOT=%LOCALAPPDATA%\HostedPlayersReport"
if "%LOCALAPPDATA%"=="" set "VENV_ROOT=%USERPROFILE%\AppData\Local\HostedPlayersReport"
set "VENV_DIR=%VENV_ROOT%\.venv"

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

if not defined BOOTSTRAP_PY (
    echo Python was not found.
    echo Install Python 3.11 or newer from the Microsoft Store or python.org, then run this again.
    pause
    exit /b 1
)

set "PYTHON_LAUNCHER="
for /f "usebackq delims=" %%P in (`%BOOTSTRAP_PY% "%~dp0check_env.py" --print-python-executable 2^>nul`) do set "PYTHON_LAUNCHER=%%P"

if not defined PYTHON_LAUNCHER (
    echo A supported Python 3.11 or newer was not found.
    echo Set HOSTED_PLAYERS_PYTHON to a full python.exe path or install Python 3.11+.
    pause
    exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating local Python environment...
    if not exist "%VENV_ROOT%" mkdir "%VENV_ROOT%"
    "%PYTHON_LAUNCHER%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create the Python virtual environment.
        pause
        exit /b 1
    )
)

echo Installing or verifying Python packages...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install required Python packages.
    echo If package installation is blocked, ask IT to allow openpyxl and pywin32.
    pause
    exit /b 1
)

echo Starting Hosted Players Report...
if exist "%VENV_DIR%\Scripts\pythonw.exe" (
    start "" "%VENV_DIR%\Scripts\pythonw.exe" gui.py
) else (
    "%VENV_DIR%\Scripts\python.exe" gui.py
)
