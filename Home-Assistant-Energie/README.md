# Home Assistant Setup – Lipper Kamp Energie

Anleitung: Home Assistant per Docker auf dem bestehenden Raspberry Pi OS installieren (Testbetrieb) und die Energiedaten des Hauses bündeln.

## Ausgangslage

- **Hardware:** Raspberry Pi 5, läuft aktuell mit Raspberry Pi OS – bleibt vorerst so, Home Assistant wird als Docker-Container ergänzt (kein Überschreiben der SD-Karte).
- **Ansatz:** Erst zum Testen auf dem bestehenden Pi ausprobieren. Bei Gefallen später optional Umzug auf einen zweiten, dedizierten Pi mit Home Assistant OS (HAOS) – siehe [Migrationspfad](#migrationspfad-später-auf-dediziertes-haos-umziehen).
- **Ziel:** folgende Datenquellen bündeln:
  1. **Shelly EM3** (Hauptzähler, Netzbezug/-einspeisung) – bereits im Sicherungskasten verbaut
  2. **Huawei SUN2000-10KTL-M1** (PV-Hauptanlage, 9,6 kWp) – aktuell nur über FusionSolar-/EnergyOrb-App sichtbar
  3. **2× Balkonkraftwerk** mit FoxESS M1-800-E Wechselrichter (Solakon) – aktuell nur über Solakon-App sichtbar, keine offizielle Schnittstelle → Lösung über 2× Shelly Plug S/Plus an der Steckdose

## Vorab zu besorgen

- [ ] 2× Shelly Plug S oder Shelly Plug+ (für die Balkonkraftwerke)
- [ ] Zugang zum Heim-WLAN/LAN-Router (Passwort griffbereit)
- [ ] SSH-Zugang zum Pi (falls noch nicht aktiv: `sudo raspi-config` → Interface Options → SSH aktivieren)
- [ ] Für Huawei-Integration später: Installer-Zugang zur FusionSolar-/EnergyOrb-App (ggf. bei Liekam Haustechnik anfragen – T 0541 86841, Projekt-Nr. 22-4262). Hinweis: Huawei überträgt das FusionSolar-System zum 15.07.2026 an den neuen Betreiber "Energy Orb" – das betrifft nur die Cloud-Verwaltung, nicht die lokale Modbus-TCP-Verbindung, die hier genutzt wird.

## Phase 1: Docker und Home Assistant Container installieren

### Schritt 1.1 – Docker installieren (falls noch nicht vorhanden)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

Danach einmal aus- und wieder einloggen (oder Pi neu starten), damit die Gruppenmitgliedschaft aktiv wird.

### Schritt 1.2 – Verzeichnis für Home-Assistant-Konfiguration anlegen

```bash
mkdir -p ~/homeassistant/config
```

### Schritt 1.3 – Home Assistant Container starten

```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Europe/Berlin \
  -v ~/homeassistant/config:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

`--network=host` ist wichtig, damit Home Assistant Geräte im lokalen Netzwerk (Shelly, Huawei-Dongle) automatisch finden kann.

### Schritt 1.4 – Ersten Start prüfen

- Ein bis zwei Minuten warten, dann im Browser: `http://<IP-des-Pi>:8123`
- Die IP-Adresse des Pi findest du z. B. mit `hostname -I` direkt am Pi oder über die Router-Oberfläche

### Schritt 1.5 – Ersteinrichtung

- Onboarding-Assistent durchlaufen: Benutzerkonto (Name, Passwort) anlegen
- Standort (Osnabrück-Hellern) und Zeitzone einstellen
- Home Assistant erkennt evtl. automatisch Geräte im Netzwerk (z. B. den Shelly EM3) – das ist normal, noch nichts anklicken, erstmal Onboarding abschließen

## Phase 2: HACS installieren (für die Huawei-Integration nötig)

Bei der Container-Installation gibt es keinen Add-on-Store, daher wird HACS über ein Installationsskript eingerichtet.

### Schritt 2.1 – HACS-Installationsskript ausführen

```bash
docker exec -it homeassistant bash -c "$(curl -fsSL https://get.hacs.xyz)"
```

### Schritt 2.2 – Container neu starten

```bash
docker restart homeassistant
```

### Schritt 2.3 – HACS in der Oberfläche aktivieren

- Einstellungen → Geräte & Dienste → Integration hinzufügen → "HACS" suchen und einrichten
- Folgt dem Login-Ablauf (GitHub-Konto wird benötigt – falls keins vorhanden, kostenlos unter github.com anlegen)

## Phase 3: Shelly EM3 einbinden (Netzbezug/-einspeisung gesamt)

### Schritt 3.1

- Einstellungen → Geräte & Dienste → Integration hinzufügen → "Shelly" suchen
- Home Assistant sollte den Shelly EM3 automatisch im Netzwerk finden (gleiches WLAN/LAN vorausgesetzt)
- Verbindung bestätigen – fertig, keine Zugangsdaten nötig (lokale Integration)

### Schritt 3.2 – Prüfen

- Unter Einstellungen → Geräte & Dienste → Shelly EM3 sollten jetzt Sensoren wie "Leistung Phase A/B/C", "Gesamt", "Energie" erscheinen
- Diese Werte solltest du mit der Shelly-App vergleichen (z. B. -5,31 kW Gesamt) – müssen übereinstimmen

## Phase 4: Huawei SUN2000 einbinden (Haupt-PV-Anlage)

### Schritt 4.1 – Modbus TCP am Wechselrichter freischalten

- In der FusionSolar-Web-Oberfläche (nicht die App, sondern fusionsolar.huawei.com im Browser) einloggen
- Wichtig: Dafür wird ein Installer-Account benötigt, nicht nur ein normaler Owner-Zugang. Falls nicht vorhanden: bei Liekam Haustechnik nachfragen (T 0541 86841)
- Linke Seitenleiste → Dongle/Smart Dongle auswählen → Konfiguration → ganz unten "Modbus TCP" aktivieren
- Optional: IP-Adressbereich einschränken (nur die IP des Raspberry Pi zulassen, aus Sicherheitsgründen)

### Schritt 4.2 – Integration installieren

- In HACS: Integrationen → Suche nach "Huawei Solar" → installieren
- Home Assistant neu starten

### Schritt 4.3 – Integration einrichten

- Einstellungen → Geräte & Dienste → Integration hinzufügen → "Huawei Solar" suchen
- Verbindungstyp: "Network" wählen
- IP-Adresse des Dongles eingeben (über die Router-Oberfläche herausfinden, z. B. Gerätename "SUN2000..." suchen)
- Port: zuerst 502 probieren, falls Verbindung fehlschlägt: 6607 probieren
- Slave-ID: meist "1" – falls nicht: kann im FusionSolar-Webportal unter Wechselrichter → Konfiguration → Geräteinformationen → Modbus-ID-Adresse nachgeschaut werden

### Schritt 4.4 – Prüfen

- Nach erfolgreicher Einrichtung erscheinen Sensoren für PV-Erzeugung, Einspeisung, Eigenverbrauch etc.
- Die FusionSolar-App funktioniert parallel weiter und zeigt weiterhin Daten an

## Phase 5: Balkonkraftwerke einbinden (über Shelly Plug)

Da der FoxESS M1-800-E Wechselrichter keine eigene Schnittstelle für Home Assistant bietet, wird die AC-Ausgangsleistung direkt an der Steckdose gemessen.

### Schritt 5.1 – Hardware

- Je einen Shelly Plug S/Plus zwischen Wechselrichter-Netzstecker und Steckdose stecken (2 Stück, für jedes Balkonkraftwerk eins)
- Über die Shelly-App einmalig ins WLAN einbinden (wie beim EM3 vorher geschehen)

### Schritt 5.2 – In Home Assistant einbinden

- Einstellungen → Geräte & Dienste → Integration hinzufügen → "Shelly" suchen
- Beide neuen Plugs sollten automatisch gefunden werden, jeweils bestätigen

### Schritt 5.3 – Prüfen

- Sensoren "Leistung" und "Energie" je Plug sollten erscheinen und mit der aktuellen Solakon-App-Anzeige übereinstimmen

## Phase 6: Energie-Dashboard einrichten (Gesamtbilanz)

### Schritt 6.1

- Einstellungen → Dashboards → Energie
- Unter "Stromnetz": den Shelly-EM3-Sensor für Netzbezug UND den für Netzeinspeisung eintragen
- Unter "Solarproduktion": den Huawei-PV-Sensor eintragen, danach "Solarproduktion hinzufügen" erneut anklicken und die beiden Shelly-Plug-Sensoren (Balkonkraftwerke) ebenfalls eintragen
- Speichern

### Schritt 6.2 – Ergebnis

Ab jetzt zeigt das Energie-Dashboard automatisch:

- Gesamt-PV-Erzeugung (Hauptanlage + beide Balkonkraftwerke zusammen)
- Netzbezug und Netzeinspeisung
- Eigenverbrauchsquote für das gesamte Haus
- Verlauf nach Tag/Woche/Monat/Jahr – wählbar

## Offene Punkte / Bekannte Stolpersteine

- **Installer-Zugang FusionSolar/EnergyOrb:** Falls nur Owner-Rechte vorhanden sind, ist dieser Schritt der wahrscheinlichste Blocker. Vorher klären.
- **Huawei-Systemumstellung (aktuell):** Huawei überträgt das FusionSolar-Cloud-System zum 15.07.2026 an den neuen Betreiber "Energy Orb" (Übergangsfrist bis 15.11.2026). Das betrifft nur die Cloud-Verwaltung/App – die `huawei_solar`-Integration verbindet sich lokal per Modbus TCP direkt mit dem Dongle im LAN und ist davon unabhängig. Die Modbus-TCP-Freischaltung (Schritt 4.1) läuft aktuell noch über die bestehende Web-Oberfläche; falls diese während der Umstellung Probleme macht, ggf. etwas abwarten oder direkt bei Liekam nachfragen.
- **Modbus-Konflikt:** FusionSolar-App und Home Assistant können nicht gleichzeitig per Modbus auf den Wechselrichter zugreifen, wenn im Portal die "Device Commissioning"-Funktion genutzt wird – dafür die HA-Integration kurz pausieren, danach wieder aktivieren.
- **Shelly Plug Belastung:** Shelly Plug S ist für bis zu 2500 W ausgelegt, Shelly Plug+ für bis zu 3680 W – beide reichen für die 800-W-Wechselrichter locker aus.
- **Container-Neustart nach Pi-Neustart:** Durch `--restart=unless-stopped` startet der Container automatisch neu, wenn der Pi neu bootet – keine zusätzliche Konfiguration nötig.

## Migrationspfad: Später auf dediziertes HAOS umziehen

Falls sich das Monitoring bewährt und ein zweiter, dedizierter Pi angeschafft wird:

1. Auf dem neuen Pi Home Assistant OS (HAOS) direkt per Raspberry Pi Imager installieren (Betriebssystem-Auswahl: "Sonstiges spezifisches Betriebssystem" → "Home Assistant")
2. Unter Einstellungen → System → Backups im bestehenden Container-Setup ein Backup erstellen
3. Dieses Backup beim Onboarding des neuen HAOS-Pi einspielen – alle Integrationen, Automatisierungen und der Verlauf werden übernommen
4. Alten Container auf dem ursprünglichen Pi stoppen: `docker stop homeassistant`

## Nächster möglicher Schritt (später, nicht Teil dieser Anleitung)

Sobald die Datenbündelung steht, ist der logische nächste Schritt die PV-gesteuerte Wallbox-Ladung (höchste Priorität aus der Optimierungsliste, ca. 280 €/Jahr Zusatzertrag) – dafür wird evcc auf demselben Pi oder ein Zweitsystem benötigt, da Home Assistant selbst keine Ladesteuerung für die KEBA-Wallbox mitbringt.
