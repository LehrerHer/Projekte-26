#!/usr/bin/env python3
"""
Punktesystem-Generator
Erzeugt befüllte ODS-Dateien für jeden Schüler aus einer Namensliste und ODS-Vorlage.

Platzhalter in der ODS-Vorlage:
  {{Name}}     – vollständiger Name (wie in der Liste)
  {{Klasse}}   – Klasse (aus dem Eingabefeld)
  {{Vorname}}  – Vorname
  {{Nachname}} – Nachname

Namensformat in der Textdatei:
  "Nachname, Vorname"  oder  "Vorname Nachname"
  Zeilen, die mit # beginnen, werden ignoriert.
"""

import os
import platform
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

try:
    from odf.opendocument import load as odf_load
    HAS_ODF = True
except ImportError:
    HAS_ODF = False


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def parse_name_list(filepath: str) -> list:
    """Liest die Namensliste aus einer .txt-Datei (eine Name pro Zeile)."""
    names = []
    with open(filepath, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                names.append(line)
    return names


def split_name(full_name: str):
    """Gibt (Vorname, Nachname) zurück.
    Erkennt 'Nachname, Vorname' und 'Vorname Nachname'."""
    if "," in full_name:
        nachname, _, vorname = full_name.partition(",")
        return vorname.strip(), nachname.strip()
    parts = full_name.split(None, 1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def replace_in_node(node, replacements: dict):
    """Ersetzt Platzhalter rekursiv in allen Textknoten eines ODF-Elements."""
    if hasattr(node, "data") and isinstance(node.data, str):
        for old, new in replacements.items():
            node.data = node.data.replace(old, new)
    if hasattr(node, "childNodes"):
        for child in node.childNodes:
            replace_in_node(child, replacements)


def create_student_ods(template_path: str, output_path: str, name: str, klasse: str):
    """Erzeugt eine befüllte ODS-Datei für einen Schüler."""
    vorname, nachname = split_name(name)
    doc = odf_load(template_path)
    replace_in_node(doc.body, {
        "{{Name}}":     name,
        "{{Klasse}}":   klasse,
        "{{Vorname}}":  vorname,
        "{{Nachname}}": nachname,
    })
    doc.save(output_path)


def safe_filename(s: str) -> str:
    """Bereinigt einen String für die Verwendung als Dateiname."""
    for ch in r'\/:*?"<>|':
        s = s.replace(ch, "_")
    return s.strip()


def open_in_filemanager(path: str):
    """Öffnet einen Ordner im nativen Dateimanager."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.run(["open", path], check=True)
    else:
        subprocess.run(["xdg-open", path], check=True)


# ---------------------------------------------------------------------------
# Drop-Zone Widget
# ---------------------------------------------------------------------------

class DropZone(tk.Frame):
    """Drag-&-Drop-Feld mit Klick-Fallback zum Öffnen eines Dateidialogs."""

    _BG_IDLE   = "#e8f0fe"
    _BG_HOVER  = "#d0e4ff"
    _BG_LOADED = "#c8e6c9"

    def __init__(self, parent, prompt: str, filetypes: list, on_file, **kw):
        super().__init__(parent, relief="ridge", bd=2,
                         bg=self._BG_IDLE, cursor="hand2", **kw)
        self._filetypes = filetypes
        self._on_file   = on_file
        self._path      = None

        self.lbl = tk.Label(
            self, text=prompt, bg=self._BG_IDLE, fg="#444",
            font=("Helvetica", 10), wraplength=230, justify="center",
        )
        self.lbl.pack(expand=True, fill="both", padx=10, pady=16)

        for w in (self, self.lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

        if HAS_DND:
            for w in (self, self.lbl):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)

    # -- event handlers --

    def _on_drop(self, event):
        path = event.data.strip()
        # tkinterdnd2 wraps paths with spaces in braces
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        self._load(path)

    def _on_click(self, _event):
        path = filedialog.askopenfilename(filetypes=self._filetypes)
        if path:
            self._load(path)

    def _on_enter(self, _event):
        if self._path is None:
            self._set_bg(self._BG_HOVER)

    def _on_leave(self, _event):
        if self._path is None:
            self._set_bg(self._BG_IDLE)

    # -- helpers --

    def _load(self, path: str):
        self._path = path
        self._set_bg(self._BG_LOADED)
        self._on_file(path)

    def _set_bg(self, color: str):
        self.configure(bg=color)
        self.lbl.configure(bg=color)

    def set_label(self, text: str):
        self.lbl.configure(text=text)

    @property
    def path(self):
        return self._path


# ---------------------------------------------------------------------------
# Hauptfenster
# ---------------------------------------------------------------------------

_BaseWindow = TkinterDnD.Tk if HAS_DND else tk.Tk


class App(_BaseWindow):
    """Hauptfenster des Punktesystem-Generators."""

    def __init__(self):
        super().__init__()
        self.title("Punktesystem-Generator")
        self.geometry("900x540")
        self.minsize(720, 460)
        self.configure(bg="#f5f5f5")

        self._names:    list = []
        self._tpl_path: str  = None
        self._out_dir:  str  = None

        self._build_ui()
        self._check_dependencies()

    # -- dependency check --

    def _check_dependencies(self):
        missing = []
        if not HAS_DND:
            missing.append("tkinterdnd2  →  pip install tkinterdnd2  (Drag & Drop deaktiviert)")
        if not HAS_ODF:
            missing.append("odfpy        →  pip install odfpy        (ODS-Erzeugung nicht möglich)")
        if missing:
            messagebox.showwarning(
                "Fehlende Bibliotheken",
                "Folgende Bibliotheken sind nicht installiert:\n\n" + "\n".join(missing),
            )

    # -- UI construction --

    def _build_ui(self):
        outer = tk.Frame(self, bg="#f5f5f5")
        outer.pack(fill="both", expand=True, padx=16, pady=14)

        left  = tk.LabelFrame(outer, text=" Eingaben ",       bg="#f5f5f5",
                               font=("Helvetica", 10, "bold"))
        right = tk.LabelFrame(outer, text=" Ausgabe / Log ",  bg="#f5f5f5",
                               font=("Helvetica", 10, "bold"))
        left.pack(side="left",  fill="both", expand=True, padx=(0, 8))
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        f = tk.Frame(parent, bg="#f5f5f5")
        f.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. Namensliste
        self._section_label(f, "1.  Namensliste  (.txt)")
        self.dz_names = DropZone(
            f,
            prompt="Datei hier ablegen\noder klicken zum Öffnen",
            filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")],
            on_file=self._load_names,
        )
        self.dz_names.pack(fill="x", pady=(0, 2))
        self.lbl_names_info = self._small_label(f)

        # 2. ODS-Vorlage
        self._section_label(f, "2.  ODS-Vorlage  (.ods)")
        self.dz_tpl = DropZone(
            f,
            prompt="Datei hier ablegen\noder klicken zum Öffnen",
            filetypes=[("ODS-Tabellen", "*.ods"), ("Alle Dateien", "*.*")],
            on_file=self._load_template,
        )
        self.dz_tpl.pack(fill="x", pady=(0, 2))
        self.lbl_tpl_info = self._small_label(f)

        # 3. Klasse
        self._section_label(f, "3.  Klasse")
        self.var_klasse = tk.StringVar()
        tk.Entry(f, textvariable=self.var_klasse, font=("Helvetica", 12)) \
            .pack(fill="x", pady=(0, 16))

        # 4. Erstellen-Button
        self.btn_create = tk.Button(
            f, text="Dateien erstellen",
            command=self._create_files,
            bg="#1a73e8", fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat", padx=14, pady=9,
            cursor="hand2",
            activebackground="#1557b0", activeforeground="white",
        )
        self.btn_create.pack(fill="x")

    def _build_right(self, parent):
        f = tk.Frame(parent, bg="#f5f5f5")
        f.pack(fill="both", expand=True, padx=12, pady=10)

        self.log = scrolledtext.ScrolledText(
            f, wrap=tk.WORD, font=("Courier", 9),
            state="disabled",
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", relief="flat",
        )
        self.log.pack(fill="both", expand=True)

        # Farbige Log-Tags
        self.log.tag_config("ok",      foreground="#4ec9b0")
        self.log.tag_config("err",     foreground="#f48771")
        self.log.tag_config("info",    foreground="#9cdcfe")
        self.log.tag_config("summary", foreground="#dcdcaa",
                             font=("Courier", 9, "bold"))

        self.btn_open = tk.Button(
            f, text="Ordner öffnen",
            command=self._open_folder,
            bg="#34a853", fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat", padx=12, pady=7,
            cursor="hand2",
            activebackground="#2d7a45", activeforeground="white",
            state="disabled",
        )
        self.btn_open.pack(fill="x", pady=(8, 0))

    # -- widget helpers --

    @staticmethod
    def _section_label(parent, text: str):
        tk.Label(parent, text=text, bg="#f5f5f5", anchor="w",
                 font=("Helvetica", 9, "bold")).pack(fill="x", pady=(8, 2))

    @staticmethod
    def _small_label(parent) -> tk.Label:
        lbl = tk.Label(parent, text="", bg="#f5f5f5", fg="#666",
                       anchor="w", font=("Helvetica", 8))
        lbl.pack(fill="x", pady=(0, 4))
        return lbl

    # -- logging --

    def _log(self, msg: str, tag: str = ""):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag if tag else ())
        self.log.see("end")
        self.log.configure(state="disabled")
        self.update_idletasks()

    # -- file loading --

    def _load_names(self, path: str):
        try:
            self._names = parse_name_list(path)
            fname = Path(path).name
            self.dz_names.set_label(f"✓  {fname}\n{len(self._names)} Namen erkannt")
            self.lbl_names_info.configure(text=f"{len(self._names)} Schüler geladen")
            self._log(f"Namensliste: {fname}  ({len(self._names)} Namen)", "info")
        except Exception as exc:
            messagebox.showerror("Fehler beim Lesen der Namensliste", str(exc))

    def _load_template(self, path: str):
        self._tpl_path = path
        fname = Path(path).name
        self.dz_tpl.set_label(f"✓  {fname}")
        self.lbl_tpl_info.configure(text=path)
        self._log(f"Vorlage: {fname}", "info")

    # -- main action --

    def _create_files(self):
        if not self._names:
            messagebox.showwarning("Eingabe fehlt", "Bitte zuerst eine Namensliste laden.")
            return
        if not self._tpl_path:
            messagebox.showwarning("Eingabe fehlt", "Bitte zuerst eine ODS-Vorlage laden.")
            return
        klasse = self.var_klasse.get().strip()
        if not klasse:
            messagebox.showwarning("Eingabe fehlt", "Bitte eine Klasse eingeben.")
            return
        if not HAS_ODF:
            messagebox.showerror(
                "odfpy fehlt",
                "odfpy ist nicht installiert.\n\nInstallation:  pip install odfpy",
            )
            return

        out_dir = Path(self._tpl_path).parent / f"Ausgabe_{safe_filename(klasse)}"
        out_dir.mkdir(exist_ok=True)
        self._out_dir = str(out_dir)

        self._log(f"\n{'─' * 46}", "")
        self._log(f"Klasse: {klasse}   –   {len(self._names)} Schüler", "info")
        self._log(f"Ausgabe: {out_dir}", "info")
        self._log("─" * 46, "")

        self.btn_create.configure(state="disabled", text="Bitte warten …")
        self.btn_open.configure(state="disabled")

        ok = err = 0
        for name in self._names:
            filename = f"{safe_filename(klasse)}_{safe_filename(name)}.ods"
            dest = str(out_dir / filename)
            try:
                create_student_ods(self._tpl_path, dest, name, klasse)
                self._log(f"  ✓  {filename}", "ok")
                ok += 1
            except Exception as exc:
                self._log(f"  ✗  {name}: {exc}", "err")
                err += 1

        self._log("─" * 46, "")
        summary = f"Fertig: {ok} Datei(en) erstellt"
        if err:
            summary += f",  {err} Fehler"
        self._log(summary, "summary")
        self._log(str(out_dir), "summary")

        self.btn_create.configure(state="normal", text="Dateien erstellen")
        self.btn_open.configure(state="normal")

    def _open_folder(self):
        if self._out_dir and os.path.isdir(self._out_dir):
            try:
                open_in_filemanager(self._out_dir)
            except Exception as exc:
                messagebox.showerror("Fehler", f"Ordner konnte nicht geöffnet werden:\n{exc}")
        else:
            messagebox.showinfo("Hinweis", "Kein Ausgabeordner vorhanden.")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = App()
    app.mainloop()
