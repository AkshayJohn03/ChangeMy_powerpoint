@echo off
title Launching BrandMorph Studio...
echo Starting BrandMorph Backend & Studio Interface...

powershell -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"

:: Start Backend Engine
start /min "" "%~dp0backend\venv\Scripts\python.exe" "%~dp0backend\main.py"

:: Start Frontend Studio
cd /d "%~dp0ui"
start /min "" npm run dev -- --open

exit
