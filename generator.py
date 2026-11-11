import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white, black
from pypdf import PdfReader, PdfWriter

# ========================================================
# 1. НАСТРОЙКИ СЕРТИФИКАТА (Точно по скриншоту 2252)
# ========================================================
CERT_TEMPLATE = "cert_template.jpg"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

# Координаты под шаблон 1024x759 (cert_template.jpg)
CERT_Y_NUM = 178        # На синей плашке под "СЕРТИФИКАТ ДИЛЕРА"
CERT_Y_COMPANY = 262    # Над чертой (крупно)
CERT_Y_INN = 315        # Над чертой под компанией
CERT_Y_DATE = 471       # В одну строку со "Срок действия сертификата до"
CERT_X_DATE = 562       # Сразу после слова "до "

SIZE_CERT_NUM = 22
SIZE_COMPANY  = 28
SIZE_INN      = 19
SIZE_DATE     = 21

COLOR_CERT_NUM = (142, 160, 182)
COLOR_MAIN     = (27, 46, 75)


def generate_certificate(cert_num: str, company_name: str, inn: str, valid_until: str) -> tuple[io.BytesIO, io.BytesIO]:
    if not os.path.exists(CERT_TEMPLATE):
        raise FileNotFoundError(f"Файл {CERT_TEMPLATE} не найден.")

    image = Image.open(CERT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Автоматическое масштабирование, если разрешение шаблона отличается от 1024px по ширине
    scale_x = width / 1024.0
    scale_y = height / 759.0

    font_num = ImageFont.truetype(FONT_FILE_SERIF, size=int(SIZE_CERT_NUM * scale_y))
    font_company = ImageFont.truetype(FONT_FILE_SANS, size=int(SIZE_COMPANY * scale_y))
    font_inn = ImageFont.truetype(FONT_FILE_SANS, size=int(SIZE_INN * scale_y))
    font_date = ImageFont.truetype(FONT_FILE_BOLD, size=int(SIZE_DATE * scale_y))

    clean_num = cert_num.strip()
    if not clean_num.startswith("№"):
        clean_num = f"№{clean_num}"

    clean_inn = inn.strip()
    if not clean_inn.upper().startswith("ИНН"):
        clean_inn = f"ИНН:{clean_inn}"

    # 1. Номер сертификата
    draw.text((width / 2, CERT_Y_NUM * scale_y), clean_num, font=font_num, fill=COLOR_CERT_NUM, anchor="mm")
    # 2. Название компании (выше линии!)
    draw.text((width / 2, CERT_Y_COMPANY * scale_y), company_name.strip(), font=font_company, fill=COLOR_MAIN, anchor="mm")
    # 3. ИНН (между компанией и линией!)
    draw.text((width / 2, CERT_Y_INN * scale_y), clean_inn, font=font_inn, fill=COLOR_MAIN, anchor="mm")
    # 4. Дата окончания
    draw.text((CERT_X_DATE * scale_x, CERT_Y_DATE * scale_y), valid_until.strip(), font=font_date, fill=COLOR_MAIN, anchor="lm")

    jpg_buffer = io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95)
    jpg_buffer.seek(0)

    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)

    return jpg_buffer, pdf_buffer


# ========================================================
# 2. НАСТРОЙКИ ДОВЕРЕННОСТИ М-2 (ЗАЧИСТКА + ЗАПОЛНЕНИЕ)
# ========================================================
DOVER_TEMPLATE = "МИШКА Доверенность м2 с печатями и подписью заполнять в середине-4.pdf"

try:
    pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов Arial для PDF: {e}")

# Белые прямоугольники (x, y, width, height) для зачистки старых данных ("15", "Мамыкин...", "Лестница..." и т.д.)
# Координаты заданы в системе PDF (0,0 — левый нижний угол листа A4 595.27 x 841.89)
DOVER_MASKS = [
    # 1. Таблица корешка (верхняя часть)
    (25, 746, 52, 16),     # Старый номер "15" в корешке
    (82, 746, 65, 16),     # Старая дата выдачи "13.10.2026"
    (152, 746, 68, 16),    # Старый срок "20.10.2026"
    (225, 746, 210, 16),   # Старое ФИО "Мамыкин Алексей Константинович"
    (25, 688, 195, 18),    # Старый поставщик "ООО СТАИРС ПРОФИ" в корешке
    (225, 688, 150, 18),   # Графа 7 корешка (номер и дата наряда/счета)

    # 2. Основная часть доверенности (середина)
    (305, 590, 60, 18),    # Старый номер "15" после "ДОВЕРЕННОСТЬ №"
    (128, 563, 85, 14),    # Старая дата выдачи "13.10.2026"
    (218, 545, 85, 14),    # Старый срок действия "20.10.2026"
    (138, 434, 95, 14),    # Старая должность "экспедитор"
    (242, 434, 280, 14),   # Старое ФИО "Мамыкин Алексей Константинович"
    (120, 415, 55, 14),    # Серия паспорта "4621"
    (205, 415, 80, 14),    # Номер паспорта "22318"
    (105, 398, 380, 14),   # Кем выдан "ГУ МВД России по Московской области"
    (115, 380, 120, 14),   # Дата выдачи паспорта "24.02.2021"
    (132, 362, 380, 14),   # На получение от "ООО СТАИРС ПРОФИ"
    (178, 344, 340, 14),   # Материальных ценностей по "счету №1397 от 01 октября 2026"

    # 3. Таблица ТМЦ (зачищаем строки 1, 2, 3 внутри границ ячеек)
    (68, 250, 295, 15), (370, 250, 58, 15), (435, 250, 125, 15), # Строка 1 (Лестница... | 100)
    (68, 231, 295, 15), (370, 231, 58, 15), (435, 231, 125, 15), # Строка 2 (Заглушка... | Шт | 400)
    (68, 212, 295, 15), (370, 212, 58, 15), (435, 212, 125, 15), # Строка 3
]

