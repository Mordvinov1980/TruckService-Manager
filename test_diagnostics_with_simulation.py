# test_diagnostics_with_simulation.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.vehicle_diagnostics import VehicleDiagnostics
from modules.diagnostic_repository import DiagnosticRepository

def test_with_simulation():
    """Тест с режимом эмуляции для разработки"""
    print("🔧 ТЕСТ ДИАГНОСТИКИ С РЕЖИМОМ ЭМУЛЯЦИИ")
    print("=" * 55)
    
    # Тестируем в режиме эмуляции
    print("1. Тестирование в РЕЖИМЕ ЭМУЛЯЦИИ:")
    diag_sim = VehicleDiagnostics(simulation_mode=True)
    repo = DiagnosticRepository()
    
    if diag_sim.connect():
        print("✅ Режим эмуляции активирован")
        
        vehicle_info = diag_sim.get_vehicle_info()
        live_data = diag_sim.read_live_data()
        dtc_codes = diag_sim.read_dtc_codes()
        
        print(f"🚗 VIN: {vehicle_info.get('vin')}")
        print(f"📡 Протокол: {vehicle_info.get('protocol')}")
        
        print("\n📊 ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ:")
        for param, value_data in live_data.get('parameters', {}).items():
            print(f"   {param}: {value_data['value']} {value_data['units']}")
        
        if dtc_codes.get('count', 0) > 0:
            print(f"\n⚠️  ОБНАРУЖЕНЫ ОШИБКИ: {dtc_codes['count']} шт.")
            for code in dtc_codes.get('codes', []):
                print(f"   {code}")
        
        # Сохраняем тестовые данные
        diagnostic_data = {
            "vehicle_info": vehicle_info,
            "live_data": live_data,
            "dtc_codes": dtc_codes
        }
        repo.save_diagnostic_session(vehicle_info, diagnostic_data)
        print(f"\n💾 Тестовая сессия сохранена")
    
    print("\n" + "=" * 55)
    print("2. Тестирование РЕАЛЬНОГО ПОДКЛЮЧЕНИЯ:")
    
    # Тестируем реальное подключение
    diag_real = VehicleDiagnostics(simulation_mode=False)
    
    if diag_real.connect():
        print("✅ Реальное подключение установлено")
        # ... тестируем реальные данные ...
    else:
        print("❌ Реальное подключение недоступно")
        print("   (Это нормально - адаптер еще не подключен)")
        print("\n💡 РЕКОМЕНДАЦИИ ДЛЯ РЕАЛЬНОГО ПОДКЛЮЧЕНИЯ:")
        print("   1. Подключите ELM327 к OBD2 разъему автомобиля")
        print("   2. Включите зажигание (двигатель можно не заводить)")
        print("   3. Убедитесь, что Bluetooth/Wi-Fi адаптер включен")
        print("   4. Проверьте сопряжение с компьютером")

if __name__ == "__main__":
    test_with_simulation()