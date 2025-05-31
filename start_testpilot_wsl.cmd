powershell ps1\path_wsl.ps1

start wsl cd /home/ziqiw/NapCat;sudo ./launcher.sh
cd ..\testpilot_qqbot\web
start server.cmd
cd ..
nb run --reload