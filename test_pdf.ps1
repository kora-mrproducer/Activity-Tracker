$today=(Get-Date).ToString('yyyy-MM-dd')
$past=(Get-Date).AddDays(-30).ToString('yyyy-MM-dd')
$body='start_date='+$past+'&end_date='+$today
Invoke-WebRequest -Uri http://127.0.0.1:5000/report/pdf -Method POST -Body $body -ContentType 'application/x-www-form-urlencoded' -OutFile report_test.pdf
if (Test-Path report_test.pdf) {
    Write-Host "PDF created: $(( Get-Item report_test.pdf ).Length) bytes"
} else {
    Write-Host "PDF creation failed"
}
