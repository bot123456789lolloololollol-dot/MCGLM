@echo off
:: MCGLM overlay launcher — opens all three Python tools in separate windows
:: Requirements: Python 3.10+ installed, "pip install -r requirements.txt" run
:: The game must have the feed-mod loaded and be in windowed/borderless mode

echo MCGLM overlay launcher
echo =====================
echo.
echo Starting trajectory overlay (F9 to quit)...
start "MCGLM Trajectory" cmd /k "python "%~dp0python\trajectory_overlay.py""
timeout /t 1 /nobreak >nul

echo Starting logout tracker (F9 to quit)...
start "MCGLM Logout" cmd /k "python "%~dp0python\logout_tracker.py""
timeout /t 1 /nobreak >nul

echo Starting status HUD (F9 to quit)...
start "MCGLM HUD" cmd /k "python "%~dp0python\status_hud.py""

echo.
echo All overlays started. Press F9 in any overlay window to close it.
echo Close this window when done.
pause
