@echo off
title BrandMorph Git Sync ^& Push
cd /d "%~dp0"

echo ========================================================
echo   BrandMorph - Git Clean Sync ^& Push to Live Vercel
echo ========================================================
echo.

echo [1/3] Staging all resolved files...
git add .

echo.
echo [2/3] Finalizing merge and commit...
git commit -m "feat(engine): resolve merge conflicts and integrate corporate style DNA rules"
if %ERRORLEVEL% NEQ 0 (
    echo Note: Working tree already committed or up to date.
)

echo.
echo [3/3] Pushing to origin main (triggers Vercel build)...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Non-fast-forward detected, pulling latest changes...
    git pull origin main --no-rebase
    git push origin main
)

echo.
echo ========================================================
echo Sync and Push completed!
echo Vercel is now deploying your updates live to:
echo https://brandmorph-tau.vercel.app/
echo ========================================================
pause
