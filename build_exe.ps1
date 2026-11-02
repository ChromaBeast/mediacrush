# MediaCrush standalone .exe build script (PyInstaller)
Write-Host "Installing PyInstaller..." -ForegroundColor Cyan
python -m pip install pyinstaller

Write-Host "Packaging MediaCrush executable..." -ForegroundColor Cyan
pyinstaller `
    --onefile `
    --name mediacrush `
    --hidden-import mediacrush.gui.app `
    --hidden-import mediacrush.gui.worker `
    --hidden-import mediacrush.gui.components `
    mediacrush_launcher.py

Write-Host "Build complete: dist\mediacrush.exe" -ForegroundColor Green
