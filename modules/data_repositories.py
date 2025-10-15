"""
🚀 РЕПОЗИТОРИИ ДЛЯ РАБОТЫ С ДАННЫМИ
ПАТТЕРН REPOSITORY ДЛЯ АБСТРАКЦИИ ДОСТУПА К ДАННЫМ
"""

import pandas as pd
import pickle
import time
import pathlib
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
import logging

# ✅ БАЗОВЫЕ ИСКЛЮЧЕНИЯ ДЛЯ РЕПОЗИТОРИЕВ
class RepositoryError(Exception):
    """Базовая ошибка репозитория"""
    pass

class DataNotFoundError(RepositoryError):
    """Данные не найдены"""
    pass

class CacheError(RepositoryError):
    """Ошибка кэширования"""
    pass


# ✅ АБСТРАКТНЫЕ БАЗОВЫЕ КЛАССЫ
class BaseRepository(ABC):
    """Базовый репозиторий с кэшированием"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self.logger = logging.getLogger('Repository')
    
    def _load_from_cache(self, cache_key: str, cache_file: pathlib.Path) -> Optional[Any]:
        """Загрузка данных из кэша"""
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    self.logger.info(f"✅ Загружено из кэша: {cache_key}")
                    return cached_data['data']
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка загрузки кэша {cache_key}: {e}")
        return None
    
    def _save_to_cache(self, data: Any, cache_key: str, cache_file: pathlib.Path) -> None:
        """Сохранение данных в кэш"""
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump({'data': data, 'timestamp': time.time()}, f)
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка сохранения кэша {cache_key}: {e}")


class WorksRepository(BaseRepository):
    """Репозиторий для работы с работами"""
    
    @abstractmethod
    def get_works(self, section: str) -> List[Tuple[str, float]]:
        """Получить список работ для раздела"""
        pass
    
    @abstractmethod
    def get_works_count(self, section: str) -> int:
        """Получить количество работ в разделе"""
        pass


class MaterialsRepository(BaseRepository):
    """Репозиторий для работы с материалами"""
    
    @abstractmethod
    def get_materials(self) -> List[str]:
        """Получить список материалов"""
        pass
    
    @abstractmethod
    def get_material_price(self, material_name: str) -> float:
        """Получить цену материала"""
        pass


class AccountingRepository(BaseRepository):
    """Репозиторий для учета заказов"""
    
    @abstractmethod
    def save_order(self, session: Dict[str, Any], excel_filename: str, has_photos: str) -> bool:
        """Сохранить заказ в учет"""
        pass
    
    @abstractmethod
    def get_order_statistics(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Получить статистику заказов"""
        pass


# ✅ КОНКРЕТНЫЕ РЕАЛИЗАЦИИ ДЛЯ EXCEL
class ExcelWorksRepository(WorksRepository):
    """Реализация репозитория работ для Excel"""
    
    def __init__(self, main_folder: pathlib.Path, sections_config: Dict[str, Any], cache_ttl: int = 3600):
        super().__init__(cache_ttl)
        self.main_folder = main_folder
        self.sections_config = sections_config
        
        # Стандартные работы на случай отсутствия файлов
        self.default_works = {
            'base': [
                ("Осмотр ТС", 0.4), ("Замена нижней накладки правой фары", 0.6),
                ("Замена верхней накладки правой фары", 0.8), ("Замена нижней накладки левой фары", 0.6),
                ("Замена верхней накладки левой фары", 0.8), ("Замена правой подножки", 1.4),
                ("Замена левой подножки", 1.4), ("Замена накладки правой подножки", 0.2),
                ("Замена накладки левой подножки", 0.2), ("Замена лючка правой подножки", 0.4),
            ]
        }
    
    def get_works(self, section: str) -> List[Tuple[str, float]]:
        """Получить работы для раздела с кэшированием"""
        if section not in self.sections_config:
            raise DataNotFoundError(f"Раздел не найден: {section}")
        
        # Проверяем кэш
        cache_key = f"{section}_works"
        cache_file = self.sections_config[section]['folder'] / "cache" / f"{cache_key}.pkl"
        
        cached_data = self._load_from_cache(cache_key, cache_file)
        if cached_data is not None:
            return cached_data
        
        # Загружаем из Excel
        works = self._load_works_from_excel(section)
        
        # Сохраняем в кэш
        self._save_to_cache(works, cache_key, cache_file)
        
        return works
    
    def get_works_count(self, section: str) -> int:
        """Получить количество работ в разделе"""
        works = self.get_works(section)
        return len(works)
    
    def _load_works_from_excel(self, section: str) -> List[Tuple[str, float]]:
        """Загрузка работ из Excel файла"""
        section_data = self.sections_config[section]
        works_file = section_data['works_file']
        
        try:
            # Ищем в корневой папке Шаблоны
            excel_path = self.main_folder / "Шаблоны" / works_file
            
            if not excel_path.exists():
                # Если нет в папке Шаблоны, пробуем прямо по имени файла
                excel_path = pathlib.Path(works_file)
            
            if excel_path.exists():
                df = pd.read_excel(excel_path)
                works = []
                valid_count = 0
                
                for idx, row in df.iterrows():
                    work_name = str(row.iloc[0]).strip()
                    work_hours = row.iloc[1]
                    
                    if work_name and work_name != 'nan' and pd.notna(work_hours):
                        try:
                            hours = float(work_hours)
                            works.append((work_name, hours))
                            valid_count += 1
                        except (ValueError, TypeError):
                            continue
                    else:
                        continue
                
                self.logger.info(f"✅ Загружено {valid_count} работ для раздела {section}")
                return works
            else:
                self.logger.warning(f"❌ Файл {works_file} не найден, используем стандартные работы")
                return self.default_works.get(section, [])
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки Excel файла работ: {e}")
            return self.default_works.get(section, [])


