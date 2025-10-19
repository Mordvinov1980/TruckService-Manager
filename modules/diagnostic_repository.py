# modules/diagnostic_repository.py
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging

class DiagnosticRepository:
    """Репозиторий для хранения и управления данными диагностики"""
    
    def __init__(self, data_file: str = "data/diagnostic_sessions.json"):
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Создает файл данных, если он не существует"""
        try:
            import os
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
        except Exception as e:
            self.logger.error(f"Ошибка создания файла данных: {e}")
    
    def save_diagnostic_session(self, vehicle_data: Dict, diagnostic_data: Dict) -> bool:
        """Сохранение сессии диагностики"""
        try:
            # Чтение существующих данных
            with open(self.data_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            # Создание новой записи
            session_record = {
                "session_id": f"diag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "vehicle_info": vehicle_data,
                "diagnostic_data": diagnostic_data,
                "has_errors": len(diagnostic_data.get('dtc_codes', {}).get('codes', [])) > 0
            }
            
            # Добавление и сохранение
            sessions.append(session_record)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✅ Сессия диагностики сохранена: {session_record['session_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения сессии: {e}")
            return False
    
    def get_vehicle_diagnostic_history(self, vin: str) -> List[Dict]:
        """Получение истории диагностики по VIN"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            vehicle_sessions = [
                session for session in sessions 
                if session.get('vehicle_info', {}).get('vin') == vin
            ]
            
            return sorted(vehicle_sessions, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения истории: {e}")
            return []
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Получение последних сессий диагностики"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            return sorted(sessions, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения сессий: {e}")
            return []

# Интеграция с основным репозиторием диагностики
class EnhancedVehicleDiagnostics:
    """Расширенный класс диагностики с интеграцией репозитория"""
    
    def __init__(self):
        self.diagnostics = VehicleDiagnostics()
        self.repository = DiagnosticRepository()
    
    def full_diagnostic_scan(self) -> Dict:
        """Полная диагностика с сохранением в репозиторий"""
        if not self.diagnostics.connect():
            return {"error": "Не удалось подключиться к адаптеру"}
        
        try:
            # Сбор всех данных
            vehicle_info = self.diagnostics.get_vehicle_info()
            live_data = self.diagnostics.read_live_data()
            dtc_codes = self.diagnostics.read_dtc_codes()
            
            # Формирование полного отчета
            diagnostic_report = {
                "vehicle_info": vehicle_info,
                "live_data": live_data,
                "dtc_codes": dtc_codes,
                "summary": {
                    "has_errors": dtc_codes.get('count', 0) > 0,
                    "error_count": dtc_codes.get('count', 0),
                    "parameters_monitored": len(live_data.get('parameters', {})),
                    "status": "WITH_ERRORS" if dtc_codes.get('count', 0) > 0 else "OK"
                }
            }
            
            # Сохранение в репозиторий
            self.repository.save_diagnostic_session(vehicle_info, diagnostic_report)
            
            return diagnostic_report
            
        except Exception as e:
            logging.error(f"Ошибка полной диагностики: {e}")
            return {"error": str(e)}
        finally:
            self.diagnostics.disconnect()