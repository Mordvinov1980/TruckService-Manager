import pathlib
import logging
import json
import re  # ✅ ДОБАВЛЯЕМ ДЛЯ ВАЛИДАЦИИ ID ШАБЛОНОВ
from typing import Dict, List, Tuple
from telebot import types

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self, bot_instance=None):
        self.custom_lists_path = pathlib.Path("Пользовательские_списки")
        self.custom_lists_path.mkdir(exist_ok=True)
        self.header_templates_path = pathlib.Path("Шаблоны") / "header_templates"
        self.header_templates_path.mkdir(parents=True, exist_ok=True)
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
        """Обновленная админ-панель с кнопками управления шаблонами"""
        print(f"🔍 DEBUG show_admin_panel_sync: bot={self.bot is not None}")
        if not self.bot:
            print("❌ DEBUG: bot instance not set")
            return
        
        keyboard = [
            [types.InlineKeyboardButton("➕ ДОБАВИТЬ СПИСОК", callback_data="admin_add_list")],
            [types.InlineKeyboardButton("📋 УПРАВЛЕНИЕ СПИСКАМИ", callback_data="admin_manage_lists")],
            [types.InlineKeyboardButton("🏢 УПРАВЛЕНИЕ ШАБЛОНАМИ", callback_data="admin_manage_templates")],
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

    def show_templates_management_sync(self, call):
        """Панель управления шаблонами шапок"""
        if not self.bot:
            return
            
        templates = self._load_header_templates()
        
        keyboard = []
        
        for template_id, template_data in templates.items():
            keyboard.append([
                types.InlineKeyboardButton(
                    f"📄 {template_data['name']}", 
                    callback_data=f"admin_view_template:{template_id}"
                )
            ])
        
        keyboard.append([
            types.InlineKeyboardButton("➕ ДОБАВИТЬ ШАБЛОН", callback_data="admin_add_template"),
            types.InlineKeyboardButton("🔄 ОБНОВИТЬ СПИСОК", callback_data="admin_refresh_templates")
        ])
        keyboard.append([
            types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_back_to_main")
        ])
        
        reply_markup = types.InlineKeyboardMarkup(keyboard)
        
        try:
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🏢 УПРАВЛЕНИЕ ШАБЛОНАМИ ШАПОК\n\nДоступно шаблонов: {len(templates)}\n\nВыберите шаблон для просмотра или действие:",
                reply_markup=reply_markup
            )
        except Exception as e:
            if "message is not modified" not in str(e):
                # Игнорируем ошибку "message is not modified"
                print(f"⚠️ Ошибка обновления сообщения: {e}")

    def _load_header_templates(self) -> Dict[str, Dict]:
        """Загрузка всех шаблонов шапок"""
        templates = {}
        try:
            template_files = list(self.header_templates_path.glob("*.json"))
            for template_file in template_files:
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates[template_data['id']] = template_data
                except Exception as e:
                    print(f"❌ Ошибка загрузки шаблона {template_file}: {e}")
        except Exception as e:
            print(f"❌ Ошибка загрузки шаблонов: {e}")
        
        return templates

    def _save_header_template(self, template_data: Dict) -> bool:
        """Сохранение шаблона шапки"""
        try:
            template_file = self.header_templates_path / f"{template_data['id']}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения шаблона: {e}")
            return False

    def handle_add_template_start_sync(self, call):
        """Начало добавления нового шаблона"""
        print(f"🔍 DEBUG: handle_add_template_start_sync вызван")
        if not self.bot:
            return
            
        chat_id = call.message.chat.id
        print(f"🔍 DEBUG: Устанавливаем awaiting_input_users[{chat_id}] = 'add_template_id'")
        self.awaiting_input_users[chat_id] = 'add_template_id'
        print(f"🔍 DEBUG: awaiting_input_users после установки: {self.awaiting_input_users}")
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🏢 ДОБАВЛЕНИЕ НОВОГО ШАБЛОНА\n\nВведите уникальный ID для шаблона (латинские буквы и цифры):\nПример: company_b, client_123"
        )

    def handle_add_template_id_sync(self, message):
        """Обработка ввода ID шаблона"""
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or self.awaiting_input_users[chat_id] != 'add_template_id':
            return
            
        template_id = message.text.strip().lower()
        
        # Валидация ID
        if not template_id or not re.match(r'^[a-z0-9_]+$', template_id):
            self.bot.send_message(chat_id, "❌ ID шаблона должен содержать только латинские буквы, цифры и подчеркивания")
            return
            
        # Проверяем, не существует ли уже шаблон с таким ID
        templates = self._load_header_templates()
        if template_id in templates:
            self.bot.send_message(chat_id, f"❌ Шаблон с ID '{template_id}' уже существует")
            return
            
        # Сохраняем ID и переходим к вводу названия
        self.awaiting_input_users[chat_id] = f'add_template_name:{template_id}'
        
        self.bot.send_message(
            chat_id,
            f"✅ ID шаблона: {template_id}\n\nТеперь введите название шаблона:\nПример: 🏭 Компания Б, 🏢 Клиент ООО"
        )

    def handle_add_template_name_sync(self, message):
        """Обработка ввода названия шаблона"""
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or not self.awaiting_input_users[chat_id].startswith('add_template_name:'):
            return
            
        # Получаем ID шаблона
        full_status = self.awaiting_input_users[chat_id]
        template_id = full_status.split(':')[1]
        template_name = message.text.strip()
        
        if not template_name or len(template_name) < 2:
            self.bot.send_message(chat_id, "❌ Название шаблона должно содержать минимум 2 символа")
            return
            
        # Сохраняем название и переходим к вводу компании заказчика
        self.awaiting_input_users[chat_id] = f'add_template_company:{template_id}:{template_name}'
        
        self.bot.send_message(
            chat_id,
            f"✅ Название: {template_name}\n\nТеперь введите название компании-заказчика:\nПример: ООО «Компания Б», ЗАО «Клиент ООО»"
        )

    def handle_add_template_company_sync(self, message):
        """Обработка ввода компании заказчика"""
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or not self.awaiting_input_users[chat_id].startswith('add_template_company:'):
            return
            
        # Получаем данные шаблона
        full_status = self.awaiting_input_users[chat_id]
        parts = full_status.split(':')
        template_id = parts[1]
        template_name = parts[2]
        company_name = message.text.strip()
        
        if not company_name or len(company_name) < 2:
            self.bot.send_message(chat_id, "❌ Название компании должно содержать минимум 2 символа")
            return
            
        # Сохраняем компанию и переходим к вводу адреса
        self.awaiting_input_users[chat_id] = f'add_template_address:{template_id}:{template_name}:{company_name}'
        
        self.bot.send_message(
            chat_id,
            f"✅ Компания: {company_name}\n\nТеперь введите адрес компании:\nПример: 600026, г. Владимир, ул. Ленина д. 1"
        )

    def handle_add_template_address_sync(self, message):
        """Обработка ввода адреса и завершение создания шаблона"""
        if not self.bot:
            return
            
        chat_id = message.chat.id
        
        if chat_id not in self.awaiting_input_users or not self.awaiting_input_users[chat_id].startswith('add_template_address:'):
            return
            
        # Получаем данные шаблона
        full_status = self.awaiting_input_users[chat_id]
        parts = full_status.split(':')
        template_id = parts[1]
        template_name = parts[2]
        company_name = parts[3]
        address = message.text.strip()
        
        if not address or len(address) < 5:
            self.bot.send_message(chat_id, "❌ Адрес должен содержать минимум 5 символов")
            return
            
        # Создаем шаблон
        template_data = {
            "id": template_id,
            "name": template_name,
            "customer": {
                "company": company_name,
                "address": address
            },
            "contractor": {
                "company": "ИП Айрапетян Кристина Тиграновна",
                "address": "600033, Владимирская обл., г. Владимир, ул. Сущевская, д. 7, кв. 152",
                "inn": "234206956031",
                "ogrnip": "321332800018501",
                "email": "airanetan93@gmail.com",
                "phone": "+79190130122"
            },
            "default_vehicle": "Грузовой автомобиль"
        }
        
        # Сохраняем шаблон
        success = self._save_header_template(template_data)

        # ✅ ОТЛАДОЧНАЯ ПЕЧАТЬ
        print(f"🔍 DEBUG: Шаблон создан: {success}")
        print(f"🔍 DEBUG: excel_processor доступен: {hasattr(self, 'excel_processor')}")
        if hasattr(self, 'excel_processor'):
            print(f"🔍 DEBUG: header_manager доступен: {hasattr(self.excel_processor, 'header_manager')}")
        
        if success:
            # ✅ ВАЖНО: УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ ИЗ ОЖИДАНИЯ ПЕРВЫМ ДЕЛОМ
            if chat_id in self.awaiting_input_users:
                del self.awaiting_input_users[chat_id]
            
            # ✅ ПЕРЕЗАГРУЗИТЬ ШАБЛОНЫ В ОСНОВНОМ БОТЕ
            if hasattr(self, 'excel_processor'):
                print("🔄 Вызываем reload_templates...")
                self.excel_processor.header_manager.reload_templates()
            
            # ✅ ОТПРАВИТЬ СООБЩЕНИЕ О УСПЕХЕ
            self.bot.send_message(
                chat_id,
                f"✅ Шаблон '{template_name}' успешно создан!\n\n"
                f"🏢 Компания: {company_name}\n"
                f"📍 Адрес: {address}\n\n"
                f"Шаблон теперь доступен при создании заказ-нарядов."
            )
            
            # ✅ ВОЗВРАТ В ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ
            keyboard = [
                [types.InlineKeyboardButton("➕ ДОБАВИТЬ СПИСОК", callback_data="admin_add_list")],
                [types.InlineKeyboardButton("📋 УПРАВЛЕНИЕ СПИСКАМИ", callback_data="admin_manage_lists")],
                [types.InlineKeyboardButton("🏢 УПРАВЛЕНИЕ ШАБЛОНАМИ", callback_data="admin_manage_templates")],
                [types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_back")]
            ]
            reply_markup = types.InlineKeyboardMarkup(keyboard)
            
            self.bot.send_message(
                chat_id,
                "👨‍💻 АДМИН ПАНЕЛЬ\n\nВыберите действие:",
                reply_markup=reply_markup
            )
            
            # ✅ ВАЖНО: ВЕРНУТЬ УПРАВЛЕНИЕ, ЧТОБЫ ИЗБЕЖАТЬ ДАЛЬНЕЙШЕЙ ОБРАБОТКИ
            return

        else:
            self.bot.send_message(chat_id, "❌ Ошибка при создании шаблона")
            del self.awaiting_input_users[chat_id]

    def handle_view_template_sync(self, call, template_id: str):
        """Просмотр информации о шаблоне"""
        if not self.bot:
            return
            
        templates = self._load_header_templates()
        template = templates.get(template_id)
        
        if not template:
            self.bot.answer_callback_query(call.id, "❌ Шаблон не найден")
            return
            
        customer = template['customer']
        contractor = template['contractor']
        
        template_info = f"""
📄 ШАБЛОН: {template['name']}
🆔 ID: {template['id']}

🏢 ЗАКАЗЧИК:
Компания: {customer['company']}
Адрес: {customer['address']}

👤 ИСПОЛНИТЕЛЬ:
{contractor['company']}
ИНН: {contractor['inn']}
ОГРНИП: {contractor['ogrnip']}
Адрес: {contractor['address']}
Телефон: {contractor['phone']}
Email: {contractor['email']}

🚗 Автомобиль по умолчанию: {template.get('default_vehicle', 'Грузовой автомобиль')}
        """
        
        keyboard = [
            [types.InlineKeyboardButton("✏️ РЕДАКТИРОВАТЬ", callback_data=f"admin_edit_template:{template_id}")],
            [types.InlineKeyboardButton("🗑️ УДАЛИТЬ", callback_data=f"admin_delete_template:{template_id}")],
            [types.InlineKeyboardButton("🔙 НАЗАД", callback_data="admin_manage_templates")]
        ]
        
        reply_markup = types.InlineKeyboardMarkup(keyboard)
        
        self.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=template_info,
            reply_markup=reply_markup
        )

    def handle_delete_template_sync(self, call, template_id: str):
        """Удаление шаблона"""
        if not self.bot:
            return
            
        templates = self._load_header_templates()
        template = templates.get(template_id)
        
        if not template:
            self.bot.answer_callback_query(call.id, "❌ Шаблон не найден")
            return

        # Удаляем файл шаблона
        template_file = self.header_templates_path / f"{template_id}.json"
        try:
            template_file.unlink(missing_ok=True)
            
            # ✅ ПЕРЕЗАГРУЗИТЬ ШАБЛОНЫ В ОСНОВНОМ БОТЕ
            if hasattr(self, 'excel_processor'):
                self.excel_processor.header_manager.reload_templates()
            
            self.bot.answer_callback_query(call.id, f"✅ Шаблон '{template['name']}' удален")
            self.show_templates_management_sync(call)

        except Exception as e:
            self.bot.answer_callback_query(call.id, f"❌ Ошибка удаления шаблона: {e}")

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
        application.add_handler(types.CallbackQueryHandler(self.show_admin_panel_sync, func=lambda call: call.data == 'admin_back_to_main'))
        application.add_handler(types.CallbackQueryHandler(self.show_templates_management_sync, func=lambda call: call.data == 'admin_manage_templates'))
        application.add_handler(types.CallbackQueryHandler(self.handle_add_template_start_sync, func=lambda call: call.data == 'admin_add_template'))
        
        # ✅ ОБРАБОТЧИКИ ДЛЯ ПРОСМОТРА И УДАЛЕНИЯ ШАБЛОНОВ
        application.add_handler(types.CallbackQueryHandler(
            lambda call: self.handle_view_template_sync(call, call.data.split(':')[1]), 
            func=lambda call: call.data.startswith('admin_view_template:')
        ))
        application.add_handler(types.CallbackQueryHandler(
            lambda call: self.handle_delete_template_sync(call, call.data.split(':')[1]), 
            func=lambda call: call.data.startswith('admin_delete_template:')
        ))
        
# Инициализация админ-панели
# admin_panel = AdminPanel()