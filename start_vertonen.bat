@echo off
chcp 65001 >nul
title Text vertonen (Piper)

:: Nutzung: Textdatei (.txt) per Drag & Drop auf diese Datei ziehen
:: oder doppelklicken und den Pfad eingeben.

set "STIMMENORDNER=%USERPROFILE%\piper-voices"
set "STIMME=%STIMMENORDNER%\de_DE-thorsten-high.onnx"
set "URL=https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high"

echo ============================================
echo   Text vertonen (offline, Piper)
echo ============================================
echo.

:: Python vorhanden?
python --version >nul 2>&1
if errorlevel 1 (
    echo Python wurde nicht gefunden.
    echo Bitte installieren: https://www.python.org/downloads/
    echo Wichtig: "Add Python to PATH" ankreuzen!
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ffmpeg vorhanden?
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ffmpeg wird installiert ...
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    echo.
    echo Bitte dieses Fenster schliessen und start_vertonen.bat neu starten,
    echo damit ffmpeg gefunden wird.
    pause
    exit /b 1
)

:: Piper installieren / pruefen
echo Piper wird geprueft und ggf. installiert...
python -m pip install --quiet --upgrade piper-tts
if errorlevel 1 (
    echo Fehler beim Installieren von piper-tts. Internetverbindung pruefen.
    pause
    exit /b 1
)

:: Stimme einmalig herunterladen
if not exist "%STIMME%" (
    echo Stimme "Thorsten" wird heruntergeladen ^(einmalig^) ...
    mkdir "%STIMMENORDNER%" 2>nul
    curl -L -o "%STIMME%" "%URL%/de_DE-thorsten-high.onnx"
    curl -L -o "%STIMME%.json" "%URL%/de_DE-thorsten-high.onnx.json"
    if errorlevel 1 (
        echo Download fehlgeschlagen.
        del "%STIMME%" "%STIMME%.json" 2>nul
        pause
        exit /b 1
    )
)

:: Textdatei bestimmen
set "TEXT=%~1"
if "%TEXT%"=="" set /p "TEXT=Pfad zur Textdatei (.txt): "
set "TEXT=%TEXT:"=%"
if not exist "%TEXT%" (
    echo Datei nicht gefunden: %TEXT%
    pause
    exit /b 1
)

:: Tempo abfragen
set "TEMPO=1.0"
set /p "TEMPO=Tempo 0.5-2.0 (Enter = 1.0, 0.9 = langsamer): "
if "%TEMPO%"=="" set "TEMPO=1.0"

echo.
echo Erzeuge MP3 ...
python "%~dp0text_zu_mp3_piper.py" "%TEXT%" --stimme "%STIMME%" --tempo %TEMPO%
echo.
pause