class ExcelMaterialsRepository(MaterialsRepository):
    """Реализация репозитория материалов для Excel"""
    
    def __init__(self, main_folder: pathlib.Path, cache_ttl: int = 3600):
        super().__init__(cache_ttl)
        self.main_folder = main_folder
        
        # Цены материалов
        self.material_prices = {
            "ВД-40": 375,
            "Перчатки": 95,
            "Смазка": 210,
            "Диск отрезной": 120
        }
    
    def get_materials(self) -> List[str]:
        """Получить список материалов с кэшированием"""
        cache_key = "materials"
        cache_file = self.main_folder / "cache" / f"{cache_key}.pkl"
        
        cached_data = self._load_from_cache(cache_key, cache_file)
        if cached_data is not None:
            return cached_data
        
        # Загружаем из Excel
        materials = self._load_materials_from_excel()
        
        # Сохраняем в кэш
        self._save_to_cache(materials, cache_key, cache_file)
        
        return materials
    
    def get_material_price(self, material_name: str) -> float:
        """Получить цену материала"""
        return self.material_prices.get(material_name, 0)
    
    def _load_materials_from_excel(self) -> List[str]:
        """Загрузка материалов из Excel файла"""
        try:
            materials_path = self.main_folder / "Шаблоны" / "list_materials.xlsx"
            
            if not materials_path.exists():
                materials_path = pathlib.Path("list_materials.xlsx")
            
            if materials_path.exists():
                df = pd.read_excel(materials_path)
                materials = []
                valid_count = 0
                
                for idx, row in df.iterrows():
                    material_name = str(row.iloc[0]).strip()
                    
                    if material_name and material_name != 'nan':
                        materials.append(material_name)
                        valid_count += 1
                
                self.logger.info(f"✅ Загружено {valid_count} материалов")
                return materials
            else:
                self.logger.warning("❌ Файл list_materials.xlsx не найден, используем стандартные материалы")
                return list(self.material_prices.keys())
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки материалов Excel: {e}")
            return list(self.material_prices.keys())


