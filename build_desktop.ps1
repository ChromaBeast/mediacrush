# Build script for MediaCrush Native Flutter Desktop on Windows
Write-Host "Building MediaCrush Native Windows App..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\desktop"

flutter pub get
flutter build windows --release

$OutDir = "$PSScriptRoot\dist\MediaCrush-Windows-x64"
if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Copy-Item -Path "build\windows\x64\runner\Release\*" -Destination $OutDir -Recurse -Force
Write-Host "Native Windows app assembled in: $OutDir" -ForegroundColor Green
Set-Location -Path $PSScriptRoot
