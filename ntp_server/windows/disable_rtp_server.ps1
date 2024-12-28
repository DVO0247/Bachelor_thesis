Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpServer" -Name "Enabled" -Value 0 | Out-Null
w32tm /config /update | Out-Null
Get-NetFirewallRule -DisplayName "Local NTP server" -ErrorAction SilentlyContinue | Out-Null
if($?){
    Remove-NetFirewallRule -DisplayName "Local NTP server" | Out-Null
}
pause