# Точные координаты вставки нового текста: (x, y, font_name, font_size, align)
DOVER_FIELDS = {
    # --- КОРЕШОК ---
    "k_number":       (51,  750, "Arial", 9, "center"),
    "k_date_issue":   (114, 750, "Arial", 9, "center"),
    "k_date_valid":   (186, 750, "Arial", 9, "center"),
    "k_person":       (230, 750, "Arial", 8.5, "left"),
    "k_supplier":     (30,  693, "Arial", 9, "left"),
    "k_invoice":      (230, 693, "Arial", 8.5, "left"),

    # --- ОСНОВНАЯ ЧАСТЬ ---
    "number":          (312, 594, "Arial-Bold", 11, "left"),
    "date_issue":      (132, 566, "Arial", 9.5, "left"),
    "date_valid":      (222, 548, "Arial", 9.5, "left"),
    "position":        (185, 437, "Arial", 9.5, "center"),
    "person_fio":      (250, 437, "Arial", 9.5, "left"),
    "passport_series": (145, 418, "Arial", 9.5, "center"),
    "passport_num":    (240, 418, "Arial", 9.5, "center"),
    "passport_issued": (112, 401, "Arial", 9.5, "left"),
    "passport_date":   (122, 383, "Arial", 9.5, "left"),
    "supplier":        (140, 365, "Arial", 9.5, "left"),
    "invoice":         (184, 347, "Arial", 9.5, "left"),
}

# Координаты строк таблицы ТМЦ (до 3 строк)
DOVER_TABLE = {
    "rows_y": [254, 235, 216],  # Y-координаты для 1-й, 2-й и 3-й строки
    "font": "Arial",
    "size": 9,
    "cols": {
        "num":  (44,  "center"), # Колонка 1: № п/п
        "name": (72,  "left"),   # Колонка 2: Материальные ценности
        "unit": (399, "center"), # Колонка 3: Ед. изм.
        "qty":  (498, "center"), # Колонка 4: Количество
    }
}


def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
        raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")

    reader = PdfReader(DOVER_TEMPLATE)
    first_page = reader.pages[0]
    page_w = float(first_page.mediabox.width)
    page_h = float(first_page.mediabox.height)

    # Масштабируем на случай, если PDF сохранен в нестандартном размере
    sx = page_w / 595.27
    sy = page_h / 841.89

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    # ШАГ 1: Зачищаем старые данные белыми плашками
    c.setFillColor(white)
    c.setStrokeColor(white)
    for (mx, my, mw, mh) in DOVER_MASKS:
        c.rect(mx * sx, my * sy, mw * sx, mh * sy, fill=1, stroke=0)

    # ШАГ 2: Вписываем новые поля тем же шрифтом и размером
    c.setFillColor(black)
    for key, (fx, fy, font_name, font_size, align) in DOVER_FIELDS.items():
        val = str(data.get(key, "")).strip()
        if not val:
            continue
        c.setFont(font_name, font_size * sy)
        if align == "center":
            c.drawCentredString(fx * sx, fy * sy, val)
        else:
            c.drawString(fx * sx, fy * sy, val)

    # ШАГ 3: Заполняем таблицу ТМЦ (до 3 позиций)
    c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"] * sy)
    for idx, item in enumerate(items[:3]):
        ry = DOVER_TABLE["rows_y"][idx] * sy
        
        # Номер строки (в 3-й строке дописываем "3", если заполнена)
        num_x, _ = DOVER_TABLE["cols"]["num"]
        c.drawCentredString(num_x * sx, ry, str(idx + 1))

        # Наименование товара
        name_x, _ = DOVER_TABLE["cols"]["name"]
        c.drawString(name_x * sx, ry, str(item.get("name", "")).strip())

        # Единица измерения
        unit_x, _ = DOVER_TABLE["cols"]["unit"]
        c.drawCentredString(unit_x * sx, ry, str(item.get("unit", "")).strip())

        # Количество
        qty_x, _ = DOVER_TABLE["cols"]["qty"]
        c.drawCentredString(qty_x * sx, ry, str(item.get("qty", "")).strip())

    c.save()
    packet.seek(0)

    # ШАГ 4: Безопасное слияние для pypdf >= 4.0 / 7.0+
    overlay_reader = PdfReader(packet)
    writer = PdfWriter(clone_from=DOVER_TEMPLATE)
    writer.pages[0].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return output_stream
