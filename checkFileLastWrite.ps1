param (
    [Parameter(Mandatory=$true)][string]$fileName1 = "",
    [Parameter(Mandatory=$true)][string]$fileName2 = ""
)
if ((Test-Path -Path $fileName1) -and (Test-Path -Path $fileName2 )) {
    #$fileName = "C:\Users\1563500\Documents\My Data\BitBucket_Repos\Environment_Provisioning\Readme.md"
    $server = $env:computername
    $fn1 = Get-ChildItem $fileName11 | select -expand basename
    $fn2 = Get-ChildItem $fileName12 | select -expand basename
    $sourceLastWriteTime1 = (Get-Item $fileName1).LastWriteTime
    $sourceLastWriteTime2 = (Get-Item $fileName2).LastWriteTime
    $variance = $sourceLastWriteTime1.Subtract($sourceLastWriteTime2)
    if ( $variance.Days -ne 0 -or $variance.Hours -ne 0 -or $variance.Minutes -ge 5 -or $variance.Minutes -ge -5) {
        Write-Output "File '$fn' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn not updated on host $server" -BodyAsHtml "File '$fn' is not updated on host $server, since $($variance.Days) Days, $($variance.Hours) Hours, $($variance.Minutes) Minutes"
    }
}
else {
    Write-Error "File '$fn' is not found"
    Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn not found on host $server" -BodyAsHtml "File '$fn' is not found on host $server"
}