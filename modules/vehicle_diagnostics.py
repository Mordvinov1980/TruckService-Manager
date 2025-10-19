# modules/vehicle_diagnostics.py
import obd
import logging
from typing import Dict, List, Optional
from datetime import datetime

class VehicleDiagnostics:
    """Основной класс для диагностики автомобилей через ELM327"""
    
    def __init__(self, simulation_mode: bool = False):
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.simulation_mode = simulation_mode
        self.simulation_data = self._get_simulation_data()
    
    def _get_simulation_data(self) -> Dict:
        """Данные для режима эмуляции (Actros MP4)"""
        return {
            "vin": "WDB9340321L123456",
            "protocol": "J1939",
            "live_data": {
                "rpm": 650,
                "speed": 0,
                "coolant_temp": 85,
                "engine_load": 45.5,
                "fuel_pressure": 4.8,
                "intake_pressure": 1.2,
                "maf": 12.3,
                "throttle_pos": 0.0,
                "engine_runtime": 1250,
                "fuel_level": 75.5
            },
            "dtc_codes": ["P0670", "U0100"]
        }
    
    def _get_units_for_param(self, param_name: str) -> str:
        """Получение единиц измерения для параметра"""
        units_map = {
            'rpm': 'RPM',
            'speed': 'km/h',
            'coolant_temp': '°C',
            'engine_load': '%',
            'fuel_pressure': 'bar',
            'intake_pressure': 'bar',
            'maf': 'g/s',
            'throttle_pos': '%',
            'engine_runtime': 's',
            'fuel_level': '%'
        }
        return units_map.get(param_name, 'N/A')
    
    def connect(self, port: str = None) -> bool:
        """
        Подключение к ELM327 адаптеру
        port: COM порт (например: 'COM3' на Windows)
        """
        if self.simulation_mode:
            self.is_connected = True
            self.logger.info("🔧 РЕЖИМ ЭМУЛЯЦИИ АКТИВИРОВАН (Actros MP4)")
            return True
        
        try:
            self.logger.info("Попытка подключения к ELM327...")
            
            if port:
                self.connection = obd.OBD(portstr=port)
            else:
                # Автоматическое подключение
                self.connection = obd.OBD()
            
            self.is_connected = self.connection.is_connected()
            
            if self.is_connected:
                self.logger.info("✅ Успешное подключение к ELM327")
                protocol = self.connection.protocol_name()
                self.logger.info(f"📡 Используемый протокол: {protocol}")
            else:
                self.logger.warning("❌ Не удалось подключиться к ELM327")
                
            return self.is_connected
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения: {e}")
            self.is_connected = False
            return False
    
    def get_vehicle_info(self) -> Dict:
        """Получение базовой информации об автомобиле"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        if self.simulation_mode:
            return {
                "vin": self.simulation_data["vin"],
                "protocol": self.simulation_data["protocol"],
                "timestamp": datetime.now().isoformat(),
                "simulation": True
            }
        
        info = {
            "timestamp": datetime.now().isoformat(),
            "vin": "N/A",
            "protocol": self.connection.protocol_name() if self.connection else "N/A",
            "simulation": False
        }
        
        # Чтение VIN
        try:
            response = self.connection.query(obd.commands.VIN)
            if not response.is_null():
                info["vin"] = str(response.value)
        except Exception as e:
            self.logger.warning(f"Не удалось прочитать VIN: {e}")
        
        return info
    
    def read_live_data(self) -> Dict:
        """Чтение данных в реальном времени"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        if self.simulation_mode:
            simulated_data = {
                "timestamp": datetime.now().isoformat(),
                "parameters": {},
                "simulation": True
            }
            
            for param_name, value in self.simulation_data["live_data"].items():
                simulated_data["parameters"][param_name] = {
                    'value': value,
                    'units': self._get_units_for_param(param_name)
                }
            
            return simulated_data
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "parameters": {},
            "simulation": False
        }
        
        # Основные параметры для грузовиков
        commands = {
            "rpm": obd.commands.RPM,
            "speed": obd.commands.SPEED,
            "coolant_temp": obd.commands.COOLANT_TEMP,
            "engine_load": obd.commands.ENGINE_LOAD,
            "fuel_pressure": obd.commands.FUEL_PRESSURE,
            "intake_pressure": obd.commands.INTAKE_PRESSURE,
            "maf": obd.commands.MAF,
            "throttle_pos": obd.commands.THROTTLE_POS,
            "engine_runtime": obd.commands.RUN_TIME,
            "fuel_level": obd.commands.FUEL_LEVEL
        }
        
        for param_name, command in commands.items():
            try:
                response = self.connection.query(command)
                if not response.is_null():
                    data["parameters"][param_name] = {
                        'value': float(response.value.magnitude),
                        'units': str(response.value.units)
                    }
            except Exception as e:
                self.logger.debug(f"Не удалось прочитать {param_name}: {e}")
        
        return data
    
    def read_truck_specific_data(self) -> Dict:
        """Чтение специфичных параметров для грузовиков"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        if self.simulation_mode:
            return {
                "engine_hours": {"value": 2450.5, "units": "hours"},
                "fuel_rate": {"value": 12.8, "units": "L/h"},
                "barometric_pressure": {"value": 101.3, "units": "kPa"},
                "boost_pressure": {"value": 2.1, "units": "bar"},
                "simulation": True
            }
        
        truck_data = {
            "simulation": False
        }
        
        # Параметры специфичные для грузовиков
        truck_commands = {
            "engine_hours": obd.commands.RUN_TIME,
            "fuel_rate": obd.commands.FUEL_RATE,
            "barometric_pressure": obd.commands.BAROMETRIC_PRESSURE,
            "boost_pressure": obd.commands.INTAKE_PRESSURE,
        }
        
        for param_name, command in truck_commands.items():
            try:
                response = self.connection.query(command)
                if not response.is_null():
                    truck_data[param_name] = {
                        'value': float(response.value.magnitude),
                        'units': str(response.value.units)
                    }
            except Exception as e:
                self.logger.debug(f"Не удалось прочитать {param_name}: {e}")
        
        return truck_data
    
    def check_j1939_support(self) -> bool:
        """Проверка поддержки протокола J1939 для грузовиков"""
        if not self.is_connected:
            return False
        
        if self.simulation_mode:
            return True
        
        protocol = self.connection.protocol_name()
        j1939_protocols = ['J1939', 'CAN', 'ISO 15765']
        
        return any(proto in protocol for proto in j1939_protocols)
    
    def read_dtc_codes(self) -> Dict:
        """Чтение и расшифровка кодов ошибок"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        if self.simulation_mode:
            return {
                "count": len(self.simulation_data["dtc_codes"]),
                "codes": self.simulation_data["dtc_codes"],
                "timestamp": datetime.now().isoformat(),
                "simulation": True
            }
        
        try:
            response = self.connection.query(obd.commands.GET_DTC)
            if not response.is_null():
                dtc_codes = response.value
                return {
                    "count": len(dtc_codes),
                    "codes": dtc_codes,
                    "timestamp": datetime.now().isoformat(),
                    "simulation": False
                }
            return {
                "count": 0, 
                "codes": [], 
                "timestamp": datetime.now().isoformat(),
                "simulation": False
            }
        except Exception as e:
            self.logger.error(f"Ошибка чтения DTC: {e}")
            return {"error": str(e)}
    
    def clear_dtc_codes(self) -> Dict:
        """Очистка кодов ошибок"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        if self.simulation_mode:
            self.simulation_data["dtc_codes"] = []
            return {
                "success": True,
                "message": "Коды ошибок очищены (симуляция)",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            response = self.connection.query(obd.commands.CLEAR_DTC)
            success = not response.is_null()
            return {
                "success": success,
                "message": "Коды ошибок очищены" if success else "Не удалось очистить коды ошибок",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Ошибка очистки DTC: {e}")
            return {"error": str(e)}
    
    def disconnect(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            self.logger.info("🔌 Соединение с ELM327 закрыто")
        elif self.simulation_mode:
            self.is_connected = False
            self.logger.info("🔌 Режим эмуляции завершен")

# Тестовые функции
def test_diagnostics():
    """Функция для тестирования диагностики"""
    print("🧪 ТЕСТИРОВАНИЕ ДИАГНОСТИЧЕСКОГО МОДУЛЯ")
    print("=" * 50)
    
    diag = VehicleDiagnostics()
    
    if diag.connect():
        print("✅ Подключение к ELM327 установлено")
        
        # Базовая информация
        vehicle_info = diag.get_vehicle_info()
        print(f"🚗 VIN: {vehicle_info.get('vin')}")
        print(f"📡 Протокол: {vehicle_info.get('protocol')}")
        
        # Данные в реальном времени
        live_data = diag.read_live_data()
        print("\n📊 ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ:")
        for param, value_data in live_data.get("parameters", {}).items():
            print(f"   {param}: {value_data['value']} {value_data['units']}")
        
        # Коды ошибок
        dtc_info = diag.read_dtc_codes()
        if "codes" in dtc_info and dtc_info["codes"]:
            print(f"\n⚠️  НАЙДЕНЫ КОДЫ ОШИБОК ({dtc_info['count']}):")
            for code in dtc_info["codes"]:
                print(f"   {code}")
        else:
            print("\n✅ Коды ошибок не найдены")
        
        # Закрываем соединение
        diag.disconnect()
        print("\n🔌 Тестирование завершено")
    else:
        print("❌ Не удалось подключиться к ELM327")
        print("💡 Проверьте:")
        print("   - Подключен ли адаптер к OBD2 разъему")
        print("   - Включено ли зажигание")
        print("   - Сопряжен ли адаптер с компьютером")

def test_simulation_mode():
    """Тестирование режима эмуляции"""
    print("🔧 ТЕСТИРОВАНИЕ РЕЖИМА ЭМУЛЯЦИИ")
    print("=" * 45)
    
    diag = VehicleDiagnostics(simulation_mode=True)
    
    if diag.connect():
        print("✅ Режим эмуляции активирован")
        
        # Базовая информация
        vehicle_info = diag.get_vehicle_info()
        print(f"🚗 VIN: {vehicle_info.get('vin')}")
        print(f"📡 Протокол: {vehicle_info.get('protocol')}")
        
        # Данные в реальном времени
        live_data = diag.read_live_data()
        print("\n📊 ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ:")
        for param, value_data in live_data.get("parameters", {}).items():
            print(f"   {param}: {value_data['value']} {value_data['units']}")
        
        # Специфичные данные грузовика
        truck_data = diag.read_truck_specific_data()
        print("\n🚛 СПЕЦИФИЧНЫЕ ДАННЫЕ ГРУЗОВИКА:")
        for param, value_data in truck_data.items():
            if param != 'simulation':
                print(f"   {param}: {value_data['value']} {value_data['units']}")
        
        # Коды ошибок
        dtc_info = diag.read_dtc_codes()
        if dtc_info.get('count', 0) > 0:
            print(f"\n⚠️  НАЙДЕНЫ КОДЫ ОШИБОК ({dtc_info['count']}):")
            for code in dtc_info["codes"]:
                print(f"   {code}")
        
        # Проверка J1939
        j1939_support = diag.check_j1939_support()
        print(f"\n🔌 Поддержка J1939: {'✅ ДА' if j1939_support else '❌ НЕТ'}")
        
        # Очистка ошибок
        clear_result = diag.clear_dtc_codes()
        print(f"\n🧹 Очистка ошибок: {clear_result.get('message')}")
        
        # Проверяем, что ошибки очистились
        dtc_after_clear = diag.read_dtc_codes()
        print(f"📋 Ошибок после очистки: {dtc_after_clear.get('count', 0)}")
        
        diag.disconnect()
        print("\n🔌 Тестирование эмуляции завершено")

if __name__ == "__main__":
    # Тестируем оба режима
    test_simulation_mode()
    print("\n" + "=" * 60)
    test_diagnostics()