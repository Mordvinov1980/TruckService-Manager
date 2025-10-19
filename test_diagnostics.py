# test_diagnostics.py - в корне проекта
import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.vehicle_diagnostics import VehicleDiagnostics
from modules.diagnostic_repository import DiagnosticRepository

def quick_test():
    """Быстрый тест диагностики без интеграции с основной системой"""
    print("🚛 БЫСТРЫЙ ТЕСТ ДИАГНОСТИКИ ACTROS MP4")
    print("=" * 50)
    
    # Инициализация
    diag = VehicleDiagnostics()
    repo = DiagnosticRepository()
    
    # Подключение
    if diag.connect():
        print("✅ Подключение к ELM327 установлено")
        
        # Сбор данных
        vehicle_info = diag.get_vehicle_info()
        live_data = diag.read_live_data()
        dtc_codes = diag.read_dtc_codes()
        
        print(f"🚗 VIN: {vehicle_info.get('vin', 'N/A')}")
        print(f"📡 Протокол: {vehicle_info.get('protocol', 'N/A')}")
        
        # Показываем основные параметры
        print("\n📊 ОСНОВНЫЕ ПАРАМЕТРЫ:")
        key_params = ['rpm', 'speed', 'coolant_temp', 'engine_load']
        for param in key_params:
            if param in live_data.get('parameters', {}):
                value_data = live_data['parameters'][param]
                print(f"   {param}: {value_data['value']} {value_data['units']}")
        
        # Коды ошибок
        if dtc_codes.get('count', 0) > 0:
            print(f"\n⚠️  НАЙДЕНЫ ОШИБКИ: {dtc_codes['count']} шт.")
            for code in dtc_codes.get('codes', []):
                print(f"   {code}")
        else:
            print("\n✅ Ошибок не найдено")
        
        # Сохраняем в репозиторий
        diagnostic_data = {
            "vehicle_info": vehicle_info,
            "live_data": live_data,
            "dtc_codes": dtc_codes
        }
        
        repo.save_diagnostic_session(vehicle_info, diagnostic_data)
        print(f"\n💾 Данные диагностики сохранены")
        
        diag.disconnect()
    else:
        print("❌ Не удалось подключиться к ELM327")

if __name__ == "__main__":
    quick_test()