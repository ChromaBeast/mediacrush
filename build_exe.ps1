param (
    [string]$Arch = "x64"
)

Write-Host "Building MediaCrush standalone Windows executable for architecture: $Arch..." -ForegroundColor Cyan
python -m pip install --upgrade pip pyinstaller

pyinstaller `
    --onefile `
    --name "mediacrush-windows-$Arch" `
    --hidden-import mediacrush.gui.app `
    --hidden-import mediacrush.gui.worker `
    --hidden-import mediacrush.gui.components `
    mediacrush_launcher.py

Write-Host "Build complete: dist\mediacrush-windows-$Arch.exe" -ForegroundColor Green
