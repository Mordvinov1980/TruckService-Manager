"""
🎯 PATCH-ФАЙЛ: ЗАГРУЗКА ФАЙЛОВ РАБОТ - ИСПРАВЛЕННАЯ ВЕРСИЯ
Добавляет функционал загрузки Excel файлов с работами через Telegram
СИСТЕМА ДОБАВЛЕНИЯ РАБОТ (вместо перезаписи)
"""

import pandas as pd
import tempfile
import os
import logging
import time
import shutil
from typing import Dict, Any, List, Tuple
from telebot import types
import pathlib
from datetime import datetime

class FileUploadPatch:
    """ИСПРАВЛЕННЫЙ патч для загрузки файлов с работами - ДОБАВЛЕНИЕ вместо ПЕРЕЗАПИСИ"""
    
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.bot = bot_instance.bot
        self.user_sessions = bot_instance.user_sessions
        self.main_folder = bot_instance.main_folder
        self.sections = bot_instance.sections
        self.logger = logging.getLogger('FileUploadPatch')
        
        # ID администраторов
        self.admin_ids = [1364203895]  # Ваш ID
        
    def apply_patch(self):
        """Применяет патч загрузки файлов"""
        self._patch_bot_menu()
        self._add_handlers()
        self._patch_show_section_selection()
        
        self.logger.info("✅ FileUploadPatch применен успешно")
    
    def _patch_bot_menu(self):
        """Добавляет команду загрузки в меню бота"""
        try:
            new_commands = [
                types.BotCommand("start", "Запустить бота"),
                types.BotCommand("new_order", "Создать новый заказ-наряд"),
                types.BotCommand("upload_works", "📤 Загрузить работы (админ)"),
                types.BotCommand("help", "Помощь по боту")
            ]
            
            self.bot.set_my_commands(new_commands)
            self.logger.info("✅ Меню бота обновлено с загрузкой файлов")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления меню: {e}")
    
    def _add_handlers(self):
        """Добавляет обработчики для загрузки файлов"""
        
        @self.bot.message_handler(commands=['upload_works'])
        def handle_upload_command(message: types.Message):
            """Обработчик команды загрузки работ"""
            chat_id = message.chat.id
            
            if chat_id not in self.admin_ids:
                self.bot.send_message(chat_id, "❌ Эта функция доступна только администраторам")
                return
            
            self.show_upload_menu(chat_id)
        
        @self.bot.message_handler(content_types=['document'])
        def handle_document(message: types.Message):
            """Обработчик загружаемых документов"""
            chat_id = message.chat.id
            
            # Проверяем, ожидаем ли мы загрузку файла
            if (chat_id in self.user_sessions and 
                self.user_sessions[chat_id].get('step') == 'waiting_upload'):
                
                if chat_id not in self.admin_ids:
                    self.bot.send_message(chat_id, "❌ Нет прав для загрузки")
                    return
                
                self.process_uploaded_file(message)
        
        self.logger.info("✅ Обработчики файлов добавлены")
    
    def _patch_show_section_selection(self):
        """Патчим метод show_section_selection для добавления админ-кнопки"""
        original_method = self.bot_instance.show_section_selection
        
        def patched_show_section_selection(chat_id: int):
            """Обновленный выбор раздела с админ-кнопкой"""
            markup = types.InlineKeyboardMarkup()
            
            for section_id, section_data in self.sections.items():
                markup.add(types.InlineKeyboardButton(
                    section_data['name'], 
                    callback_data=f"section_{section_id}"
                ))
            
            if chat_id in self.admin_ids:
                markup.add(types.InlineKeyboardButton("👨‍💻 АДМИН ПАНЕЛЬ", callback_data="admin_panel"))
            
            markup.add(types.InlineKeyboardButton("🐛 DEBUG", callback_data="debug_menu"))
            
            # ✅ ИСПРАВЛЕНИЕ: Используем константу DEBUG_MODE из модуля bot
            from bot import DEBUG_MODE
            debug_status = "🔧 РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН" if DEBUG_MODE else "⚙️ РАБОЧИЙ РЕЖИМ"
            
            self.bot.send_message(
                chat_id,
                f"🏢 TruckService Manager\n\n{debug_status}\nЗаказы {'НЕ БУДУТ' if DEBUG_MODE else 'БУДУТ'} сохраняться в учет\n\nВыберите раздел работ:",
                reply_markup=markup
            )
        
        self.bot_instance.show_section_selection = patched_show_section_selection
        self.logger.info("✅ Метод show_section_selection обновлен")
    
    def show_upload_menu(self, chat_id: int):
        """Показывает меню загрузки файлов"""
        markup = types.InlineKeyboardMarkup()
        
        for section_id, section_data in self.sections.items():
            markup.add(types.InlineKeyboardButton(
                section_data['name'], 
                callback_data=f"upload_section_{section_id}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
        
        self.bot.send_message(
            chat_id,
            "📤 **ЗАГРУЗКА ФАЙЛА РАБОТ**\n\n"
            "Выберите раздел, для которого хотите загрузить работы:\n\n"
            "🔄 **НОВАЯ СИСТЕМА:** Работы ДОБАВЛЯЮТСЯ к существующим\n"
            "📋 **Формат файла:**\n"
            "• Excel файл (.xlsx)\n"  
            "• Столбец A: Название работы\n"
            "• Столбец B: Нормочасы (число)\n"
            "• Первая строка - заголовки\n\n"
            "📝 **Пример:**\n"
            "| Замена фары | 1.5 |\n"
            "| Осмотр ТС   | 0.4 |",
            reply_markup=markup
        )
    
    def process_uploaded_file(self, message: types.Message):
        """Обрабатывает загруженный файл с системой ДОБАВЛЕНИЯ работ"""
        chat_id = message.chat.id
        
        try:
            # Проверяем сессию
            if chat_id not in self.user_sessions:
                self.user_sessions[chat_id] = {}
            
            session = self.user_sessions[chat_id]
            uploaded_section = session.get('upload_section')
            
            if not uploaded_section:
                self.bot.send_message(chat_id, "❌ Ошибка: раздел не выбран. Начните заново.")
                return
            
            # Уведомляем о начале обработки
            processing_msg = self.bot.send_message(chat_id, "📥 Начинаю обработку файла...")
            
            # Скачиваем файл
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сохраняем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                temp_file.write(downloaded_file)
                temp_path = temp_file.name
            
            # Парсим и проверяем файл
            works_data = self.parse_excel_file(temp_path, uploaded_section)
            
            if works_data['valid_count'] == 0:
                os.unlink(temp_path)
                self.bot.edit_message_text(
                    "❌ Не найдено валидных работ в файле. Проверьте формат.",
                    chat_id, processing_msg.message_id
                )
                return
            
            # 🔄 ОСНОВНОЕ ИЗМЕНЕНИЕ: ДОБАВЛЯЕМ работы к существующим
            merge_result = self.merge_works_with_existing(uploaded_section, works_data['works'])
            
            # Сохраняем объединенный файл
            success = self.save_merged_works_file(merge_result['all_works'], uploaded_section)
            
            # Очищаем временный файл
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if not success:
                self.bot.edit_message_text(
                    "❌ Не удалось сохранить файл. Возможно, он открыт в Excel.",
                    chat_id, processing_msg.message_id
                )
                return
            
            # Очищаем кэш для этого раздела
            self.clear_section_cache(uploaded_section)
            
            # ✅ ВОССТАНАВЛИВАЕМ СЕССИЮ ДЛЯ ПРОДОЛЖЕНИЯ РАБОТЫ
            session.update({
                'step': 'selecting_works',
                'section': uploaded_section,  # Сохраняем раздел для создания заказа
                'upload_section': None  # Очищаем флаг загрузки
            })
            
            # Загружаем обновленные работы
            try:
                works = self.bot_instance.load_works_from_excel(uploaded_section, use_cache=False)
                session['works'] = works
            except Exception as e:
                self.logger.error(f"❌ Ошибка загрузки работ после обновления: {e}")
            
            # Отправляем результат с навигацией
            self.send_merge_result_with_navigation(chat_id, works_data, merge_result, uploaded_section)
            
            # Удаляем сообщение о обработке
            self.bot.delete_message(chat_id, processing_msg.message_id)
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка обработки файла: {e}")
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="upload_works_menu"),
                types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
            )
            
            self.bot.send_message(
                chat_id, 
                f"❌ Критическая ошибка обработки файла:\n<code>{str(e)}</code>", 
                parse_mode='HTML',
                reply_markup=markup
            )
    
    def merge_works_with_existing(self, section_id: str, new_works: List[Tuple[str, float]]) -> Dict[str, Any]:
        """🔄 ОСНОВНАЯ ФУНКЦИЯ: Объединяет новые работы с существующими"""
        try:
            section_data = self.sections[section_id]
            works_file = section_data['works_file']
            works_path = self.main_folder / "Шаблоны" / works_file
            
            existing_works = []
            new_count = 0
            duplicate_count = 0
            
            # Загружаем существующие работы, если файл есть
            if works_path.exists():
                try:
                    df_existing = pd.read_excel(works_path)
                    for idx, row in df_existing.iterrows():
                        work_name = str(row.iloc[0]).strip()
                        work_hours = row.iloc[1]
                        
                        if work_name and work_name != 'nan' and pd.notna(work_hours):
                            try:
                                hours = float(work_hours)
                                existing_works.append((work_name, hours))
                            except (ValueError, TypeError):
                                continue
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка чтения существующего файла: {e}")
                    existing_works = []
            
            # Создаем множество для проверки дубликатов (по названию работы)
            existing_names = {name.lower().strip() for name, _ in existing_works}
            
            # Фильтруем новые работы, убираем дубликаты
            unique_new_works = []
            for work_name, hours in new_works:
                if work_name.lower().strip() not in existing_names:
                    unique_new_works.append((work_name, hours))
                    new_count += 1
                    existing_names.add(work_name.lower().strip())  # Добавляем в множество
                else:
                    duplicate_count += 1
            
            # Объединяем списки
            all_works = existing_works + unique_new_works
            
            return {
                'existing_count': len(existing_works),
                'new_count': new_count,
                'duplicate_count': duplicate_count,
                'total_count': len(all_works),
                'all_works': all_works
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка объединения работ: {e}")
            # В случае ошибки возвращаем только новые работы
            return {
                'existing_count': 0,
                'new_count': len(new_works),
                'duplicate_count': 0,
                'total_count': len(new_works),
                'all_works': new_works
            }
    
    def save_merged_works_file(self, works: List[Tuple[str, float]], section_id: str, max_retries: int = 3) -> bool:
        """Сохраняет объединенный список работ с повторными попытками"""
        section_data = self.sections[section_id]
        works_file = section_data['works_file']
        save_path = self.main_folder / "Шаблоны" / works_file
        
        for attempt in range(max_retries):
            try:
                # Создаем папку если нужно
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Создаем DataFrame с объединенными работами
                df = pd.DataFrame(works, columns=['Название работы', 'Нормочасы'])
                
                # Сохраняем в Excel
                df.to_excel(save_path, index=False)
                
                # Создаем backup предыдущей версии
                if attempt == 0 and save_path.exists():
                    backup_path = save_path.parent / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{works_file}"
                    shutil.copy2(save_path, backup_path)
                    self.logger.info(f"✅ Создан backup: {backup_path}")
                
                self.logger.info(f"✅ Объединенный файл работ сохранен: {save_path} (всего работ: {len(works)})")
                return True
                
            except PermissionError:
                if attempt < max_retries - 1:
                    self.logger.warning(f"⚠️ Файл заблокирован, пробую снова через 2 секунды...")
                    time.sleep(2)
                else:
                    self.logger.error(f"❌ Не удалось сохранить файл после {max_retries} попыток")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Ошибка сохранения объединенного файла: {e}")
                return False
        
        return False
    
    def clear_section_cache(self, section_id: str):
        """Очищает кэш для раздела"""
        try:
            cache_file = self.sections[section_id]['folder'] / "cache" / f"{section_id}_works.pkl"
            if cache_file.exists():
                cache_file.unlink()
                self.logger.info(f"✅ Кэш очищен для раздела: {section_id}")
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось очистить кэш: {e}")
    
    def parse_excel_file(self, file_path: str, section_id: str) -> Dict[str, Any]:
        """Парсит Excel файл с работами с улучшенной обработкой ошибок"""
        try:
            df = pd.read_excel(file_path)
            
            if len(df.columns) < 2:
                raise ValueError("Файл должен содержать минимум 2 столбца")
            
            works = []
            valid_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row.iloc[0]) and (len(row) < 2 or pd.isna(row.iloc[1])):
                        continue
                    
                    work_name = str(row.iloc[0]).strip()
                    work_hours = row.iloc[1]
                    
                    # Проверяем название работы
                    if not work_name or work_name == 'nan' or work_name.lower() in ['название', 'работа', 'work']:
                        continue
                    
                    # Проверяем нормочасы
                    if pd.isna(work_hours):
                        errors.append(f"Строка {idx+2}: отсутствуют нормочасы")
                        continue
                    
                    try:
                        hours = float(work_hours)
                        if hours <= 0:
                            errors.append(f"Строка {idx+2}: нормочасы должны быть > 0")
                            continue
                        if hours > 100:  # Разумный лимит
                            errors.append(f"Строка {idx+2}: нормочасы слишком большие (>100)")
                            continue
                    except (ValueError, TypeError):
                        errors.append(f"Строка {idx+2}: неверный формат нормочасов '{work_hours}'")
                        continue
                    
                    works.append((work_name, hours))
                    valid_count += 1
                    
                except Exception as e:
                    errors.append(f"Строка {idx+2}: {str(e)}")
                    continue
            
            return {
                'works': works,
                'valid_count': valid_count,
                'total_rows': len(df),
                'errors': errors
            }
            
        except Exception as e:
            raise ValueError(f"Ошибка чтения Excel файла: {e}")
    
    def send_merge_result_with_navigation(self, chat_id: int, works_data: Dict[str, Any], 
                                        merge_result: Dict[str, Any], section_id: str):
        """Отправляет результат ОБЪЕДИНЕНИЯ работ с кнопками для продолжения работы"""
        section_name = self.sections[section_id]['name']
        
        text = f"📊 <b>РЕЗУЛЬТАТ ОБЪЕДИНЕНИЯ РАБОТ</b>\n\n"
        text += f"🏗️ <b>Раздел:</b> {section_name}\n"
        text += f"📈 <b>Обработано строк:</b> {works_data['total_rows']}\n"
        text += f"✅ <b>Валидных работ в файле:</b> {works_data['valid_count']}\n\n"
        
        text += f"🔄 <b>СТАТИСТИКА ОБЪЕДИНЕНИЯ:</b>\n"
        text += f"• 📁 Было работ: {merge_result['existing_count']}\n"
        text += f"• ➕ Добавлено новых: {merge_result['new_count']}\n"
        text += f"• 🔄 Пропущено дубликатов: {merge_result['duplicate_count']}\n"
        text += f"• 📊 Всего стало: {merge_result['total_count']} работ\n"
        
        if works_data['errors']:
            text += f"\n❌ <b>Ошибки ({len(works_data['errors'])}):</b>\n"
            for error in works_data['errors'][:2]:  # Показываем только первые 2 ошибки
                text += f"• {error}\n"
            if len(works_data['errors']) > 2:
                text += f"• ... и еще {len(works_data['errors']) - 2} ошибок\n"
        
        if merge_result['new_count'] > 0:
            text += f"\n📋 <b>Примеры новых работ:</b>\n"
            new_works_start = merge_result['existing_count']
            for work_name, hours in merge_result['all_works'][new_works_start:new_works_start+3]:
                text += f"• {work_name} ({hours} ч)\n"
        
        text += f"\n🔄 <b>Кэш очищен</b> - новые работы уже доступны!"
        
        # ✅ СОЗДАЕМ КНОПКИ ДЛЯ НЕМЕДЛЕННОГО ПРОДОЛЖЕНИЯ РАБОТЫ
        markup = types.InlineKeyboardMarkup()
        
        # Основные кнопки действий
        markup.row(
            types.InlineKeyboardButton("🚀 Создать заказ", callback_data=f"section_{section_id}"),
            types.InlineKeyboardButton("📤 Еще файл", callback_data="upload_works_menu")
        )
        
        # Кнопки навигации
        markup.row(
            types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            types.InlineKeyboardButton("👨‍💻 Админ панель", callback_data="admin_panel")
        )
        
        self.bot.send_message(
            chat_id, 
            text, 
            parse_mode='HTML',
            reply_markup=markup
        )

