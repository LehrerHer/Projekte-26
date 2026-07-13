# Home Assistant Setup – Lipper Kamp Energie

Home Assistant per Docker auf dem bestehenden Raspberry Pi OS (Testbetrieb), um die
Energiedaten von Hauptzähler, PV-Hauptanlage und beiden Balkonkraftwerken in einem
Dashboard zu bündeln.

## Ausgangslage

- **Hardware:** Raspberry Pi 5, läuft mit Raspberry Pi OS – bleibt vorerst so, Home
  Assistant wird als Docker-Container ergänzt (kein Überschreiben der SD-Karte).
- **Ansatz:** Erst auf dem bestehenden Pi testen. Bei Gefallen später optional Umzug
  auf einen zweiten, dedizierten Pi mit Home Assistant OS (HAOS) – siehe
  [Migrationspfad](#migrationspfad-später-auf-dediziertes-haos-umziehen).
- **Datenquellen:**
  1. Shelly EM3 (Hauptzähler, Netzbezug/-einspeisung) – bereits im Sicherungskasten
     verbaut
  2. Huawei SUN2000-10KTL-M1 (PV-Hauptanlage, 9,6 kWp) – aktuell nur über
     FusionSolar-/EnergyOrb-App sichtbar
  3. 2× Balkonkraftwerk mit FoxESS M1-800-E Wechselrichter (Solakon) – aktuell nur
     über Solakon-App sichtbar, keine offizielle Schnittstelle → Lösung über
     2× Shelly Plug S/Plus an der Steckdose

## Vorab zu besorgen

- [ ] 2× Shelly Plug S oder Shelly Plug+ (für die Balkonkraftwerke)
- [ ] Zugang zum Heim-WLAN/LAN-Router (Passwort griffbereit)
- [ ] SSH-Zugang zum Pi (falls noch nicht aktiv: `sudo raspi-config` → Interface
      Options → SSH aktivieren)
- [ ] Für Huawei-Integration später: Installer-Zugang zur FusionSolar-/EnergyOrb-App
      (ggf. bei Liekam Haustechnik anfragen – T 0541 86841, Projekt-Nr. 22-4262).
      Hinweis: Huawei überträgt das FusionSolar-System zum 15.07.2026 an den neuen
      Betreiber "Energy Orb" (Übergangsfrist bis 15.11.2026) – das betrifft nur die
      Cloud-Verwaltung, nicht die lokale Modbus-TCP-Verbindung, die hier genutzt wird.

## Phase 1: Docker und Home Assistant Container installieren

Alle Befehle **per SSH auf dem Pi selbst** ausführen, nicht lokal.

```bash
git clone <repo-url>
cd Projekte-26/raspberry-pi-home-automation
./install.sh
```

`install.sh` übernimmt:

- Docker-Installation (falls noch nicht vorhanden) inkl. Hinzufügen des Nutzers zur
  `docker`-Gruppe
- Anlegen von `config/` für die Home-Assistant-Konfiguration
- Start des Containers über `docker-compose.yml` (verwendet `--network=host`, damit
  Home Assistant Geräte im lokalen Netzwerk wie Shelly und den Huawei-Dongle
  automatisch findet)

Danach 1–2 Minuten warten, dann im Browser: `http://<IP-des-Pi>:8123`
(IP z. B. mit `hostname -I` am Pi oder über die Router-Oberfläche ermitteln).

**Ersteinrichtung:** Onboarding-Assistent durchlaufen (Benutzerkonto anlegen, Standort
Osnabrück-Hellern und Zeitzone einstellen). Home Assistant erkennt evtl. automatisch
Geräte im Netzwerk (z. B. den Shelly EM3) – das ist normal, noch nichts anklicken,
erstmal Onboarding abschließen.

## Phase 2: HACS installieren (für die Huawei-Integration nötig)

Bei der Container-Installation gibt es keinen Add-on-Store, daher wird HACS über ein
Installationsskript eingerichtet:

```bash
docker exec -it homeassistant bash -c "$(curl -fsSL https://get.hacs.xyz)"
docker compose restart
```

Danach in der Oberfläche: Einstellungen → Geräte & Dienste → Integration hinzufügen →
"HACS" suchen und einrichten. Login-Ablauf folgen (GitHub-Konto wird benötigt – falls
keins vorhanden, kostenlos unter github.com anlegen).

## Phase 3: Shelly EM3 einbinden (Netzbezug/-einspeisung gesamt)

1. Einstellungen → Geräte & Dienste → Integration hinzufügen → "Shelly" suchen
2. Home Assistant sollte den Shelly EM3 automatisch im Netzwerk finden (gleiches
   WLAN/LAN vorausgesetzt)
3. Verbindung bestätigen – fertig, keine Zugangsdaten nötig (lokale Integration)

**Prüfen:** Unter Einstellungen → Geräte & Dienste → Shelly EM3 sollten Sensoren wie
"Leistung Phase A/B/C", "Gesamt", "Energie" erscheinen. Werte mit der Shelly-App
vergleichen – müssen übereinstimmen.

## Phase 4: Huawei SUN2000 einbinden (Haupt-PV-Anlage)

1. **Modbus TCP am Wechselrichter freischalten:** In der FusionSolar-Web-Oberfläche
   (fusionsolar.huawei.com im Browser, nicht die App) mit **Installer-Account**
   einloggen (nicht nur Owner-Zugang – falls nicht vorhanden: bei Liekam Haustechnik
   nachfragen, T 0541 86841). Linke Seitenleiste → Dongle/Smart Dongle → Konfiguration
   → ganz unten "Modbus TCP" aktivieren. Optional: IP-Adressbereich auf die IP des Pi
   einschränken.
2. **Integration installieren:** In HACS → Integrationen → Suche nach "Huawei Solar"
   → installieren → Home Assistant neu starten.
3. **Integration einrichten:** Einstellungen → Geräte & Dienste → Integration
   hinzufügen → "Huawei Solar" → Verbindungstyp "Network" → IP-Adresse des Dongles
   eingeben (über Router-Oberfläche, Gerätename "SUN2000..." suchen) → Port zuerst
   `502` probieren, sonst `6607` → Slave-ID meist `1` (sonst im FusionSolar-Webportal
   unter Wechselrichter → Konfiguration → Geräteinformationen → Modbus-ID-Adresse
   nachschauen).

**Prüfen:** Sensoren für PV-Erzeugung, Einspeisung, Eigenverbrauch etc. erscheinen. Die
FusionSolar-App funktioniert parallel weiter.

## Phase 5: Balkonkraftwerke einbinden (über Shelly Plug)

Da der FoxESS M1-800-E Wechselrichter keine eigene Schnittstelle bietet, wird die
AC-Ausgangsleistung direkt an der Steckdose gemessen.

1. Je einen Shelly Plug S/Plus zwischen Wechselrichter-Netzstecker und Steckdose
   stecken (2 Stück) und über die Shelly-App einmalig ins WLAN einbinden.
2. Einstellungen → Geräte & Dienste → Integration hinzufügen → "Shelly" – beide neuen
   Plugs sollten automatisch gefunden werden, jeweils bestätigen.

**Prüfen:** Sensoren "Leistung" und "Energie" je Plug erscheinen und stimmen mit der
Solakon-App überein.

## Phase 6: Energie-Dashboard einrichten (Gesamtbilanz)

1. Einstellungen → Dashboards → Energie
2. Unter "Stromnetz": Shelly-EM3-Sensor für Netzbezug UND Netzeinspeisung eintragen
3. Unter "Solarproduktion": Huawei-PV-Sensor eintragen, dann erneut
   "Solarproduktion hinzufügen" und die beiden Shelly-Plug-Sensoren
   (Balkonkraftwerke) ebenfalls eintragen
4. Speichern

Ab jetzt zeigt das Energie-Dashboard automatisch Gesamt-PV-Erzeugung (Hauptanlage +
beide Balkonkraftwerke), Netzbezug/-einspeisung, Eigenverbrauchsquote fürs gesamte
Haus sowie den Verlauf nach Tag/Woche/Monat/Jahr.

## Offene Punkte / bekannte Stolpersteine

- **Installer-Zugang FusionSolar/EnergyOrb:** Falls nur Owner-Rechte vorhanden sind,
  ist dieser Schritt der wahrscheinlichste Blocker – vorher klären.
- **Huawei-Systemumstellung:** Cloud-Verwaltung wechselt zum 15.07.2026 zu
  "Energy Orb" (Übergangsfrist bis 15.11.2026). Betrifft nur die Cloud/App, nicht die
  lokale Modbus-TCP-Verbindung. Falls die Modbus-TCP-Freischaltung (Phase 4.1) während
  der Umstellung Probleme macht: etwas abwarten oder direkt bei Liekam nachfragen.
- **Modbus-Konflikt:** FusionSolar-App und Home Assistant können nicht gleichzeitig
  per Modbus zugreifen, wenn im Portal "Device Commissioning" genutzt wird – dafür die
  HA-Integration kurz pausieren, danach wieder aktivieren.
- **Shelly-Plug-Belastung:** Plug S bis 2500 W, Plug+ bis 3680 W – beide reichen für
  die 800-W-Wechselrichter locker aus.
- **Neustart nach Pi-Reboot:** `restart: unless-stopped` in der `docker-compose.yml`
  startet den Container automatisch neu, wenn der Pi neu bootet – keine zusätzliche
  Konfiguration nötig.

## Migrationspfad: Später auf dediziertes HAOS umziehen

Falls sich das Monitoring bewährt und ein zweiter, dedizierter Pi angeschafft wird:

1. Auf dem neuen Pi Home Assistant OS (HAOS) direkt per Raspberry Pi Imager
   installieren (Betriebssystem-Auswahl: "Sonstiges spezifisches Betriebssystem" →
   "Home Assistant")
2. Unter Einstellungen → System → Backups im bestehenden Container-Setup ein Backup
   erstellen
3. Backup beim Onboarding des neuen HAOS-Pi einspielen – alle Integrationen,
   Automatisierungen und der Verlauf werden übernommen
4. Alten Container stoppen: `docker compose down`

## Nächster möglicher Schritt (später, nicht Teil dieser Anleitung)

Sobald die Datenbündelung steht: PV-gesteuerte Wallbox-Ladung (höchste Priorität aus
der Optimierungsliste, ca. 280 €/Jahr Zusatzertrag) – dafür wird `evcc` auf demselben
Pi oder einem Zweitsystem benötigt, da Home Assistant selbst keine Ladesteuerung für
die KEBA-Wallbox mitbringt.
