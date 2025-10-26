# 🔌 API DOCUMENTATION - ДОКУМЕНТАЦИЯ API TRUCKSERVICE MANAGER

## 🎯 ОБЗОР API

TRUCKSERVICE MANAGER предоставляет программные интерфейсы для интеграции с внешними системами и расширения функциональности.

### 📋 ДОСТУПНЫЕ API
- **Telegram Bot API** - взаимодействие с пользователем
- **Diagnostics API** - работа с диагностикой автомобилей  
- **Data Repository API** - доступ к данным системы
- **Document Factory API** - генерация документов

## 🤖 TELEGRAM BOT API

### ОСНОВНЫЕ КОМАНДЫ БОТА

#### 📋 КОМАНДЫ ПОЛЬЗОВАТЕЛЯ
```python
# Создание заказ-наряда
"/start" - Главное меню
"Создать заказ-наряд" - Начало создания документа
"Админ-панель" - Доступ к управлению системой
"Диагностика автомобиля" - Запуск диагностического модуля
⚙️ КОМАНДЫ АДМИНИСТРАТОРА
python
# Управление системой
"Управление шаблонами" - CRUD операции с шаблонами
"Управление списками" - Редактирование списков работ
"Просмотр статистики" - Аналитика и отчеты
"Настройки системы" - Конфигурация бота
ОБРАБОТЧИКИ СООБЩЕНИЙ
ТЕКСТОВЫЕ СООБЩЕНИЯ
python
@bot.message_handler(func=lambda message: message.text == "Создать заказ-наряд")
def handle_order_creation(message):
    """
    Обработчик начала создания заказ-наряда.
    
    Args:
        message: Объект сообщения Telegram
        
    Flow:
        1. Запрос раздела работ
        2. Выбор конкретных работ
        3. Выбор материалов
        4. Загрузка фото
        5. Генерация документов
    """
    user_id = message.from_user.id
    # ... логика создания заказа ...
ОБРАБОТКА ДОКУМЕНТОВ
python
@bot.message_handler(content_types=['document'])
def handle_document(message):
    """
    Обработка загруженных документов (шаблонов, списков).
    
    Supported formats:
        - .json (шаблоны документов)
        - .txt (списки работ)
        - .xlsx (Excel шаблоны)
    """
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    # ... обработка документа ...
ОБРАБОТКА ФОТОГРАФИЙ
python
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """
    Обработка фотографий автомобиля.
    
    Requirements:
        - 3 фотографии (спереди, справа, слева)
        - Минимальное качество: 800x600
        - Форматы: JPEG, PNG
        
    Storage:
        - Сохраняются в папку заказа
        - Прикрепляются к документам
    """
    photos = message.photo
    # ... обработка и сохранение фото ...
🔧 DIAGNOSTICS API
VEHICLEDIAGNOSTICS CLASS
КОНСТРУКТОР
python
VehicleDiagnostics(simulation_mode: bool = False)
"""
Инициализация диагностического модуля.

Args:
    simulation_mode: Режим эмуляции для разработки
    
Attributes:
    connection: OBD соединение
    is_connected: Статус подключения
    logger: Логгер модуля
"""
МЕТОДЫ ПОДКЛЮЧЕНИЯ
python
def connect(self, port: str = None) -> bool
"""
Подключение к OBD2 адаптеру.

Args:
    port: COM-порт для подключения (опционально)
    
Returns:
    bool: True если подключение успешно
    
Raises:
    ConnectionError: При невозможности подключения
    
Example:
    >>> diag = VehicleDiagnostics()
    >>> diag.connect()  # Автопоиск
    True
    >>> diag.connect('COM3')  # Ручное указание порта
    True
"""
ЧТЕНИЕ ДАННЫХ
python
def get_vehicle_info(self) -> Dict[str, Any]
"""
Получение базовой информации об автомобиле.

Returns:
    Dict: {
        "vin": "WDB9340321L123456",
        "protocol": "J1939", 
        "timestamp": "2025-10-19T14:30:25",
        "simulation": false
    }
    
Example:
    >>> info = diag.get_vehicle_info()
    >>> print(info["vin"])
    WDB9340321L123456
"""

def read_live_data(self) -> Dict[str, Any]
"""
Чтение параметров в реальном времени.

Returns:
    Dict: {
        "timestamp": "2025-10-19T14:30:25",
        "parameters": {
            "rpm": {"value": 650, "units": "RPM"},
            "speed": {"value": 0, "units": "km/h"}
        }
    }
"""

def read_dtc_codes(self) -> Dict[str, Any]
"""
Чтение кодов ошибок (DTC).

Returns:
    Dict: {
        "count": 2,
        "codes": ["P0670", "U0100"],
        "timestamp": "2025-10-19T14:30:25"
    }
"""
СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ
python
def read_truck_specific_data(self) -> Dict[str, Any]
"""
Чтение специфичных параметров для грузовиков.

Returns:
    Dict с параметрами: engine_hours, fuel_rate, etc.
"""

def check_j1939_support(self) -> bool
"""
Проверка поддержки протокола J1939.

Returns:
    bool: True если протокол поддерживается
"""

def clear_dtc_codes(self) -> Dict[str, Any]
"""
Очистка кодов ошибок.

Returns:
    Dict: {"success": True, "message": "Коды очищены"}
"""
📊 DATA REPOSITORY API
WORKSREPOSITORY
python
class WorksRepository:
    def get_works_by_section(self, section: str) -> List[str]
    """
    Получение списка работ по разделу.
    
    Args:
        section: Раздел работ (ДВИГАТЕЛЬ, ТРАНСМИССИЯ, etc.)
        
    Returns:
        List[str]: Список работ
        
    Example:
        >>> repo = WorksRepository()
        >>> works = repo.get_works_by_section("ДВИГАТЕЛЬ")
        >>> print(works[:2])
        ['Замена масла двигателя', 'Замена воздушного фильтра']
    """
    
    def get_available_sections(self) -> List[str]
    """
    Получение доступных разделов работ.
    """
MATERIALSREPOSITORY
python
class MaterialsRepository:
    def get_materials_list(self) -> List[str]
    """
    Получение списка доступных материалов.
    """
    
    def get_material_price(self, material: str) -> float
    """
    Получение цены материала.
    """
DIAGNOSTICREPOSITORY
python
class DiagnosticRepository:
    def save_diagnostic_session(self, vehicle_info: Dict, diagnostic_data: Dict) -> bool
    """
    Сохранение диагностической сессии.
    
    Args:
        vehicle_info: Информация об автомобиле
        diagnostic_data: Данные диагностики
        
    Returns:
        bool: True если сохранение успешно
    """
    
    def get_vehicle_diagnostic_history(self, vin: str) -> List[Dict]
    """
    Получение истории диагностики по VIN.
    """
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]
    """
    Получение последних сессий диагностики.
    """
📄 DOCUMENT FACTORY API
DOCUMENTFACTORY CLASS
python
class DocumentFactory:
    @staticmethod
    def create_excel_document(order_data: Dict, template: Dict) -> str
    """
    Создание Excel документа заказ-наряда.
    
    Args:
        order_data: Данные заказа
        template: Шаблон документа
        
    Returns:
        str: Путь к созданному файлу
        
    Example:
        >>> excel_path = DocumentFactory.create_excel_document(order_data, template)
        >>> print(excel_path)
        'заказы/заказ_наряд_20251019_143025.xlsx'
    """
    
    @staticmethod
    def create_text_draft(order_data: Dict) -> str
    """
    Создание текстового черновика.
    
    Returns:
        str: Текст черновика
    """
DIAGNOSTICORDERFACTORY
python
class DiagnosticOrderFactory:
    @staticmethod
    def create_order_from_diagnostics(base_order: Dict, diagnostic_report: Dict) -> Dict
    """
    Создание заказ-наряда на основе диагностики.
    
    Args:
        base_order: Базовые данные заказа
        diagnostic_report: Отчет диагностики
        
    Returns:
        Dict: Обогащенный заказ-наряд с предложенными работами
    """
    
    @staticmethod
    def _suggest_works_by_dtc(dtc_codes: List[str]) -> List[str]
    """
    Предложение работ на основе кодов ошибок.
    """
🔌 INTEGRATION EXAMPLES
ИНТЕГРАЦИЯ С ВНЕШНЕЙ СИСТЕМОЙ
python
import requests
from modules.vehicle_diagnostics import VehicleDiagnostics

class ExternalSystemIntegration:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.diagnostics = VehicleDiagnostics()
    
    def sync_vehicle_data(self):
        """Синхронизация данных автомобиля с внешней системой"""
        if self.diagnostics.connect():
            vehicle_info = self.diagnostics.get_vehicle_info()
            diagnostic_data = {
                "vehicle_info": vehicle_info,
                "live_data": self.diagnostics.read_live_data(),
                "dtc_codes": self.diagnostics.read_dtc_codes()
            }
            
            # Отправка во внешнюю систему
            response = requests.post(
                f"{self.api_url}/vehicles/sync",
                json=diagnostic_data,
                headers={"Content-Type": "application/json"}
            )
            
            return response.json()
СОЗДАНИЕ КАСТОМНОГО ОБРАБОТЧИКА
python
from telebot import TeleBot
from modules.data_repositories import WorksRepository

class CustomOrderHandler:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.works_repo = WorksRepository()
    
    def register_handlers(self):
        """Регистрация кастомных обработчиков"""
        
        @self.bot.message_handler(func=lambda m: m.text == "Быстрый заказ")
        def handle_quick_order(message):
            """Обработчик быстрого создания заказа"""
            user_id = message.from_user.id
            
            # Автоматический выбор популярных работ
            popular_works = self._get_popular_works()
            
            # Создание заказа без дополнительных вопросов
            order_data = {
                "user_id": user_id,
                "works": popular_works,
                "materials": self._get_default_materials(),
                "quick_order": True
            }
            
            # Генерация документа
            document_path = DocumentFactory.create_excel_document(order_data)
            
            # Отправка пользователю
            with open(document_path, 'rb') as doc:
                self.bot.send_document(message.chat.id, doc)
🧪 TESTING API
ТЕСТИРОВАНИЕ МОДУЛЕЙ
python
import pytest
from modules.vehicle_diagnostics import VehicleDiagnostics

class TestVehicleDiagnosticsAPI:
    def test_connection_api(self):
        """Тест API подключения"""
        diag = VehicleDiagnostics(simulation_mode=True)
        assert diag.connect() == True
        assert diag.is_connected == True
    
    def test_vehicle_info_api(self):
        """Тест API получения информации"""
        diag = VehicleDiagnostics(simulation_mode=True)
        diag.connect()
        info = diag.get_vehicle_info()
        
        assert "vin" in info
        assert "protocol" in info
        assert isinstance(info["vin"], str)
ИНТЕГРАЦИОННЫЕ ТЕСТЫ
python
class TestIntegrationAPI:
    def test_diagnostic_to_order_flow(self):
        """Тест полного потока от диагностики до заказ-наряда"""
        # Диагностика
        diag = VehicleDiagnostics(simulation_mode=True)
        diag.connect()
        diagnostic_report = {
            "vehicle_info": diag.get_vehicle_info(),
            "dtc_codes": diag.read_dtc_codes()
        }
        
        # Создание заказа
        base_order = {"works": [], "materials": []}
        final_order = DiagnosticOrderFactory.create_order_from_diagnostics(
            base_order, diagnostic_report
        )
        
        assert "diagnostic_data" in final_order
        assert "suggested_works" in final_order
📝 ERROR HANDLING
СТАНДАРТНЫЕ ОШИБКИ И ИХ ОБРАБОТКА
DIAGNOSTICS ERRORS
python
try:
    diag = VehicleDiagnostics()
    if not diag.connect():
        raise ConnectionError("Не удалось подключиться к адаптеру")
    
    data = diag.read_live_data()
    
except ConnectionError as e:
    logger.error(f"Ошибка подключения: {e}")
    return {"error": "connection_failed", "message": str(e)}
    
except Exception as e:
    logger.error(f"Неожиданная ошибка: {e}")
    return {"error": "unexpected_error", "message": str(e)}
DATA VALIDATION ERRORS
python
def validate_order_data(order_data: Dict) -> bool:
    """Валидация данных заказа"""
    required_fields = ["works", "vehicle_info", "materials"]
    
    for field in required_fields:
        if field not in order_data:
            raise ValueError(f"Отсутствует обязательное поле: {field}")
    
    if not order_data["works"]:
        raise ValueError("Список работ не может быть пустым")
    
    return True
🔐 SECURITY API
ПРОВЕРКА ПРАВ ДОСТУПА
python
def admin_required(func):
    """Декоратор для проверки прав администратора"""
    def wrapper(message):
        user_id = message.from_user.id
        if user_id not in config.ADMIN_IDS:
            bot.reply_to(message, "❌ Доступ запрещен")
            return
        
        return func(message)
    return wrapper

@bot.message_handler(func=lambda m: m.text == "Админ-панель")
@admin_required
def handle_admin_panel(message):
    """Обработчик админ-панели (только для админов)"""
    # ... логика админ-панели ...
ВАЛИДАЦИЯ ВХОДНЫХ ДАННЫХ
python
def sanitize_user_input(text: str) -> str:
    """Очистка пользовательского ввода"""
    import html
    return html.escape(text.strip())

def validate_file_upload(file_path: str, allowed_extensions: List[str]) -> bool:
    """Проверка загружаемых файлов"""
    extension = file_path.split('.')[-1].lower()
    return extension in allowed_extensions
📞 SUPPORT AND CONTRIBUTION
СООБЩЕНИЕ ОБ ОШИБКАХ
При обнаружении ошибок в API:

Проверьте актуальность документации

Создайте Issue на GitHub с примером кода

Укажите версию системы и параметры окружения

ПРЕДЛОЖЕНИЯ ПО РАСШИРЕНИЮ API
Для предложений новых методов API:

Опишите use-case

Предложите сигнатуру метода

Укажите ожидаемое поведение

Обновлено: 19.10.2025 | Версия API: 2.5 | Статус: 🟢 STABLE