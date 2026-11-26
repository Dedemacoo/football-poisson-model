@echo off
chcp 65001 > nul
title AI Futbol Tahmin & Canlı Kupon Botu
cd /d "%~dp0\football_poisson_model"
echo ===================================================
echo   ⚽ AI Futbol Tahmin & Canlı Otonom Kupon Botu
echo ===================================================
echo [1/2] Canlı maçlar ve güncel oranlar güncelleniyor...
python live_fetcher.py
echo.
echo [2/2] Web Arayüzü Başlatılıyor (http://localhost:5000)...
start http://localhost:5000
python dashboard.py
pause
