@echo off
chcp 65001 >nul
cd /d %USERPROFILE%\Desktop\TruckService_Manager

echo 📊 ИНФОРМАЦИЯ О ПРОЕКТЕ
echo ======================
echo.
echo 🚛 TruckService Manager v2.1
echo 📅 Последнее обновление: 10.10.2025
echo.
echo 🏗️ АРХИТЕКТУРА:
echo • bot.py - основной модуль
echo • modules/ - модули системы
echo • patches/ - экспериментальные фичи
echo • Шаблоны/ - Excel шаблоны и базы
echo.
echo 🎯 РЕЖИМЫ ЗАПУСКА:
echo • start_bot.bat - стабильная версия
echo • start_experimental.bat - с новыми фичами
echo • start_menu.bat - меню выбора
echo.
echo 💡 СОВЕТ: Используйте experimental для тестирования
echo          новых функций без риска!
echo.
pause