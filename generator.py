import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white, black
from pypdf import PdfReader, PdfWriter

# ========================================================
# НАСТРОЙКИ СЕРТИФИКАТА (PILLOW)
# ========================================================
CERT_TEMPLATE = "cert_template.jpg"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

# Координаты для сертификата (Y - высота, X - ширина)
CERT_Y_NUM = 285
CERT_Y_COMPANY = 360
CERT_Y_INN = 425
CERT_Y_DATE = 568
CERT_X_DATE = 755

# ========================================================
# НАСТРОЙКИ ДОВЕРЕННОСТИ (REPORTLAB - PDF)
# ========================================================
DOVER_TEMPLATE = "МИШКА Доверенность м2 с печатями и подписью заполнять в середине-4.pdf"

try:
    pdfmetrics.registerFont(TTFont('Arial', FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont('Arial-Bold', FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов Arial для PDF: {e}")

# МАСКИ (Зачистка старого текста белыми прямоугольниками поверх PDF)
# (x, y, width, height) - Y считается от нижнего края листа, эти координаты не задевают линии!
DOVER_MASKS = [
    # Корешок
    (60, 713.8, 20, 9.5),     # 15
    (107, 713.8, 50, 9.5),    # 13.10
    (176, 713.8, 50, 9.5),    # 20.10
    (259, 713.8, 140, 9.5),   # Мамыкин...
    (64, 663.9, 110, 9.5),    # ООО СТАИРС...

    # Шапка и Даты (Справа)
    (250, 562.0, 25, 10.0),   # 15 (номер)
    (167, 544.5, 50, 9.5),    # 13.10
    (167, 534.6, 50, 9.5),    # 20.10

    # ФИО и Должность
    (204, 440.9, 48, 9.5),    # экспедитор
    (310, 440.9, 140, 9.5),   # Мамыкин...

    # Паспортные данные
    (148, 423.6, 25, 9.5),    # 4621
    (231, 423.6, 45, 9.5),    # № 22318
    (148, 413.6, 160, 9.5),   # ГУ МВД...
    (148, 403.7, 50, 9.5),    # 24.02.2021

    # Поставщик и Счет
    (148, 386.4, 110, 9.5),   # ООО СТАИРС...
    (148, 369.1, 130, 9.5),   # счету №...
]

# Добавляем маски для всех 4 строк таблицы (Колонки: №, Название, Ед, Кол-во)
for ty in [277.6, 267.6, 257.6, 247.6]:
    DOVER_MASKS.append((48, ty, 10, 9.5))      # Col 1
    DOVER_MASKS.append((125, ty, 200, 9.5))    # Col 2
    DOVER_MASKS.append((345, ty, 20, 9.5))     # Col 3
    DOVER_MASKS.append((435, ty, 30, 9.5))     # Col 4


# ТОЧНЫЕ КООРДИНАТЫ НОВОГО ТЕКСТА (вставляется ровно на +1.5 пикселя выше линии)
# Формат: "ключ": (X, Y, "Шрифт", Размер, "выравнивание")
DOVER_FIELDS = {
    # --- КОРЕШОК ---
    "k_number":       (70,  715.0, "Arial", 8.5, "center"),
    "k_date_issue":   (132, 715.0, "Arial", 8.5, "center"),
    "k_date_valid":   (201, 715.0, "Arial", 8.5, "center"),
    "k_person":       (261, 715.0, "Arial", 8.5, "left"),
    "k_supplier":     (67,  665.0, "Arial", 8.5, "left"),

    # --- ОСНОВНАЯ ЧАСТЬ ---
    "number":          (255, 564.0, "Arial-Bold", 9.5, "left"),
    "date_issue":      (190, 546.0, "Arial", 8.5, "center"),
    "date_valid":      (190, 536.0, "Arial", 8.5, "center"),
    
    "position":        (227, 442.0, "Arial", 8.5, "center"),
    "person_fio":      (312, 442.0, "Arial", 8.5, "left"),
    
    "passport_series": (150, 425.0, "Arial", 8.5, "left"),
    "passport_num":    (245, 425.0, "Arial", 8.5, "left"),
    "passport_issued": (150, 415.0, "Arial", 8.5, "left"),
    "passport_date":   (150, 405.0, "Arial", 8.5, "left"),
    
    "supplier":        (150, 388.0, "Arial", 8.5, "left"),
    "invoice":         (150, 370.5, "Arial", 8.5, "left"),
}

# Координаты для таблицы ТМЦ
DOVER_TABLE = {
    "rows_y": [279.0, 269.0, 259.0], # Ровно над линиями таблицы
    "font": "Arial",
    "size": 8.5,
    "cols": {
        "num":  (53,  "center"),
        "name": (128, "left"),
        "unit": (355, "center"),
        "qty":  (450, "center")
    }
}

def generate_certificate(cert_num: str, company_name: str, inn: str, valid_until: str) -> tuple[io.BytesIO, io.BytesIO]:
    if not os.path.exists(CERT_TEMPLATE):
         raise FileNotFoundError(f"Файл {CERT_TEMPLATE} не найден.")
         
    image = Image.open(CERT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, _ = image.size

    font_num = ImageFont.truetype(FONT_FILE_SERIF, size=42)
    font_company = ImageFont.truetype(FONT_FILE_SANS, size=52)
    font_inn = ImageFont.truetype(FONT_FILE_SANS, size=38)
    font_date = ImageFont.truetype(FONT_FILE_BOLD, size=40)

    color_num = (110, 128, 150)
    color_main = (27, 46, 75)

    clean_num = cert_num.strip() if cert_num.strip().startswith("№") else f"№{cert_num.strip()}"
    clean_inn = inn.strip() if inn.strip().upper().startswith("ИНН") else f"ИНН:{inn.strip()}"

    draw.text((width / 2, CERT_Y_NUM), clean_num, font=font_num, fill=color_num, anchor="mm")
    draw.text((width / 2, CERT_Y_COMPANY), company_name.strip(), font=font_company, fill=color_main, anchor="mm")
    draw.text((width / 2, CERT_Y_INN), clean_inn, font=font_inn, fill=color_main, anchor="mm")
    draw.text((CERT_X_DATE, CERT_Y_DATE), valid_until.strip(), font=font_date, fill=color_main, anchor="lm")

    jpg_buffer, pdf_buffer = io.BytesIO(), io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95)
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    
    jpg_buffer.seek(0)
    pdf_buffer.seek(0)
    return jpg_buffer, pdf_buffer


def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
         raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")
         
    # Открываем оригинальный PDF чтобы узнать его размеры
    reader = PdfReader(DOVER_TEMPLATE)
    first_page = reader.pages[0]
    page_w = float(first_page.mediabox.width)
    page_h = float(first_page.mediabox.height)
    
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))
    
    # ШАГ 1: Зачищаем старые данные (Рисуем белые прямоугольники без контура)
    c.setFillColor(white)
    c.setStrokeColor(white)
    for (mx, my, mw, mh) in DOVER_MASKS:
        c.rect(mx, my, mw, mh, fill=1, stroke=0)
        
    # ШАГ 2: Вписываем новые поля
    c.setFillColor(black)
    for key, (fx, fy, font_name, font_size, align) in DOVER_FIELDS.items():
        val = str(data.get(key, "")).strip()
        if not val:
            continue
            
        c.setFont(font_name, font_size)
        if align == "center":
            c.drawCentredString(fx, fy, val)
        elif align == "right":
            c.drawRightString(fx, fy, val)
        else:
            c.drawString(fx, fy, val)
            
    # ШАГ 3: Заполняем таблицу ТМЦ
    c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"])
    for idx, item in enumerate(items[:3]):
        ry = DOVER_TABLE["rows_y"][idx]
        
        # Номер строки (1, 2, 3)
        num_x, _ = DOVER_TABLE["cols"]["num"]
        c.drawCentredString(num_x, ry, str(idx + 1))

        # Наименование
        name_x, _ = DOVER_TABLE["cols"]["name"]
        c.drawString(name_x, ry, str(item.get("name", "")).strip())

        # Единица измерения
        unit_x, _ = DOVER_TABLE["cols"]["unit"]
        c.drawCentredString(unit_x, ry, str(item.get("unit", "")).strip())

        # Количество
        qty_x, _ = DOVER_TABLE["cols"]["qty"]
        c.drawCentredString(qty_x, ry, str(item.get("qty", "")).strip())

    c.save()
    packet.seek(0)
    
    # ШАГ 4: Слияние зачищенного+написанного слоя с оригинальным шаблоном
    new_pdf = PdfReader(packet)
    output = PdfWriter(clone_from=DOVER_TEMPLATE)
    output.pages[0].merge_page(new_pdf.pages[0])
    
    output_stream = io.BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    
    return output_stream
