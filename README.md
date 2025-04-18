# Datové centrum pro sběr a vizualizaci dat ze senzorů a jejich vizualizace

## Zásady pro vypracování
Cílem práce je implementace datového centra, které bude zajišťovat sběr dat ze senzorů pomocí protokolu TCP nebo UDP, jejich ukládání do databázové struktury a jejich vizualizaci v prostředí Grafana. Datové centrum bude implementováno v Pythonu pomocí frameworku Django. Součástí práce bude také realizace teplotního senzoru využívajícího zařízení ESP32 s odesíláním dat do datového centra.
1. Navrhněte architekturu, protokol přenášení dat a implementujte datové centrum ve frameworku Django.
2. Implementujte grafickou vizualizaci dat pomocí nástroje Grafana.
3. Realizujte teplotní senzor využívající zařízení ESP32 s odesíláním dat do datového centra.
4. Ověřte funkčnost senzoru a datového centra dlouhodobým měřením teploty.

## Instalace prerekvizit
### Docker
https://docs.docker.com/engine/install/debian/#install-using-the-repository

### NTP Server (Volitelné)
Instalace:
```bash
apt install -y ntp
```
Konfigurace pro ntp server se nachází v souboru `/etc/ntpsec/ntp.conf`.

## Spuštění
1. Nastavení parametrů v souboru `.env`.
2. zadání příkazu `docker compose up --build` pro sestavení všech Docker image a spuštění kontejnerů.
