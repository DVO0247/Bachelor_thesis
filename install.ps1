$ErrorActionPreference = "Inquire"

$PythonPath = python -c "import sys; print(sys.executable)"
$WorkingDir = "./" | Resolve-Path
$ScriptPath = Join-Path $WorkingDir "receiver_server/main.py" 
$ServiceName = "MyPythonService"

pip install -r requirements.txt --upgrade
python django_web/manage.py makemigrations control_center
python django_web/manage.py migrate
python django_web/manage.py collectstatic --noinput --clear

<#
# Příkaz pro spuštění Python skriptu v rámci virtuálního prostředí
$ExecStart = "$PythonPath $ScriptPath"

# Vytvoření služby
New-Service -Name $ServiceName -Binary $ExecStart -StartupType Automatic

# Volitelně: Nastavení pracovní složky pro službu
Set-Service -Name $ServiceName -StartupType Automatic
Set-Content -Path "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName" -Name "WorkingDirectory" -Value $WorkingDir

# 2. Spuštění služby
Start-Service -Name $ServiceName

# 3. Zkontrolování stavu služby

sc delete MyPythonService
Get-Service -Name $ServiceName

#>