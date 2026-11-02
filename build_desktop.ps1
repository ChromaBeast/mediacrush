# Build script for MediaCrush Native Flutter Desktop on Windows with Inno Setup Installer
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

# Check if Inno Setup is available
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if ($null -ne $iscc) {
    Write-Host "Compiling Inno Setup Windows Installer..." -ForegroundColor Cyan
    & iscc scripts\windows_installer.iss
    Write-Host "Windows Installer assembled: dist\MediaCrush-Windows-Setup-x64.exe" -ForegroundColor Green
} else {
    Write-Host "Inno Setup (iscc) not found in PATH. Skipping installer compilation." -ForegroundColor Yellow
}
