import io
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import white, black
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont

# ========================================================
# 1. НАСТРОЙКИ СЕРТИФИКАТА (PILLOW + PYPDF)
# ========================================================
CERT_TEMPLATE = "cert_template.jpg"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

try:
    pdfmetrics.registerFont(TTFont("Times", FONT_FILE_SERIF))
    pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов для PDF: {e}")

# Координаты для чистого jpg сертификата (1024x723)
# - номер поднял выше (178 -> 150)
# - компанию опустил ниже (260 -> 290)
# - инн тоже немного опустил (327 -> 335) чтобы смотрелось гармонично над чертой
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
# 2. НАСТРОЙКИ ДОВЕРЕННОСТИ (PDF)
# ========================================================
DOVER_TEMPLATE = "dover_template.pdf"

# Текст вставляется поверх ЧИСТОГО шаблона, белые маски не нужны
# Формат: "ключ": (X, Y, "Шрифт", Размер, "выравнивание")
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
