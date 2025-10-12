"""
🚀 ФАБРИКА ДОКУМЕНТОВ ДЛЯ TRUCKSERVICE MANAGER
ПАТТЕРН FACTORY ДЛЯ ЦЕНТРАЛИЗОВАННОГО СОЗДАНИЯ ДОКУМЕНТОВ
"""

import pathlib
from typing import Dict, Any, List, Tuple, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime

# ✅ БАЗОВЫЕ ИСКЛЮЧЕНИЯ ДЛЯ ДОКУМЕНТОВ
class DocumentError(Exception):
    """Базовая ошибка создания документов"""
    pass

class DocumentCreationError(DocumentError):
    """Ошибка создания документа"""
    pass

class DocumentValidationError(DocumentError):
    """Ошибка валидации данных документа"""
    pass


# ✅ АБСТРАКТНЫЙ БАЗОВЫЙ КЛАСС ДОКУМЕНТА
class Document(ABC):
    """Базовый класс для всех типов документов"""
    
    def __init__(self, session: Dict[str, Any]):
        self.session = session
        self.logger = logging.getLogger('Document')
        self._validate_session()
    
    def _validate_session(self) -> None:
        """Валидация обязательных данных сессии"""
        required_fields = ['license_plate', 'date', 'order_number', 'workers', 'selected_works']
        for field in required_fields:
            if field not in self.session or not self.session[field]:
                raise DocumentValidationError(f"Отсутствует обязательное поле: {field}")
    
    @abstractmethod
    def create(self, output_path: pathlib.Path) -> bool:
        """Создание документа"""
        pass
    
    @abstractmethod
    def get_filename(self) -> str:
        """Получение имени файла документа"""
        pass
    
    def _get_base_filename(self) -> str:
        """Базовое имя файла для всех документов"""
        order_number = self.session.get('order_number', '000')
        date_str = self.session['date'].strftime('%d.%m.%Y')
        license_plate = self.session['license_plate']
        return f"№{order_number} {date_str} {license_plate}"


# ✅ КОНКРЕТНЫЕ РЕАЛИЗАЦИИ ДОКУМЕНТОВ
class ExcelDocument(Document):
    """Excel заказ-наряд"""
    
    def __init__(self, session: Dict[str, Any], excel_processor):
        super().__init__(session)
        self.excel_processor = excel_processor
    
    def create(self, output_path: pathlib.Path) -> bool:
        """Создание Excel документа"""
        try:
            template_path = output_path.parent.parent / "Шаблоны" / "template_autoservice.xlsx"
            success = self.excel_processor.create_professional_order(
                self.session, 
                str(template_path), 
                str(output_path)
            )
            
            if success and output_path.exists():
                self.logger.info(f"✅ Excel документ создан: {output_path}")
                return True
            else:
                raise DocumentCreationError(f"Не удалось создать Excel документ: {output_path}")
                
        except Exception as e:
            raise DocumentCreationError(f"Ошибка создания Excel документа: {e}") from e
    
    def get_filename(self) -> str:
        """Получение имени Excel файла"""
        return f"{self._get_base_filename()}.xlsx"


class TextDocument(Document):
    """Текстовый черновик заказ-наряда"""
    
    def create(self, output_path: pathlib.Path) -> bool:
        """Создание текстового документа"""
        try:
            content = self._create_draft_content()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if output_path.exists():
                self.logger.info(f"✅ Текстовый документ создан: {output_path}")
                return True
            else:
                raise DocumentCreationError(f"Не удалось создать текстовый документ: {output_path}")
                
        except Exception as e:
            raise DocumentCreationError(f"Ошибка создания текстового документа: {e}") from e
    
    def get_filename(self) -> str:
        """Получение имени текстового файла"""
        return f"{self._get_base_filename()}.txt"
    
    def _create_draft_content(self) -> str:
        """Создание содержимого текстового черновика"""
        content = []
        content.append(f"{self.session['license_plate']} / {self.session['date'].strftime('%d.%m.%Y')}")
        content.append(self.session['workers'])
        content.append("")
        
        content.append("РАБОТЫ:")
        for name, hours in self.session['selected_works']:
            content.append(f"• {name}")
        
        if self.session.get('selected_materials'):
            content.append("")
            content.append("МАТЕРИАЛЫ:")
            for material in self.session['selected_materials']:
                content.append(f"• {material}")
        
        return '\n'.join(content)


