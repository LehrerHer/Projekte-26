@echo off
chcp 65001 >nul
title Punktesystem-Generator – EXE erstellen

echo ============================================
echo   Erstelle eigenstaendige Windows-EXE
echo ============================================
echo.
echo Dieser Vorgang dauert 1-3 Minuten.
echo.

:: Python vorhanden?
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nicht gefunden. Bitte zuerst Python installieren:
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Abhaengigkeiten + PyInstaller installieren
echo Installiere Abhaengigkeiten...
python -m pip install --quiet --upgrade tkinterdnd2 odfpy pyinstaller
if errorlevel 1 (
    echo Fehler beim Installieren. Bitte Internetverbindung pruefen.
    pause
    exit /b 1
)

:: EXE bauen
echo.
echo Baue EXE ...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "Punktesystem-Generator" ^
    --collect-all tkinterdnd2 ^
    "%~dp0punktesystem_generator.py"

if errorlevel 1 (
    echo.
    echo Fehler beim Erstellen der EXE.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Fertig!
echo   Die Datei liegt in:  dist\Punktesystem-Generator.exe
echo   Diese EXE kann auf beliebige Rechner kopiert werden.
echo   Kein Python noetig.
echo ============================================
echo.
pause
