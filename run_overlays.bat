@echo off
setlocal EnableExtensions

:: MCGLM overlay launcher for Dawn / Minecraft 26.2.
:: Install dependencies first with: python -m pip install -r requirements.txt
:: The game must have the feed-mod loaded and be in windowed/borderless mode.

set "ROOT=%~dp0"
set "PYTHON_EXE=python"
set "PYTHON_ARGS="

:: Prefer a project-local environment, then the Windows Python launcher.
if exist "%ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
    )
)

"%PYTHON_EXE%" %PYTHON_ARGS% --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.10 or newer was not found.
    echo Install Python and run: python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo MCGLM overlay launcher
echo =====================
echo.
echo Starting trajectory overlay (F9 to quit)...
start "MCGLM Trajectory" "%ComSpec%" /k "cd /d ""%ROOT%"" && ""%PYTHON_EXE%"" %PYTHON_ARGS% ""%ROOT%python\trajectory_overlay.py"""
timeout /t 1 /nobreak >nul

echo Starting logout tracker (F9 to quit)...
start "MCGLM Logout" "%ComSpec%" /k "cd /d ""%ROOT%"" && ""%PYTHON_EXE%"" %PYTHON_ARGS% ""%ROOT%python\logout_tracker.py"""
timeout /t 1 /nobreak >nul

echo Starting status HUD (F9 to quit)...
start "MCGLM HUD" "%ComSpec%" /k "cd /d ""%ROOT%"" && ""%PYTHON_EXE%"" %PYTHON_ARGS% ""%ROOT%python\status_hud.py"""

echo.
echo All overlays started. Press F9 in any overlay window to close it.
echo Close this window when done.
pause
