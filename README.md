# Datové centrum pro sběr a vizualizaci dat ze senzorů

## Zásady pro vypracování
Cílem práce je implementace datového centra, které bude zajišťovat sběr dat ze senzorů pomocí protokolu TCP nebo UDP, jejich ukládání do databázové struktury a jejich vizualizaci v prostředí Grafana. Datové centrum bude implementováno v Pythonu pomocí frameworku Django. Součástí práce bude také realizace teplotního senzoru využívajícího zařízení ESP32 s odesíláním dat do datového centra.
1. Navrhněte architekturu, protokol přenášení dat a implementujte datové centrum ve frameworku Django.
2. Implementujte grafickou vizualizaci dat pomocí nástroje Grafana.
3. Realizujte teplotní senzor využívající zařízení ESP32 s odesíláním dat do datového centra.
4. Ověřte funkčnost senzoru a datového centra dlouhodobým měřením teploty.

## Instalace prerekvizit
### Docker
Podle návodu zde:
https://docs.docker.com/engine/install/debian/#install-using-the-repository

### NTP Server (Volitelné)
```bash
apt install -y chrony
```
Konfigurace pro ntp server se nachází v souboru `/etc/chrony/chrony.conf`. Pro povolení komunikace se všemi klienty stačí na konec souboru přidat řádek:
```
allow all
```

## Spuštění
1. Vygenerování InfluxDB tokenu pomocí příkazu `bash generate_token.sh`
2. Nastavení parametrů v souboru `.env`.
3. Zadání příkazu `docker compose up --build` pro sestavení všech Docker image a spuštění kontejnerů. Pro spuštění kontejnerů v odděleném režimu (tedy aby běžely na pozadí, a neblokovaly terminál), přidejte parametr `-d`.
