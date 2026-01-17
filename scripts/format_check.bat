@echo off
REM Quick format check script for Windows - run before committing
REM Usage: scripts\format_check.bat

echo 🔍 Running format check...
uv run ruff format --check .

if %ERRORLEVEL% EQU 0 (
    echo ✅ Formatting check passed!
    echo.
    echo 💡 Tip: Run 'uv run ruff format .' to auto-fix formatting issues
    exit /b 0
) else (
    echo ❌ Formatting check failed!
    echo.
    echo 💡 Run 'uv run ruff format .' to auto-fix, then commit again
    exit /b 1
)
