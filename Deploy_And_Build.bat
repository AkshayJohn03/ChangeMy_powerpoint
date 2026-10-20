@echo off
title BrandMorph Build and Deploy Gate
cd /d "%~dp0"

echo ========================================================
echo   BrandMorph Engine - Corporate DNA Verification Gate
echo ========================================================
echo.

set PY_BIN="%~dp0backend\venv\Scripts\python.exe"
if not exist %PY_BIN% (
    set PY_BIN=python
)

echo [1/3] Running Python Corporate DNA Tests...
%PY_BIN% -m pytest morphlite/tests/test_corporate_dna.py -v
if %errorlevel% neq 0 (
    echo [ERROR] Unit tests failed!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Building Frontend Studio (ui)...
cd "%~dp0ui"
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b %errorlevel%
)
cd "%~dp0"

echo.
echo [3/3] Ready for Git Commit and Deployment!
echo To commit and push to live Vercel:
echo   git add .
echo   git commit -m "feat(engine): integrate corporate style DNA rules, image rendering, and fixed canvas layout"
echo   git push origin main
echo ========================================================
pause
