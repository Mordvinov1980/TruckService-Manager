"""
🚀 МЕНЕДЖЕР НАВИГАЦИИ ДЛЯ TRUCKSERVICE MANAGER
ЦЕНТРАЛИЗОВАННОЕ УПРАВЛЕНИЕ МЕНЮ И НАВИГАЦИЕЙ
"""

import telebot
from telebot import types
import logging
from typing import Dict, Any, Optional, List

class NavigationManager:
    """Менеджер навигации для бота"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('NavigationManager')
        self.admin_panel = None
        self.excel_processor = None
        self.sections = {}
        
    def set_dependencies(self, admin_panel, excel_processor):
        """Установка зависимостей"""
        self.admin_panel = admin_panel
        self.excel_processor = excel_processor
    
    def set_sections(self, sections: Dict[str, Any]) -> None:
        """Установка разделов системы"""
        self.sections = sections

    def show_main_menu(self, chat_id: int) -> None:
        """Главное меню"""
        try:
            markup = types.InlineKeyboardMarkup(row_width=2)
            
            buttons = [
                types.InlineKeyboardButton("🚛 СОЗДАТЬ ЗАКАЗ", callback_data="nav:sections_menu"),  # ← ОБЪЕДИНЕННАЯ КНОПКА
                types.InlineKeyboardButton("⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel"),
                types.InlineKeyboardButton("🔧 ДИАГНОСТИКА", callback_data="nav:diagnostics"),
                types.InlineKeyboardButton("📖 ПОМОЩЬ", callback_data="nav:help")
            ]
            
            markup.add(*buttons)
            
            welcome_text = """
🤖 TRUCKSERVICE MANAGER 
Профессиональная система управления автосервисом

Выберите действие:
• 🚛 СОЗДАТЬ ЗАКАЗ - выбор раздела и создание заказ-наряда
• ⚙️ АДМИН-ПАНЕЛЬ - управление системой
• 🔧 ДИАГНОСТИКА - диагностика автомобилей  
• 📖 ПОМОЩЬ - справка по использованию
            """
            
            self.bot.send_message(chat_id, welcome_text, reply_markup=markup)
            
        except Exception as e:
            self.logger.error(f"Ошибка показа главного меню: {e}")
            self.bot.send_message(chat_id, "❌ Ошибка загрузки меню")

    def show_sections_menu(self, chat_id: int) -> None:
        """Единое меню выбора разделов"""
        try:
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # Стандартные разделы
            if self.sections:
                for section_id, section_data in self.sections.items():
                    markup.add(types.InlineKeyboardButton(
                        section_data['name'],
                        callback_data=f"section_{section_id}"
                    ))
            
            # Пользовательские списки
            if self.admin_panel:
                custom_lists = self.admin_panel.get_available_lists()
                for list_name in custom_lists:
                    markup.add(types.InlineKeyboardButton(
                        f"📁 {list_name}",
                        callback_data=f"custom_list_{list_name}"
                    ))
            
            markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="nav:main_menu"))
            
            section_count = len(self.sections) if self.sections else 0
            custom_count = len(self.admin_panel.get_available_lists()) if self.admin_panel else 0
            
            self.bot.send_message(
                chat_id,
                f"🏗️ ВЫБЕРИТЕ РАЗДЕЛ ДЛЯ РАБОТЫ\n\n"
                f"📊 Доступно:\n"
                f"• Стандартные разделы: {section_count}\n"
                f"• Пользовательские списки: {custom_count}\n\n"
                f"Выберите раздел для создания заказ-наряда:",
                reply_markup=markup
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка показа меню разделов: {e}")
            self.bot.send_message(chat_id, "❌ Ошибка загрузки разделов")

    def show_menu(self, chat_id: int, menu_type: str) -> None:
        """Универсальный метод показа меню"""
        if menu_type == 'main_menu':
            self.show_main_menu(chat_id)
        elif menu_type == 'sections_menu':  # ← ЕДИНСТВЕННЫЙ ТИП ДЛЯ РАЗДЕЛОВ
            self.show_sections_menu(chat_id)
        elif menu_type == 'diagnostics':
            self.show_diagnostics_menu(chat_id)
        elif menu_type == 'help':
            self.show_help(chat_id)
        else:
            self.bot.send_message(chat_id, f"❌ Неизвестный тип меню: {menu_type}")
  
    def handle_back(self, chat_id: int) -> None:
        """Обработка кнопки Назад"""
        try:
            self.show_main_menu(chat_id)
        except Exception as e:
            self.logger.error(f"Ошибка обработки назад: {e}")
            self.bot.send_message(chat_id, "❌ Ошибка навигации")

    def show_help(self, chat_id: int) -> None:
        """Показать справку с кнопкой назад"""
        help_text = """
🤖 TruckService Manager - система управления заказ-нарядами

Основные команды:
/start - начать работу с ботом
/new_order - создать новый заказ-наряд
/help - показать эту справку

Для начала работы используйте /start
        """
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 НАЗАД", callback_data="nav:main_menu"))
        
        self.bot.send_message(chat_id, help_text, reply_markup=markup)
    
    def show_diagnostics_menu(self, chat_id: int) -> None:
        """Меню диагностики"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        buttons = [
            types.InlineKeyboardButton("🔍 БЫСТРАЯ ДИАГНОСТИКА", callback_data="diagnostics_quick"),
            types.InlineKeyboardButton("📊 ПОЛНАЯ ДИАГНОСТИКА", callback_data="diagnostics_full"),
            types.InlineKeyboardButton("📈 ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ", callback_data="diagnostics_live"),
            types.InlineKeyboardButton("⚠️ ПРОЧИТАТЬ ОШИБКИ", callback_data="diagnostics_dtc"),
            types.InlineKeyboardButton("🧹 ОЧИСТИТЬ ОШИБКИ", callback_data="diagnostics_clear"),
            types.InlineKeyboardButton("🔙 НАЗАД", callback_data="nav:main_menu")
        ]
        
        markup.add(*buttons)
        
        self.bot.send_message(
            chat_id,
            "🔧 ДИАГНОСТИКА АВТОМОБИЛЕЙ\n\n"
            "Подключение через ELM327 адаптер:\n"
            "• 🔍 Быстрая диагностика - основные параметры\n"
            "• 📊 Полная диагностика - все доступные данные\n"
            "• 📈 Данные в реальном времени - мониторинг\n"
            "• ⚠️ Чтение ошибок - коды неисправностей\n"
            "• 🧹 Очистка ошибок - сброс кодов\n\n"
            "Выберите действие:",
            reply_markup=markup
        )