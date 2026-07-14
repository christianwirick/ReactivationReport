@echo off
cd /d "%~dp0\.."
set PYTHONDONTWRITEBYTECODE=1
python -m compileall hpr tools gui.py cli.py check_env.py
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 exit /b 1
python -m ruff check .
if errorlevel 1 exit /b 1
python -m ruff format --check .
if errorlevel 1 exit /b 1
python -m mypy hpr cli.py check_env.py gui.py
if errorlevel 1 exit /b 1
