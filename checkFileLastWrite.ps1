param (
    [string]$fName1 = "SXT01_10.log*",
    [string]$path1 = "",
    [string]$fName2 = "SXT02_10.log*",
    [string]$path2 = ""
)
$fileName1 = Get-ChildItem -Path -Filter $fName1 | % { Write-Host $_.FullName }
$fileName2 = Get-ChildItem -Path -Filter $fName2 | % { Write-Host $_.FullName }
if ((Test-Path -Path $fileName1) -and (Test-Path -Path $fileName2 )) {
    #$fileName = "C:\Users\1563500\Documents\My Data\BitBucket_Repos\Environment_Provisioning\Readme.md"
    $server = $env:computername
    $fn1 = Get-ChildItem $fileName1 | select -expand basename
    $fn2 = Get-ChildItem $fileName2 | select -expand basename
    $sourceLastWriteTime1 = (Get-Item $fileName1).LastWriteTime
    $sourceLastWriteTime2 = (Get-Item $fileName2).LastWriteTime
    $variance1 = $sourceLastWriteTime1.Subtract($sourceLastWriteTime2)
    $variance2 = $sourceLastWriteTime2.Subtract($sourceLastWriteTime1)
    if ( $variance1.Days -ge 0 -or $variance1.Hours -ge 0 -or $variance1.Minutes -ge 5 ) {
        Write-Output "File '$fn1' is not updated on host $server, since $($variance1.Days) Days, $($variance1.Hours) Hours, $($variance1.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn1 not updated on host $server" -BodyAsHtml "File '$fn1' is not updated on host $server, since $($variance1.Days) Days, $($variance1.Hours) Hours, $($variance1.Minutes) Minutes"
    }
    elseif ( $variance2.Days -ge 0 -or $variance2.Hours -ge 0 -or $variance2.Minutes -ge 5 ) {
        Write-Output "File '$fn2' is not updated on host $server, since $($variance2.Days) Days, $($variance2.Hours) Hours, $($variance2.Minutes) Minutes"
        Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - File $fn2 not updated on host $server" -BodyAsHtml "File '$fn2' is not updated on host $server, since $($variance2.Days) Days, $($variance2.Hours) Hours, $($variance2.Minutes) Minutes"
    }    
}
else {
    Write-Error "Files $fn1 or $fn2 not found on host $server"
    Send-MailMessage -From FROM_EMAIL@dummy.com -To TO_EMAIL1#dummy.com,TO_EMAIL2@dummy.com -Cc CC_MAILS@dummy.com -Subject "Notificaton - Files $fn1 or $fn2 not found on host $server" -BodyAsHtml "Files $fn1 or $fn2 not found on host $server"
}