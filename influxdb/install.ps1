Invoke-WebRequest https://download.influxdata.com/influxdb/releases/influxdb2-2.7.11-windows.zip -OutFile .\influx.zip
Expand-Archive .\influx.zip -DestinationPath .
Remove-Item .\influx.zip
Write-Output 'Instalation completed'
pause
