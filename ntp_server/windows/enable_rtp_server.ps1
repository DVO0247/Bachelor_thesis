Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpServer" -Name "Enabled" -Value 1 | Out-Null
w32tm /config /update | Out-Null
Get-NetFirewallRule -DisplayName "Local NTP server" -ErrorAction SilentlyContinue | Out-Null
if(!$?){
    New-NetFirewallRule -DisplayName "Local NTP server" -Protocol UDP -LocalPort 123 -Action Allow -Enabled True -Description "Allow incoming NTP traffic on UDP port 123" | Out-Null
}
pause
