@echo off
chcp 65001 >nul
title Punktesystem-Generator

echo ============================================
echo   Punktesystem-Generator wird gestartet ...
echo ============================================
echo.

:: Python vorhanden?
python --version >nul 2>&1
if errorlevel 1 (
    echo Python wurde nicht gefunden.
    echo.
    echo Bitte Python von der offiziellen Website herunterladen:
    echo   https://www.python.org/downloads/
    echo.
    echo Wichtig beim Installieren:
    echo   [x] "Add Python to PATH" ankreuzen!
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Abhaengigkeiten installieren / aktualisieren
echo Bibliotheken werden geprueft und ggf. installiert...
python -m pip install --quiet --upgrade tkinterdnd2 odfpy
if errorlevel 1 (
    echo.
    echo Fehler beim Installieren der Bibliotheken.
    echo Bitte Internetverbindung pruefen und erneut versuchen.
    pause
    exit /b 1
)

:: Anwendung starten
echo Starte Anwendung...
python "%~dp0punktesystem_generator.py"
