#!/usr/bin/env python3
"""Text vertonen (offline): kleines Fenster, Textdatei waehlen -> MP3.

Gedacht zum Einpacken mit PyInstaller (siehe .github/workflows/build-vertonen.yml).
Die Stimme (Thorsten) und ffmpeg (imageio-ffmpeg) sind dann in der Programmdatei
enthalten, es muss nichts installiert werden.

Zum Testen mit Python:
  pip install piper-tts imageio-ffmpeg
  python vertonen_app.py     (Stimme in ~/piper-voices/de_DE-thorsten-high.onnx)
"""

import subprocess
import sys
import tempfile
import threading
import wave
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

STIMME_NAME = "de_DE-thorsten-high.onnx"


def finde_stimme() -> Path:
    basis = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    for kandidat in (basis / "voice" / STIMME_NAME,
                     Path.home() / "piper-voices" / STIMME_NAME):
        if kandidat.exists():
            return kandidat
    raise FileNotFoundError(f"Stimmdatei {STIMME_NAME} nicht gefunden.")


def vertone(quelle: Path, ziel: Path, tempo: float) -> None:
    from piper import PiperVoice          # erst hier, damit das Fenster schnell erscheint
    import imageio_ffmpeg

    stimme = finde_stimme()
    text = quelle.read_text(encoding="utf-8")
    voice = PiperVoice.load(stimme)

    with tempfile.TemporaryDirectory() as tmp:
        wav_pfad = Path(tmp) / "ausgabe.wav"
        with wave.open(str(wav_pfad), "wb") as wav:
            voice.synthesize_wav(text, wav)

        befehl = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                  "-i", str(wav_pfad)]
        if tempo != 1.0:
            befehl += ["-filter:a", f"atempo={tempo}"]
        befehl += ["-codec:a", "libmp3lame", "-qscale:a", "4", str(ziel)]
        ergebnis = subprocess.run(befehl, capture_output=True, text=True)
        if ergebnis.returncode != 0:
            raise RuntimeError(f"ffmpeg ist fehlgeschlagen:\n{ergebnis.stderr}")


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
            vertone(quelle, ziel, tempo)
            self.after(0, lambda: self.fertig(f"Fertig: {ziel}"))
        except Exception as fehler:
            self.after(0, lambda: self.fertig(f"Fehler: {fehler}", fehler=True))

    def fertig(self, meldung: str, fehler: bool = False) -> None:
        self.status.set(meldung)
        self.knopf.state(["!disabled"])
        if fehler:
            messagebox.showerror("Fehler", meldung)


if __name__ == "__main__":
    App().mainloop()
