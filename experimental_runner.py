"""
🚀 ЭКСПЕРИМЕНТАЛЬНЫЙ ЗАПУСК БОТА С PATCH-ФАЙЛАМИ
Запускает бота с примененными улучшениями без изменения основного кода
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Добавляем пути для импорта
sys.path.append(os.path.dirname(__file__))

from bot import TruckServiceManagerBot, BOT_TOKEN
from patches.patch_file_upload import FileUploadPatch, patch_callback_handler

class ExperimentalBotRunner:
    """Запускает бота с примененными патчами"""
    
    def __init__(self):
        self.logger = logging.getLogger('ExperimentalRunner')
        self.setup_logging()
    
    def setup_logging(self):
        """Настраивает логирование для экспериментов"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("experimental_log.txt", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def apply_patches(self, bot_instance):
        """Применяет все экспериментальные патчи"""
        try:
            self.logger.info("🛠️ Применяем экспериментальные патчи...")
            
            # ✅ ПАТЧ 1: Загрузка файлов
            file_upload_patch = FileUploadPatch(bot_instance)
            file_upload_patch.apply_patch()
            
            # ✅ ПАТЧ 2: Обработчик callback для админ панели
            patch_callback_handler(bot_instance)
            
            self.logger.info("✅ Все патчи успешно применены!")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка применения патчей: {e}")
    
    def run_experimental_bot(self):
        """Запускает бота с примененными патчами"""
        try:
            self.logger.info("🚀 Запускаем экспериментальную версию бота...")
            
            if not BOT_TOKEN:
                self.logger.error("❌ Токен бота не найден!")
                return
            
            # Создаем экземпляр бота
            bot = TruckServiceManagerBot(BOT_TOKEN)
            
            # Применяем патчи
            self.apply_patches(bot)
            
            # Запускаем бота
            self.logger.info("🎯 Бот запущен с экспериментальными улучшениями!")
            bot.run()
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка запуска: {e}")

def main():
    """Основная функция запуска"""
    print("🔬 ЭКСПЕРИМЕНТАЛЬНЫЙ РЕЖИМ TRUCKSERVICE MANAGER")
    print("=" * 50)
    print("🎯 Активные улучшения:")
    print("• 👨‍💻 Админ панель с загрузкой файлов")
    print("• 📤 Загрузка Excel файлов с работами")
    print("• 📋 Валидация и автоматическое сохранение")
    print("=" * 50)
    
    runner = ExperimentalBotRunner()
    runner.run_experimental_bot()

if __name__ == "__main__":
    main()