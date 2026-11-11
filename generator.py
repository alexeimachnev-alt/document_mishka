import io
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white
from pypdf import PdfReader, PdfWriter

# ========================================================
# 1. НАСТРОЙКИ СЕРТИФИКАТА (PDF)
# ========================================================
CERT_TEMPLATE = "cert_template.pdf"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

try:
    pdfmetrics.registerFont(TTFont("Times", FONT_FILE_SERIF))
    pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов для PDF: {e}")

# Белые прямоугольники (x, y, width, height) для зачистки старых данных в сертификате
CERT_MASKS = [
    (350, 440, 150, 30),  # Зачистка номера "№2708/25"
    (150, 310, 540, 40),  # Зачистка "ООО фирма Мосводопром"
    (300, 275, 240, 25),  # Зачистка "ИНН:7721023832"
    (490, 205, 120, 25),  # Зачистка даты "27.08.2026"
]

# Координаты нового текста: (x, y, font_name, font_size, align)
CERT_FIELDS = {
    "number":  (421, 448, "Times", 24, "center"),
    "company": (421, 320, "Arial", 28, "center"),
    "inn":     (421, 282, "Arial", 18, "center"),
    "date":    (500, 212, "Arial-Bold", 16, "left"),
}

def generate_certificate(cert_num: str, company_name: str, inn: str, valid_until: str) -> io.BytesIO:
    if not os.path.exists(CERT_TEMPLATE):
        raise FileNotFoundError(f"Файл {CERT_TEMPLATE} не найден.")

    # Используем размер листа из оригинального PDF
    reader = PdfReader(CERT_TEMPLATE)
    first_page = reader.pages[0]
    page_w = float(first_page.mediabox.width)
    page_h = float(first_page.mediabox.height)

    # При необходимости масштабируем координаты под фактический размер (стандарт A4 Landscape ~ 842x595)
    sx = page_w / 841.89
    sy = page_h / 595.27

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    # 1. Зачищаем старые данные
    c.setFillColor(white)
    c.setStrokeColor(white)
    for (mx, my, mw, mh) in CERT_MASKS:
        c.rect(mx * sx, my * sy, mw * sx, mh * sy, fill=1, stroke=0)

    # Форматируем данные
    clean_num = cert_num.strip() if cert_num.strip().startswith("№") else f"№{cert_num.strip()}"
    clean_inn = inn.strip() if inn.strip().upper().startswith("ИНН") else f"ИНН:{inn.strip()}"

    data = {
        "number": clean_num,
        "company": company_name.strip(),
        "inn": clean_inn,
        "date": valid_until.strip()
    }

    # 2. Вписываем новый текст
    for key, (fx, fy, font_name, font_size, align) in CERT_FIELDS.items():
        val = data.get(key, "")
        if not val:
            continue
        c.setFont(font_name, font_size * sy)
        if key == "number":
            c.setFillColorRGB(0.55, 0.62, 0.71) # Приглушенный серо-голубой для номера
        else:
            c.setFillColorRGB(0.1, 0.18, 0.29) # Темно-синий цвет шрифта

        if align == "center":
            c.drawCentredString(fx * sx, fy * sy, val)
        else:
            c.drawString(fx * sx, fy * sy, val)

    c.save()
    packet.seek(0)

    # 3. Слияние (безопасный метод pypdf 7.0+)
    overlay_reader = PdfReader(packet)
    writer = PdfWriter(clone_from=CERT_TEMPLATE)
    writer.pages[0].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return output_stream


# ========================================================
# 3. НАСТРОЙКИ ДОВЕРЕННОСТИ
# ========================================================
DOVER_TEMPLATE = "dover_template.pdf"

# Координаты для зачистки белым квадратом
DOVER_MASKS = [
    (25, 746, 52, 16), (82, 746, 65, 16), (152, 746, 68, 16), (225, 746, 210, 16),
    (25, 688, 195, 18), (225, 688, 150, 18), (305, 590, 60, 18), (128, 563, 85, 14),
    (218, 545, 85, 14), (138, 434, 95, 14), (242, 434, 280, 14), (120, 415, 55, 14),
    (205, 415, 80, 14), (105, 398, 380, 14), (115, 380, 120, 14), (132, 362, 380, 14),
    (178, 344, 340, 14), (68, 250, 295, 15), (370, 250, 58, 15), (435, 250, 125, 15),
    (68, 231, 295, 15), (370, 231, 58, 15), (435, 231, 125, 15), (68, 212, 295, 15),
    (370, 212, 58, 15), (435, 212, 125, 15),
]

# Формат: "ключ": (X, Y, "Шрифт", Размер, "выравнивание")
DOVER_FIELDS = {
    "k_number":       (51,  750, "Arial", 9, "center"),
    "k_date_issue":   (114, 750, "Arial", 9, "center"),
    "k_date_valid":   (186, 750, "Arial", 9, "center"),
    "k_person":       (230, 750, "Arial", 8.5, "left"),
    "k_supplier":     (30,  693, "Arial", 9, "left"),
    "k_invoice":      (230, 693, "Arial", 8.5, "left"),
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

DOVER_TABLE = {
    "rows_y": [254, 235, 216],
    "font": "Arial", "size": 9,
    "cols": {
        "num":  (44,  "center"), "name": (72,  "left"),
        "unit": (399, "center"), "qty":  (498, "center"),
    }
}

def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
        raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")

    reader = PdfReader(DOVER_TEMPLATE)
    page_w = float(reader.pages[0].mediabox.width)
    page_h = float(reader.pages[0].mediabox.height)
    sx, sy = page_w / 595.27, page_h / 841.89

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    c.setFillColor(white)
    c.setStrokeColor(white)
    for (mx, my, mw, mh) in DOVER_MASKS:
        c.rect(mx * sx, my * sy, mw * sx, mh * sy, fill=1, stroke=0)

    c.setFillColorRGB(0, 0, 0)
    for key, (fx, fy, font_name, font_size, align) in DOVER_FIELDS.items():
        val = str(data.get(key, "")).strip()
        if val:
            c.setFont(font_name, font_size * sy)
            if align == "center":
                c.drawCentredString(fx * sx, fy * sy, val)
            elif align == "right":
                c.drawRightString(fx * sx, fy * sy, val)
            else:
                c.drawString(fx * sx, fy * sy, val)

    c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"] * sy)
    for idx, item in enumerate(items[:3]):
        ry = DOVER_TABLE["rows_y"][idx] * sy
        c.drawCentredString(DOVER_TABLE["cols"]["num"][0] * sx, ry, str(idx + 1))
        c.drawString(DOVER_TABLE["cols"]["name"][0] * sx, ry, str(item.get("name", "")).strip())
        c.drawCentredString(DOVER_TABLE["cols"]["unit"][0] * sx, ry, str(item.get("unit", "")).strip())
        c.drawCentredString(DOVER_TABLE["cols"]["qty"][0] * sx, ry, str(item.get("qty", "")).strip())

    c.save()
    packet.seek(0)

    overlay_reader = PdfReader(packet)
    writer = PdfWriter(clone_from=DOVER_TEMPLATE)
    writer.pages[0].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream
