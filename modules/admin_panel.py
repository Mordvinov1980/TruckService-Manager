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
      
    def is_awaiting_excel(self, message) -> bool:
        """Проверяет, ожидает ли бот Excel файл от пользователя"""
        chat_id = message.chat.id
        # ✅ ДОБАВЛЯЕМ НОВЫЙ ТИП add_excel_file
        return (chat_id in self.awaiting_input_users and 
                (self.awaiting_input_users[chat_id].startswith('excel_file:') or
                 self.awaiting_input_users[chat_id].startswith('add_excel_file:')))    
    
    def is_awaiting_input(self, message) -> bool:
        """Проверяет, ожидает ли бот ввод от пользователя"""
        return message.chat.id in self.awaiting_input_users

    def show_admin_panel_sync(self, call):
        """Обновленная админ-панель с одной кнопкой добавления"""
        print(f"🔍 DEBUG show_admin_panel_sync: bot={self.bot is not None}")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
        
        keyboard = [
            [types.InlineKeyboardButton("➕ ДОБАВИТЬ СПИСОК", callback_data="admin_add_list")],
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

    def handle_add_list_start_sync(self, call):
        """Начало добавления списка (объединенная логика)"""
        print(f"🔍 DEBUG handle_add_list_start_sync: вызван, chat_id={call.message.chat.id}")
    
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
        
        chat_id = call.message.chat.id
        self.awaiting_input_users[chat_id] = 'add_list_name'
        print(f"✅ DEBUG: Установлен awaiting_input для {chat_id}")
    
        try:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="➕ ДОБАВЛЕНИЕ СПИСКА\n\nВведите название для нового списка:"
            )
            print("✅ DEBUG: Сообщение 'Введите название' отправлено")
        except Exception as e:
            print(f"❌ DEBUG: Ошибка отправки сообщения: {e}")
    
    def handle_add_list_name_sync(self, message):
        """Обработка введенного названия для добавления списка"""
        print(f"🔍 DEBUG handle_add_list_name_sync: вызван")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
        
        chat_id = message.chat.id
    
        if chat_id not in self.awaiting_input_users or self.awaiting_input_users[chat_id] != 'add_list_name':
            print(f"❌ DEBUG: Не ожидается ввод от {chat_id}")
            return
        
        list_name = message.text.strip()
        print(f"🔍 DEBUG: Получено название: '{list_name}'")
    
        # Валидация названия
        if not list_name or len(list_name) < 2:
            self.bot.send_message(chat_id, "❌ Название списка должно содержать минимум 2 символа")
            return
    
        # Проверяем, не существует ли уже список с таким названием
        existing_lists = self.get_available_lists()
        if list_name in existing_lists:
            self.bot.send_message(
                chat_id, 
                f"❌ Список с названием '{list_name}' уже существует\n\nВыберите другое название:"
            )
            return
    
        # Создаем структуру папок и переключаем на ожидание Excel файла
        success = self._create_list_structure(list_name)
    
        if success:
            # Сохраняем имя списка и переключаем на ожидание файла
            self.awaiting_input_users[chat_id] = f'add_excel_file:{list_name}'
            self.bot.send_message(
                chat_id,
                f"✅ Структура для списка '{list_name}' создана!\n\n"
                f"📤 Теперь отправьте Excel файл со списком работ\n\n"
                f"📋 Формат файла:\n"
                f"• Колонка A: 'Наименование работ' - название работы\n"
                f"• Колонка B: 'Нормочасы' - время выполнения"
            )
            print(f"✅ DEBUG: Ожидаем Excel файл для списка '{list_name}'")
        else:
            self.bot.send_message(chat_id, "❌ Ошибка при создании структуры списка")
            del self.awaiting_input_users[chat_id]
            print("❌ DEBUG: Ошибка создания структуры списка")
    
    def handle_add_excel_file_sync(self, message):
        """Обработка загруженного Excel файла с возвратом в главное меню"""
        print(f"🔍 DEBUG handle_add_excel_file_sync: вызван")
        if not self.bot:
            return
        
        chat_id = message.chat.id
    
        if chat_id not in self.awaiting_input_users or not ('add_excel_file:' in self.awaiting_input_users[chat_id]):
            current_status = self.awaiting_input_users.get(chat_id, 'НЕТ СТАТУСА')
            print(f"❌ DEBUG: Не ожидается Excel от {chat_id}, текущий статус: {current_status}")
            return
    
        # Получаем имя списка
        full_status = self.awaiting_input_users[chat_id]
        list_name = full_status.split(':')[1]
        print(f"🔍 DEBUG: Обрабатываем список: '{list_name}'")
                
        if not list_name:
            self.bot.send_message(chat_id, "❌ Не найден созданный список")
            del self.awaiting_input_users[chat_id]
            return
    
        try:
            if message.document:
                file_info = self.bot.get_file(message.document.file_id)
                file_name = message.document.file_name
                print(f"🔍 DEBUG: Получен файл: {file_name}")
            
                if not file_name.lower().endswith(('.xlsx', '.xls')):
                    self.bot.send_message(chat_id, "❌ Пожалуйста, загрузите файл в формате Excel (.xlsx или .xls)")
                    return
            
                downloaded_file = self.bot.download_file(file_info.file_path)
                print(f"🔍 DEBUG: Файл скачан, размер: {len(downloaded_file)} байт")
            
                # Сохраняем файл
                list_path = self.custom_lists_path / list_name
                list_path.mkdir(parents=True, exist_ok=True)
            
                excel_file_path = list_path / f"works_list_{list_name}.xlsx"
            
                with open(excel_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
            
                # Валидация
                validation_result = self._validate_excel_file(excel_file_path)
            
                if not validation_result['valid']:
                    excel_file_path.unlink(missing_ok=True)
                    self.bot.send_message(
                        chat_id,
                        f"❌ Ошибка валидации файла:\n{validation_result['error']}\n\n"
                        f"Пожалуйста, исправьте файл и попробуйте снова."
                    )
                    del self.awaiting_input_users[chat_id]
                    return
            
                # ✅ УСПЕШНАЯ ЗАГРУЗКА - ВОЗВРАЩАЕМ В ГЛАВНОЕ МЕНЮ
                del self.awaiting_input_users[chat_id]
            
                success_message = (
                    f"✅ Список '{list_name}' успешно загружен!\n\n"
                    f"📊 Файл сохранен: {excel_file_path.name}\n"
                    f"📋 Загружено работ: {validation_result['work_count']}\n"
                    f"⏱️ Общее время: {validation_result['total_hours']:.1f} н/ч\n\n"
                    f"🔄 Возвращаем в главное меню..."
                )
            
                self.bot.send_message(chat_id, success_message)
                print(f"✅ DEBUG: Excel файл загружен для '{list_name}', работ: {validation_result['work_count']}")
            
                # ✅ ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
                self.bot.send_message(
                    chat_id,
                    f"🏠 Список '{list_name}' теперь доступен в главном меню!\n"
                    f"Используйте /start чтобы увидеть его."
                )
            
            else:
                self.bot.send_message(chat_id, "❌ Пожалуйста, загрузите Excel файл")
                
        except Exception as e:
            print(f"❌ DEBUG: Критическая ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
            self.bot.send_message(chat_id, f"❌ Ошибка загрузки файла: {e}")
            logger.error(f"Error handling Excel file upload: {e}")
            del self.awaiting_input_users[chat_id]

    def handle_upload_list_start_sync(self, call):
        """Начало загрузки списка работ"""
        print(f"🔍 DEBUG handle_upload_list_start_sync: вызван, chat_id={call.message.chat.id}")
        
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
            
        chat_id = call.message.chat.id
        self.awaiting_input_users[chat_id] = 'upload_list_name'
        print(f"✅ DEBUG: Установлен awaiting_input для {chat_id}")
        
        try:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="📥 ЗАГРУЗКА СПИСКА РАБОТ\n\nВведите название для нового списка:"
            )
            print("✅ DEBUG: Сообщение 'Введите название' отправлено")
        except Exception as e:
            print(f"❌ DEBUG: Ошибка отправки сообщения: {e}")
    
    def handle_upload_list_name_sync(self, message):
        """Обработка введенного названия для загрузки списка"""
        print(f"🔍 DEBUG handle_upload_list_name_sync: вызван")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
            
        chat_id = message.chat.id

        # ✅ ИСПРАВЛЯЕМ ПРОВЕРКУ - ожидаем upload_list_name
        if chat_id not in self.awaiting_input_users or self.awaiting_input_users[chat_id] != 'upload_list_name':
            print(f"❌ DEBUG: Не ожидается ввод от {chat_id}, текущий статус: {self.awaiting_input_users.get(chat_id, 'нет')}")
            return
        
        list_name = message.text.strip()
        print(f"🔍 DEBUG: Получено название для загрузки: '{list_name}'")    
        
        # Валидация названия
        if not list_name or len(list_name) < 2:
            self.bot.send_message(chat_id, "❌ Название списка должно содержать минимум 2 символа")
            return
        
        # Проверяем, не существует ли уже список с таким названием
        existing_lists = self.get_available_lists()
        if list_name in existing_lists:
            self.bot.send_message(
                chat_id, 
                f"❌ Список с названием '{list_name}' уже существует\n\nВыберите другое название:"
            )
            return
        
        # Создаем структуру папок и переключаем на ожидание Excel файла
        success = self._create_list_structure(list_name)
        
        if success:
            # Сохраняем имя списка и переключаем на ожидание файла
            self.awaiting_input_users[chat_id] = f'upload_excel_file:{list_name}'
            self.bot.send_message(
                chat_id,
                f"✅ Структура для списка '{list_name}' создана!\n\n"
                f"📤 Теперь отправьте Excel файл со списком работ (2 колонки: работа, нормочасы)\n\n"
                f"📋 Формат файла:\n"
                f"• Колонка A: 'Наименование работ' - название работы\n"
                f"• Колонка B: 'Нормочасы' - время выполнения\n\n"
                f"Пример:\n"
                f"| Наименование работ          | Нормочасы |\n"
                f"|-----------------------------|-----------|\n"
                f"| Покраска бампера           | 1.5       |\n"
                f"| Замена фары                | 2.0       |"
            )
            print(f"✅ DEBUG: Ожидаем Excel файл для списка '{list_name}'")
        else:
            self.bot.send_message(chat_id, "❌ Ошибка при создании структуры списка")
            del self.awaiting_input_users[chat_id]
            print("❌ DEBUG: Ошибка создания структуры списка")

    def handle_upload_excel_file_sync(self, message):
        """Обработка загруженного Excel файла для списка"""
        print(f"🔍 DEBUG handle_upload_excel_file_sync: вызван")
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        # ✅ ДОБАВИМ ПОДРОБНУЮ ОТЛАДКУ
        print(f"🔍 DEBUG: awaiting_input_users: {self.awaiting_input_users}")
        print(f"🔍 DEBUG: chat_id в awaiting: {chat_id in self.awaiting_input_users}")
                
        if chat_id not in self.awaiting_input_users or not ('excel_file:' in self.awaiting_input_users[chat_id]):
            current_status = self.awaiting_input_users.get(chat_id, 'НЕТ СТАТУСА')
            print(f"❌ DEBUG: Не ожидается Excel от {chat_id}, текущий статус: {current_status}")
            return
        
        # Получаем имя списка из awaiting_input_users
        full_status = self.awaiting_input_users[chat_id]
        list_name = full_status.split(':')[1]  # Берем только часть после ':'
        print(f"🔍 DEBUG: Обрабатываем список: '{list_name}'")
                    
        if not list_name:
            self.bot.send_message(chat_id, "❌ Не найден созданный список")
            del self.awaiting_input_users[chat_id]
            return
        
        try:
            # Проверяем что это документ
            if message.document:
                file_info = self.bot.get_file(message.document.file_id)
                file_name = message.document.file_name
                print(f"🔍 DEBUG: Получен файл: {file_name}")
                
                # Проверяем расширение файла
                if not file_name.lower().endswith(('.xlsx', '.xls')):
                    self.bot.send_message(chat_id, "❌ Пожалуйста, загрузите файл в формате Excel (.xlsx или .xls)")
                    return
                
                downloaded_file = self.bot.download_file(file_info.file_path)
                print(f"🔍 DEBUG: Файл скачан, размер: {len(downloaded_file)} байт")
                
                # ✅ ПРОВЕРЯЕМ И СОЗДАЕМ СТРУКТУРУ ПАПОК
                list_path = self.custom_lists_path / list_name
                print(f"🔍 DEBUG: Путь для сохранения: {list_path}")
                
                # Создаем папку если не существует
                list_path.mkdir(parents=True, exist_ok=True)
                print(f"🔍 DEBUG: Папка создана/проверена: {list_path.exists()}")
                
                # Сохраняем файл в папку списка
                excel_file_path = list_path / f"works_list_{list_name}.xlsx"
                print(f"🔍 DEBUG: Полный путь файла: {excel_file_path}")
                
                with open(excel_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                print(f"🔍 DEBUG: Файл записан на диск: {excel_file_path.exists()}")
                
                # Проверяем структуру файла
                validation_result = self._validate_excel_file(excel_file_path)
                print(f"🔍 DEBUG: Результат валидации: {validation_result}")
                
                if not validation_result['valid']:
                    # Удаляем невалидный файл
                    excel_file_path.unlink(missing_ok=True)
                    self.bot.send_message(
                        chat_id,
                        f"❌ Ошибка валидации файла:\n{validation_result['error']}\n\n"
                        f"Пожалуйста, исправьте файл и попробуйте снова."
                    )
                    del self.awaiting_input_users[chat_id]
                    return
                
                del self.awaiting_input_users[chat_id]
                
                self.bot.send_message(
                    chat_id,
                    f"✅ Список '{list_name}' успешно загружен!\n\n"
                    f"📊 Файл сохранен: {excel_file_path.name}\n"
                    f"📋 Загружено работ: {validation_result['work_count']}\n"
                    f"⏱️ Общее время: {validation_result['total_hours']:.1f} н/ч\n\n"
                    f"🔄 Список теперь доступен в главном меню."
                )
                print(f"✅ DEBUG: Excel файл загружен для '{list_name}', работ: {validation_result['work_count']}")
            else:
                self.bot.send_message(chat_id, "❌ Пожалуйста, загрузите Excel файл")
                    
        except Exception as e:
            print(f"❌ DEBUG: Критическая ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
            self.bot.send_message(chat_id, f"❌ Ошибка загрузки файла: {e}")
            logger.error(f"Error handling Excel file upload: {e}")
            del self.awaiting_input_users[chat_id]        
 
    def _validate_excel_file(self, file_path: pathlib.Path) -> Dict[str, any]:
        """Валидация структуры Excel файла"""
        try:
            import pandas as pd
            
            df = pd.read_excel(file_path)
            
            # Проверяем минимальное количество колонок
            if len(df.columns) < 2:
                return {'valid': False, 'error': 'Файл должен содержать минимум 2 колонки'}
            
            # Проверяем наличие данных
            if len(df) == 0:
                return {'valid': False, 'error': 'Файл не содержит данных'}
            
            # Проверяем формат данных
            valid_works = []
            total_hours = 0.0
            
            for index, row in df.iterrows():
                if len(row) >= 2 and pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                    work_name = str(row.iloc[0]).strip()
                    if work_name and work_name != 'nan':
                        try:
                            hours = float(row.iloc[1])
                            if hours > 0:  # Проверяем что нормочасы положительные
                                valid_works.append((work_name, hours))
                                total_hours += hours
                        except (ValueError, TypeError):
                            continue
            
            if len(valid_works) == 0:
                return {'valid': False, 'error': 'Не найдено валидных работ в файле'}
            
            return {
                'valid': True,
                'work_count': len(valid_works),
                'total_hours': total_hours
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Ошибка чтения файла: {e}'}

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

    def register_handlers(self, application):
        """Регистрация обработчиков для админ-панели"""
        # ✅ ОБНОВЛЯЕМ ОБРАБОТЧИКИ - РЕГИСТРИРУЕМ НОВЫЕ
        application.add_handler(types.CallbackQueryHandler(self.handle_add_list_start_sync, func=lambda call: call.data == 'admin_add_list'))
        application.add_handler(types.CallbackQueryHandler(self.show_admin_panel_sync, func=lambda call: call.data == 'admin_back'))
        
# Инициализация админ-панели
admin_panel = AdminPanel()