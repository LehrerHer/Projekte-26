#!/usr/bin/env python3
"""Wandelt eine Textdatei offline und kostenlos in eine MP3 um (Piper + ffmpeg).

Einmalige Vorbereitung:
  1. Piper installieren:            pip install piper-tts
  2. ffmpeg installieren (für MP3): Mac: brew install ffmpeg
                                    Windows: winget install ffmpeg
                                    Linux: sudo apt install ffmpeg
  3. Deutsche Stimme "Thorsten" herunterladen (zwei Dateien, in einen Ordner,
     z. B. ~/piper-voices):
       https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx
       https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high/de_DE-thorsten-high.onnx.json

Aufruf:
  python text_zu_mp3_piper.py text.txt --stimme ~/piper-voices/de_DE-thorsten-high.onnx

Langsamer sprechen (z. B. für Lernende):
  python text_zu_mp3_piper.py text.txt --stimme ... --tempo 0.9
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def pruefe_programm(name: str, hinweis: str) -> None:
    if shutil.which(name) is None:
        sys.exit(f"'{name}' wurde nicht gefunden. {hinweis}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Text → MP3 mit Piper (offline)")
    parser.add_argument("datei", help="Textdatei (UTF-8)")
    parser.add_argument("--stimme", required=True,
                        help="Pfad zur .onnx-Stimmdatei (die .json muss daneben liegen)")
    parser.add_argument("--ausgabe", help="Name der MP3 (Standard: wie Textdatei)")
    parser.add_argument("--tempo", type=float, default=1.0,
                        help="Sprechtempo per ffmpeg, 0.5 bis 2.0 (Standard 1.0, z. B. 0.9 = langsamer)")
    args = parser.parse_args()

    if not 0.5 <= args.tempo <= 2.0:
        sys.exit("--tempo muss zwischen 0.5 und 2.0 liegen.")

    pruefe_programm("piper", "Installation: pip install piper-tts")
    pruefe_programm("ffmpeg", "Bitte ffmpeg installieren (siehe Hinweis oben in der Datei).")

    quelle = Path(args.datei)
    stimme = Path(args.stimme).expanduser()
    if not stimme.exists():
        sys.exit(f"Stimmdatei nicht gefunden: {stimme}")
    text = quelle.read_text(encoding="utf-8")
    ziel = Path(args.ausgabe) if args.ausgabe else quelle.with_suffix(".mp3")

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "ausgabe.wav"

        # 1) Piper: Text über stdin einlesen, WAV schreiben
        piper = subprocess.run(
            ["piper", "--model", str(stimme), "--output_file", str(wav)],
            input=text, text=True, encoding="utf-8",
        )
        if piper.returncode != 0 or not wav.exists():
            sys.exit("Piper ist fehlgeschlagen (siehe Meldung oben).")

        # 2) ffmpeg: WAV → MP3, optional mit angepasstem Tempo
        befehl = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav)]
        if args.tempo != 1.0:
            befehl += ["-filter:a", f"atempo={args.tempo}"]
        befehl += ["-codec:a", "libmp3lame", "-qscale:a", "4", str(ziel)]
        if subprocess.run(befehl).returncode != 0:
            sys.exit("ffmpeg ist fehlgeschlagen (siehe Meldung oben).")

    print(f"Fertig: {ziel}")


if __name__ == "__main__":
    main()
