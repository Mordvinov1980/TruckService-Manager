# 👨‍💻 DEVELOPMENT GUIDE - РУКОВОДСТВО РАЗРАБОТЧИКА TRUCKSERVICE MANAGER

## 🚀 НАЧАЛО РАБОТЫ

### ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ
- Python 3.8 или выше
- Git
- Telegram Bot Token
- Доступ к OBD2 адаптеру (для разработки диагностики)

### УСТАНОВКА РАЗРАБОЧНОЙ СРЕДЫ
```bash
# Клонирование репозитория
git clone https://github.com/Mordvinov1980/TruckService-Manager.git
cd TruckService_Manager

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка дополнительных dev-зависимостей
pip install pytest black flake8 mypy
НАСТРОЙКА КОНФИГУРАЦИИ
python
# config.py
BOT_TOKEN = "your_telegram_bot_token_here"
ADMIN_IDS = [123456789]  # Ваш Telegram ID
WORK_CHAT_ID = -1001234567890  # ID рабочего чата
DEBUG_MODE = True  # Режим отладки
🏗️ АРХИТЕКТУРА РАЗРАБОТКИ
СТРУКТУРА ПРОЕКТА
text
TruckService_Manager/
├── bot.py                          # Точка входа
├── modules/                        # Основные модули
│   ├── admin_panel.py             # Админ-панель
│   ├── excel_processor.py         # Обработка Excel
│   ├── data_repositories.py       # Репозитории данных
│   ├── document_factory.py        # Фабрика документов
│   ├── vehicle_diagnostics.py     # Модуль диагностики
│   └── diagnostic_repository.py   # Репозиторий диагностики
├── Пользовательские_списки/       # Динамические списки
├── Шаблоны/                       # Шаблоны документов
├── data/                          # Данные диагностики
├── guides/                        # Инструкции
├── utils/                         # Утилиты
└── tests/                         # Тесты
ПАТТЕРНЫ РАЗРАБОТКИ
1. REPOSITORY PATTERN
python
# modules/data_repositories.py
class WorksRepository:
    def __init__(self):
        self.works_data = self._load_works_data()
    
    def get_works_by_section(self, section: str) -> List[str]:
        return self.works_data.get(section, [])
2. FACTORY PATTERN
python
# modules/document_factory.py
class DocumentFactory:
    @staticmethod
    def create_document(doc_type: str, data: Dict) -> Document:
        if doc_type == "excel":
            return ExcelDocument(data)
        elif doc_type == "text":
            return TextDocument(data)
3. MODULAR ARCHITECTURE
Каждый модуль отвечает за одну зону ответственности

Минимальная связность между модулями

Четкие интерфейсы взаимодействия

🔧 РАБОЧИЙ ПРОЦЕСС РАЗРАБОТКИ
ВЕТКИ GIT
master - стабильная версия (только мерж через PR)

production - облачная версия (PythonAnywhere)

feature/* - разработка новых функций

hotfix/* - срочные исправления

docs/* - обновление документации

ПРОЦЕСС РАЗРАБОТКИ НОВОЙ ФУНКЦИИ
bash
# 1. Создание feature ветки
git checkout master
git pull origin master
git checkout -b feature/amazing-feature

# 2. Разработка
# ... пишем код ...

# 3. Тестирование
python -m pytest tests/
python bot.py  # ручное тестирование

# 4. Коммит и пуш
git add .
git commit -m "feat: добавил amazing-feature"
git push origin feature/amazing-feature

# 5. Создание Pull Request на GitHub
СТАНДАРТЫ КОДА
КОДСТАЙЛ
Используйте Black для форматирования

Flake8 для проверки стиля

MyPy для проверки типов

bash
# Автоматическое форматирование
black modules/ bot.py

# Проверка стиля
flake8 modules/ bot.py

# Проверка типов
mypy modules/ bot.py
ДОКУМЕНТИРОВАНИЕ КОДА
python
def calculate_order_total(works: List[str], materials: List[str]) -> float:
    """
    Рассчитывает общую стоимость заказ-наряда.
    
    Args:
        works: Список выбранных работ
        materials: Список выбранных материалов
        
    Returns:
        float: Общая стоимость в рублях
        
    Raises:
        ValueError: Если списки пусты
    """
    if not works and not materials:
        raise ValueError("Не выбраны работы и материалы")
    
    # ... расчет стоимости ...
    return total
🧪 ТЕСТИРОВАНИЕ
ТИПЫ ТЕСТОВ
Unit тесты - тестирование отдельных функций

Интеграционные тесты - тестирование взаимодействия модулей

E2E тесты - тестирование полного потока

СТРУКТУРА ТЕСТОВ
text
tests/
├── unit/
│   ├── test_document_factory.py
│   ├── test_data_repositories.py
│   └── test_vehicle_diagnostics.py
├── integration/
│   ├── test_bot_workflow.py
│   └── test_diagnostic_integration.py
└── conftest.py  # Фикстуры
ПРИМЕР ТЕСТА
python
# tests/unit/test_vehicle_diagnostics.py
import pytest
from modules.vehicle_diagnostics import VehicleDiagnostics

class TestVehicleDiagnostics:
    def test_simulation_mode_connection(self):
        """Тест подключения в режиме эмуляции"""
        diag = VehicleDiagnostics(simulation_mode=True)
        assert diag.connect() == True
        assert diag.is_connected == True
    
    def test_read_vehicle_info_simulation(self):
        """Тест чтения информации об автомобиле в эмуляции"""
        diag = VehicleDiagnostics(simulation_mode=True)
        diag.connect()
        info = diag.get_vehicle_info()
        
        assert "vin" in info
        assert "protocol" in info
        assert info["simulation"] == True
ЗАПУСК ТЕСТОВ
bash
# Все тесты
pytest

# Конкретный файл тестов
pytest tests/unit/test_vehicle_diagnostics.py

# С покрытием кода
pytest --cov=modules

# С подробным выводом
pytest -v
🔌 РАЗРАБОТКА ДИАГНОСТИЧЕСКОГО МОДУЛЯ
РАБОТА С ELM327
python
# Пример разработки новой диагностической функции
from modules.vehicle_diagnostics import VehicleDiagnostics

class EnhancedVehicleDiagnostics(VehicleDiagnostics):
    def read_advanced_parameters(self):
        """Чтение расширенных параметров для грузовиков"""
        if not self.is_connected:
            return {"error": "Нет подключения"}
        
        advanced_data = {}
        # ... реализация чтения специфичных параметров ...
        return advanced_data
РЕЖИМ ЭМУЛЯЦИИ
Используется для разработки без физического адаптера

Возвращает реалистичные тестовые данные

Позволяет тестировать логику обработки

python
# Тестирование с эмуляцией
diag = VehicleDiagnostics(simulation_mode=True)
diag.connect()
data = diag.read_live_data()  # Возвращает тестовые данные
🐛 ОТЛАДКА И ЛОГИРОВАНИЕ
НАСТРОЙКА ЛОГИРОВАНИЯ
python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
ОТЛАДОЧНЫЕ ИНСТРУМЕНТЫ
python
# DEBUG режим в конфигурации
DEBUG_MODE = True

# Логирование важных событий
logger.info("Пользователь начал создание заказ-наряда")
logger.debug(f"Данные заказа: {order_data}")
logger.error("Ошибка подключения к адаптеру", exc_info=True)
📦 ДЕПЛОЙ И РАЗВЕРТЫВАНИЕ
ЛОКАЛЬНЫЙ ДЕПЛОЙ
bash
# Запуск бота
python bot.py

# Запуск с логированием
python bot.py >> bot.log 2>&1 &
ОБЛАЧНЫЙ ДЕПЛОЙ (PythonAnywhere)
Залить код через Git

Установить зависимости

Настроить веб-приложение

Запустить бота через Always-on task

ПРОИЗВОДСТВЕННАЯ КОНФИГУРАЦИЯ
python
# config.py для production
DEBUG_MODE = False
LOG_LEVEL = logging.INFO
ENABLE_DIAGNOSTICS = True  # Включить диагностику
🔄 CI/CD (PLANNED)
GITHUB ACTIONS
yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest
      - run: black --check modules/ bot.py
      - run: flake8 modules/ bot.py
📚 ПОЛЕЗНЫЕ РЕСУРСЫ
ДОКУМЕНТАЦИЯ
Python Telegram Bot

OBD Python Library

Pandas Documentation

ИНСТРУМЕНТЫ
Black - форматирование кода

Flake8 - проверка стиля

Pytest - тестирование

MyPy - проверка типов

🆘 ПОЛУЧЕНИЕ ПОМОЩИ
Создайте Issue на GitHub для багов и предложений

Используйте Discussions для вопросов по разработке

Проверяйте CHANGELOG.md перед обновлениями

Обновлено: 19.10.2025 | Для разработчиков: Python 3.8+