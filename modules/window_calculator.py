# 📁 modules/window_calculator.py
# [file content begin]
"""
🪟 КАЛЬКУЛЯТОР ОКОН - ПРОДВИНУТЫЙ ЭСКИЗ
"""

import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, gray, silver

class WindowCalculator:
    def __init__(self):
        # База цен
        self.prices = {
            'profiles': {'econom': 2500, 'standard': 3200, 'premium': 4200},
            'glass': {'single': 1800, 'double': 2400, 'energy': 3200},
            'fittings': {'basic': 2000, 'comfort': 3000, 'security': 4500}
        }
        
        self.names = {
            'profiles': {'econom': 'Эконом', 'standard': 'Стандарт', 'premium': 'Премиум'},
            'glass': {'single': 'Однокамерный', 'double': 'Двухкамерный', 'energy': 'Энергосберегающий'},
            'fittings': {'basic': 'Базовая', 'comfort': 'Комфорт', 'security': 'Безопасность'}
        }

    def calculate_window(self, width, height, profile, glass, fittings):
        """Расчет стоимости окна"""
        try:
            area = (width * height) / 1000000
            profile_cost = area * self.prices['profiles'][profile]
            glass_cost = area * self.prices['glass'][glass]
            fittings_cost = self.prices['fittings'][fittings]
            total = profile_cost + glass_cost + fittings_cost
            
            return {
                'area': area,
                'profile_cost': profile_cost,
                'glass_cost': glass_cost,
                'fittings_cost': fittings_cost,
                'total': round(total)
            }
        except Exception as e:
            return {'error': str(e)}

    def create_detailed_window_pdf(self, width, height, profile, glass, fittings, 
                                 calculation, filename='window_detailed.pdf'):
        """Создание PDF с детализированным эскизом окна"""
        try:
            c = canvas.Canvas(filename, pagesize=A4)
            width_pdf, height_pdf = A4
            
            # ===== ЗАГОЛОВОК =====
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height_pdf - 40, "ДЕТАЛИЗИРОВАННЫЙ ЭСКИЗ ОКНА")
            
            # ===== ОСНОВНЫЕ ПАРАМЕТРЫ ЭСКИЗА =====
            frame_x = 80  # позиция X рамки
            frame_y = height_pdf - 250  # позиция Y рамки
            frame_width = 200  # ширина рамки в PDF
            frame_height = 150  # высота рамки в PDF
            
            # Масштабируем реальные размеры к размерам в PDF
            scale_x = frame_width / width
            scale_y = frame_height / height
            scale = min(scale_x, scale_y) * 0.9  # запас 10%
            
            # ===== 1. ОСНОВНАЯ РАМА (толстая) =====
            c.setLineWidth(2.5)
            c.setStrokeColor(black)
            c.rect(frame_x, frame_y, frame_width, frame_height)
            
            # ===== 2. ПРОФИЛЬ РАМЫ (двойная линия) =====
            c.setLineWidth(1)
            c.setStrokeColor(gray)
            profile_offset = 3
            c.rect(frame_x + profile_offset, frame_y + profile_offset, 
                   frame_width - 2*profile_offset, frame_height - 2*profile_offset)
            
            # ===== 3. ИМПОСТЫ (перегородки) =====
            c.setLineWidth(1.2)
            c.setStrokeColor(black)
            
            # Вертикальные импосты
            impost_x_positions = [frame_x + frame_width/3, frame_x + 2*frame_width/3]
            for x_pos in impost_x_positions:
                c.line(x_pos, frame_y, x_pos, frame_y + frame_height)
            
            # Горизонтальные импосты
            impost_y_positions = [frame_y + frame_height/3, frame_y + 2*frame_height/3]
            for y_pos in impost_y_positions:
                c.line(frame_x, y_pos, frame_x + frame_width, y_pos)
            
            # ===== 4. СТВОРКИ (открывающиеся части) =====
            c.setLineWidth(0.8)
            c.setStrokeColor(silver)
            
            # Левая створка
            sash_margin = 8
            sash_width = frame_width/3 - sash_margin
            sash_height = frame_height - 2*sash_margin
            
            # Верхняя левая створка
            c.rect(frame_x + sash_margin/2, frame_y + frame_height*2/3 + sash_margin/2, 
                   sash_width, frame_height/3 - sash_margin)
            
            # Нижняя левая створка  
            c.rect(frame_x + sash_margin/2, frame_y + sash_margin/2, 
                   sash_width, frame_height/3 - sash_margin)
            
            # Правая створка
            c.rect(frame_x + 2*frame_width/3 + sash_margin/2, frame_y + sash_margin/2,
                   sash_width, frame_height - sash_margin)
            
            # ===== 5. РУЧКИ И ФУРНИТУРА =====
            c.setFillColor(black)
            
            # Ручки на левых створках
            handle_radius = 2
            left_handles = [
                (frame_x + frame_width/6, frame_y + frame_height*5/6),  # верхняя левая
                (frame_x + frame_width/6, frame_y + frame_height/6)     # нижняя левая
            ]
            
            for handle_x, handle_y in left_handles:
                c.circle(handle_x, handle_y, handle_radius, fill=1)
                # Линия от ручки
                c.line(handle_x, handle_y, handle_x + 10, handle_y)
            
            # Ручка на правой створке
            right_handle_x = frame_x + frame_width*5/6
            right_handle_y = frame_y + frame_height/2
            c.circle(right_handle_x, right_handle_y, handle_radius, fill=1)
            c.line(right_handle_x, right_handle_y, right_handle_x - 10, right_handle_y)
            
            # ===== 6. РАЗМЕРНЫЕ ЛИНИИ =====
            c.setLineWidth(0.5)
            c.setStrokeColor(gray)
            dim_offset = 15
            
            # Вертикальные размеры
            c.line(frame_x - dim_offset, frame_y, frame_x - dim_offset, frame_y + frame_height)
            c.line(frame_x + frame_width + dim_offset, frame_y, frame_x + frame_width + dim_offset, frame_y + frame_height)
            
            # Горизонтальные размеры
            c.line(frame_x, frame_y - dim_offset, frame_x + frame_width, frame_y - dim_offset)
            c.line(frame_x, frame_y + frame_height + dim_offset, frame_x + frame_width, frame_y + frame_height + dim_offset)
            
            # ===== 7. ПОДПИСИ РАЗМЕРОВ =====
            c.setFont("Helvetica", 8)
            c.setFillColor(black)
            
            # Вертикальные подписи
            c.drawString(frame_x - 35, frame_y + frame_height/2 - 5, f"{height} мм")
            c.drawString(frame_x + frame_width + 20, frame_y + frame_height/2 - 5, f"{height} мм")
            
            # Горизонтальные подписи
            c.drawString(frame_x + frame_width/2 - 15, frame_y - 20, f"{width} мм")
            c.drawString(frame_x + frame_width/2 - 15, frame_y + frame_height + 15, f"{width} мм")
            
            # ===== 8. ЛЕГЕНДА И ОБОЗНАЧЕНИЯ =====
            legend_y = frame_y - 80
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, legend_y, "ОБОЗНАЧЕНИЯ:")
            legend_y -= 15
            
            c.setFont("Helvetica", 9)
            legends = [
                "▪ Основная рама",
                "▪ Импосты", 
                "▪ Створки",
                "● Ручки",
                "─ Размерные линии"
            ]
            
            for i, legend in enumerate(legends):
                c.drawString(50 + (i % 2) * 120, legend_y - (i // 2) * 15, legend)
            
            # ===== 9. ТЕХНИЧЕСКИЕ ДАННЫЕ =====
            tech_y = legend_y - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, tech_y, "ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:")
            tech_y -= 20
            
            c.setFont("Helvetica", 10)
            tech_data = [
                f"Размер: {width} × {height} мм",
                f"Площадь: {calculation['area']:.2f} м²",
                f"Профиль: {self.names['profiles'][profile]}",
                f"Стеклопакет: {self.names['glass'][glass]}",
                f"Фурнитура: {self.names['fittings'][fittings]}"
            ]
            
            for i, data in enumerate(tech_data):
                c.drawString(50, tech_y - i * 15, data)
            
            # ===== 10. СТОИМОСТЬ =====
            cost_y = tech_y - 80
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, cost_y, f"ИТОГО: {calculation['total']} руб.")
            cost_y -= 20
            
            c.setFont("Helvetica", 10)
            c.drawString(50, cost_y - 15, f"Профиль: {calculation['profile_cost']:.0f} руб.")
            c.drawString(50, cost_y - 30, f"Стеклопакет: {calculation['glass_cost']:.0f} руб.")
            c.drawString(50, cost_y - 45, f"Фурнитура: {calculation['fittings_cost']:.0f} руб.")
            
            # ===== 11. КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ =====
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, 80, "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ")
            c.setFont("Helvetica", 9)
            c.drawString(50, 65, "Срок действия: 30 дней")
            c.drawString(50, 50, "Контакты: +7 (XXX) XXX-XX-XX")
            
            c.save()
            return filename
            
        except Exception as e:
            return f"Ошибка создания PDF: {str(e)}"

# Создаем глобальный экземпляр
calculator = WindowCalculator()
# [file content end]