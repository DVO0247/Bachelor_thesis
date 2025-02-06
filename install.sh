#!/bin/bash

pip install -r requirements.txt
python django_web/manage.py makemigrations control_center
python django_web/manage.py migrate
python django_web/manage.py collectstatic --noinput --clear

# Zjistit absolutní cestu ke skriptu a pracovním adresářům
BASE_DIR="$(pwd)"  # Aktuální pracovní adresář (odkud je skript spuštěn)

# Relativní cesty k souborům
SCRIPT_PATH="${BASE_DIR}/script.py"  # Relativní cesta k Python skriptu
PYTHON_PATH=$(python -c "import sys; print(sys.executable)")  # Relativní cesta k virtuálnímu prostředí
SERVICE_NAME="my_python_service"
WORKING_DIR="${BASE_DIR}"  # Můžete změnit, pokud chcete specifický pracovní adresář

# 1. Vytvoření systemd služebního souboru
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Vytvářím systemd unit soubor: ${SERVICE_FILE}"

cat > $SERVICE_FILE <<EOL
[Unit]
Description=My Python Script as a daemon
After=network.target

[Service]
Type=simple
ExecStart=${VENV_PATH}/bin/python ${SCRIPT_PATH}
WorkingDirectory=${WORKING_DIR}
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 2. Načtení a povolení služby
echo "Načítám a aktivuji službu: ${SERVICE_NAME}"

# Načte nové soubory systemd a povolí službu
systemctl daemon-reload

# Povolit službu, aby se spouštěla při startu systému
systemctl enable ${SERVICE_NAME}

# Spustit službu
systemctl start ${SERVICE_NAME}

# 3. Zkontrolovat stav služby
echo "Stav služby ${SERVICE_NAME}:"
systemctl status ${SERVICE_NAME}