# ✅ ФАБРИКА ДОКУМЕНТОВ
class DocumentFactory:
    """Фабрика для создания документов заказ-нарядов"""
    
    def __init__(self, excel_processor):
        self.excel_processor = excel_processor
        self.logger = logging.getLogger('DocumentFactory')
    
    def create_all(self, session: Dict[str, Any], section_folder: pathlib.Path) -> Dict[str, pathlib.Path]:
        """Создание всех типов документов для заказа"""
        try:
            orders_folder = section_folder / "Заказы"
            orders_folder.mkdir(parents=True, exist_ok=True)
            
            documents = {}
            
            # Создаем Excel документ
            excel_doc = ExcelDocument(session, self.excel_processor)
            excel_filename = excel_doc.get_filename()
            excel_path = orders_folder / excel_filename
            
            if excel_doc.create(excel_path):
                documents['excel'] = excel_path
            
            # Создаем текстовый документ
            text_doc = TextDocument(session)
            text_filename = text_doc.get_filename()
            text_path = orders_folder / text_filename
            
            if text_doc.create(text_path):
                documents['text'] = text_path
            
            self.logger.info(f"✅ Создано документов: {len(documents)}")
            return documents
            
        except Exception as e:
            raise DocumentCreationError(f"Ошибка создания документов через фабрику: {e}") from e
    
    def create_excel(self, session: Dict[str, Any], section_folder: pathlib.Path) -> Optional[pathlib.Path]:
        """Создание только Excel документа"""
        try:
            excel_doc = ExcelDocument(session, self.excel_processor)
            orders_folder = section_folder / "Заказы"
            orders_folder.mkdir(parents=True, exist_ok=True)
            
            excel_filename = excel_doc.get_filename()
            excel_path = orders_folder / excel_filename
            
            if excel_doc.create(excel_path):
                return excel_path
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания Excel документа: {e}")
            return None
    
    def create_text(self, session: Dict[str, Any], section_folder: pathlib.Path) -> Optional[pathlib.Path]:
        """Создание только текстового документа"""
        try:
            text_doc = TextDocument(session)
            orders_folder = section_folder / "Заказы"
            orders_folder.mkdir(parents=True, exist_ok=True)
            
            text_filename = text_doc.get_filename()
            text_path = orders_folder / text_filename
            
            if text_doc.create(text_path):
                return text_path
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания текстового документа: {e}")
            return None


# ✅ УТИЛИТЫ ДЛЯ РАБОТЫ С ДОКУМЕНТАМИ
class DocumentUtils:
    """Утилиты для работы с документами"""
    
    @staticmethod
    def validate_session_for_documents(session: Dict[str, Any]) -> bool:
        """Проверка сессии на возможность создания документов"""
        required_fields = ['license_plate', 'date', 'order_number', 'workers', 'selected_works']
        return all(field in session and session[field] for field in required_fields)
    
    @staticmethod
    def calculate_totals(session: Dict[str, Any]) -> Dict[str, float]:
        """Расчет итоговых сумм для документов"""
        works_total = sum(hours for _, hours in session['selected_works']) * 2500
        
        materials_data = {
            "ВД-40": 375,
            "Перчатки": 95, 
            "Смазка": 210,
            "Диск отрезной": 120
        }
        
        selected_materials = session.get('selected_materials', [])
        if not selected_materials:
            selected_materials = list(materials_data.keys())
        
        materials_total = sum(materials_data.get(material, 0) for material in selected_materials)
        total_amount = works_total + materials_total
        
        return {
            'works_total': works_total,
            'materials_total': materials_total,
            'total_amount': total_amount
        }