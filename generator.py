import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from pypdf import PdfReader, PdfWriter

# ========================================================
# 1. НАСТРОЙКИ СЕРТИФИКАТА 
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

CERT_FIELDS = {
    "number":  (512, 140, "times.ttf", 25, (142, 160, 182), "mm"),
    "company": (512, 275, "arial.ttf", 30, (27, 46, 75), "mm"),
    "inn":     (512, 335, "arial.ttf", 22, (27, 46, 75), "mm"),
    "date":    (566, 521, "arialbd.ttf", 23, (27, 46, 75), "lm"),
}

def generate_certificate(cert_num: str, company_name: str, inn: str, valid_until: str) -> io.BytesIO:
    if not os.path.exists(CERT_TEMPLATE):
        raise FileNotFoundError(f"Файл {CERT_TEMPLATE} не найден.")

    image = Image.open(CERT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    sx, sy = width / 1024.0, height / 723.0

    clean_num = cert_num.strip() if cert_num.strip().startswith("№") else f"№{cert_num.strip()}"
    clean_inn = inn.strip() if inn.strip().upper().startswith("ИНН") else f"ИНН:{inn.strip()}"

    data = {"number": clean_num, "company": company_name.strip(), "inn": clean_inn, "date": valid_until.strip()}

    for key, (fx, fy, font_name, font_size, fcolor, anchor) in CERT_FIELDS.items():
        val = data.get(key, "")
        if not val: continue
        try:
            font = ImageFont.truetype(font_name, size=int(font_size * sy))
        except:
            font = ImageFont.load_default()
        draw.text((fx * sx, fy * sy), val, font=font, fill=fcolor, anchor=anchor)

    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)
    return pdf_buffer


# ========================================================
# 2. НАСТРОЙКИ ДОВЕРЕННОСТИ (PDF)
# ========================================================
# ВАЖНО: Используй скачанный dover_template.pdf (он полностью зачищен программно)
DOVER_TEMPLATE = "dover_template.pdf"

# Идеальные координаты, вытащенные прямо из исходного PDF
DOVER_FIELDS = {
    # --- КОРЕШОК ---
    "k_number":       (62, 714, "Arial", 8.04, "left"),
    "k_date_issue":   (110, 714, "Arial", 8.04, "left"),
    "k_date_valid":   (179, 714, "Arial", 8.04, "left"),
    "k_person":       (261, 714, "Arial", 8.04, "left"),
    "k_supplier":     (67, 664, "Arial", 8.04, "left"),
    "k_invoice":      (225, 664, "Arial", 8.04, "left"),
    
    # --- ОСНОВНАЯ ЧАСТЬ ---
    "number":          (254, 562, "Arial-Bold", 9.0, "left"),
    "date_issue":      (170, 545, "Arial", 8.04, "left"),
    "date_valid":      (170, 535, "Arial", 8.04, "left"),
    "position":        (206, 441, "Arial", 8.04, "left"),
    "person_fio":      (313, 441, "Arial", 8.04, "left"),
    "passport_series": (150, 424, "Arial", 8.04, "left"),
    "passport_num":    (254, 424, "Arial", 8.04, "left"),
    "passport_issued": (150, 414, "Arial", 8.04, "left"),
    "passport_date":   (150, 404, "Arial", 8.04, "left"),
    "supplier":        (150, 387, "Arial", 8.04, "left"),
    "invoice":         (150, 369, "Arial", 8.04, "left"),
}

DOVER_TABLE = {
    "rows_y": [279, 269, 259],
    "font": "Arial", 
    "size": 6.0,
    "cols": {
        "num":  (51,  "left"),
        "name": (128, "left"),
        "unit": (349, "left"),
        "qty":  (443, "left"),
    }
}

def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
        raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")

    reader = PdfReader(DOVER_TEMPLATE)
    page_w = float(reader.pages[0].mediabox.width)
    page_h = float(reader.pages[0].mediabox.height)
    sx, sy = page_w / 612.0, page_h / 792.0 # Исходный размер документа (Letter)

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))
    c.setFillColor(black)

    # Заполняем поля (без всяких белых масок)
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

    # Заполняем таблицу ТМЦ
    try:
        c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"] * sy)
    except:
        pass
        
    for idx, item in enumerate(items[:3]):
        ry = DOVER_TABLE["rows_y"][idx] * sy
        c.drawString(DOVER_TABLE["cols"]["num"][0] * sx, ry, str(idx + 1))
        c.drawString(DOVER_TABLE["cols"]["name"][0] * sx, ry, str(item.get("name", "")).strip())
        c.drawString(DOVER_TABLE["cols"]["unit"][0] * sx, ry, str(item.get("unit", "")).strip())
        c.drawString(DOVER_TABLE["cols"]["qty"][0] * sx, ry, str(item.get("qty", "")).strip())

    c.save()
    packet.seek(0)

    # Накладываем текст
    overlay_reader = PdfReader(packet)
    writer = PdfWriter(clone_from=DOVER_TEMPLATE)
    writer.pages[0].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    
    return output_stream
