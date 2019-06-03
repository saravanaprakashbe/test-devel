param (
    [string]$fileName = "dummy"
)
if ( Test-Path -Path $fileName ) {
    #$fileName = "C:\Users\1563500\Documents\My Data\BitBucket_Repos\Environment_Provisioning\Readme.md"
    $server = $env:computername
    $fn = Get-ChildItem $fileName | select -expand basename
    $sourceLastWriteTime = (Get-Item $fileName).LastWriteTime
    $curDate = [datetime]::Now
    $variance = $curDate.Subtract($sourceLastWriteTime)
    if ( $variance.Days -ne 0 -or $variance.Hours -ne 0 -or $variance.Minutes -ge 5) {
        Write-Output "File '$fn' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn not updated on host $server" -BodyAsHtml "File '$fn' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
    }
}
else {
    Write-Error "File '$fn' is not found"
    Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn not found on host $server" -BodyAsHtml "File '$fn' is not found on host $server"
}