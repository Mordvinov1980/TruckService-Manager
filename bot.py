import telebot
from telebot import types
import pandas as pd
import datetime
import os
import re
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import range_boundaries
import shutil
import pathlib
from dotenv import load_dotenv
import time
from num2words import num2words
import logging
import pickle
from typing import Dict, List, Tuple, Optional, Union, Any

# ✅ ИМПОРТ МОДУЛЕЙ
from modules.excel_processor import ExcelProcessor, ExcelProcessingError
from modules.data_repositories import (RepositoryFactory, WorksRepository, MaterialsRepository, 
                                     AccountingRepository, RepositoryError, DataNotFoundError)
from modules.document_factory import DocumentFactory, DocumentCreationError  # 🆕 ИМПОРТ ФАБРИКИ ДОКУМЕНТОВ
from modules.admin_panel import AdminPanel

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

DEBUG_MODE = True
CHAT_ID = "-1003145822387"

# ✅ КОНКРЕТНЫЕ ИСКЛЮЧЕНИЯ ДЛЯ BOT.PY
class BotProcessingError(Exception):
    """Базовая ошибка обработки бота"""
    pass

class SessionError(BotProcessingError):
    """Ошибка работы с сессиями пользователей"""
    pass

class FileSystemError(BotProcessingError):
    """Ошибка файловой системы"""
    pass

class ExcelLoadError(BotProcessingError):
    """Ошибка загрузки Excel файлов"""
    pass

class PhotoProcessingError(BotProcessingError):
    """Ошибка обработки фотографий"""
    pass

class TelegramAPIError(BotProcessingError):
    """Ошибка взаимодействия с Telegram API"""
    pass

class ValidationError(BotProcessingError):
    """Ошибка валидации данных"""
    pass

class AccountingError(BotProcessingError):
    """Ошибка учета данных"""
    pass


class TruckServiceManagerBot:
    def __init__(self, token: str) -> None:
        self.bot = telebot.TeleBot(token)
        # ✅ СОЗДАЕМ ЭКЗЕМПЛЯР ExcelProcessor
        self.excel_processor = ExcelProcessor()
        # ✅ СОЗДАЕМ ФАБРИКУ ДОКУМЕНТОВ 🆕
        self.document_factory = DocumentFactory(self.excel_processor)
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self.chat_id = CHAT_ID
        
        # ✅ КОНСТАНТЫ СИСТЕМЫ
        self.WORKS_PER_PAGE = 8
        self.MATERIALS_PER_PAGE = 8
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1
        
        self.setup_directories()
        self.setup_logging()
        self.setup_repositories()  # ✅ ИНИЦИАЛИЗИРУЕМ РЕПОЗИТОРИИ
        self.setup_handlers()
        self.setup_bot_menu()
        
        # ✅ СОЗДАЕМ АДМИН-ПАНЕЛЬ ПОСЛЕ setup_handlers()
        self.admin_panel = AdminPanel(self.bot)
        # ✅ РЕГИСТРИРУЕМ ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ
        ##self.admin_panel.register_handlers(self.bot)
        
        print("🤖 TruckService Manager запущен!")

    def setup_repositories(self) -> None:
        """Инициализация репозиториев для работы с данными"""
        try:
            # ✅ СОЗДАЕМ РЕПОЗИТОРИИ ЧЕРЕЗ ФАБРИКУ
            self.works_repository: WorksRepository = RepositoryFactory.create_works_repository(
                self.main_folder, self.sections
            )
            self.materials_repository: MaterialsRepository = RepositoryFactory.create_materials_repository(
                self.main_folder
            )
            self.accounting_repository: AccountingRepository = RepositoryFactory.create_accounting_repository(
                self.main_folder, self.sections, self.common_accounting_folder
            )
            
            print("✅ Репозитории данных инициализированы")
            
        except Exception as e:
            raise BotProcessingError(f"Ошибка инициализации репозиториев: {e}") from e

    def setup_logging(self) -> None:
        """Настраивает расширенное логирование"""
        log_file = self.main_folder / "bot_log.txt"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('TruckServiceBot')

    def setup_bot_menu(self) -> None:
        menu_commands = [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("new_order", "Создать новый заказ-наряд"),
            types.BotCommand("help", "Помощь по боту")
        ]
        try:
            self.bot.set_my_commands(menu_commands)
            print("✅ Меню бота настроено")
        except Exception as e:
            print(f"⚠️ Предупреждение при настройке меню: {e}")

    def setup_directories(self) -> None:
        """УЛУЧШЕННОЕ СОЗДАНИЕ СТРУКТУРЫ ПАПОК - ТОЛЬКО ОДНА ПАПКА ШАБЛОНЫ"""
        try:
            desktop = pathlib.Path.home() / "Desktop"
            self.main_folder = desktop / "TruckService_Manager"
            
            # ОСНОВНЫЕ ПАПКИ
            essential_folders = [
                self.main_folder,
                self.main_folder / "Шаблоны",  # ✅ ТОЛЬКО ОДНА ПАПКА ШАБЛОНЫ
                self.main_folder / "Общий_учет",
                self.main_folder / "Логи"
            ]
            
            for folder in essential_folders:
                folder.mkdir(exist_ok=True)
            
            self.sections: Dict[str, Dict[str, Any]] = {
                'base': {
                    'name': '📋 Типовой заказ-наряд',
                    'folder': self.main_folder / "Типовой_заказ",
                    'works_file': "works_list_base.xlsx"
                }
            }
            
            # ПАПКИ РАЗДЕЛОВ - БЕЗ ПАПКИ "ШАБЛОНЫ"
            for section_id, section_data in self.sections.items():
                section_folders = [
                    section_data['folder'],
                    section_data['folder'] / "Заказы", 
                    section_data['folder'] / "Учет",
                    section_data['folder'] / "Фото",
                    section_data['folder'] / "cache"
                ]
                
                for folder in section_folders:
                    folder.mkdir(parents=True, exist_ok=True)
                
                print(f"📁 Создана структура папок для: {section_data['name']}")
            
            # ДОБАВЛЯЕМ ОПРЕДЕЛЕНИЕ common_accounting_folder
            self.common_accounting_folder = self.main_folder / "Общий_учет"
            self.common_accounting_folder.mkdir(exist_ok=True)
            print(f"📁 Создана папка общего учета: {self.common_accounting_folder}")
            
        except Exception as e:
            raise FileSystemError(f"Ошибка создания структуры папок: {e}") from e

    def setup_handlers(self) -> None:
        """Настройка обработчиков с улучшенной обработкой ошибок"""
        
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message: types.Message) -> None:
            try:
                self.show_section_selection(message.chat.id)
            except Exception as e:
                self._handle_critical_error(message.chat.id, f"Ошибка при запуске: {e}")

        @self.bot.message_handler(commands=['help'])
        def send_help(message: types.Message) -> None:
            try:
                self.show_help(message.chat.id)
            except Exception as e:
                self._handle_critical_error(message.chat.id, f"Ошибка при показе помощи: {e}")

        @self.bot.message_handler(commands=['new_order'])
        def start_new_order(message: types.Message) -> None:
            try:
                chat_id = message.chat.id
                if chat_id in self.user_sessions and 'section' in self.user_sessions[chat_id]:
                    self.user_sessions[chat_id].update({
                        'step': 'license_plate',
                        'selected_works': [],
                        'selected_materials': [],
                        'current_page': 0
                    })
                    
                    section_name = self.sections[self.user_sessions[chat_id]['section']]['name']
                    self.bot.send_message(
                        chat_id,
                        f"🏗️ {section_name}\n\n📋 Создание нового заказ-наряда\n\nВведите госномер автомобиля:\nПример: А123ВС77 или 1234АВ"
                    )
                else:
                    self.show_section_selection(chat_id)
            except Exception as e:
                self._handle_critical_error(message.chat.id, f"Ошибка при создании нового заказа: {e}")

        @self.bot.message_handler(content_types=['photo'])
        def handle_photos(message: types.Message) -> None:
            try:
                chat_id = message.chat.id
                
                if chat_id not in self.user_sessions:
                    return
                    
                session = self.user_sessions[chat_id]
                
                if session.get('step') == 'waiting_photos':
                    if 'processing' in session and session['processing']:
                        return
                    
                    session['processing'] = True
                    
                    try:
                        if 'photo_file_ids' not in session:
                            session['photo_file_ids'] = []
                        
                        file_id = message.photo[-1].file_id
                        
                        if file_id not in session['photo_file_ids']:
                            session['photo_file_ids'].append(file_id)
                            
                            file_info = self.bot.get_file(file_id)
                            downloaded_file = self.bot.download_file(file_info.file_path)
                            
                            photo_index = len(session['photo_file_ids'])
                            
                            # ✅ ОПРЕДЕЛЯЕМ ПАПКУ РАЗДЕЛА
                            if session['section'].startswith('custom_'):
                                section_folder = pathlib.Path("Пользовательские_списки") / session['custom_list']
                            else:
                                section_folder = self.sections[session['section']]['folder']

                            photos_folder = section_folder / "Фото"
                            
                            photo_filename = f"{session['license_plate']}_{session.get('order_number', '000')}_{photo_index}.jpg"
                            photo_path = photos_folder / photo_filename
                            
                            with open(photo_path, 'wb') as new_file:
                                new_file.write(downloaded_file)
                            
                            print(f"✅ Фото {photo_index} сохранено: {photo_filename}")
                        
                        current_count = len(session['photo_file_ids'])
                        
                        photo_names = ["СПЕРЕДИ", "СПРАВА", "СЛЕВА"]
                        
                        if current_count < 3:
                            self.bot.send_message(
                                chat_id,
                                f"✅ Фото {current_count} ({photo_names[current_count-1]}) получено!\nОтправьте фото {current_count + 1} ({photo_names[current_count]}):"
                            )
                        else:
                            self.bot.send_message(chat_id, "✅ Все 3 фото получены! Создаю заказ...")
                            time.sleep(1)
                            self.finalize_order_with_photos(chat_id)
                            
                    except Exception as e:
                        raise PhotoProcessingError(f"Ошибка обработки фото: {e}") from e
                    finally:
                        session['processing'] = False
                        
            except PhotoProcessingError as e:
                self._handle_photo_error(message.chat.id, str(e))
            except Exception as e:
                self._handle_critical_error(message.chat.id, f"Критическая ошибка обработки фото: {e}")

        # ✅ УНИФИЦИРОВАННЫЙ ОБРАБОТЧИК ДЛЯ ТЕКСТА И ДОКУМЕНТОВ
        @self.bot.message_handler(content_types=['text', 'document'])
        def handle_all_messages(message: types.Message) -> None:
            """УНИФИЦИРОВАННЫЙ ОБРАБОТЧИК для текста и документов"""
            try:
                chat_id = message.chat.id
                print(f"🔍 DEBUG handle_all_messages: получено сообщение от {chat_id}")
                
                # ✅ ПЕРВЫЙ ПРИОРИТЕТ: АДМИН-ПАНЕЛЬ
                if message.content_type == 'document' and hasattr(self, 'admin_panel') and self.admin_panel.is_awaiting_excel(message):
                    print(f"🔍 DEBUG: Админ-панель ожидает Excel документ")
                    await_type = self.admin_panel.awaiting_input_users.get(chat_id, '')
                    print(f"🔍 DEBUG: Тип ожидания: '{await_type}'")
                    
                    if 'add_excel_file:' in await_type:
                        print(f"🔍 DEBUG: Вызываем handle_add_excel_file_sync")
                        self.admin_panel.handle_add_excel_file_sync(message)
                        return
                    elif 'excel_file:' in await_type:
                        print(f"🔍 DEBUG: Вызываем handle_excel_file_sync")
                        self.admin_panel.handle_excel_file_sync(message)
                        return
                
                elif message.content_type == 'text' and hasattr(self, 'admin_panel') and self.admin_panel.is_awaiting_input(message):
                    print(f"🔍 DEBUG: Админ-панель ожидает текстовый ввод")
                    await_type = self.admin_panel.awaiting_input_users.get(chat_id, '')
                    print(f"🔍 DEBUG: Ожидается ввод типа: '{await_type}'")
                
                    # ✅ ОБРАБОТЧИКИ ДЛЯ ШАБЛОНОВ И СПИСКОВ
                    if await_type == 'add_list_name':
                        print(f"🔍 DEBUG: Вызываем handle_add_list_name_sync")
                        self.admin_panel.handle_add_list_name_sync(message)
                        return
                    elif await_type == 'add_template_id':
                        print(f"🔍 DEBUG: Вызываем handle_add_template_id_sync")
                        self.admin_panel.handle_add_template_id_sync(message)
                        return
                    elif await_type.startswith('add_template_name:'):
                        print(f"🔍 DEBUG: Вызываем handle_add_template_name_sync")
                        self.admin_panel.handle_add_template_name_sync(message)
                        return
                    elif await_type.startswith('add_template_company:'):
                        print(f"🔍 DEBUG: Вызываем handle_add_template_company_sync")
                        self.admin_panel.handle_add_template_company_sync(message)
                        return
                    elif await_type.startswith('add_template_address:'):
                        print(f"🔍 DEBUG: Вызываем handle_add_template_address_sync")
                        self.admin_panel.handle_add_template_address_sync(message)
                        return
                    else:
                        print(f"🔍 DEBUG: Неизвестный тип ожидания: '{await_type}'")
                
                # ✅ ВТОРОЙ ПРИОРИТЕТ: ОСНОВНОЙ БОТ
                if message.content_type == 'text':
                    self.process_user_input(message)
                else:
                    print(f"📄 Получен документ не для админ-панели: {message.document.file_name if message.document else 'N/A'}")
                    
            except Exception as e:
                self._handle_critical_error(message.chat.id, f"Ошибка обработки сообщения: {e}")

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call: types.CallbackQuery) -> None:
            try:
                self.handle_button_click(call)
            except Exception as e:
                self._handle_critical_error(call.message.chat.id, f"Ошибка обработки callback: {e}")

    def _handle_photo_error(self, chat_id: int, error_message: str) -> None:
        """Обработка ошибок при работе с фото"""
        try:
            self.bot.send_message(
                chat_id,
                f"❌ Ошибка при обработке фотографии: {error_message}\n\nПожалуйста, попробуйте отправить фото еще раз."
            )
            self.logger.error(f"Ошибка фото в chat_id {chat_id}: {error_message}")
        except Exception as e:
            self.logger.error(f"Не удалось отправить сообщение об ошибке фото: {e}")

    def _handle_critical_error(self, chat_id: int, error_message: str) -> None:
        """Обработка критических ошибок"""
        try:
            self.bot.send_message(
                chat_id,
                f"❌ Произошла ошибка. Попробуйте еще раз.\n\nОшибка: {error_message}"
            )
            self.logger.error(f"Критическая ошибка в chat_id {chat_id}: {error_message}")
        except Exception as e:
            self.logger.error(f"Не удалось отправить сообщение об ошибке: {e}")            

    def show_help(self, chat_id: int) -> None:
        help_text = """
🤖 TruckService Manager - система управления заказ-нарядами

Основные команды:
/start - начать работу с ботом
/new_order - создать новый заказ-наряд
/help - показать эту справку

Для начала работы используйте /start
        """
        self.bot.send_message(chat_id, help_text)

    def show_section_selection(self, chat_id: int) -> None:
        markup = types.InlineKeyboardMarkup()
        
        for section_id, section_data in self.sections.items():
            markup.add(types.InlineKeyboardButton(
                section_data['name'], 
                callback_data=f"section_{section_id}"
            ))
        
        custom_lists = self.admin_panel.get_available_lists()
        print(f"🔍 DEBUG: найдено пользовательских списков: {custom_lists}")
        
        for list_name in custom_lists:
            markup.add(types.InlineKeyboardButton(
                f"📁 {list_name}", 
                callback_data=f"custom_list_{list_name}"
            ))
        
        markup.row(
            types.InlineKeyboardButton("🐛 DEBUG", callback_data="debug_menu"),
            types.InlineKeyboardButton("👨‍💻 АДМИН", callback_data="admin_panel")
        )
        
        debug_status = "🔧 РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН" if DEBUG_MODE else "⚙️ РАБОЧИЙ РЕЖИМ"
        
        lists_info = ""
        if custom_lists:
            lists_info = f"\n\n📂 Доступно списков: {len(custom_lists)}"
            for list_name in custom_lists:
                lists_info += f"\n• {list_name}"
        
        self.bot.send_message(
            chat_id,
            f"🏢 TruckService Manager\n\n{debug_status}\nЗаказы {'НЕ БУДУТ' if DEBUG_MODE else 'БУДУТ'} сохраняться в учет\n\nВыберите раздел работ:{lists_info}",
            reply_markup=markup
        )    
       
    def show_debug_menu(self, chat_id: int) -> None:
        """Показывает меню отладки с тестовыми данными"""
        print(f"🔍 DEBUG: show_debug_menu вызван для chat_id={chat_id}")
        
        try:
            markup = types.InlineKeyboardMarkup()
            
            # Кнопки меню отладки
            markup.row(
                types.InlineKeyboardButton("🧪 ТЕСТ", callback_data="debug_test"),
                types.InlineKeyboardButton("⚙️ Настройки", callback_data="debug_settings")
            )
            markup.row(
                types.InlineKeyboardButton("📊 Переменные", callback_data="debug_variables"),
                types.InlineKeyboardButton("🔄 Автозаполнение", callback_data="debug_autofill")
            )
            markup.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="debug_back")
            )
            
            debug_info = f"""
🐛 МЕНЮ ОТЛАДКИ

Доступные функции:
• 🧪 ТЕСТ - тестовый вызов методов
• ⚙️ Настройки - настройки системы
• 📊 Переменные - просмотр текущих переменных
• 🔄 Автозаполнение - заполнить тестовыми данными
• 🔙 Назад - вернуться к выбору раздела

Режим: {'ВКЛЮЧЕН' if DEBUG_MODE else 'ВЫКЛЮЧЕН'}
            """
            
            print(f"🔍 DEBUG: Пытаюсь отправить сообщение в chat_id={chat_id}")
            self.bot.send_message(chat_id, debug_info, reply_markup=markup)
            print("✅ DEBUG: Меню отладки отправлено успешно")
            
        except Exception as e:
            print(f"❌ Ошибка в show_debug_menu: {e}")
            import traceback
            traceback.print_exc()

    def debug_show_settings(self, chat_id: int) -> None:
        """Показывает настройки системы"""
        settings_text = f"""
⚙️ НАСТРОКИ СИСТЕМЫ

• Режим отладки: {'ВКЛЮЧЕН' if DEBUG_MODE else 'ВЫКЛЮЧЕН'}
• Чат для уведомлений: {self.chat_id}
• Ставка за час: {self.excel_processor.rate_per_hour} руб.
• Версия: 2.0 (модульная)

*Настройки в разработке*
"""
        self.bot.send_message(chat_id, settings_text)

    def debug_show_variables(self, chat_id: int) -> None:
        """Показывает текущие переменные"""
        if chat_id in self.user_sessions:
            session = self.user_sessions[chat_id]
            variables_text = f"""
📊 ПЕРЕМЕННЫЕ СЕССИИ

• Раздел: {session.get('section', 'не выбран')}
• Госномер: {session.get('license_plate', 'не введен')}
• Дата: {session.get('date', 'не введена')}
• Номер ЗН: {session.get('order_number', 'не введен')}
• Исполнители: {session.get('workers', 'не введены')}
• Выбрано работ: {len(session.get('selected_works', []))}
• Выбрано материалов: {len(session.get('selected_materials', []))}
• Текущий шаг: {session.get('step', 'не определен')}
"""
        else:
            variables_text = """
📊 ПЕРЕМЕННЫЕ СЕССИИ

Активная сессия отсутствует
Используйте 🔄 Автозаполнение для теста
"""
        
        self.bot.send_message(chat_id, variables_text)

    # ✅ УПРОЩЕННАЯ ВАЛИДАЦИЯ (ШАГ 3)
    def validate_license_plate(self, text: str) -> bool:
        """УПРОЩЕННАЯ ВАЛИДАЦИЯ ГОСНОМЕРОВ"""
        text = text.upper().strip()
        
        # Очищаем от лишних символов
        text = re.sub(r'[^\w]', '', text)
        
        # Основные российские форматы госномеров
        standard_pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'  # Стандартный
        numeric_pattern = r'^\d{4}[АВЕКМНОРСТУХ]{2}\d{2,3}$'                  # Числовой
        
        return bool(re.match(standard_pattern, text) or re.match(numeric_pattern, text))

    def validate_date(self, text: str) -> Tuple[bool, Union[str, datetime.datetime]]:
        """УЛУЧШЕННАЯ ВАЛИДАЦИЯ ДАТЫ - РАЗРЕШАЕМ ПРОШЛЫЕ ДАТЫ"""
        try:
            date = datetime.datetime.strptime(text, '%d.%m.%Y')
        
            # ✅ РАЗРЕШАЕМ ДАТЫ ИЗ ПРОШЛОГО (для реальных случаев автосервиса)
            # ✅ НО ПРОВЕРЯЕМ, ЧТОБЫ ДАТА БЫЛА НЕ СЛИШКОМ ДАВНЕЙ
            today = datetime.date.today()
            max_past_days = 30  # Максимум 30 дней назад
        
            if date.date() > today + datetime.timedelta(days=365):
                return False, "❌ Дата не может быть больше чем на год вперед"
            
            if date.date() < today - datetime.timedelta(days=max_past_days):
                return False, f"❌ Дата не может быть раньше чем {max_past_days} дней назад"
            
            return True, date
        
        except ValueError:
            return False, "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ"

    def validate_order_number(self, text: str) -> Tuple[bool, Union[str, str]]:
        """УПРОЩЕННАЯ ВАЛИДАЦИЯ НОМЕРА ЗАКАЗА"""
        if text.isdigit() and 1 <= len(text) <= 10:
            return True, text
        return False, "❌ Номер заказ-наряда должен содержать только цифры (1-10 символов)"

    def validate_workers(self, text: str) -> Tuple[bool, Union[str, str]]:
        """УПРОЩЕННАЯ ВАЛИДАЦИЯ ИСПОЛНИТЕЛЕЙ"""
        text = text.strip()
        
        if len(text) < 2:
            return False, "❌ Введите имена исполнителей"
        
        if len(text) > 100:
            return False, "❌ Слишком длинный список (макс. 100 символов)"
        
        # Проверяем что только буквы, запятые, пробелы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s,]+$', text):
            return False, "❌ Недопустимые символы. Используйте только буквы, запятые и пробелы"
        
        # Проверяем что есть хотя бы одно имя
        names = [name.strip() for name in text.split(',') if name.strip()]
        if len(names) < 1:
            return False, "❌ Введите хотя бы одного исполнителя"
        
        return True, text

    def cleanup_session(self, chat_id: int) -> None:
        if chat_id in self.user_sessions:
            del self.user_sessions[chat_id]

    def handle_button_click(self, call: types.CallbackQuery) -> None:
        chat_id = call.message.chat.id
        data = call.data
        
        print(f"🔍 DEBUG: Нажата кнопка с data='{data}', chat_id={chat_id}")

        # ✅ ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ (ВСЕ ВМЕСТЕ В НАЧАЛЕ)
        if data == 'admin_panel':
            self.bot.answer_callback_query(call.id, "Открываю админ-панель...")
            self.admin_panel.show_admin_panel_sync(call)
            return

        if data == 'admin_add_list':
            self.bot.answer_callback_query(call.id, "Добавляем новый список...")
            self.admin_panel.handle_add_list_start_sync(call)
            return

        if data == 'admin_manage_lists':
            self.bot.answer_callback_query(call.id, "Управление списками в разработке...")
            self.bot.send_message(chat_id, "📋 Управление списками - в разработке 🚧")
            return

        if data == 'admin_back':
            self.bot.answer_callback_query(call.id, "Возвращаемся...")
            self.show_section_selection(chat_id)
            return

        # ✅ ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ ШАБЛОНАМИ
        if data == 'admin_manage_templates':
            self.bot.answer_callback_query(call.id, "Управление шаблонами...")
            self.admin_panel.show_templates_management_sync(call)
            return

        if data == 'admin_add_template':
            print(f"🔍 DEBUG: Вызываем handle_add_template_start_sync для admin_add_template")
            self.bot.answer_callback_query(call.id, "Добавляем новый шаблон...")
            self.admin_panel.handle_add_template_start_sync(call)
            return

        if data == 'admin_refresh_templates':
            self.bot.answer_callback_query(call.id, "Обновляем список шаблонов...")
            self.admin_panel.show_templates_management_sync(call)
            return

        if data == 'admin_back_to_main':
            self.bot.answer_callback_query(call.id, "Возвращаемся...")
            self.admin_panel.show_admin_panel_sync(call)
            return

        # ✅ ОБРАБОТЧИКИ ДЛЯ ПРОСМОТРА И УДАЛЕНИЯ ШАБЛОНОВ
        if data.startswith('admin_view_template:'):
            template_id = data.replace('admin_view_template:', '')
            self.bot.answer_callback_query(call.id, "Загружаем информацию о шаблоне...")
            self.admin_panel.handle_view_template_sync(call, template_id)
            return

        if data.startswith('admin_delete_template:'):
            template_id = data.replace('admin_delete_template:', '')
            self.bot.answer_callback_query(call.id, "Удаляем шаблон...")
            self.admin_panel.handle_delete_template_sync(call, template_id)
            return

        if data.startswith('admin_edit_template:'):
            template_id = data.replace('admin_edit_template:', '')
            self.bot.answer_callback_query(call.id, "Редактирование шаблона...")
            self.bot.send_message(chat_id, "✏️ Редактирование шаблонов - в разработке 🚧")
            return

        # ✅ ОБРАБОТЧИК ВЫБОРА ШАПКИ
        if data == 'select_header':
            if chat_id not in self.user_sessions:
                self.bot.answer_callback_query(call.id, "❌ Сессия устарела. Начните с /start")
                return
                
            self.bot.answer_callback_query(call.id, "Выбираем шапку документа...")
            self.ask_header_selection(chat_id)
            return

        # ✅ ОБРАБОТЧИК ВЫБОРА КОНКРЕТНОГО ШАБЛОНА ШАПКИ
        if data.startswith('header_'):
            template_id = data.replace('header_', '')
            
            if chat_id not in self.user_sessions:
                self.bot.answer_callback_query(call.id, "❌ Сессия устарела. Начните с /start")
                return
                
            session = self.user_sessions[chat_id]
            session['header_template'] = template_id
            
            template = self.excel_processor.header_manager.get_template(template_id)
            template_name = template['name'] if template else "Бриджтаун Фудс"
            
            self.bot.answer_callback_query(call.id, f"✅ Выбрано: {template_name}")
            self.show_materials_selection(chat_id)
            return

        # ✅ ОБРАБОТЧИКИ DEBUG МЕНЮ
        if data == 'debug_menu':
            self.bot.answer_callback_query(call.id, "Открываю меню отладки...")
            self.show_debug_menu(chat_id)
            return
        
        elif data == 'debug_back':
            self.bot.answer_callback_query(call.id, "Возвращаюсь...")
            self.show_section_selection(chat_id)
            return
        
        elif data == 'debug_test':
            self.bot.answer_callback_query(call.id, "🧪 Запускаю тест...")
            self.debug_test_function(chat_id)
            return
            
        elif data == 'debug_autofill':
            self.bot.answer_callback_query(call.id, "🔄 Заполняю тестовыми данными...")
            self.debug_autofill(chat_id)
            return

        elif data == 'debug_settings':
            self.bot.answer_callback_query(call.id, "⚙️ Настройки в разработке...")
            self.debug_show_settings(chat_id)
            return

        elif data == 'debug_variables':
            self.bot.answer_callback_query(call.id, "📊 Переменные в разработке...")
            self.debug_show_variables(chat_id)
            return

        # ✅ ОБРАБОТЧИК ПОЛЬЗОВАТЕЛЬСКИХ СПИСКОВ
        elif data.startswith('custom_list_'):
            list_name = data.replace('custom_list_', '')
            print(f"🔍 DEBUG: Обрабатываем список '{list_name}'")
            
            self.bot.answer_callback_query(call.id, f"Выбран список: {list_name}")
            
            works = self.admin_panel.load_works_from_custom_list(list_name)
            
            if works:
                self.user_sessions[chat_id] = {
                    'section': f'custom_{list_name}',
                    'custom_list': list_name,
                    'step': 'license_plate',
                    'selected_works': [],
                    'selected_materials': [],
                    'current_page': 0,
                    'works': works
                }
                
                # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
                materials = self.materials_repository.get_materials()
                self.user_sessions[chat_id]['materials'] = materials
                
                print(f"🔍 DEBUG: Создана сессия для списка '{list_name}'")
                print(f"🔍 DEBUG: Работ в сессии: {len(works)}")
                print(f"🔍 DEBUG: Материалов в сессии: {len(materials)}")
                
                self.bot.send_message(
                    chat_id,
                    f"✅ Выбран список: {list_name}\n"
                    f"📊 Загружено работ: {len(works)}\n\n"
                    f"🏗️ Создание заказ-наряда\n\nВведите госномер автомобиля:\nПример: А123ВС77 или 1234АВ"
                )
            else:
                self.bot.send_message(
                    chat_id,
                    f"❌ В списке '{list_name}' нет работ или файл поврежден"
                )
            return        
        
        # ✅ ОБРАБОТЧИК ВЫБОРА РАЗДЕЛА
        elif data.startswith('section_'):
            section_id = data.split('_')[1]
            if section_id in self.sections:
                self.bot.answer_callback_query(call.id, f"Выбран раздел: {self.sections[section_id]['name']}")
                
                self.user_sessions[chat_id] = {
                    'section': section_id,
                    'step': 'license_plate',
                    'selected_works': [],
                    'selected_materials': [],
                    'current_page': 0
                }
                
                # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
                works = self.works_repository.get_works(section_id)
                if not works:
                    self.bot.send_message(
                        chat_id,
                        "⚠️ Список работ для этого раздела пуст.\nПожалуйста, добавьте работы в файл Excel или обратитесь к администратору."
                    )
                    return
                
                self.user_sessions[chat_id]['works'] = works
                
                section_name = self.sections[section_id]['name']
                self.bot.send_message(
                    chat_id,
                    f"🏗️ {section_name}\n\n📋 Создание нового заказ-наряда\n\nВведите госномер автомобиля:\nПример: А123ВС77 или 1234АВ"
                )
            return
        
        # ✅ ТЕПЕРЬ ПРОВЕРКА СЕССИИ - только для work_, page_, create_order и т.д.
        if chat_id not in self.user_sessions:
            self.bot.answer_callback_query(call.id, "Сессия устарела. Начните с /start")
            return
        
        session = self.user_sessions[chat_id]
        
        if data.startswith('work_'):
            work_index = int(data.split('_')[1])
            works = session.get('works', [])
            if work_index < len(works):
                work = works[work_index]
                
                if work in session['selected_works']:
                    session['selected_works'].remove(work)
                    self.bot.answer_callback_query(call.id, f"❌ Удалено: {work[0]}")
                else:
                    session['selected_works'].append(work)
                    self.bot.answer_callback_query(call.id, f"✅ Добавлено: {work[0]}")
                
                self.update_works_message(call.message, session)
        
        elif data.startswith('material_'):
            material_index = int(data.split('_')[1])
            materials = session.get('materials', [])
            if material_index < len(materials):
                material = materials[material_index]
                
                if material in session['selected_materials']:
                    session['selected_materials'].remove(material)
                    self.bot.answer_callback_query(call.id, f"❌ Удалено: {material}")
                else:
                    session['selected_materials'].append(material)
                    self.bot.answer_callback_query(call.id, f"✅ Добавлено: {material}")
                
                self.update_materials_message(call.message, session)
        
        elif data.startswith('page_'):
            page_type = data.split('_')[1]
            page = int(data.split('_')[2])
            try:
                self.bot.delete_message(chat_id, call.message.message_id)
            except Exception as e:
                print(f"⚠️ Не удалось удалить сообщение: {e}")
            
            if page_type == 'works':
                self.show_works_selection(chat_id, page)
            elif page_type == 'materials':
                self.show_materials_selection(chat_id, page)
        
        elif data == 'reset_works':
            session['selected_works'] = []
            self.bot.answer_callback_query(call.id, "Выбор работ сброшен")
            self.update_works_message(call.message, session)
            
        elif data == 'reset_materials':
            session['selected_materials'] = []
            self.bot.answer_callback_query(call.id, "Выбор материалов сброшен")
            self.update_materials_message(call.message, session)
            
        elif data == 'select_materials':
            self.bot.answer_callback_query(call.id, "Переходим к выбору материалов...")
            self.show_materials_selection(chat_id)
            
        elif data == 'create_order':
            if not session['selected_works']:
                self.bot.answer_callback_query(call.id, "❌ Выберите хотя бы одну работу")
                return
            
            self.bot.answer_callback_query(call.id, "Создаю заказ-наряд...")
            self.ask_about_photos(chat_id)
            
        elif data == 'skip_materials':
            self.bot.answer_callback_query(call.id, "Использую материалы по умолчанию")
            session['selected_materials'] = []
            self.ask_about_photos(chat_id)
            
        elif data == 'add_photos_yes':
            self.bot.answer_callback_query(call.id, "Отлично! Отправьте фото по одному...")
            self.request_photos(chat_id)
            
        elif data == 'add_photos_no':
            self.bot.answer_callback_query(call.id, "Создаю заказ без фото...")
            self._finalize_order_common(chat_id, has_photos=False)            

    def debug_test_function(self, chat_id: int) -> None:
        """Тестовая функция для отладки - тестируем генерацию Excel"""
        try:
            self.bot.send_message(chat_id, "🧪 Запускаю тест генерации Excel...")
            
            # Создаем тестовую сессию с 5 работами и всеми материалами
            test_session = {
                'section': 'base',
                'license_plate': 'ТЕСТ001',
                'date': datetime.datetime.now(),
                'order_number': '999',
                'workers': 'Тестовый Исполнитель',
                'selected_works': [],
                'selected_materials': [],
                'header_template': 'bridge_town'  # ✅ ДОБАВЛЯЕМ ШАБЛОН ШАПКИ
            }
            
            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
            works = self.works_repository.get_works('base')
            if len(works) >= 5:
                test_session['selected_works'] = works[:5]
                works_info = "\n".join([f"• {work[0]} ({work[1]} ч)" for work in works[:5]])
            else:
                test_session['selected_works'] = works
                works_info = "\n".join([f"• {work[0]} ({work[1]} ч)" for work in works])
            
            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
            materials = self.materials_repository.get_materials()
            test_session['selected_materials'] = materials
            materials_info = "\n".join([f"• {material}" for material in materials])
            
            # ✅ ИСПОЛЬЗУЕМ ФАБРИКУ ДОКУМЕНТОВ ДЛЯ СОЗДАНИЯ ТЕСТОВОГО ЗАКАЗА 🆕
            section_folder = self.sections['base']['folder']
            documents = self.document_factory.create_all(test_session, section_folder)
            
            if documents:
                # Отправляем результат теста
                result_text = f"""
🧪 ТЕСТ ГЕНЕРАЦИИ ДОКУМЕНТОВ ВЫПОЛНЕН!

📊 СТРУКТУРА ТЕСТОВОГО ЗАКАЗА:

🏗️ Раздел: {self.sections['base']['name']}
🚗 Госномер: {test_session['license_plate']}
📅 Дата: {test_session['date'].strftime('%d.%m.%Y')}
🔢 Номер ЗН: {test_session['order_number']}
👥 Исполнитель: {test_session['workers']}
🏢 Шаблон шапки: {test_session['header_template']}

📋 РАБОТЫ ({len(test_session['selected_works'])}):
{works_info}

📦 МАТЕРИАЛЫ ({len(test_session['selected_materials'])}):
{materials_info}

💾 Создано документов: {len(documents)}
• Excel: {documents.get('excel', 'не создан')}
• Текст: {documents.get('text', 'не создан')}

✅ Документы созданы успешно через DocumentFactory!
                """
                
                self.bot.send_message(chat_id, result_text)
                
                # Отправляем созданные файлы
                for doc_type, doc_path in documents.items():
                    try:
                        with open(doc_path, 'rb') as doc_file:
                            caption = f"🧪 {doc_type.upper()} документ"
                            self.bot.send_document(chat_id, doc_file, caption=caption)
                    except Exception as e:
                        self.bot.send_message(chat_id, f"⚠️ Не удалось отправить {doc_type} файл: {e}")
                    
            else:
                self.bot.send_message(chat_id, "❌ Ошибка создания документов через фабрику")
            
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка теста: {e}")
            import traceback
            traceback.print_exc()

    def debug_autofill(self, chat_id: int) -> None:
        """Автозаполнение тестовыми данными"""
        try:
            # Создаем тестовую сессию
            self.user_sessions[chat_id] = {
                'section': 'base',
                'step': 'selecting_works',
                'license_plate': 'А333АА33',  # Тестовый госномер
                'date': datetime.datetime.now(),  # Сегодняшняя дата
                'order_number': '333',  # Тестовый номер заказа
                'workers': 'Мордвинов',  # Тестовый исполнитель
                'selected_works': [],
                'selected_materials': [],
                'current_page': 0,
                'header_template': 'bridge_town'  # ✅ ДОБАВЛЯЕМ ШАБЛОН ШАПКИ
            }
            
            session = self.user_sessions[chat_id]
            
            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
            works = self.works_repository.get_works('base')
            session['works'] = works
            
            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
            materials = self.materials_repository.get_materials()
            session['materials'] = materials
            
            # Выбираем первые 5 работ
            if len(works) >= 5:
                session['selected_works'] = works[:5]
                works_info = "\n".join([f"• {work[0]} ({work[1]} ч)" for work in works[:5]])
            else:
                session['selected_works'] = works
                works_info = "\n".join([f"• {work[0]} ({work[1]} ч)" for work in works])
            
            # Выбираем первые 2 материала
            if len(materials) >= 2:
                session['selected_materials'] = materials[:2]
                materials_info = "\n".join([f"• {material}" for material in materials[:2]])
            else:
                session['selected_materials'] = materials
                materials_info = "\n".join([f"• {material}" for material in materials])
            
            # Показываем результат автозаполнения
            result_text = f"""
🔄 АВТОЗАПОЛНЕНИЕ ВЫПОЛНЕНО!

Тестовые данные:
🚗 Госномер: {session['license_plate']}
📅 Дата: {session['date'].strftime('%d.%m.%Y')}
🔢 Номер ЗН: {session['order_number']}
👥 Исполнитель: {session['workers']}
🏗️ Раздел: {self.sections[session['section']]['name']}
🏢 Шаблон шапки: {session['header_template']}

Выбранные работы ({len(session['selected_works'])}):
{works_info}

Выбранные материалы ({len(session['selected_materials'])}):
{materials_info}

Теперь можно создать заказ-наряд!
            """
            
            self.bot.send_message(chat_id, result_text)
            
            # Показываем меню выбора работ с уже выбранными работами
            self.show_works_selection(chat_id)
            
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка автозаполнения: {e}")
            import traceback
            traceback.print_exc()

    def ask_about_photos(self, chat_id: int) -> None:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Да", callback_data="add_photos_yes"),
            types.InlineKeyboardButton("❌ Нет", callback_data="add_photos_no")
        )
        
        self.bot.send_message(
            chat_id,
            "📸 Прикрепить фотографии автомобиля?\n\n• Да - отправить 3 фото по одному (спереди, справа, слева)\n• Нет - отправить заказ без фото",
            reply_markup=markup
        )

    def request_photos(self, chat_id: int) -> None:
        session = self.user_sessions[chat_id]
        session['step'] = 'waiting_photos'
        session['photo_file_ids'] = []
        session['processing'] = False
        
        self.bot.send_message(
            chat_id,
            "📸 Отправьте 3 фото автомобиля ПО ОДНОМУ в порядке:\n\n1. 📷 СПЕРЕДИ\n2. 📷 СПРАВА\n3. 📷 СЛЕВА\n\nОтправьте первое фото (СПЕРЕДИ):"
        )

    def finalize_order_with_photos(self, chat_id: int) -> None:
        self._finalize_order_common(chat_id, has_photos=True)

    # ✅ РАЗДЕЛЕНИЕ _finalize_order_common НА ЧАСТИ (ШАГ 4)
    def _finalize_order_common(self, chat_id: int, has_photos: bool = False) -> None:
        """УЛУЧШЕННАЯ ОБРАБОТКА ЗАВЕРШЕНИЯ ЗАКАЗА - ТЕПЕРЬ С РАЗДЕЛЕНИЕМ"""
        try:
            if not self._validate_session(chat_id):
                return
                
            session = self.user_sessions[chat_id]
            
            if not self._validate_order_data(session, chat_id):
                return
            
            session['order_finalized'] = True
            
            if not self._validate_calculations(session, chat_id):
                return
            
            # ✅ СОЗДАНИЕ ФАЙЛОВ ЧЕРЕЗ ФАБРИКУ ДОКУМЕНТОВ 🆕
            success = self._create_order_files_with_factory(session, chat_id, "ДА" if has_photos else "НЕТ")
            
            if success:
                # ОТПРАВКА В ЧАТ
                self._send_to_work_chat(session, has_photos)
                self._show_order_result(chat_id, session, "прикреплены (3 фото)" if has_photos else "не прикреплены")
            else:
                self.bot.send_message(chat_id, "❌ Не удалось создать файлы заказа")
            
            # ОЧИСТКА СЕССИИ ДАЖЕ ПРИ ОШИБКАХ
            self.cleanup_session(chat_id)
            
        except Exception as e:
            print(f"❌ Критическая ошибка завершения заказа: {e}")
            self.bot.send_message(chat_id, "❌ Произошла ошибка при создании заказа. Попробуйте еще раз.")
            self.cleanup_session(chat_id)

    def _validate_session(self, chat_id: int) -> bool:
        """Проверяет валидность сессии"""
        if chat_id not in self.user_sessions:
            self.bot.send_message(chat_id, "❌ Сессия устарела. Начните с /start")
            return False
            
        session = self.user_sessions[chat_id]
        
        if 'order_finalized' in session and session['order_finalized']:
            self.bot.send_message(chat_id, "✅ Заказ уже создан ранее")
            return False
            
        return True

    def _validate_order_data(self, session: Dict[str, Any], chat_id: int) -> bool:
        """Проверяет обязательные данные заказа"""
        required_fields = ['license_plate', 'date', 'order_number', 'workers', 'selected_works']
        for field in required_fields:
            if field not in session or not session[field]:
                self.bot.send_message(chat_id, f"❌ Отсутствуют данные: {field}")
                return False
        return True

    def _validate_calculations(self, session: Dict[str, Any], chat_id: int) -> bool:
        """Проверяет корректность расчетов сумм"""
        try:
            works_total = sum(hours for _, hours in session['selected_works']) * 2500
            materials_total = 375 + 95 + 210 + 120  # Пока оставляем по умолчанию
            total_amount = works_total + materials_total
            
            if total_amount <= 0:
                raise ValueError("Некорректная сумма заказа")
                
            return True
                
        except Exception as e:
            self.bot.send_message(chat_id, f"❌ Ошибка расчета суммы: {e}")
            return False

    def _send_to_work_chat(self, session: Dict[str, Any], has_photos: bool) -> None:
        """Отправляет заказ в рабочий чат"""
        try:
            # ✅ ИСПОЛЬЗУЕМ ОБЩИЙ МЕТОД ДЛЯ ОТПРАВКИ В ЧАТ
            self._send_order_to_work_chat(session, has_photos)
        except Exception as e:
            print(f"⚠️ Ошибка отправки в чат: {e}")
            # НЕ ПРЕРЫВАЕМ ВЫПОЛНЕНИЕ ИЗ-ЗА ОШИБКИ ОТПРАВКИ

    # ✅ ОБЩИЙ МЕТОД ДЛЯ ОТПРАВКИ В ЧАТ (ШАГ 5)
    def _send_order_to_work_chat(self, session: Dict[str, Any], has_photos: bool) -> None:
        """ОБЩИЙ МЕТОД ДЛЯ ОТПРАВКИ ЗАКАЗА В РАБОЧИЙ ЧАТ - С ФОТО ИЛИ БЕЗ"""
        try:
            # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА
            if session['section'].startswith('custom_'):
                section_name = f"📁 {session['custom_list']}"
            else:
                section_name = self.sections[session['section']]['name']

            selected_count = len(session['selected_works'])
            materials_count = len(session.get('selected_materials', []))
            total_hours = sum(hours for _, hours in session['selected_works'])
            
            # ✅ ПОЛУЧАЕМ ИМЯ ШАБЛОНА ШАПКИ
            template_id = session.get('header_template', 'bridge_town')
            template = self.excel_processor.header_manager.get_template(template_id)
            template_name = template['name'] if template else "Бриджтаун Фудс"
            
            # ОТПРАВКА ФОТО ЕСЛИ ЕСТЬ
            if has_photos:
                photo_file_ids = session.get('photo_file_ids', [])
                if photo_file_ids:
                    print(f"✅ Отправляем {len(photo_file_ids)} фото в чат")
                    
                    media = []
                    for file_id in photo_file_ids[:3]:
                        media.append(types.InputMediaPhoto(file_id))
                    
                    if media:
                        self.bot.send_media_group(self.chat_id, media)
                        print(f"✅ Отправлено {len(media)} фото в чат")
            
            # ОБЩАЯ ИНФОРМАЦИЯ О ЗАКАЗЕ
            text_content = self.create_draft_content(session)
            photo_status = "прикреплены" if has_photos else "не прикреплены"
            
            chat_message = f"""
📋 ЗАКАЗ-НАРЯД №{session.get('order_number', '000')}

{text_content}

🏗️ Раздел: {section_name}
🏢 Шаблон: {template_name}
📊 Работ: {selected_count}
📦 Материалов: {materials_count}
⏱️ Время: {total_hours:.1f} н/ч
📸 Фото: {photo_status}

✅ Создан через @TruckServiceManager_bot
            """
            
            self.bot.send_message(self.chat_id, chat_message)
            print(f"✅ Заказ отправлен в рабочий чат {self.chat_id}, фото: {photo_status}")
            
        except Exception as e:
            print(f"⚠️ Не удалось отправить заказ в чат: {e}")
            raise  # Пробрасываем исключение для обработки в вызывающем коде

    def _create_order_files_with_factory(self, session: Dict[str, Any], chat_id: int, photos_text: str) -> bool:
        """СОЗДАНИЕ ФАЙЛОВ ЧЕРЕЗ ФАБРИКУ ДОКУМЕНТОВ 🆕"""
        try:
            # ✅ ОПРЕДЕЛЯЕМ ПУТЬ ДЛЯ СОХРАНЕНИЯ: стандартный раздел ИЛИ пользовательский список
            if session['section'].startswith('custom_'):
                # Пользовательский список - используем его папку
                list_name = session['custom_list']
                section_folder = pathlib.Path("Пользовательские_списки") / list_name
            else:
                # Стандартный раздел
                section_id = session['section']
                section_folder = self.sections[section_id]['folder']
            
            # ✅ ИСПОЛЬЗУЕМ ФАБРИКУ ДЛЯ СОЗДАНИЯ ВСЕХ ДОКУМЕНТОВ
            documents = self.document_factory.create_all(session, section_folder)
            
            if not documents:
                raise DocumentCreationError("Не удалось создать документы через фабрику")
            
            # Отправляем созданные документы пользователю
            for doc_type, doc_path in documents.items():
                try:
                    with open(doc_path, 'rb') as doc_file:
                        caption = f"📄 {doc_type.upper()} документ"
                        self.bot.send_document(chat_id, doc_file, caption=caption)
                        print(f"✅ {doc_type} документ отправлен пользователю: {doc_path}")
                except Exception as e:
                    print(f"⚠️ Не удалось отправить {doc_type} документ: {e}")
            
            # Сохраняем в учет (используем имя Excel файла для обратной совместимости)
            excel_filename = documents.get('excel', pathlib.Path()).name
            accounting_success = self.accounting_repository.save_order(session, excel_filename, photos_text)
            
            return True
            
        except DocumentCreationError as e:
            print(f"❌ Ошибка создания документов через фабрику: {e}")
            self.bot.send_message(chat_id, f"❌ Ошибка создания документов: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка создания файлов: {e}")
            self.bot.send_message(chat_id, f"❌ Неожиданная ошибка создания файлов: {e}")
            return False

    def _show_order_result(self, chat_id: int, session: Dict[str, Any], photo_status: str) -> None:
        selected_count = len(session['selected_works'])
        materials_count = len(session.get('selected_materials', []))
        total_hours = sum(hours for _, hours in session['selected_works'])

        # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА: стандартный ИЛИ пользовательский
        if session['section'].startswith('custom_'):
            section_name = f"📁 {session['custom_list']}"  # Имя пользовательского списка
        else:
            section_name = self.sections[session['section']]['name']
        
        # ✅ ПОЛУЧАЕМ ИМЯ ШАБЛОНА ШАПКИ
        template_id = session.get('header_template', 'bridge_town')
        template = self.excel_processor.header_manager.get_template(template_id)
        template_name = template['name'] if template else "Бриджтаун Фудс"
        
        result_text = f"""✅ Заказ-наряд успешно создан!

🏗️ {section_name}
🏢 Шаблон: {template_name}

Данные заказа:
🚗 Госномер: {session['license_plate']}
📅 Дата: {session['date'].strftime('%d.%m.%Y')}
🔢 Номер ЗН: {session.get('order_number', '000')}
👥 Исполнители: {session['workers']}

Статистика:
📊 Выбрано работ: {selected_count}
📦 Выбрано материалов: {materials_count}
⏱️ Общее время: {total_hours:.1f} н/ч
📸 Фото: {photo_status}

💬 Заказ отправлен в рабочий чат

Для нового заказа используйте /new_order
        """
        
        self.bot.send_message(chat_id, result_text)

    # ✅ НОВЫЕ МЕТОДЫ ДЛЯ ОБРАБОТКИ ВВОДА (ШАГ 2)

    def process_user_input(self, message: types.Message) -> None:
        """ОСНОВНОЙ ОБРАБОТЧИК ВВОДА ПОЛЬЗОВАТЕЛЯ - ТЕПЕРЬ С РОУТИНГОМ"""
        print(f"🔍 DEBUG process_user_input: получен текст '{message.text}' от {message.chat.id}")
        chat_id = message.chat.id
        
        # 🔧 ПРОВЕРКА АДМИН-ПАНЕЛИ (первый приоритет)
        if hasattr(self, 'admin_panel') and self.admin_panel.is_awaiting_input(message):
            print(f"🔍 DEBUG: Админ-панель ожидает ввод, передаем управление напрямую")
            await_type = self.admin_panel.awaiting_input_users.get(chat_id, '')
            print(f"🔍 DEBUG: Ожидается ввод типа: '{await_type}'")
        
            # ✅ ОБРАБОТЧИКИ ДЛЯ ШАБЛОНОВ И СПИСКОВ
            if await_type == 'add_list_name':
                print(f"🔍 DEBUG: Вызываем handle_add_list_name_sync")
                self.admin_panel.handle_add_list_name_sync(message)
                return
            elif await_type == 'add_template_id':
                print(f"🔍 DEBUG: Вызываем handle_add_template_id_sync")
                self.admin_panel.handle_add_template_id_sync(message)
                return
            elif await_type.startswith('add_template_name:'):
                print(f"🔍 DEBUG: Вызываем handle_add_template_name_sync")
                self.admin_panel.handle_add_template_name_sync(message)
                return
            elif await_type.startswith('add_template_company:'):
                print(f"🔍 DEBUG: Вызываем handle_add_template_company_sync")
                self.admin_panel.handle_add_template_company_sync(message)
                return
            elif await_type.startswith('add_template_address:'):
                print(f"🔍 DEBUG: Вызываем handle_add_template_address_sync")
                self.admin_panel.handle_add_template_address_sync(message)
                return
            else:
                print(f"🔍 DEBUG: Неизвестный тип ожидания: '{await_type}'")
            return
        
        if chat_id not in self.user_sessions:
            self.bot.send_message(chat_id, "Начните с команды /start")
            return
        
        session = self.user_sessions[chat_id]
        current_step = session.get('step')
        
        # ✅ РОУТИНГ ПО ШАГАМ - КАЖДЫЙ ШАГ В СВОЕМ МЕТОДЕ
        step_handlers = {
            'license_plate': self._handle_license_plate_input,
            'date': self._handle_date_input, 
            'order_number': self._handle_order_number_input,
            'workers': self._handle_workers_input
        }
        
        if current_step in step_handlers:
            step_handlers[current_step](message, session)
        else:
            self.bot.send_message(chat_id, "Неизвестный шаг. Начните с /start")

    def _handle_license_plate_input(self, message: types.Message, session: Dict[str, Any]) -> None:
        """Обрабатывает ввод госномера"""
        if self.validate_license_plate(message.text):
            session['license_plate'] = message.text.upper()
            session['step'] = 'date'
            self.ask_date(message.chat.id)
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат госномера!\n\nПримеры корректных номеров:\n• А123ВС77\n• 1234АВ\n• В567ОР177\n\nПопробуйте еще раз:"
            )

    def _handle_date_input(self, message: types.Message, session: Dict[str, Any]) -> None:
        """Обрабатывает ввод даты"""
        is_valid, result = self.validate_date(message.text)
        if is_valid:
            session['date'] = result
            session['step'] = 'order_number'
            self.ask_order_number(message.chat.id)
        else:
            self.bot.send_message(message.chat.id, result)

    def _handle_order_number_input(self, message: types.Message, session: Dict[str, Any]) -> None:
        """Обрабатывает ввод номера заказа"""
        is_valid, result = self.validate_order_number(message.text)
        if is_valid:
            session['order_number'] = result
            session['step'] = 'workers'
            self.ask_workers(message.chat.id)
        else:
            self.bot.send_message(message.chat.id, result)

    def _handle_workers_input(self, message: types.Message, session: Dict[str, Any]) -> None:
        """Обрабатывает ввод исполнителей"""
        is_valid, result = self.validate_workers(message.text)
        if is_valid:
            session['workers'] = result
            session['step'] = 'selecting_works'
            session['current_page'] = 0
            self.show_works_selection(message.chat.id)
        else:
            self.bot.send_message(message.chat.id, result)

    def ask_date(self, chat_id: int) -> None:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        
        today = datetime.date.today()
        dates = [
            today.strftime('%d.%m.%Y'),
            (today + datetime.timedelta(days=1)).strftime('%d.%m.%Y'),
            (today + datetime.timedelta(days=2)).strftime('%d.%m.%Y')
        ]
        
        for date in dates:
            markup.add(date)
            
        self.bot.send_message(
            chat_id,
            "📅 Выберите или введите дату в формате ДД.ММ.ГГГГ:",
            reply_markup=markup
        )

    def ask_order_number(self, chat_id: int) -> None:
        markup = types.ReplyKeyboardRemove()
        self.bot.send_message(
            chat_id,
            "🔢 Введите номер заказ-наряда:\nПример: 575",
            reply_markup=markup
        )

    def ask_workers(self, chat_id: int) -> None:
        self.bot.send_message(
            chat_id,
            "👥 Введите исполнителей (через запятую):\nПример: Иванов, Петров"
        )

    def ask_header_selection(self, chat_id: int) -> None:
        """✅ НОВЫЙ МЕТОД: Запрос выбора шаблона шапки"""
        try:
            templates = self.excel_processor.header_manager.get_available_templates()
            
            if not templates:
                # Если шаблонов нет, используем шапку по умолчанию
                session = self.user_sessions[chat_id]
                session['header_template'] = 'bridge_town'
                self.show_materials_selection(chat_id)
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            for template in templates:
                markup.add(types.InlineKeyboardButton(
                    template['name'],
                    callback_data=f"header_{template['id']}"
                ))
            
            # Кнопка "По умолчанию" для обратной совместимости
            markup.add(types.InlineKeyboardButton(
                "🏢 Бриджтаун Фудс (по умолчанию)",
                callback_data="header_bridge_town"
            ))
            
            self.bot.send_message(
                chat_id,
                "🏢 ВЫБЕРИТЕ ШАБЛОН ШАПКИ ДОКУМЕНТА\n\n"
                "Выберите компанию-заказчика для заказ-наряда:",
                reply_markup=markup
            )
            
        except Exception as e:
            print(f"❌ Ошибка выбора шапки: {e}")
            # При ошибке используем шапку по умолчанию
            session = self.user_sessions[chat_id]
            session['header_template'] = 'bridge_town'
            self.show_materials_selection(chat_id)

    def show_works_selection(self, chat_id: int, page: int = 0) -> None:
        """УЛУЧШЕННЫЙ ИНТЕРФЕКС ВЫБОРА РАБОТ"""
        session = self.user_sessions[chat_id]
        session['current_page'] = page
        
        works = session.get('works', [])
        
        if not works:
            self.bot.send_message(
                chat_id,
                "⚠️ Список работ для этого раздела пуст.\nПожалуйста, добавьте работы в файл Excel или обратитесь к администратору."
            )
            return
        
        # ✅ ИСПОЛЬЗУЕМ КОНСТАНТУ
        start_index = page * self.WORKS_PER_PAGE
        end_index = start_index + self.WORKS_PER_PAGE
        current_works = works[start_index:end_index]
        
        selected_count = len(session['selected_works'])
        total_hours = sum(hours for _, hours in session['selected_works'])
        total_cost = total_hours * 2500
        total_pages = (len(works) + self.WORKS_PER_PAGE - 1) // self.WORKS_PER_PAGE
        
        # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА: стандартный ИЛИ пользовательский
        if session['section'].startswith('custom_'):
            section_name = f"📁 {session['custom_list']}"  # Имя пользовательского списка
        else:
            section_name = self.sections[session['section']]['name']
        
        text = f"🏗️ {section_name}\n\n"
        text += f"📋 Выбор работ (стр. {page + 1}/{total_pages})\n\n"
        text += f"✅ Выбрано: {selected_count} работ\n"
        text += f"⏱️ Время: {total_hours:.1f} н/ч\n"
        text += f"💰 Стоимость работ: {total_cost:,.0f} руб.\n\n"
        text += "🛠️ Выберите работы:\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for i, (name, hours) in enumerate(current_works):
            global_index = start_index + i
            is_selected = (name, hours) in session['selected_works']
            icon = "✅" if is_selected else "⚪"
            cost = hours * 2500
            short_name = name[:35] + "..." if len(name) > 38 else name
            button_text = f"{icon} {short_name} ({hours}ч - {cost:,.0f}р)"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"work_{global_index}"))
        
        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"page_works_{page-1}"))
        
        navigation_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            navigation_buttons.append(types.InlineKeyboardButton("Вперед ▶️", callback_data=f"page_works_{page+1}"))
        
        if navigation_buttons:
            markup.row(*navigation_buttons)
        
        action_buttons = []
        if selected_count > 0:
            # ✅ МЕНЯЕМ КНОПКУ: было "Выбрать материалы" → стало "Выбрать шапку"
            action_buttons.append(types.InlineKeyboardButton("🏢 Выбрать шапку", callback_data="select_header"))
            action_buttons.append(types.InlineKeyboardButton("🔄 Сбросить работы", callback_data="reset_works"))
        else:
            # ✅ МЕНЯЕМ КНОПКУ: было "Продолжить" → стало "Выбрать шапку"  
            action_buttons.append(types.InlineKeyboardButton("🏢 Выбрать шапку", callback_data="select_header"))
        
        markup.row(*action_buttons)
        
        self.bot.send_message(chat_id, text, reply_markup=markup)        

    def show_materials_selection(self, chat_id: int, page: int = 0) -> None:
        """ИНТЕРФЕЙС ВЫБОРА МАТЕРИАЛОВ"""
        session = self.user_sessions[chat_id]
        
        # Загружаем материалы если еще не загружены
        if 'materials' not in session:
            # ✅ ИСПОЛЬЗУЕМ РЕПОЗИТОРИЙ ВМЕСТО СТАРОГО МЕТОДА
            materials = self.materials_repository.get_materials()
            session['materials'] = materials
        else:
            materials = session['materials']
        
        if not materials:
            # Если материалов нет, пропускаем этот шаг
            self.bot.send_message(chat_id, "📦 Список материалов пуст. Переходим к следующему шагу...")
            self.ask_about_photos(chat_id)
            return
        
        session['current_materials_page'] = page
        
        # ✅ ИСПОЛЬЗУЕМ КОНСТАНТУ
        start_index = page * self.MATERIALS_PER_PAGE
        end_index = start_index + self.MATERIALS_PER_PAGE
        current_materials = materials[start_index:end_index]
        
        selected_count = len(session.get('selected_materials', []))
        total_pages = (len(materials) + self.MATERIALS_PER_PAGE - 1) // self.MATERIALS_PER_PAGE
        
        # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА: стандартный ИЛИ пользовательский
        if session['section'].startswith('custom_'):
            section_name = f"📁 {session['custom_list']}"  # Имя пользовательского списка
        else:
            section_name = self.sections[session['section']]['name']
        
        text = f"🏗️ {section_name}\n\n"
        text += f"📦 Выбор материалов (стр. {page + 1}/{total_pages})\n\n"
        text += f"✅ Выбрано: {selected_count} материалов\n\n"
        text += "🎯 Выберите материалы (опционально):\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for i, material_name in enumerate(current_materials):
            global_index = start_index + i
            is_selected = material_name in session.get('selected_materials', [])
            icon = "✅" if is_selected else "⚪"
            short_name = material_name[:35] + "..." if len(material_name) > 38 else material_name
            button_text = f"{icon} {short_name}"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"material_{global_index}"))
        
        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"page_materials_{page-1}"))
        
        navigation_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            navigation_buttons.append(types.InlineKeyboardButton("Вперед ▶️", callback_data=f"page_materials_{page+1}"))
        
        if navigation_buttons:
            markup.row(*navigation_buttons)
        
        action_buttons = []
        if selected_count > 0:
            action_buttons.append(types.InlineKeyboardButton("📸 Далее к фото", callback_data="create_order"))
            action_buttons.append(types.InlineKeyboardButton("🔄 Сбросить материалы", callback_data="reset_materials"))
        else:
            action_buttons.append(types.InlineKeyboardButton("⏭️ Пропустить материалы", callback_data="skip_materials"))
            action_buttons.append(types.InlineKeyboardButton("📸 Далее к фото", callback_data="create_order"))
        
        markup.row(*action_buttons)
        
        self.bot.send_message(chat_id, text, reply_markup=markup)

    def update_works_message(self, message: types.Message, session: Dict[str, Any]) -> None:
        chat_id = message.chat.id
        page = session.get('current_page', 0)
        
        works = session.get('works', [])
        # ✅ ИСПОЛЬЗУЕМ КОНСТАНТУ
        start_index = page * self.WORKS_PER_PAGE
        end_index = start_index + self.WORKS_PER_PAGE
        current_works = works[start_index:end_index]
        
        selected_count = len(session['selected_works'])
        total_hours = sum(hours for _, hours in session['selected_works'])
        total_cost = total_hours * 2500
        total_pages = (len(works) + self.WORKS_PER_PAGE - 1) // self.WORKS_PER_PAGE
        
        # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА: стандартный ИЛИ пользовательский
        if session['section'].startswith('custom_'):
            section_name = f"📁 {session['custom_list']}"  # Имя пользовательского списка
        else:
            section_name = self.sections[session['section']]['name']
        
        text = f"🏗️ {section_name}\n\n"
        text += f"📋 Выбор работ (стр. {page + 1}/{total_pages})\n\n"
        text += f"✅ Выбрано: {selected_count} работ\n"
        text += f"⏱️ Время: {total_hours:.1f} н/ч\n"
        text += f"💰 Стоимость работ: {total_cost:,.0f} руб.\n\n"
        text += "🛠️ Выберите работы:\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for i, (name, hours) in enumerate(current_works):
            global_index = start_index + i
            is_selected = (name, hours) in session['selected_works']
            icon = "✅" if is_selected else "⚪"
            cost = hours * 2500
            short_name = name[:35] + "..." if len(name) > 38 else name
            button_text = f"{icon} {short_name} ({hours}ч - {cost:,.0f}р)"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"work_{global_index}"))
        
        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"page_works_{page-1}"))
        
        navigation_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            navigation_buttons.append(types.InlineKeyboardButton("Вперед ▶️", callback_data=f"page_works_{page+1}"))
        
        if navigation_buttons:
            markup.row(*navigation_buttons)
        
        action_buttons = []
        if selected_count > 0:
            # ✅ МЕНЯЕМ КНОПКУ: было "Выбрать материалы" → стало "Выбрать шапку"
            action_buttons.append(types.InlineKeyboardButton("🏢 Выбрать шапку", callback_data="select_header"))
            action_buttons.append(types.InlineKeyboardButton("🔄 Сбросить работы", callback_data="reset_works"))
        else:
            # ✅ МЕНЯЕМ КНОПКУ: было "Продолжить" → стало "Выбрать шапку"  
            action_buttons.append(types.InlineKeyboardButton("🏢 Выбрать шапку", callback_data="select_header"))
        
        markup.row(*action_buttons)
        
        try:
            self.bot.edit_message_text(text, chat_id, message.message_id, reply_markup=markup)
        except Exception as e:
            if "message is not modified" not in str(e):
                print(f"⚠️ Ошибка обновления сообщения: {e}")

    def update_materials_message(self, message: types.Message, session: Dict[str, Any]) -> None:
        chat_id = message.chat.id
        page = session.get('current_materials_page', 0)
        
        materials = session.get('materials', [])
        # ✅ ИСПОЛЬЗУЕМ КОНСТАНТУ
        start_index = page * self.MATERIALS_PER_PAGE
        end_index = start_index + self.MATERIALS_PER_PAGE
        current_materials = materials[start_index:end_index]
        
        selected_count = len(session.get('selected_materials', []))
        total_pages = (len(materials) + self.MATERIALS_PER_PAGE - 1) // self.MATERIALS_PER_PAGE
        
        # ✅ ОПРЕДЕЛЯЕМ ИМЯ РАЗДЕЛА: стандартный ИЛИ пользовательский
        if session['section'].startswith('custom_'):
            section_name = f"📁 {session['custom_list']}"  # Имя пользовательского списка
        else:
            section_name = self.sections[session['section']]['name']
        
        text = f"🏗️ {section_name}\n\n"
        text += f"📦 Выбор материалов (стр. {page + 1}/{total_pages})\n\n"
        text += f"✅ Выбрано: {selected_count} материалов\n\n"
        text += "🎯 Выберите материалы (опционально):\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for i, material_name in enumerate(current_materials):
            global_index = start_index + i
            is_selected = material_name in session.get('selected_materials', [])
            icon = "✅" if is_selected else "⚪"
            short_name = material_name[:35] + "..." if len(material_name) > 38 else material_name
            button_text = f"{icon} {short_name}"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"material_{global_index}"))
        
        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"page_materials_{page-1}"))
        
        navigation_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            navigation_buttons.append(types.InlineKeyboardButton("Вперед ▶️", callback_data=f"page_materials_{page+1}"))
        
        if navigation_buttons:
            markup.row(*navigation_buttons)
        
        action_buttons = []
        if selected_count > 0:
            action_buttons.append(types.InlineKeyboardButton("📸 Далее к фото", callback_data="create_order"))
            action_buttons.append(types.InlineKeyboardButton("🔄 Сбросить материалы", callback_data="reset_materials"))
        else:
            action_buttons.append(types.InlineKeyboardButton("⏭️ Пропустить материалы", callback_data="skip_materials"))
            action_buttons.append(types.InlineKeyboardButton("📸 Далее к фото", callback_data="create_order"))
        
        markup.row(*action_buttons)
        
        try:
            self.bot.edit_message_text(text, chat_id, message.message_id, reply_markup=markup)
        except Exception as e:
            if "message is not modified" not in str(e):
                print(f"⚠️ Ошибка обновления сообщения: {e}")

    def create_draft_content(self, session: Dict[str, Any]) -> str:
        content = []
        content.append(f"{session['license_plate']} / {session['date'].strftime('%d.%m.%Y')}")
        content.append(session['workers'])
        content.append("")
        
        content.append("РАБОТЫ:")
        for name, hours in session['selected_works']:
            content.append(f"• {name}")
        
        if session.get('selected_materials'):
            content.append("")
            content.append("МАТЕРИАЛЫ:")
            for material in session['selected_materials']:
                content.append(f"• {material}")
        
        return '\n'.join(content)

    def run(self) -> None:
        print("🔄 Запускаю TruckService Manager...")
        try:
            self.bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"⚠️ Перезапуск бота из-за ошибки: {e}")
            self.run()

if __name__ == "__main__":
    if BOT_TOKEN:
        bot = TruckServiceManagerBot(BOT_TOKEN)
        bot.run()
    else:
        print("❌ Токен бота не найден! Создай файл .env с BOT_TOKEN=твой_токен")