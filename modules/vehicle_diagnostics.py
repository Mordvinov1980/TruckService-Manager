# modules/vehicle_diagnostics.py
import obd
import logging
from typing import Dict, List, Optional
from datetime import datetime

class VehicleDiagnostics:
    """Основной класс для диагностики автомобилей через ELM327"""
    
    def __init__(self):
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
    
    def connect(self, port: str = None) -> bool:
        """
        Подключение к ELM327 адаптеру
        port: COM порт (например: 'COM3' на Windows)
        """
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
                self.logger.error("❌ Не удалось подключиться к ELM327")
                
            return self.is_connected
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения: {e}")
            self.is_connected = False
            return False
    
    def get_vehicle_info(self) -> Dict:
        """Получение базовой информации об автомобиле"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        info = {
            "timestamp": datetime.now().isoformat(),
            "vin": "N/A",
            "protocol": self.connection.protocol_name() if self.connection else "N/A",
            "supported_commands": []
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
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "parameters": {}
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
    
    def read_dtc_codes(self) -> Dict:
        """Чтение и расшифровка кодов ошибок"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
        try:
            response = self.connection.query(obd.commands.GET_DTC)
            if not response.is_null():
                dtc_codes = response.value
                return {
                    "count": len(dtc_codes),
                    "codes": dtc_codes,
                    "timestamp": datetime.now().isoformat()
                }
            return {"count": 0, "codes": [], "timestamp": datetime.now().isoformat()}
        except Exception as e:
            self.logger.error(f"Ошибка чтения DTC: {e}")
            return {"error": str(e)}
    
    def clear_dtc_codes(self) -> Dict:
        """Очистка кодов ошибок"""
        if not self.is_connected:
            return {"error": "Нет подключения к адаптеру"}
        
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

if __name__ == "__main__":
    test_diagnostics()