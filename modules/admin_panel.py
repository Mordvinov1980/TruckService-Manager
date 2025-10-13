import pathlib
import logging
from typing import Dict, List
from typing import Dict, List, Tuple
from telebot import types

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self, bot_instance=None):
        self.custom_lists_path = pathlib.Path("Пользовательские_списки")
        self.custom_lists_path.mkdir(exist_ok=True)
        self.awaiting_input_users: Dict[int, str] = {}  # user_id -> тип ожидаемого ввода
        self.bot = bot_instance
        print("✅ AdminPanel инициализирован")
    
    def set_bot(self, bot_instance):
        """Установить экземпляр бота для отправки сообщений"""
        self.bot = bot_instance
        print(f"✅ Bot установлен в AdminPanel: {self.bot is not None}")
    
    def is_awaiting_input(self, message) -> bool:
        """Проверяет, ожидает ли бот ввод от пользователя"""
        return message.chat.id in self.awaiting_input_users
    
    def is_awaiting_excel(self, message) -> bool:
        """Проверяет, ожидает ли бот Excel файл от пользователя"""
        chat_id = message.chat.id
        return chat_id in self.awaiting_input_users and self.awaiting_input_users[chat_id].startswith('excel_file:')
    
    def show_admin_panel_sync(self, call):
        """Синхронная версия для совместимости с pyTelegramBotAPI"""
        print(f"🔍 DEBUG show_admin_panel_sync: bot={self.bot is not None}")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
            
        keyboard = [
            [types.InlineKeyboardButton("➕ СОЗДАТЬ НОВЫЙ СПИСОК", callback_data="admin_create_list")],
            [types.InlineKeyboardButton("📋 УПРАВЛЕНИЕ СПИСКАМИ", callback_data="admin_manage_lists")],
            [types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_back")]
        ]
        reply_markup = types.InlineKeyboardMarkup(keyboard)
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👨‍💻 АДМИН ПАНЕЛЬ\n\nВыберите действие:",
            reply_markup=reply_markup
        )
        print("✅ DEBUG: Админ-панель показана")
    
    def create_new_list_start_sync(self, call):
        """Начало создания нового списка"""
        print(f"🔍 DEBUG create_new_list_start_sync: вызван, chat_id={call.message.chat.id}")
        print(f"🔍 DEBUG: self.bot = {self.bot is not None}")
        
        if not self.bot:
            print("❌ DEBUG: bot instance not set - ВОТ ПРОБЛЕМА!")
            return
            
        chat_id = call.message.chat.id
        self.awaiting_input_users[chat_id] = 'list_name'
        print(f"✅ DEBUG: Установлен awaiting_input для {chat_id}")
        
        try:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📝 СОЗДАНИЕ НОВОГО СПИСКА\n\nВведите название списка:"
            )
            print("✅ DEBUG: Сообщение 'Введите название' отправлено")
        except Exception as e:
            print(f"❌ DEBUG: Ошибка отправки сообщения: {e}")
    
    def handle_list_name_sync(self, message):
        """Обработка введенного названия списка"""
        print(f"🔍 DEBUG handle_list_name_sync: вызван")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or self.awaiting_input_users[chat_id] != 'list_name':
            print(f"❌ DEBUG: Не ожидается ввод от {chat_id}")
            return
            
        list_name = message.text.strip()
        print(f"🔍 DEBUG: Получено название: '{list_name}'")
        
        # Валидация названия
        if not list_name or len(list_name) < 2:
            self.bot.send_message(chat_id, "❌ Название списка должно содержать минимум 2 символа")
            return
        
        # Создаем структуру папок
        success = self._create_list_structure(list_name)
        
        if success:
            # Переключаем на ожидание Excel файла и сохраняем имя списка
            self.awaiting_input_users[chat_id] = f'excel_file:{list_name}'
            self.bot.send_message(
                chat_id,
                f"✅ Список '{list_name}' создан!\n\n"
                f"📁 Структура создана:\n"
                f"• Пользовательские_списки/{list_name}/\n"
                f"• ├── Заказы/\n"
                f"• ├── Учет/\n"
                f"• ├── Фото/\n"
                f"• └── cache/\n\n"
                f"📤 Теперь загрузите Excel файл с работами (2 колонки: работа, нормочасы)"
            )
            print(f"✅ DEBUG: Список '{list_name}' создан, ожидаем Excel файл")
        else:
            self.bot.send_message(chat_id, "❌ Ошибка при создании списка")
            del self.awaiting_input_users[chat_id]
            print("❌ DEBUG: Ошибка создания списка")
    
    def handle_excel_file_sync(self, message):
        """Обработка загруженного Excel файла"""
        print(f"🔍 DEBUG handle_excel_file_sync: вызван")
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or not self.awaiting_input_users[chat_id].startswith('excel_file:'):
            return
        
        # Получаем имя списка из awaiting_input_users
        list_name = self.awaiting_input_users[chat_id].replace('excel_file:', '')
                
        if not list_name:
            self.bot.send_message(chat_id, "❌ Не найден созданный список")
            del self.awaiting_input_users[chat_id]
            return
        
        try:
            # Проверяем что это документ
            if message.document:
                file_info = self.bot.get_file(message.document.file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                
                # Сохраняем файл в папку списка
                list_path = self.custom_lists_path / list_name
                excel_file_path = list_path / f"works_list_{list_name.lower()}.xlsx"
                
                with open(excel_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                del self.awaiting_input_users[chat_id]
                
                self.bot.send_message(
                    chat_id,
                    f"✅ Excel файл успешно загружен для списка '{list_name}'!\n\n"
                    f"📊 Файл сохранен: {excel_file_path}\n\n"
                    f"🔄 Теперь список доступен в главном меню. Используйте /start для обновления."
                )
                print(f"✅ DEBUG: Excel файл загружен для '{list_name}'")
            else:
                self.bot.send_message(chat_id, "❌ Пожалуйста, загрузите Excel файл")
                
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка загрузки файла: {e}")
            logger.error(f"Error handling Excel file: {e}")
            del self.awaiting_input_users[chat_id]

    def _create_list_structure(self, list_name: str) -> bool:
        """Создание структуры папок для нового списка"""
        try:
            base_path = self.custom_lists_path / list_name
            folders = ["Заказы", "Учет", "Фото", "cache"]
            
            for folder in folders:
                (base_path / folder).mkdir(parents=True, exist_ok=True)
            
            # Создаем пустой Excel файл (будет заменен загруженным)
            excel_path = base_path / f"works_list_{list_name.lower()}.xlsx"
            excel_path.touch()
            
            return True
        except Exception as e:
            logger.error(f"Error creating list structure: {e}")
            return False
    

    def load_works_from_custom_list(self, list_name: str) -> List[Tuple[str, float]]:
        """Загрузка работ из пользовательского списка"""
        try:
            list_path = self.custom_lists_path / list_name
            excel_file = list_path / f"works_list_{list_name.lower()}.xlsx"
            
            if not excel_file.exists():
                print(f"❌ DEBUG: Файл {excel_file} не существует")
                return []
                
            # Используем pandas для загрузки Excel файла
            import pandas as pd
            df = pd.read_excel(excel_file)
            
            print(f"🔍 DEBUG: Загружен DataFrame с {len(df)} строками")
            print(f"🔍 DEBUG: Колонки: {df.columns.tolist()}")
            
            works = []
            for index, row in df.iterrows():
                # Используем iloc для доступа по позиции
                if len(row) >= 2 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                    work_name = str(row.iloc[0]).strip()
                    try:
                        hours = float(row.iloc[1])
                        works.append((work_name, hours))
                        print(f"✅ DEBUG: Добавлена работа '{work_name}' - {hours} ч")
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ DEBUG: Ошибка преобразования часов в строке {index}: {e}")
                        continue
                else:
                    print(f"⚠️ DEBUG: Пропущена строка {index} - недостаточно данных")
                        
            print(f"✅ DEBUG: Всего загружено {len(works)} работ")
            return works
            
        except Exception as e:
            logger.error(f"Error loading works from custom list {list_name}: {e}")
            print(f"❌ DEBUG: Ошибка загрузки: {e}")
            return []

    def get_available_lists(self) -> List[str]:
        """Получить список доступных пользовательских списков"""
        print(f"🔍 DEBUG get_available_lists: путь={self.custom_lists_path}")
        print(f"🔍 DEBUG: путь существует? {self.custom_lists_path.exists()}")
        lists = []
        for folder in self.custom_lists_path.iterdir():
            print(f"🔍 DEBUG: найдена папка: {folder.name} (is_dir: {folder.is_dir()})")
            if folder.is_dir():
                lists.append(folder.name)
        print(f"🔍 DEBUG: возвращаем списки: {lists}")
        return lists

# Инициализация админ-панели
admin_panel = AdminPanel()
