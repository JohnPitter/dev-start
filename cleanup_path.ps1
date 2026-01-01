# PowerShell script to clean up temporary test paths from user PATH
# Run this script as: powershell -ExecutionPolicy Bypass -File cleanup_path.ps1

Write-Host "Cleaning up temporary paths from user PATH..." -ForegroundColor Yellow

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not $currentPath) {
    Write-Host "User PATH is empty or not set." -ForegroundColor Red
    exit 0
}

Write-Host "`nCurrent PATH entries:" -ForegroundColor Cyan
$pathEntries = $currentPath -split ";"
$pathEntries | ForEach-Object { Write-Host "  $_" }

# Filter out temporary paths (paths containing \Temp\tmp or \AppData\Local\Temp\tmp)
$cleanedEntries = $pathEntries | Where-Object {
    $_ -and
    $_ -notmatch "\\Temp\\tmp[^\\]*\\tools\\" -and
    $_ -notmatch "\\AppData\\Local\\Temp\\tmp[^\\]*\\"
}

# Remove empty entries and duplicates
$cleanedEntries = $cleanedEntries | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique

Write-Host "`nCleaned PATH entries:" -ForegroundColor Green
$cleanedEntries | ForEach-Object { Write-Host "  $_" }

# Count removed entries
$removedCount = $pathEntries.Count - $cleanedEntries.Count
Write-Host "`nRemoved $removedCount temporary path entries." -ForegroundColor Yellow

# Join and set the new PATH
$newPath = $cleanedEntries -join ";"

# Confirm before making changes
Write-Host "`nDo you want to apply this change? (Y/N)" -ForegroundColor Cyan
$confirm = Read-Host

if ($confirm -eq "Y" -or $confirm -eq "y") {
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "`nPATH cleaned successfully!" -ForegroundColor Green
    Write-Host "Please restart your terminal/IDE to see the changes." -ForegroundColor Yellow
} else {
    Write-Host "`nOperation cancelled. No changes made." -ForegroundColor Red
}
