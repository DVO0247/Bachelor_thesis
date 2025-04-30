# Datové centrum pro sběr a vizualizaci dat ze senzorů

## Zásady pro vypracování
Cílem práce je implementace datového centra, které bude zajišťovat sběr dat ze senzorů pomocí protokolu TCP nebo UDP, jejich ukládání do databázové struktury a jejich vizualizaci v prostředí Grafana. Datové centrum bude implementováno v Pythonu pomocí frameworku Django. Součástí práce bude také realizace teplotního senzoru využívajícího zařízení ESP32 s odesíláním dat do datového centra.
1. Navrhněte architekturu, protokol přenášení dat a implementujte datové centrum ve frameworku Django.
2. Implementujte grafickou vizualizaci dat pomocí nástroje Grafana.
3. Realizujte teplotní senzor využívající zařízení ESP32 s odesíláním dat do datového centra.
4. Ověřte funkčnost senzoru a datového centra dlouhodobým měřením teploty.

## Prerekvizity
- InfluxDB v2
- Grafana
- Python >= 3.12

## Instalace

### InfluxDB v2
Podle návodu zde:
https://docs.influxdata.com/influxdb/v2/install/?t=Linux

### Grafana
Podle návodu zde:
https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/

### Python pro Debian 12
Instalace Pythonu 3.13.3:
```bash
su -
apt update
apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev pkg-config
curl -O https://www.python.org/ftp/python/3.13.3/Python-3.13.3.tar.xz
tar -xvf Python-3.13.3.tar.xz
cd Python-3.13.3
./configure --enable-optimizations
make
make install
```
Nejnovější verzi Pythonu lze případně nalézt na webu:
https://www.python.org/downloads/source/

### Instalace Python knihoven a inicializace Ovládacího centra

```bash
pip install -r requirements.txt
python django_web/manage.py migrate
python django_web/manage.py collectstatic --noinput --clear
python django_web/manage.py createadmin
```

### Instalace NTP serveru (volitelné)
```bash
apt install ntp
```

## Spuštění
1. Nastavení parametrů v souboru `config.toml`.
2. Spuštění Ovládacího centra: `python django_web/manage.py runserver`.
3. Spuštění Serveru pro příjem dat: `python receiver_server/main.py`.
