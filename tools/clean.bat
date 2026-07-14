@echo off
cd /d "%~dp0\.."
REM Remove local Python/macOS cache files without touching source, outputs, or user data.
REM This is intentionally pure Windows batch so it works before Python setup exists.
setlocal EnableDelayedExpansion

set /a REMOVED=0
set /a FAILED=0

echo Cleaning cache artifacts under:
echo %CD%
echo.

for /d /r %%D in (__pycache__ .pytest_cache .mypy_cache .ruff_cache) do (
    if exist "%%D\" (
        echo Removing directory: %%D
        rmdir /s /q "%%D" 2>nul
        if exist "%%D\" (
            echo   WARNING: Could not remove %%D
            set /a FAILED+=1
        ) else (
            set /a REMOVED+=1
        )
    )
)

for /r %%F in (*.pyc *.pyo .DS_Store) do (
    if exist "%%F" (
        echo Removing file: %%F
        del /f /q "%%F" 2>nul
        if exist "%%F" (
            echo   WARNING: Could not remove %%F
            set /a FAILED+=1
        ) else (
            set /a REMOVED+=1
        )
    )
)

echo.
if !FAILED! gtr 0 (
    echo Cleanup finished with !FAILED! item(s) that could not be removed.
    echo Close any open Python windows, terminals, or editors, then run this again.
    exit /b 1
)

if !REMOVED! equ 0 (
    echo No cache artifacts found.
) else (
    echo Cleanup complete. Removed !REMOVED! item(s).
)
