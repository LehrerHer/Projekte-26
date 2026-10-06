#!/bin/bash
# Mac-Startdatei: Text vertonen (offline, Piper)
# Einmalig ausfuehrbar machen:  chmod +x start_vertonen.command
# Danach per Doppelklick starten. Die Textdatei kann ins Terminalfenster gezogen werden.

cd "$(dirname "$0")" || exit 1

STIMMENORDNER="$HOME/piper-voices"
STIMME="$STIMMENORDNER/de_DE-thorsten-high.onnx"
URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high"

echo "============================================"
echo "  Text vertonen (offline, Piper)"
echo "============================================"
echo

fehler() {
    echo "$1"
    read -r -p "Enter zum Beenden ..."
    exit 1
}

# Python vorhanden?
command -v python3 >/dev/null 2>&1 || fehler "python3 nicht gefunden. Bitte installieren: https://www.python.org/downloads/"

# ffmpeg vorhanden? (Installation ueber Homebrew)
if ! command -v ffmpeg >/dev/null 2>&1; then
    command -v brew >/dev/null 2>&1 || fehler "ffmpeg fehlt und Homebrew ist nicht installiert. Siehe https://brew.sh und danach: brew install ffmpeg"
    echo "ffmpeg wird installiert ..."
    brew install ffmpeg || fehler "Installation von ffmpeg fehlgeschlagen."
fi

# Piper installieren / pruefen
echo "Piper wird geprueft und ggf. installiert..."
python3 -m pip install --quiet --upgrade piper-tts || fehler "Fehler beim Installieren von piper-tts. Internetverbindung pruefen."

# Stimme einmalig herunterladen
if [ ! -f "$STIMME" ]; then
    echo "Stimme \"Thorsten\" wird heruntergeladen (einmalig) ..."
    mkdir -p "$STIMMENORDNER"
    if ! curl -L -f -o "$STIMME" "$URL/de_DE-thorsten-high.onnx" \
       || ! curl -L -f -o "$STIMME.json" "$URL/de_DE-thorsten-high.onnx.json"; then
        rm -f "$STIMME" "$STIMME.json"
        fehler "Download fehlgeschlagen."
    fi
fi

# Textdatei bestimmen (Pfad eintippen oder Datei ins Fenster ziehen)
TEXT="$1"
if [ -z "$TEXT" ]; then
    read -r -p "Pfad zur Textdatei (.txt, gern ins Fenster ziehen): " TEXT
fi
# Anfuehrungszeichen, Backslashes (vom Ziehen) und Leerzeichen am Ende entfernen
TEXT="$(printf '%s' "$TEXT" | sed -e "s/[\"']//g" -e 's/\\//g' -e 's/[[:space:]]*$//')"
[ -f "$TEXT" ] || fehler "Datei nicht gefunden: $TEXT"

# Tempo abfragen
read -r -p "Tempo 0.5-2.0 (Enter = 1.0, 0.9 = langsamer): " TEMPO
TEMPO="${TEMPO:-1.0}"

echo
echo "Erzeuge MP3 ..."
python3 text_zu_mp3_piper.py "$TEXT" --stimme "$STIMME" --tempo "$TEMPO"
echo
read -r -p "Fertig. Enter zum Beenden ..."