def patch_callback_handler(bot_instance):
    """Патчит обработчик callback для админ панели"""
    original_handler = bot_instance.handle_button_click
    
    def patched_handle_button_click(call: types.CallbackQuery):
        """Обновленный обработчик с админ функционалом"""
        chat_id = call.message.chat.id
        data = call.data
        
        # ✅ ОБРАБОТКА АДМИН ПАНЕЛИ
        if data == 'admin_panel':
            bot_instance.bot.answer_callback_query(call.id, "Открываю админ панель...")
            show_admin_panel(bot_instance, chat_id)
            return
        
        # ✅ ОБРАБОТКА КНОПОК АДМИН ПАНЕЛИ
        elif data == 'upload_works_menu':
            bot_instance.bot.answer_callback_query(call.id, "Открываю меню загрузки...")
            temp_patch = FileUploadPatch(bot_instance)
            temp_patch.show_upload_menu(chat_id)
            return
        
        elif data == 'admin_stats':
            bot_instance.bot.answer_callback_query(call.id, "Статистика в разработке...")
            bot_instance.bot.send_message(
                chat_id,
                "📊 <b>СТАТИСТИКА СИСТЕМЫ</b>\n\n"
                "🔄 Функция в разработке\n"
                "Скоро здесь появится:\n"
                "• Количество заказов\n"
                "• Общая выручка\n" 
                "• Статистика по разделам\n"
                "• Популярные работы",
                parse_mode='HTML'
            )
            return
        
        elif data == 'admin_back':
            bot_instance.bot.answer_callback_query(call.id, "Возвращаюсь...")
            bot_instance.show_section_selection(chat_id)
            return
        
        # ✅ ОБРАБОТКА ГЛАВНОГО МЕНЮ
        elif data == 'main_menu':
            bot_instance.bot.answer_callback_query(call.id, "Главное меню...")
            bot_instance.show_section_selection(chat_id)
            return
        
        # ✅ ОБРАБОТКА ВЫБОРА РАЗДЕЛА ДЛЯ ЗАГРУЗКИ
        elif data.startswith('upload_section_'):
            section_id = data.split('_')[2]
            temp_patch = FileUploadPatch(bot_instance)
            
            if chat_id in temp_patch.admin_ids and section_id in bot_instance.sections:
                bot_instance.bot.answer_callback_query(call.id, f"Готов к загрузке для {section_id}")
                
                if chat_id not in bot_instance.user_sessions:
                    bot_instance.user_sessions[chat_id] = {}
                
                # ✅ СОХРАНЯЕМ РАЗДЕЛ В СЕССИИ ДЛЯ ДАЛЬНЕЙШЕЙ РАБОТЫ
                bot_instance.user_sessions[chat_id].update({
                    'step': 'waiting_upload',
                    'upload_section': section_id,
                    'section': section_id  # Сохраняем раздел для будущих заказов
                })
                
                bot_instance.bot.send_message(
                    chat_id,
                    f"📤 <b>ЗАГРУЗКА ДЛЯ {bot_instance.sections[section_id]['name']}</b>\n\n"
                    "Отправьте Excel файл с работами.\n"
                    "🔄 <b>НОВАЯ СИСТЕМА:</b> Работы ДОБАВЛЯЮТСЯ к существующим\n\n"
                    "📋 Формат: Название работы | Нормочасы\n\n"
                    "⏳ Ожидаю файл...",
                    parse_mode='HTML'
                )
                return
        
        # Вызываем оригинальный обработчик для остальных callback
        original_handler(call)
    
    bot_instance.handle_button_click = patched_handle_button_click

def show_admin_panel(bot_instance, chat_id: int):
    """Показывает админ панель"""
    markup = types.InlineKeyboardMarkup()
    
    markup.add(types.InlineKeyboardButton("📤 Загрузить работы", callback_data="upload_works_menu"))
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    bot_instance.bot.send_message(
        chat_id,
        "👨‍💻 <b>АДМИН ПАНЕЛЬ</b>\n\n"
        "Доступные функции:\n"
        "• 📤 <b>Загрузить работы</b> - ДОБАВЛЕНИЕ к существующим\n"
        "• 📊 Статистика - в разработке",
        reply_markup=markup,
        parse_mode='HTML'
    )