# 🔧 DIAGNOSTICS MODULE - ДОКУМЕНТАЦИЯ ПО ДИАГНОСТИКЕ АВТОМОБИЛЕЙ

## 🎯 ОБЗОР МОДУЛЯ ДИАГНОСТИКИ

Модуль диагностики предоставляет возможность подключения к электронным системам автомобилей через OBD2 адаптеры ELM327. Особое внимание уделено поддержке грузовых автомобилей Mercedes Actros MP4.

### ⚡ ОСНОВНЫЕ ВОЗМОЖНОСТИ
- ✅ Подключение ELM327 адаптеров (Bluetooth, Wi-Fi, USB)
- ✅ Чтение VIN номера и базовой информации
- ✅ Мониторинг параметров в реальном времени
- ✅ Чтение и очистка кодов ошибок (DTC)
- ✅ Поддержка протокола J1939 для грузовиков
- ✅ Режим эмуляции для разработки
- ✅ Сохранение диагностических сессий

## 🚀 БЫСТРЫЙ СТАРТ

### ПОДКЛЮЧЕНИЕ АДАПТЕРА
```python
from modules.vehicle_diagnostics import VehicleDiagnostics

# Быстрое подключение (автопоиск)
diag = VehicleDiagnostics()
if diag.connect():
    print("✅ Подключение установлено")
    
    # Чтение базовой информации
    vehicle_info = diag.get_vehicle_info()
    print(f"VIN: {vehicle_info.get('vin')}")
    
    # Данные в реальном времени
    live_data = diag.read_live_data()
    
    # Коды ошибок
    dtc_codes = diag.read_dtc_codes()
РЕЖИМ ЭМУЛЯЦИИ (ДЛЯ РАЗРАБОТКИ)
python
# Работа без физического адаптера
diag = VehicleDiagnostics(simulation_mode=True)
diag.connect()  # Всегда успешно в эмуляции

# Возвращает тестовые данные Mercedes Actros MP4
vehicle_info = diag.get_vehicle_info()  # VIN: WDB9340321L123456
live_data = diag.read_live_data()       # Реалистичные параметры
🔌 ПОДДЕРЖИВАЕМЫЕ АДАПТЕРЫ
ELM327 СОВМЕСТИМЫЕ АДАПТЕРЫ
ELM327 v1.5 - рекомендуемая версия

OBDLink MX+ - профессиональный вариант

Vgate iCar Pro - хорошая альтернатива

Любые клоны ELM327 с Bluetooth/Wi-Fi

ПРОТОКОЛЫ OBD2
ISO 15765-4 (CAN)

ISO 14230-4 (KWP2000)

ISO 9141-2

SAE J1850 PWM/VPW

SAE J1939 - для грузовых автомобилей

📊 ДОСТУПНЫЕ ПАРАМЕТРЫ
БАЗОВЫЕ ПАРАМЕТРЫ OBD2
python
# Всегда доступны через стандарт OBD2
parameters = {
    "rpm": "Обороты двигателя (об/мин)",
    "speed": "Скорость автомобиля (км/ч)",
    "coolant_temp": "Температура охлаждающей жидкости (°C)",
    "engine_load": "Нагрузка двигателя (%)",
    "fuel_pressure": "Давление топлива (бар)",
    "intake_pressure": "Давление во впуске (бар)",
    "maf": "Массовый расход воздуха (г/с)",
    "throttle_pos": "Положение дроссельной заслонки (%)",
    "engine_runtime": "Время работы двигателя (сек)",
    "fuel_level": "Уровень топлива (%)"
}
СПЕЦИФИЧНЫЕ ПАРАМЕТРЫ ДЛЯ ГРУЗОВИКОВ
python
truck_parameters = {
    "engine_hours": "Моточасы (часы)",
    "fuel_rate": "Расход топлива (л/ч)",
    "barometric_pressure": "Атмосферное давление (кПа)",
    "boost_pressure": "Давление наддува (бар)",
    "adblue_level": "Уровень AdBlue (%)",
    "exhaust_temp": "Температура выхлопных газов (°C)",
    "dpf_status": "Статус сажевого фильтра",
    "regeneration_status": "Статус регенерации"
}
🚛 ДИАГНОСТИКА MERCEDES ACTROS MP4
ОСОБЕННОСТИ ACTROS MP4
Протокол: J1939 (CAN)

OBD2 разъем: Стандартный 16-пин

Расположение: В кабине, слева от водителя

Требования: Включенное зажигание

КОДЫ ОШИБОК (DTC) ДЛЯ ACTROS
text
P-коды (Двигатель, трансмиссия):
P0100 - Неисправность цепи расходомера воздуха
P0670 - Неисправность цепи свечи накаливания
P2291 - Давление в Common Rail слишком низкое

C-коды (Шасси):
C1234 - Неисправность датчика ABS
C2345 - Проблема с системой стабилизации

U-коды (Сетевые ошибки):
U0100 - Потеря связи с ECM
U0401 - Недействительные данные от ECM
💻 ИСПОЛЬЗОВАНИЕ API
ОСНОВНОЙ КЛАСС VEHICLEDIAGNOSTICS
python
class VehicleDiagnostics:
    def __init__(self, simulation_mode: bool = False)
    def connect(self, port: str = None) -> bool
    def get_vehicle_info(self) -> Dict
    def read_live_data(self) -> Dict
    def read_truck_specific_data(self) -> Dict
    def read_dtc_codes(self) -> Dict
    def clear_dtc_codes(self) -> Dict
    def check_j1939_support(self) -> bool
    def disconnect(self)
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
ПОЛНАЯ ДИАГНОСТИЧЕСКАЯ СЕССИЯ
python
from modules.vehicle_diagnostics import VehicleDiagnostics
from modules.diagnostic_repository import DiagnosticRepository

def full_diagnostic_scan():
    diag = VehicleDiagnostics()
    repo = DiagnosticRepository()
    
    if diag.connect():
        # Сбор всех данных
        vehicle_info = diag.get_vehicle_info()
        live_data = diag.read_live_data()
        truck_data = diag.read_truck_specific_data()
        dtc_codes = diag.read_dtc_codes()
        j1939_support = diag.check_j1939_support()
        
        # Формирование отчета
        diagnostic_report = {
            "vehicle_info": vehicle_info,
            "live_data": live_data,
            "truck_data": truck_data,
            "dtc_codes": dtc_codes,
            "j1939_support": j1939_support
        }
        
        # Сохранение в репозиторий
        repo.save_diagnostic_session(vehicle_info, diagnostic_report)
        
        diag.disconnect()
        return diagnostic_report
МОНИТОРИНГ В РЕАЛЬНОМ ВРЕМЕНИ
python
def real_time_monitoring(duration_seconds: int = 60):
    diag = VehicleDiagnostics()
    
    if diag.connect():
        print("🚗 Начало мониторинга...")
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            live_data = diag.read_live_data()
            
            # Отображение ключевых параметров
            rpm = live_data['parameters']['rpm']['value']
            speed = live_data['parameters']['speed']['value']
            temp = live_data['parameters']['coolant_temp']['value']
            
            print(f"Обороты: {rpm} | Скорость: {speed} | Температура: {temp}°C")
            time.sleep(1)  # Обновление каждую секунду
        
        diag.disconnect()
💾 СОХРАНЕНИЕ ДАННЫХ
РЕПОЗИТОРИЙ ДИАГНОСТИЧЕСКИХ ДАННЫХ
python
from modules.diagnostic_repository import DiagnosticRepository

repo = DiagnosticRepository()

# Сохранение сессии
repo.save_diagnostic_session(vehicle_info, diagnostic_data)

# Получение истории по VIN
history = repo.get_vehicle_diagnostic_history("WDB9340321L123456")

# Последние сессии
recent_sessions = repo.get_recent_sessions(limit=10)
СТРУКТУРА ДАННЫХ СЕССИИ
json
{
  "session_id": "diag_20251019_143025",
  "timestamp": "2025-10-19T14:30:25",
  "vehicle_info": {
    "vin": "WDB9340321L123456",
    "protocol": "J1939",
    "simulation": false
  },
  "diagnostic_data": {
    "live_data": {
      "parameters": {
        "rpm": {"value": 650, "units": "RPM"},
        "speed": {"value": 0, "units": "km/h"}
      }
    },
    "dtc_codes": {
      "count": 2,
      "codes": ["P0670", "U0100"]
    }
  },
  "has_errors": true
}
🛠️ УТИЛИТЫ И ИНСТРУМЕНТЫ
ПОИСК COM-ПОРТОВ
bash
# Автоматический поиск адаптеров
python utils/port_finder.py
ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ
bash
# Базовый тест
python test_diagnostics.py

# Тест с эмуляцией
python test_diagnostics_with_simulation.py

# Финальный тест с адаптером
python test_final_diagnostics.py
ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ
bash
# Пошаговая инструкция
python guides/elm327_setup_guide.py
🔧 РЕШЕНИЕ ПРОБЛЕМ
ЧАСТЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ
❌ "No OBD-II adapters found"
Причины:

Адаптер не подключен к OBD2 разъему

Зажигание выключено

Проблемы с драйверами Bluetooth

Решение:

python
# Указание порта вручную
diag.connect('COM3')  # Windows
diag.connect('/dev/rfcomm0')  # Linux
❌ "Cannot load commands: No connection to car"
Причины:

Автомобиль не поддерживает запрашиваемые параметры

Проблемы с протоколом связи

Решение:

python
# Проверка поддержки J1939
if diag.check_j1939_support():
    print("✅ J1939 поддерживается")
else:
    print("⚠️ Используется базовый OBD2")
❌ Медленное соединение
Решение:

Используйте Bluetooth 4.0+ адаптеры

Убедитесь в хорошем сигнале

Проверьте другие Bluetooth устройства поблизости

📈 ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ЗАКАЗ-НАРЯДОВ
python
from modules.document_factory import DiagnosticOrderFactory

# Создание заказ-наряда на основе диагностики
def create_order_from_diagnostics(diagnostic_report):
    base_order = {
        "vehicle_info": diagnostic_report["vehicle_info"],
        "works": [],
        "materials": []
    }
    
    # Автоматическое добавление работ по кодам ошибок
    enriched_order = DiagnosticOrderFactory.create_order_from_diagnostics(
        base_order, diagnostic_report
    )
    
    return enriched_order
🚀 РАСШИРЕНИЕ ФУНКЦИОНАЛА
ДОБАВЛЕНИЕ НОВЫХ ПАРАМЕТРОВ
python
class CustomVehicleDiagnostics(VehicleDiagnostics):
    def read_custom_parameters(self):
        """Чтение пользовательских параметров"""
        custom_commands = {
            "custom_param1": obd.commands.CUSTOM_PID_1,
            "custom_param2": obd.commands.CUSTOM_PID_2
        }
        
        custom_data = {}
        for param_name, command in custom_commands.items():
            try:
                response = self.connection.query(command)
                if not response.is_null():
                    custom_data[param_name] = {
                        'value': response.value.magnitude,
                        'units': str(response.value.units)
                    }
            except Exception as e:
                self.logger.warning(f"Не удалось прочитать {param_name}: {e}")
        
        return custom_data
ПОДДЕРЖКА НОВЫХ АДАПТЕРОВ
python
class ProfessionalDiagnosticAdapter:
    """Поддержка профессиональных адаптеров"""
    
    def __init__(self, adapter_type: str):
        self.adapter_type = adapter_type
        
    def connect_professional(self):
        if self.adapter_type == "Jaltest":
            return self._connect_jaltest()
        elif self.adapter_type == "Texa":
            return self._connect_texa()
📞 ПОДДЕРЖКА
Проблемы с подключением: Проверьте guides/elm327_setup_guide.py

Вопросы по API: Смотрите примеры использования выше

Баги и предложения: Создайте Issue на GitHub

Обновлено: 19.10.2025 | Версия диагностики: 1.0 | Статус: 🟢 ГОТОВ К ИСПОЛЬЗОВАНИЮ