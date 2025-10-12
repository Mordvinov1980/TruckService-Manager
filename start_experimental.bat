@echo off
chcp 65001 >nul
cd /d %USERPROFILE%\Desktop\TruckService_Manager
echo 🔬 Запускаю ЭКСПЕРИМЕНТАЛЬНУЮ версию бота...
echo 🎯 Активные функции: Админ панель, загрузка файлов
python experimental_runner.py
pause