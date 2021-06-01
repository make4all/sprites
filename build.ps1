Write-Host "deploying SPRITEs"
Write-Host "printing path to appdata. Comment after testing in your machine."
echo $env:APPDATA
Write-Host "Does scratchPad exist?"
test-path $env:APPDATA/nvda/scratchpad/
copy chrome.py $env:APPDATA\NVDA\ScratchPad\AppModules/
Write-Host "copy complete. restart NVDA."