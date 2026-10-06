#!/usr/bin/env python3
"""Text vertonen (offline): kleines Fenster, Textdatei waehlen -> MP3.

Gedacht zum Einpacken mit PyInstaller (siehe .github/workflows/build-vertonen.yml).
Die Stimme (Thorsten) und ffmpeg (imageio-ffmpeg) sind dann in der Programmdatei
enthalten, es muss nichts installiert werden.

Zum Testen mit Python:
  pip install piper-tts imageio-ffmpeg
  python vertonen_app.py     (Stimme in ~/piper-voices/de_DE-thorsten-high.onnx)
"""

import faulthandler
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import wave
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

STIMME_NAME = "de_DE-thorsten-high.onnx"
LOGDATEI = Path.home() / "Vertonen-Log.txt"
# faulthandler braucht eine dauerhaft offene Datei (Referenz behalten, sonst wird sie geschlossen)
try:
    ABSTURZ_LOG = open(LOGDATEI, "a", buffering=1)
except OSError:
    ABSTURZ_LOG = None


def log(meldung: str) -> None:
    """Schreibt jeden Schritt mit Uhrzeit in ~/Vertonen-Log.txt (zur Fehlersuche)."""
    try:
        with open(LOGDATEI, "a", encoding="utf-8") as datei:
            datei.write(f"{time.strftime('%H:%M:%S')}  {meldung}\n")
    except OSError:
        pass


def finde_stimme() -> Path:
    basis = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    for kandidat in (basis / "voice" / STIMME_NAME,
                     Path.home() / "piper-voices" / STIMME_NAME):
        if kandidat.exists():
            return kandidat
    raise FileNotFoundError(f"Stimmdatei {STIMME_NAME} nicht gefunden.")


ERLAUBTE_ZEICHEN = set("äöüÄÖÜß„“”‚‘’–—…»«€§°²³·\n\r\t ")


def unplausibel(text: str) -> int:
    """Zaehlt Zeichen, die in einem deutschen Text ungewoehnlich sind."""
    return sum(1 for z in text if not (z.isascii() or z in ERLAUBTE_ZEICHEN))


def lese_text(pfad: Path) -> str:
    """Liest eine Textdatei: UTF-8, UTF-16 oder (Windows- bzw. Mac-)Altkodierung."""
    daten = pfad.read_bytes()
    if daten.startswith((b"\xff\xfe", b"\xfe\xff")):
        text, kodierung = daten.decode("utf-16"), "utf-16"
    else:
        try:
            text, kodierung = daten.decode("utf-8-sig"), "utf-8"
        except UnicodeDecodeError:
            kandidaten = {k: daten.decode(k, errors="replace") for k in ("cp1252", "mac_roman")}
            kodierung = min(kandidaten, key=lambda k: unplausibel(kandidaten[k]))
            text = kandidaten[kodierung]
    log(f"Text gelesen als {kodierung}")
    return text


