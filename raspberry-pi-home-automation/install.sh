#!/usr/bin/env bash
# Richtet Home Assistant per Docker Compose auf einem bestehenden Raspberry Pi OS ein.
# Auf dem Pi selbst ausfuehren (per SSH), NICHT hier in der Cloud-Sandbox.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker &> /dev/null; then
  echo "Docker nicht gefunden, installiere..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  rm get-docker.sh
  sudo usermod -aG docker "$USER"
  echo "Docker installiert. Bitte einmal aus- und wieder einloggen (oder Pi neu starten),"
  echo "damit die Gruppenmitgliedschaft aktiv wird, dann dieses Skript erneut ausfuehren."
  exit 0
fi

if ! command -v docker compose &> /dev/null; then
  echo "docker compose Plugin fehlt. Installation z.B. mit: sudo apt install docker-compose-plugin"
  exit 1
fi

mkdir -p config

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env aus .env.example angelegt. Bei Bedarf Zeitzone anpassen."
fi

docker compose up -d

echo ""
echo "Home Assistant startet. Nach 1-2 Minuten erreichbar unter:"
echo "  http://$(hostname -I | awk '{print $1}'):8123"
echo ""
echo "Fuer HACS (noetig fuer die Huawei-Integration) danach ausfuehren:"
echo "  docker exec -it homeassistant bash -c \"\$(curl -fsSL https://get.hacs.xyz)\""
echo "  docker compose restart"
