#!/bin/bash

curl -o influx.zip https://download.influxdata.com/influxdb/releases/influxdb2-2.7.11_linux_amd64.tar.gz
tar -xzf influx.zip -C .
rm influx.zip
echo "Installation completed"