def vertone(quelle: Path, ziel: Path, tempo: float, melde=lambda text: None) -> None:
    melde("Stimme wird geladen …")
    log("Importiere piper")
    import piper
    from piper import PiperVoice          # erst hier, damit das Fenster schnell erscheint
    import imageio_ffmpeg

    stimme = finde_stimme()
    log(f"Lade Stimme: {stimme}")
    voice = PiperVoice.load(stimme)
    text = lese_text(quelle)
    log(f"Stimme geladen, Text mit {len(text)} Zeichen")
    log(f"piper: {Path(piper.__file__).parent}, espeak-Daten vorhanden: "
        f"{(Path(piper.__file__).parent / 'espeak-ng-data').exists()}")
    log(f"ffmpeg: {imageio_ffmpeg.get_ffmpeg_exe()}")
    faulthandler.dump_traceback_later(60, repeat=True, file=ABSTURZ_LOG)
    log("Beginne Sprachsynthese")

    with tempfile.TemporaryDirectory() as tmp:
        wav_pfad = Path(tmp) / "ausgabe.wav"
        saetze = 0
        with wave.open(str(wav_pfad), "wb") as wav:
            for chunk in voice.synthesize(text):
                if saetze == 0:
                    wav.setframerate(chunk.sample_rate)
                    wav.setsampwidth(chunk.sample_width)
                    wav.setnchannels(chunk.sample_channels)
                wav.writeframes(chunk.audio_int16_bytes)
                saetze += 1
                melde(f"Gesprochen: {saetze} Satz/Sätze …")
                log(f"Satz {saetze} fertig")
        faulthandler.cancel_dump_traceback_later()
        if saetze == 0:
            raise RuntimeError("Der Text enthält nichts zum Sprechen.")

        melde("MP3 wird erzeugt …")
        log("Starte ffmpeg")
        befehl = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                  "-i", str(wav_pfad)]
        if tempo != 1.0:
            befehl += ["-filter:a", f"atempo={tempo}"]
        befehl += ["-codec:a", "libmp3lame", "-qscale:a", "4", str(ziel)]
        ergebnis = subprocess.run(befehl, capture_output=True, text=True)
        if ergebnis.returncode != 0:
            raise RuntimeError(f"ffmpeg ist fehlgeschlagen:\n{ergebnis.stderr}")
    log(f"Fertig: {ziel}")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Text vertonen")
        self.resizable(False, False)
        self.datei = tk.StringVar()
        self.tempo = tk.DoubleVar(value=1.0)
        self.status = tk.StringVar(value="Textdatei (.txt) auswählen.")

        rahmen = ttk.Frame(self, padding=16)
        rahmen.grid()
        ttk.Label(rahmen, text="Textdatei:").grid(row=0, column=0, sticky="w")
        ttk.Entry(rahmen, textvariable=self.datei, width=44).grid(row=1, column=0, padx=(0, 8))
        ttk.Button(rahmen, text="Auswählen …", command=self.waehle).grid(row=1, column=1)

        ttk.Label(rahmen, text="Tempo (0.9 = langsamer):").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(rahmen, from_=0.5, to=1.5, variable=self.tempo,
                  command=lambda _=None: self.tempo.set(round(self.tempo.get(), 2))
                  ).grid(row=3, column=0, sticky="ew")
        ttk.Label(rahmen, textvariable=self.tempo, width=5).grid(row=3, column=1)

        self.knopf = ttk.Button(rahmen, text="MP3 erstellen", command=self.start)
        self.knopf.grid(row=4, column=0, columnspan=2, pady=(16, 8))
        ttk.Label(rahmen, textvariable=self.status, wraplength=420).grid(row=5, column=0, columnspan=2)

    def waehle(self) -> None:
        pfad = filedialog.askopenfilename(filetypes=[("Textdateien", "*.txt"), ("Alle", "*.*")])
        if pfad:
            self.datei.set(pfad)

    def start(self) -> None:
        quelle = Path(self.datei.get().strip())
        if not quelle.is_file():
            messagebox.showerror("Fehler", "Bitte eine vorhandene Textdatei auswählen.")
            return
        ziel = quelle.with_suffix(".mp3")
        tempo = float(self.tempo.get())
        self.knopf.state(["disabled"])
        self.status.set("Wird erstellt … (bei langen Texten dauert das etwas)")
        threading.Thread(target=self.arbeite, args=(quelle, ziel, tempo), daemon=True).start()

    def arbeite(self, quelle: Path, ziel: Path, tempo: float) -> None:
        try:
            log(f"Start: {quelle} (Tempo {tempo})")
            vertone(quelle, ziel, tempo, lambda text: self.after(0, lambda: self.status.set(text)))
            self.after(0, lambda: self.fertig(f"Fertig: {ziel}"))
        except Exception as fehler:
            log("FEHLER:\n" + traceback.format_exc())
            meldung = f"Fehler: {fehler}\nDetails: {LOGDATEI}"
            self.after(0, lambda: self.fertig(meldung, fehler=True))

    def fertig(self, meldung: str, fehler: bool = False) -> None:
        self.status.set(meldung)
        self.knopf.state(["!disabled"])
        if fehler:
            messagebox.showerror("Fehler", meldung)


if __name__ == "__main__":
    if ABSTURZ_LOG:
        faulthandler.enable(ABSTURZ_LOG)   # Abstuerze (z. B. in onnxruntime) ins Log
    log("Programm gestartet")
    App().mainloop()
