# Патч для диагностики админ-панели
import pathlib

def patch_bot_init():
    bot_file = pathlib.Path("bot.py")
    
    if not bot_file.exists():
        print("❌ Файл bot.py не найден")
        return False
    
    content = bot_file.read_text(encoding='utf-8')
    
    # Ищем место для вставки логирования после инициализации админ-панели
    if "admin_panel = AdminPanel()" in content:
        # Добавляем логирование после инициализации админ-панели
        old_code = "admin_panel = AdminPanel()"
        new_code = '''admin_panel = AdminPanel()
        
        # 🔍 ДИАГНОСТИКА АДМИН-ПАНЕЛИ (ШАГ 1)
        print(f"🔍 DEBUG: AdminPanel создан, admin_panel.bot = {admin_panel.bot}")
        '''
        
        content = content.replace(old_code, new_code)
        
        # Сохраняем изменения
        bot_file.write_text(content, encoding='utf-8')
        print("✅ Логирование добавлено в bot.py")
        return True
    else:
        print("❌ Не найдена инициализация AdminPanel в bot.py")
        return False

if __name__ == "__main__":
    patch_bot_init()
