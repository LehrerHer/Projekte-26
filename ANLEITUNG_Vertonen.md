# Text vertonen – Anleitung für Kolleginnen und Kollegen

Mit dem Programm **Vertonen** wird eine Textdatei (`.txt`) in eine MP3 umgewandelt.
Es arbeitet **offline** (der Text verlässt den Rechner nicht) und benötigt keine Installation.

## Erster Start

### Mac (Apple Silicon, M1 oder neuer)

1. `Vertonen-Mac.zip` entpacken, die App `Vertonen` in den Ordner **Programme** ziehen.
2. Doppelklick. Es erscheint eine Warnung („Apple konnte nicht überprüfen …“). Auf **Fertig** klicken.
3. **Systemeinstellungen → Datenschutz & Sicherheit**, ganz nach unten scrollen, bei „Vertonen wurde blockiert“ auf **Trotzdem öffnen** klicken und mit Passwort oder Touch ID bestätigen.
4. Danach lässt sich die App normal öffnen. Dieser Schritt ist nur einmal nötig.

Falls der Button fehlt oder die App als „beschädigt“ gemeldet wird: Terminal öffnen und
`xattr -cr /Applications/Vertonen.app` ausführen.

### Windows

1. `Vertonen.exe` an einen beliebigen Ort kopieren (z. B. auf den Desktop) und doppelklicken.
2. Erscheint „Der Computer wurde durch Windows geschützt“: **Weitere Informationen → Trotzdem ausführen**.
3. Der allererste Start dauert etwas länger, weil sich das Programm entpackt.

## Benutzen

1. **Auswählen …** klicken und die Textdatei (`.txt`) wählen.
2. Tempo einstellen (1.0 = normal, 0.9 = etwas langsamer, z. B. für Lernende).
3. **MP3 erstellen** klicken und warten. Im Fenster steht, wie viele Sätze schon gesprochen sind.
4. Die MP3 liegt danach **im selben Ordner wie die Textdatei**, mit demselben Namen (`text.txt` → `text.mp3`).

Lange Texte brauchen einige Minuten. Das Fenster bitte nicht schließen, bis „Fertig: …“ erscheint.

## Hinweise

- Texte aus Word oder Pages vorher als **reinen Text (.txt)** speichern.
- Zeichen mit Sonderfunktion (Tabellen, Aufzählungen, Klammern mit Fußnoten) werden mitgesprochen. Den Text vorher am besten bereinigen.
- Beim ersten Start legt das Programm einen Ordner `.vertonen` im Benutzerordner an (ca. 20 MB Sprachdaten).

## Bei Problemen

Im Benutzerordner liegt die Datei **`Vertonen-Log.txt`**. Sie zeigt Schritt für Schritt, was das Programm getan hat, und enthält Fehlermeldungen. Bitte die letzten Zeilen weitergeben.
