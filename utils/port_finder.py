# utils/port_finder.py
import serial.tools.list_ports

def find_obd_ports():
    """Поиск возможных COM-портов для OBD адаптера"""
    print("🔍 ПОИСК COM-ПОРТОВ ДЛЯ ELM327")
    print("=" * 40)
    
    ports = serial.tools.list_ports.comports()
    obd_candidates = []
    
    for port in ports:
        print(f"📡 Найден порт: {port.device}")
        print(f"   Описание: {port.description}")
        print(f"   Производитель: {port.manufacturer}")
        print()
        
        # Критерии для OBD адаптеров
        if any(keyword in port.description.upper() for keyword in ['OBD', 'ELM327', 'BLUETOOTH', 'SERIAL']):
            obd_candidates.append(port.device)
    
    if obd_candidates:
        print("✅ ВОЗМОЖНЫЕ OBD-ПОРТЫ:")
        for candidate in obd_candidates:
            print(f"   🎯 {candidate}")
    else:
        print("❌ OBD-порты не обнаружены")
        print("💡 Проверьте Bluetooth сопряжение")
    
    return obd_candidates

if __name__ == "__main__":
    find_obd_ports()