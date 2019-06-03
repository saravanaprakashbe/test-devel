param (
    [string]$fileName1 = "dummy"
    [string]$fileName2 = "dummy"
)
if ( Test-Path -Path $fileName1 -and Test-Path -Path $fileName2 ) {
    #$fileName = "C:\Users\1563500\Documents\My Data\BitBucket_Repos\Environment_Provisioning\Readme.md"
    $server = $env:computername
    $fn1 = Get-ChildItem $fileName1 | select -expand basename
    $fn2 = Get-ChildItem $fileName2 | select -expand basename
    $fn1LastWriteTime = (Get-Item $fileName1).LastWriteTime
    $fn2LastWriteTime = (Get-Item $fileName2).LastWriteTime
    #$curDate = [datetime]::Now
    $variance = $fn1LastWriteTime.Subtract($fn2LastWriteTime)
    if ( $variance.Days -ne 0 -or $variance.Hours -ne 0 -or $variance.Minutes -ge 5) {
        Write-Output "File '$fn1' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1@dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn1 not updated on host $server" -BodyAsHtml "File '$fn1' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
    }
    else if ( $variance.Days -ne 0 -or $variance.Hours -ne 0 -or $variance.Minutes -le -5) {
        Write-Output "File '$fn2' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1@dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn2 not updated on host $server" -BodyAsHtml "File '$fn2' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
    }
}
else {
    Write-Error "File '$fn1' or '$fn2' not found"
    Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1@dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn1 or $fn2 not found on host $server" -BodyAsHtml "File '$fn1' or 'fn2' is not found on host $server"
}
