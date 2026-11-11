import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white, black
from pypdf import PdfReader, PdfWriter

# ========================================================
# 1. НАСТРОЙКИ СЕРТИФИКАТА (PILLOW -> PDF)
# ========================================================
CERT_TEMPLATE = "cert_template.jpg"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

# Координаты для чистого jpg сертификата (1024x723)
CERT_FIELDS = {
    "number":  (512, 150, "times.ttf", 25, (142, 160, 182), "mm"),
    "company": (512, 290, "arial.ttf", 30, (27, 46, 75), "mm"),
    "inn":     (512, 335, "arial.ttf", 22, (27, 46, 75), "mm"),
    "date":    (566, 521, "arialbd.ttf", 23, (27, 46, 75), "lm"),
}

def generate_certificate(cert_num: str, company_name: str, inn: str, valid_until: str) -> io.BytesIO:
    if not os.path.exists(CERT_TEMPLATE):
        raise FileNotFoundError(f"Файл {CERT_TEMPLATE} не найден.")

    image = Image.open(CERT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    sx = width / 1024.0
    sy = height / 723.0

    clean_num = cert_num.strip() if cert_num.strip().startswith("№") else f"№{cert_num.strip()}"
    clean_inn = inn.strip() if inn.strip().upper().startswith("ИНН") else f"ИНН:{inn.strip()}"

    data = {
        "number": clean_num,
        "company": company_name.strip(),
        "inn": clean_inn,
        "date": valid_until.strip()
    }

    # Пишем текст прямо на jpg
    for key, (fx, fy, font_name, font_size, fcolor, anchor) in CERT_FIELDS.items():
        val = data.get(key, "")
        if not val:
            continue
        try:
            font = ImageFont.truetype(font_name, size=int(font_size * sy))
        except:
            font = ImageFont.load_default()
            
        draw.text((fx * sx, fy * sy), val, font=font, fill=fcolor, anchor=anchor)

    # Сохраняем сразу в PDF (для унификации выдачи бота)
    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)

    return pdf_buffer


# ========================================================
# 2. НАСТРОЙКИ ДОВЕРЕННОСТИ (PDF + Белые маски)
# ========================================================
DOVER_TEMPLATE = "МИШКА Доверенность м2 с печатями и подписью заполнять в середине-4.pdf"

try:
    pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов для PDF: {e}")

# ВОЗВРАЩЕНЫ БЕЛЫЕ МАСКИ ДЛЯ ЗАЧИСТКИ (идеально работало в версии 3)
DOVER_MASKS = [
    (25, 746, 52, 16), (82, 746, 65, 16), (152, 746, 68, 16), (225, 746, 210, 16),
    (25, 688, 195, 18), (225, 688, 150, 18), (305, 590, 60, 18), (128, 563, 85, 14),
    (218, 545, 85, 14), (138, 434, 95, 14), (242, 434, 280, 14), (120, 415, 55, 14),
    (205, 415, 80, 14), (105, 398, 380, 14), (115, 380, 120, 14), (132, 362, 380, 14),
    (178, 344, 340, 14), 
    # Маски для таблицы
    (48, 277.6, 10, 9.5), (125, 277.6, 200, 9.5), (345, 277.6, 20, 9.5), (435, 277.6, 30, 9.5),
    (48, 267.6, 10, 9.5), (125, 267.6, 200, 9.5), (345, 267.6, 20, 9.5), (435, 267.6, 30, 9.5),
    (48, 257.6, 10, 9.5), (125, 257.6, 200, 9.5), (345, 257.6, 20, 9.5), (435, 257.6, 30, 9.5),
    (48, 247.6, 10, 9.5), (125, 247.6, 200, 9.5), (345, 247.6, 20, 9.5), (435, 247.6, 30, 9.5),
]

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

DOVER_TABLE = {
    "rows_y": [279.0, 269.0, 259.0],
    "font": "Arial", "size": 8.5,
    "cols": {
        "num":  (53,  "center"), "name": (128, "left"),
        "unit": (355, "center"), "qty":  (450, "center"),
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

    # ЗАКРАШИВАЕМ СТАРЫЕ ДАННЫЕ БЕЛЫМИ ПЛАШКАМИ (Возврат к надежной логике)
    c.setFillColor(white)
    c.setStrokeColor(white)
    for (mx, my, mw, mh) in DOVER_MASKS:
        c.rect(mx * sx, my * sy, mw * sx, mh * sy, fill=1, stroke=0)

    # НАКЛАДЫВАЕМ НОВЫЕ ДАННЫЕ
    c.setFillColor(black)
    for key, (fx, fy, font_name, font_size, align) in DOVER_FIELDS.items():
        val = str(data.get(key, "")).strip()
        if val:
            try:
                c.setFont(font_name, font_size * sy)
            except:
                pass
            if align == "center":
                c.drawCentredString(fx * sx, fy * sy, val)
            elif align == "right":
                c.drawRightString(fx * sx, fy * sy, val)
            else:
                c.drawString(fx * sx, fy * sy, val)

    try:
        c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"] * sy)
    except:
        pass
        
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
