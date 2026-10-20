@echo off
title BrandMorph Zero-Leak Golden Pair DNA Extractor
echo =====================================================================
echo   BrandMorph - Zero-Leak Golden Pair Style ^& Metadata DNA Extractor
echo   100%% Offline CPU - ZERO Text, ZERO Images, ZERO Proprietary Leakage
echo =====================================================================
echo.

cd /d "%~dp0"

set PY_BIN="%~dp0backend\venv\Scripts\python.exe"
if not exist %PY_BIN% (
    set PY_BIN=python
)

echo [1] Extracting DNA from 10 Oct Golden Pair (17 Oct Golden.pptx vs Raw.pptx)...
%PY_BIN% "%~dp0scripts\extract_golden_pair_dna.py" --pair-10oct

echo.
echo [2] Extracting DNA from 12 Dec Batch (OneDrive_2025-12-11\Updated)...
%PY_BIN% "%~dp0scripts\extract_golden_pair_dna.py" --batch-12dec

echo.
echo =====================================================================
echo Extraction complete! Learned rules saved to data\metadata\LEARNED_RULES.json
echo Full style DNA saved to data\metadata\golden_style_dna.json
echo =====================================================================
pause