class ExcelAccountingRepository(AccountingRepository):
    """Реализация репозитория учета для Excel"""
    
    def __init__(self, main_folder: pathlib.Path, sections_config: Dict[str, Any], common_accounting_folder: pathlib.Path):
        super().__init__()
        self.main_folder = main_folder
        self.sections_config = sections_config
        self.common_accounting_folder = common_accounting_folder
        
        # Инициализируем файлы учета
        self._initialize_accounting_files()
    
    def save_order(self, session: Dict[str, Any], excel_filename: str, has_photos: str) -> bool:
        """Сохранить заказ в учет"""
        try:
            section_id = session['section']
            
            # Сохраняем в раздельный учет
            section_accounting_file = self.sections_config[section_id]['folder'] / "Учет" / "учет_заказов.xlsx"
            wb_section = pd.ExcelWriter(section_accounting_file, engine='openpyxl', mode='a', if_sheet_exists='overlay')
            
            # Читаем существующие данные
            try:
                df_section = pd.read_excel(section_accounting_file)
            except:
                df_section = pd.DataFrame()
            
            # Добавляем новую запись
            now = datetime.datetime.now()
            order_id = len(df_section) + 1 if not df_section.empty else 1
            selected_count = len(session['selected_works'])
            total_hours = sum(hours for _, hours in session['selected_works'])
            
            new_record = {
                'ID': order_id,
                'Дата создания': session['date'].strftime('%d.%m.%Y'),
                'Время создания': now.strftime('%H:%M:%S'),
                'Номер ЗН': session.get('order_number', '000'),
                'Госномер': session['license_plate'],
                'Исполнители': session['workers'],
                'Кол-во работ': selected_count,
                'Общее время': total_hours,
                'Файл Excel': excel_filename,
                'Фото добавлены': has_photos
            }
            
            df_section = pd.concat([df_section, pd.DataFrame([new_record])], ignore_index=True)
            df_section.to_excel(wb_section, index=False)
            wb_section.close()
            
            # Сохраняем в общий учет
            common_accounting_file = self.common_accounting_folder / "главная_база.xlsx"
            wb_common = pd.ExcelWriter(common_accounting_file, engine='openpyxl', mode='a', if_sheet_exists='overlay')
            
            try:
                df_common = pd.read_excel(common_accounting_file)
            except:
                df_common = pd.DataFrame()
            
            section_name = self.sections_config[section_id]['name']
            
            new_common_record = {
                'ID': len(df_common) + 1 if not df_common.empty else 1,
                'Дата создания': session['date'].strftime('%d.%m.%Y'),
                'Время создания': now.strftime('%H:%M:%S'),
                'Раздел': section_name,
                'Номер ЗН': session.get('order_number', '000'),
                'Госномер': session['license_plate'],
                'Исполнители': session['workers'],
                'Кол-во работ': selected_count,
                'Общее время': total_hours,
                'Фото добавлены': has_photos
            }
            
            df_common = pd.concat([df_common, pd.DataFrame([new_common_record])], ignore_index=True)
            df_common.to_excel(wb_common, index=False)
            wb_common.close()
            
            self.logger.info(f"✅ Заказ сохранен в учет: раздел {section_id}, ID {order_id}, фото: {has_photos}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения в учет: {e}")
            return False
    
    def get_order_statistics(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Получить статистику заказов (заглушка для будущей реализации)"""
        # TODO: Реализовать сбор статистики из файлов учета
        return {
            'total_orders': 0,
            'total_hours': 0,
            'total_revenue': 0
        }
    
    def _initialize_accounting_files(self) -> None:
        """Инициализация файлов учета"""
        try:
            for section_id in self.sections_config.keys():
                accounting_file = self.sections_config[section_id]['folder'] / "Учет" / "учет_заказов.xlsx"
                self._setup_section_accounting_file(accounting_file, section_id)
            
            common_accounting_file = self.common_accounting_folder / "главная_база.xlsx"
            self._setup_common_accounting_file(common_accounting_file)
            
        except Exception as e:
            raise RepositoryError(f"Ошибка инициализации учета: {e}") from e
    
    def _setup_section_accounting_file(self, accounting_file: pathlib.Path, section_id: str) -> None:
        """Создание файла учета для раздела"""
        if not accounting_file.exists():
            df = pd.DataFrame(columns=[
                "ID", "Дата создания", "Время создания", "Номер ЗН", "Госномер", 
                "Исполнители", "Кол-во работ", "Общее время", "Файл Excel", "Фото добавлены"
            ])
            df.to_excel(accounting_file, index=False)
    
    def _setup_common_accounting_file(self, accounting_file: pathlib.Path) -> None:
        """Создание общей базы данных"""
        if not accounting_file.exists():
            df = pd.DataFrame(columns=[
                "ID", "Дата создания", "Время создания", "Раздел", "Номер ЗН", 
                "Госномер", "Исполнители", "Кол-во работ", "Общее время", "Фото добавлены"
            ])
            df.to_excel(accounting_file, index=False)


# ✅ ФАБРИКА РЕПОЗИТОРИЕВ
class RepositoryFactory:
    """Фабрика для создания репозиториев"""
    
    @staticmethod
    def create_works_repository(main_folder: pathlib.Path, sections_config: Dict[str, Any]) -> WorksRepository:
        return ExcelWorksRepository(main_folder, sections_config)
    
    @staticmethod
    def create_materials_repository(main_folder: pathlib.Path) -> MaterialsRepository:
        return ExcelMaterialsRepository(main_folder)
    
    @staticmethod
    def create_accounting_repository(main_folder: pathlib.Path, sections_config: Dict[str, Any], common_accounting_folder: pathlib.Path) -> AccountingRepository:
        return ExcelAccountingRepository(main_folder, sections_config, common_accounting_folder)