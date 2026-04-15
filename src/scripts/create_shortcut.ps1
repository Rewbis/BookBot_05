$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "BookBot_04.lnk"
$ProjectRoot = "e:\Coding\BookBot_05"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$AppPy = Join-Path $ProjectRoot "app.py"
$IconPath = Join-Path $ProjectRoot "src\scripts\bookbot.ico"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonExe
$Shortcut.Arguments = "-m streamlit run `"$AppPy`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$IconPath, 0"
$Shortcut.Description = "Launch BookBot 05 (Plot & Chapter Architect)"
$Shortcut.Save()

Write-Host "Desktop shortcut 'BookBot_04' created successfully!"
Write-Host "Target: $PythonExe"
Write-Host "App: $AppPy"
