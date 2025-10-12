@echo off
chcp 65001 >nul
cd /d %USERPROFILE%\Desktop\TruckService_Manager

:menu
cls
echo ========================================
echo    🚛 TRUCKSERVICE MANAGER - ЗАПУСК
echo ========================================
echo.
echo 1. 🚀 ОСНОВНОЙ бот (стабильная версия)
echo 2. 🔬 ЭКСПЕРИМЕНТАЛЬНЫЙ бот (с новыми фичами)
echo 3. 📊 ТЕСТ расчетов (debug режим)
echo 4. ❌ ВЫХОД
echo.
set /p choice="Выберите вариант [1-4]: "

if "%choice%"=="1" goto main
if "%choice%"=="2" goto experimental
if "%choice%"=="3" goto test
if "%choice%"=="4" exit

echo ❌ Неверный выбор! Нажмите любую клавишу...
pause >nul
goto menu

:main
echo.
echo 🚀 Запускаю ОСНОВНОЙ бота...
python bot.py
pause
goto menu

:experimental
echo.
echo 🔬 Запускаю ЭКСПЕРИМЕНТАЛЬНЫЙ бота...
python experimental_runner.py
pause
goto menu

:test
echo.
echo 🧪 Запускаю ТЕСТОВЫЙ режим...
echo 📊 Проверка расчетов и функциональности
python -c "
from bot import TruckServiceManagerBot, BOT_TOKEN
if BOT_TOKEN:
    bot = TruckServiceManagerBot(BOT_TOKEN)
    print('✅ Бот инициализирован успешно!')
    print('📊 Система готова к работе')
else:
    print('❌ Токен бота не найден!')
"
pause
goto menu