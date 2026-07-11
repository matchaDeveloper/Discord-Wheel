# Discord Wheel Executables

## Windows
Starte die 'DiscordWheel.exe' im Ordner 'windows'.

## Linux
Führe PyInstaller auf einem Linux-System im Ordner 'linux' aus, um die Binary zu generieren.

cd wheel-executables/linux
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "DiscordWheel" wheel.py
