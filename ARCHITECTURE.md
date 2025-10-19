# 🏗️ АРХИТЕКТУРА ПРОЕКТА TRUCKSERVICE MANAGER

## 📐 ОСНОВНЫЕ ПРИНЦИПЫ АРХИТЕКТУРЫ

### 🔧 ПАТТЕРНЫ ПРОЕКТИРОВАНИЯ

#### 1. FACTORY PATTERN
**Назначение**: Создание различных типов документов
**Реализация**: `DocumentFactory` в `modules/document_factory.py`

```python
class DocumentFactory:
    @staticmethod
    def create_excel_document(order_data, template):
        # Создание Excel документа
        pass
    
    @staticmethod
    def create_text_draft(order_data):
        # Создание текстового черновика
        pass
2. REPOSITORY PATTERN
Назначение: Абстракция доступа к данным
Реализация: Классы в modules/data_repositories.py

python
class WorksRepository:
    def get_works_by_section(self, section):
        # Получение работ по разделу
        pass

class MaterialsRepository:
    def get_materials_list(self):
        # Получение списка материалов
        pass
3. MODULAR ARCHITECTURE
Назначение: Разделение ответственности
Структура:

admin_panel.py - управление системой

excel_processor.py - обработка Excel

vehicle_diagnostics.py - диагностика автомобилей

diagnostic_repository.py - хранение диагностических данных

4. UNIFIED HANDLERS
Назначение: Единая обработка сообщений
Реализация: Централизованные обработчики в bot.py

📁 СТРУКТУРА ПРОЕКТА
КОРНЕВАЯ ДИРЕКТОРИЯ
text
TruckService_Manager/
├── bot.py                          # Основной бот (точка входа)
├── config.py                       # Конфигурация (не в репозитории)
├── requirements.txt                # Зависимости Python
├── README.md                       # Основная документация
├── ARCHITECTURE.md                 # Этот файл
├── CHANGELOG.md                    # История изменений
├── DEVELOPMENT.md                  # Руководство разработчика
├── DIAGNOSTICS.md                  # Документация по диагностике
└── API.md                          # API документация
МОДУЛИ (modules/)
text
modules/
├── admin_panel.py                  # Унифицированная админ-панель
├── excel_processor.py              # Обработка Excel с шаблонами
├── data_repositories.py            # Репозитории данных
├── document_factory.py             # Фабрика документов (Factory Pattern)
├── vehicle_diagnostics.py          # Модуль диагностики автомобилей 🆕
└── diagnostic_repository.py        # Репозиторий диагностических данных 🆕
ДАННЫЕ И КОНФИГУРАЦИЯ
text
Пользовательские_списки/            # Динамические списки работ
├── ДВИГАТЕЛЬ.txt
├── ТРАНСМИССИЯ.txt
├── ХОДОВАЯ.txt
└── ЭЛЕКТРИКА.txt

Шаблоны/                           # Шаблоны документов
├── header_templates/              # JSON шаблоны шапок
│   ├── company_a.json
│   ├── company_b.json
│   └── default.json
└── excel_templates/               # Шаблоны Excel (если есть)
ДИАГНОСТИКА И УТИЛИТЫ 🆕
text
data/                              # Данные диагностики
├── diagnostic_sessions.json       # Сессии диагностики
└── vehicle_history/               # История по автомобилям

guides/                            # Инструкции
├── elm327_setup_guide.py         # Настройка ELM327
└── diagnostic_usage.md           # Использование диагностики

utils/                             # Вспомогательные утилиты
├── port_finder.py                # Поиск COM-портов
└── file_helpers.py               # Помощники для работы с файлами
🔄 ПОТОКИ ДАННЫХ
1. СОЗДАНИЕ ЗАКАЗ-НАРЯДА
text
Пользователь → Бот → Выбор раздела → Выбор работ → Выбор материалов 
→ Фото автомобиля → Генерация документов → Отправка в чат
2. ДИАГНОСТИКА АВТОМОБИЛЯ
text
ELM327 → VehicleDiagnostics → DiagnosticRepository 
→ Сохранение сессии → Создание заказ-наряда (опционально)
3. АДМИНИСТРИРОВАНИЕ
text
Админ → Админ-панель → Управление шаблонами 
→ Управление списками → Просмотр статистики
🗃️ ХРАНЕНИЕ ДАННЫХ
ФАЙЛОВАЯ СИСТЕМА
JSON файлы: Конфигурация, шаблоны, диагностические данные

Текстовые файлы: Списки работ, материалы

Excel файлы: Готовые заказ-наряды, база заказов

Изображения: Фото автомобилей

СТРУКТУРА ДАННЫХ
python
# Заказ-наряд
order_data = {
    "vehicle_info": {...},
    "works": [...],
    "materials": [...],
    "photos": [...],
    "timestamps": {...},
    "prices": {...}
}

# Диагностическая сессия
diagnostic_data = {
    "vehicle_info": {...},
    "live_data": {...},
    "dtc_codes": [...],
    "session_info": {...}
}
🔧 ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ
ЯЗЫКИ И ТЕХНОЛОГИИ
Python 3.8+ - основной язык

pyTelegramBotAPI - фреймворк для бота

pandas/openpyxl - работа с Excel

obd - диагностика OBD2

Pillow - обработка изображений

АРХИТЕКТУРНЫЕ ОГРАНИЧЕНИЯ
Однопользовательский режим (расширяемо)

Файловое хранилище (можно мигрировать на БД)

Синхронная обработка (можно перевести на асинхронную)

МАСШТАБИРУЕМОСТЬ
Модульная архитектура позволяет легко добавлять функции

Repository Pattern упрощает смену хранилища данных

Factory Pattern позволяет добавлять новые типы документов

🚀 НАПРАВЛЕНИЯ РАЗВИТИЯ
КРАТКОСРОЧНЫЕ
Веб-интерфейс для администрирования

Поддержка дополнительных диагностических адаптеров

ДОЛГОСРОЧНЫЕ
Миграция на базу данных (PostgreSQL)

REST API для интеграции с другими системами

Мобильное приложение

Обновлено: 19.10.2025 | Версия архитектуры: 2.0