#!/bin/bash

apt install -y apt-transport-https software-properties-common wget gpg
mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee -a /etc/apt/sources.list.d/grafana.list
apt update && apt install -y grafana

/bin/systemctl daemon-reload
/bin/systemctl enable grafana-server.service
/bin/systemctl start grafana