# test_final_diagnostics.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.vehicle_diagnostics import VehicleDiagnostics
from modules.diagnostic_repository import DiagnosticRepository
from utils.port_finder import find_obd_ports

def final_test_with_adapter():
    """Финальный тест при получении адаптера"""
    print("🚛 ФИНАЛЬНЫЙ ТЕСТ DIAGNOSTICS MODULE")
    print("=" * 55)
    
    # Поиск портов
    ports = find_obd_ports()
    
    if not ports:
        print("❌ Адаптер не обнаружен. Проверьте:")
        print("   1. Подключен ли ELM327 к OBD2")
        print("   2. Включено ли зажигание")
        print("   3. Сопряжен ли Bluetooth")
        return
    
    # Тестируем на каждом найденном порту
    for port in ports:
        print(f"\n🔧 Тестирование на порту: {port}")
        
        diag = VehicleDiagnostics(simulation_mode=False)
        repo = DiagnosticRepository()
        
        if diag.connect(port):
            print(f"✅ УСПЕШНОЕ ПОДКЛЮЧЕНИЕ НА {port}")
            
            # Полная диагностика
            vehicle_info = diag.get_vehicle_info()
            live_data = diag.read_live_data()
            truck_data = diag.read_truck_specific_data()
            dtc_codes = diag.read_dtc_codes()
            j1939_support = diag.check_j1939_support()
            
            print(f"🚗 VIN: {vehicle_info.get('vin', 'N/A')}")
            print(f"📡 Протокол: {vehicle_info.get('protocol', 'N/A')}")
            print(f"🔌 J1939 поддержка: {'✅ ДА' if j1939_support else '❌ НЕТ'}")
            
            print(f"\n📊 Параметров получено: {len(live_data.get('parameters', {}))}")
            print(f"⚠️  Ошибок обнаружено: {dtc_codes.get('count', 0)}")
            
            # Сохраняем сессию
            diagnostic_report = {
                "vehicle_info": vehicle_info,
                "live_data": live_data,
                "truck_data": truck_data,
                "dtc_codes": dtc_codes,
                "j1939_support": j1939_support
            }
            
            repo.save_diagnostic_session(vehicle_info, diagnostic_report)
            print("💾 Диагностическая сессия сохранена")
            
            diag.disconnect()
            break  # Останавливаемся на первом успешном подключении
        else:
            print(f"❌ Не удалось подключиться на {port}")

if __name__ == "__main__":
    final_test_with_adapter()