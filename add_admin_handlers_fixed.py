import pathlib

def add_admin_handlers():
    bot_file = pathlib.Path("bot.py")
    content = bot_file.read_text(encoding='utf-8')
    
    # Находим место в handle_button_click для добавления обработчиков админ-панели
    # Ищем после обработчиков debug_menu
    if "elif data == 'debug_menu':" in content:
        # Добавляем обработчики админ-панели после debug_menu
        old_code = '''        elif data == 'debug_menu':
            self.bot.answer_callback_query(call.id, "Открываю меню отладки...")
            self.show_debug_menu(chat_id)
            return'''
        
        new_code = '''        elif data == 'debug_menu':
            self.bot.answer_callback_query(call.id, "Открываю меню отладки...")
            self.show_debug_menu(chat_id)
            return
        
        # 🔧 ОБРАБОТЧИКИ АДМИН-ПАНЕЛИ
        elif data == 'admin_panel':
            self.bot.answer_callback_query(call.id, "Открываю админ-панель...")
            self.admin_panel.show_admin_panel_sync(call)
            return
            
        elif data == 'admin_create_list':
            self.bot.answer_callback_query(call.id, "Создание нового списка...")
            self.admin_panel.create_new_list_start_sync(call)
            return
            
        elif data == 'admin_manage_lists':
            self.bot.answer_callback_query(call.id, "Управление списками...")
            self.bot.send_message(chat_id, "📋 Управление списками - в разработке")
            return
            
        elif data == 'admin_back':
            self.bot.answer_callback_query(call.id, "Возвращаюсь...")
            self.show_section_selection(chat_id)
            return'''
        
        content = content.replace(old_code, new_code)
    
    # Добавляем кнопку админ-панели в show_section_selection
    if 'markup.add(types.InlineKeyboardButton("🐛 DEBUG", callback_data="debug_menu"))' in content:
        old_code = '''        # ✅ ДОБАВЛЯЕМ КНОПКУ DEBUG
        markup.add(types.InlineKeyboardButton("🐛 DEBUG", callback_data="debug_menu"))'''
        
        new_code = '''        # ✅ ДОБАВЛЯЕМ КНОПКИ DEBUG И АДМИН
        markup.row(
            types.InlineKeyboardButton("🐛 DEBUG", callback_data="debug_menu"),
            types.InlineKeyboardButton("👨‍💻 АДМИН", callback_data="admin_panel")
        )'''
        
        content = content.replace(old_code, new_code)
    
    # Добавляем обработку сообщений для админ-панели в process_user_input
    if 'def process_user_input(self, message: types.Message) -> None:' in content:
        # Находим начало функции и добавляем проверку админ-панели
        old_code = '''    def process_user_input(self, message: types.Message) -> None:
        """ОСНОВНОЙ ОБРАБОТЧИК ВВОДА ПОЛЬЗОВАТЕЛЯ - ТЕПЕРЬ С РОУТИНГОМ"""
        chat_id = message.chat.id
        
        if chat_id not in self.user_sessions:
            self.bot.send_message(chat_id, "Начните с команды /start")
            return'''
        
        new_code = '''    def process_user_input(self, message: types.Message) -> None:
        """ОСНОВНОЙ ОБРАБОТЧИК ВВОДА ПОЛЬЗОВАТЕЛЯ - ТЕПЕРЬ С РОУТИНГОМ"""
        chat_id = message.chat.id
        
        # 🔧 ПРОВЕРКА АДМИН-ПАНЕЛИ (первый приоритет)
        if self.admin_panel.is_awaiting_input(message):
            if self.admin_panel.is_awaiting_excel(message):
                self.admin_panel.handle_excel_file_sync(message)
            else:
                self.admin_panel.handle_list_name_sync(message)
            return
        
        if chat_id not in self.user_sessions:
            self.bot.send_message(chat_id, "Начните с команды /start")
            return'''
        
        content = content.replace(old_code, new_code)
    
    bot_file.write_text(content, encoding='utf-8')
    print("✅ Обработчики админ-панели добавлены в bot.py")

if __name__ == "__main__":
    add_admin_handlers()
