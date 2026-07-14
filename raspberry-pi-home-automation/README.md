# Home Assistant Setup – Lipper Kamp Energie

Home Assistant per Docker auf dem bestehenden Raspberry Pi OS (Testbetrieb), um die
Energiedaten von Hauptzähler, PV-Hauptanlage und beiden Balkonkraftwerken in einem
Dashboard zu bündeln.

## Status

| Phase | Status |
|---|---|
| 1–3: Docker, Home Assistant, Shelly EM3 | ✅ erledigt |
| 5: Balkonkraftwerke einbinden | ✅ erledigt (1 statt 2 Shelly Plugs, siehe Hinweis unten) |
| Vorzeichen-Harmonisierung (Netzleistung) | ✅ per Template-Sensor gelöst, siehe [unten](#vorzeichen-harmonisieren-netzleistung) |
| 6: Energie-Dashboard | ✅ erledigt (Einschränkung: Verbrauch wird unterschätzt, solange Phase 4 offen ist) |
| 4: Huawei SUN2000 einbinden | ⏸ pausiert – Streit mit Liekam Haustechnik um eine Rechnung, kein Kontakt gewünscht. Bei Bedarf jederzeit nachholbar. |
| Wallbox / evcc | 🔜 eigenes, späteres Projekt (siehe [unten](#nächster-möglicher-schritt-später-nicht-teil-dieser-anleitung)) |

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

- [x] Shelly Plug S für die Balkonkraftwerke – da beide BKW an derselben
      Mehrfachsteckdose hängen, reicht **ein** Plug an der Mehrfachsteckdose (misst die
      Summe beider Wechselrichter). Elektrisch unproblematisch: 2× 800 W liegen weit
      unter der 2500-W-Grenze des Plug S. Nachteil: keine Aufschlüsselung nach
      einzelnem Balkonkraftwerk – bei Bedarf später mit einem zweiten Plug nachrüstbar.
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

Es gibt keinen automatischen Gesamt-Leistungssensor, nur die drei Phasen-Sensoren
(`..._phase_a_leistung`, `..._phase_b_leistung`, `..._phase_c_leistung`) – die Summe
bildet der Template-Sensor aus dem Abschnitt
[Vorzeichen harmonisieren](#vorzeichen-harmonisieren-netzleistung).

## Phase 4: Huawei SUN2000 einbinden (Haupt-PV-Anlage)

> **Aktuell pausiert.** Grund: laufender Streit mit Liekam Haustechnik um eine
> Rechnung, daher aktuell kein Kontakt gewünscht (Installer-Zugang wird aber
> voraussichtlich darüber benötigt). Diese Phase kann jederzeit nachgeholt werden,
> sobald das geklärt ist – bis dahin läuft das Dashboard ohne die Hauptanlage weiter
> (siehe Einschränkung in [Phase 6](#phase-6-energie-dashboard-einrichten-gesamtbilanz)).

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

**Umsetzung:** Beide Balkonkraftwerke hängen an derselben Mehrfachsteckdose, daher
wurde nur **ein** Shelly Plug S zwischen Wand-Steckdose und Mehrfachsteckdose
eingesetzt – er misst die Summe beider Wechselrichter (siehe Hinweis unter
[Vorab zu besorgen](#vorab-zu-besorgen)).

1. Shelly Plug S zwischen Wand-Steckdose und Mehrfachsteckdose (an der beide BKW
   hängen) stecken, über die Shelly-App einmalig ins WLAN einbinden.
2. Einstellungen → Geräte & Dienste → Integration hinzufügen → "Shelly" – wurde
   automatisch gefunden (Gerät: `shellyplusplugs-80646fd01aa0`, "Shelly Plug 1").

**Geprüft:** Sensor `sensor.shellyplusplugs_80646fd01aa0_leistung` zeigt die
kombinierte Leistung beider Balkonkraftwerke, bereits mit dem gewünschten Vorzeichen
(positiv bei Produktion) – keine Anpassung nötig.

## Vorzeichen harmonisieren (Netzleistung)

Der Shelly EM3 zeigt Leistung mit **umgekehrtem** Vorzeichen im Vergleich zum Shelly
Plug: negativ bei Produktion/Einspeisung, positiv bei Verbrauch/Bezug. Gewünscht war
einheitlich: **+ = Produktion/Einspeisung, - = Verbrauch/Bezug** (passend zum Shelly
Plug).

**Versuch über die Shelly-Firmware (gescheitert):** Bei neueren Shelly-3EM-Generationen
gibt es dafür einen `reverse`-Parameter pro Phase über die Geräte-API
(`/settings/emeter/{0,1,2}?reverse=true`). Bei diesem Gerät (Modell `SHEM-3`, Firmware
`v1.14.0`) existiert dieser Parameter **nicht** – `/settings` zeigt für jedes Emeter nur
`name`, `appliance_type`, `max_power`, `range_extender`, kein `reverse`-Feld. Die
CT-Zangen physisch umzudrehen wäre die einzige Hardware-Alternative, bedeutet aber
Arbeiten im Sicherungskasten – daher stattdessen Softwarelösung in Home Assistant.

**Lösung: Template-Sensor**, der die drei EM3-Phasen aufsummiert und invertiert:

```yaml
template:
  - sensor:
      - name: "Netzleistung"
        unique_id: netzleistung
        unit_of_measurement: "W"
        device_class: power
        state_class: measurement
        state: >
          {{ (states('sensor.shellyem3_349454717c12_phase_a_leistung') | float(0)
            + states('sensor.shellyem3_349454717c12_phase_b_leistung') | float(0)
            + states('sensor.shellyem3_349454717c12_phase_c_leistung') | float(0)) * -1 }}
```

Ergebnis: `sensor.netzleistung` – positiv bei Netzeinspeisung/PV-Überschuss, negativ bei
Netzbezug. Nach Anlegen des Sensors Home Assistant neu starten (`docker compose
restart`).

## Phase 6: Energie-Dashboard einrichten (Gesamtbilanz)

1. Einstellungen → Dashboards → Energie
2. Unter "Stromnetz" → "Netzbezug hinzufügen": die drei EM3-Phasen-Energiesensoren
   (`sensor.shellyem3_349454717c12_phase_{a,b,c}_energie`)
3. Unter "Stromnetz" → "Netzeinspeisung hinzufügen": die drei EM3-Phasen-
   Einspeisungssensoren (`sensor.shellyem3_349454717c12_phase_{a,b,c}_energieeinspeisung`)
4. Unter "Solarproduktion" → "Solarproduktion hinzufügen":
   `sensor.shellyplusplugs_80646fd01aa0_energie` (Balkonkraftwerke)
5. Speichern

> **Einschränkung, solange Phase 4 (Huawei) offen ist:** Home Assistant berechnet
> "Verbrauch" intern als `Netzbezug + Solarproduktion - Netzeinspeisung`. Da die
> Huawei-Hauptanlage (9,6 kWp) nicht als Solarproduktion eingetragen ist, fehlt deren
> Eigenverbrauchsanteil in dieser Rechnung komplett – der angezeigte "Verbrauch" ist
> dadurch systematisch zu niedrig, und zwar genau um den nicht erfassten
> Huawei-Eigenverbrauch. Netzbezug/-einspeisung und Balkonkraftwerk-Produktion selbst
> sind davon nicht betroffen und stimmen. Sobald Phase 4 nachgeholt wird, korrigiert
> sich das automatisch für alle Daten ab dem Einbindungszeitpunkt – rückwirkend lässt
> sich die Lücke nicht schließen (keine historischen Modbus-Daten vorhanden).

## Offene Punkte / bekannte Stolpersteine

- **Installer-Zugang FusionSolar/EnergyOrb:** Falls nur Owner-Rechte vorhanden sind,
  ist dieser Schritt der wahrscheinlichste Blocker – vorher klären. Aktuell ohnehin
  pausiert, siehe [Status](#status).
- **Verbrauch im Energie-Dashboard zu niedrig**, solange Phase 4 offen ist – siehe
  Hinweis in [Phase 6](#phase-6-energie-dashboard-einrichten-gesamtbilanz).
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
