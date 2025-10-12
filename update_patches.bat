@echo off
chcp 65001 >nul
cd /d %USERPROFILE%\Desktop\TruckService_Manager

echo 🛠️ ОБНОВЛЕНИЕ PATCH-ФАЙЛОВ
echo =========================
echo.
echo 📝 Скопируйте новый код патча из чата и:
echo 1. Создайте файл в папке patches/
echo 2. Обновите experimental_runner.py
echo 3. Запустите экспериментальную версию
echo.
echo 📁 Структура папок:
echo TruckService_Manager/
echo ├── patches/
echo │   └── patch_*.py
echo ├── experimental_runner.py
echo └── start_*.bat
echo.
pause