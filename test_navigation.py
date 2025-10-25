# test_navigation.py - для проверки новой навигации
"""
🧪 ТЕСТ НОВОЙ СИСТЕМЫ НАВИГАЦИИ
Запуск: python test_navigation.py
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_navigation_structure():
    """Проверка структуры новой навигации"""
    print("🧪 ТЕСТ СТРУКТУРЫ НАВИГАЦИИ")
    print("=" * 50)
    
    try:
        # Проверяем импорты
        from modules.navigation_manager import NavigationManager, NavigationState
        
        print("✅ Модуль navigation_manager импортирован успешно")
        
        # Тестируем класс NavigationState
        state = NavigationState()
        state.current_menu = 'main_menu'
        state.previous_menus = ['settings']
        
        assert state.current_menu == 'main_menu'
        assert 'settings' in state.previous_menus
        print("✅ Класс NavigationState работает корректно")
        
        # Тестируем карту меню
        expected_menus = ['main_menu', 'quick_order', 'my_lists', 'settings', 'help']
        manager = NavigationManager(None)  # bot=None для теста
        
        for menu in expected_menus:
            assert menu in manager.menu_handlers, f"Меню {menu} отсутствует в обработчиках"
        
        print("✅ Все ожидаемые меню присутствуют в системе")
        print("✅ Базовая структура навигации готова к использованию!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    success = test_navigation_structure()
    if success:
        print("\n🎉 ТЕСТ ПРОЙДЕН! Можно запускать бота с новой навигацией.")
    else:
        print("\n💥 ТЕСТ НЕ ПРОЙДЕН! Проверьте структуру файлов.")