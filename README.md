# Datové centrum pro sběr a vizualizaci dat ze senzorů a jejich vizualizace

## Zásady pro vypracování
Cílem práce je implementace datového centra, které bude zajišťovat sběr dat ze senzorů pomocí protokolu TCP nebo UDP, jejich ukládání do databázové struktury a jejich vizualizaci v prostředí Grafana. Datové centrum bude implementováno v Pythonu pomocí frameworku Django. Součástí práce bude také realizace teplotního senzoru využívajícího zařízení ESP32 s odesíláním dat do datového centra.
1. Navrhněte architekturu, protokol přenášení dat a implementujte datové centrum ve frameworku Django.
2. Implementujte grafickou vizualizaci dat pomocí nástroje Grafana.
3. Realizujte teplotní senzor využívající zařízení ESP32 s odesíláním dat do datového centra.
4. Ověřte funkčnost senzoru a datového centra dlouhodobým měřením teploty.

## Instalace

### InfluxDB v2
https://docs.influxdata.com/influxdb/v2/install/

### Grafana
https://grafana.com/docs/grafana/latest/setup-grafana/installation/

### Python
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update && sudo apt install python3.13-venv
```

### Control center
Nastavení parametrů v souboru `config.toml`.

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python django_web/manage.py makemigrations control_center
python django_web/manage.py migrate
python django_web/manage.py collectstatic --noinput --clear
python django_web/manage.py createsuperuser
python django_web/manage.py runserver
```