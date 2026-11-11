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
FONT_FILE_CALIBRI = "calibri.ttf"
FONT_FILE_CALIBRI_BOLD = "calibrib.ttf"

try:
    pdfmetrics.registerFont(TTFont("Times", FONT_FILE_SERIF))
    pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))
    pdfmetrics.registerFont(TTFont("Calibri", FONT_FILE_CALIBRI))
    pdfmetrics.registerFont(TTFont("Calibri-Bold", FONT_FILE_CALIBRI_BOLD))
except Exception as e:
    print(f"Внимание: Ошибка загрузки некоторых шрифтов (убедитесь, что arial, times, calibri.ttf лежат в папке): {e}")

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
    
    data_map = {"number": clean_num, "company": company_name.strip(), "inn": clean_inn, "date": valid_until.strip()}

    for key, val in data_map.items():
        fx, fy, fname, fsize, fcolor, fanchor = CERT_FIELDS[key]
        try:
            font = ImageFont.truetype(fname, size=int(fsize * sy))
        except:
            font = ImageFont.load_default()
        draw.text((fx * sx, fy * sy), val, font=font, fill=fcolor, anchor=fanchor)

    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)
    return pdf_buffer


# ========================================================
# 2. НАСТРОЙКИ ДОВЕРЕННОСТИ
# ========================================================
DOVER_TEMPLATE = "dover_template.pdf"
DOVER_FIELDS = {
    "k_number":       (62, 714, "Arial", 8.04, "left"),
    "k_date_issue":   (110, 714, "Arial", 8.04, "left"),
    "k_date_valid":   (179, 714, "Arial", 8.04, "left"),
    "k_person":       (261, 714, "Arial", 8.04, "left"),
    "k_supplier":     (67, 664, "Arial", 8.04, "left"),
    
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
    "font": "Arial", "size": 6.0,
    "cols": {
        "num":  (51,  "left"), "name": (128, "left"),
        "unit": (349, "left"), "qty":  (443, "left"),
    }
}

def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
        raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")

    reader = PdfReader(DOVER_TEMPLATE)
    page_w = float(reader.pages[0].mediabox.width)
    page_h = float(reader.pages[0].mediabox.height)
    sx, sy = page_w / 612.0, page_h / 792.0 

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))
    c.setFillColor(black)

    for key, (fx, fy, font_name, font_size, align) in DOVER_FIELDS.items():
        val = str(data.get(key, "")).strip()
        if val:
            try: c.setFont(font_name, font_size * sy)
            except: pass
            if align == "center": c.drawCentredString(fx * sx, fy * sy, val)
            elif align == "right": c.drawRightString(fx * sx, fy * sy, val)
            else: c.drawString(fx * sx, fy * sy, val)

    try: c.setFont(DOVER_TABLE["font"], DOVER_TABLE["size"] * sy)
    except: pass
        
    for idx, item in enumerate(items[:3]):
        ry = DOVER_TABLE["rows_y"][idx] * sy
        c.drawString(DOVER_TABLE["cols"]["num"][0] * sx, ry, str(idx + 1))
        c.drawString(DOVER_TABLE["cols"]["name"][0] * sx, ry, str(item.get("name", "")).strip())
        c.drawString(DOVER_TABLE["cols"]["unit"][0] * sx, ry, str(item.get("unit", "")).strip())
        c.drawString(DOVER_TABLE["cols"]["qty"][0] * sx, ry, str(item.get("qty", "")).strip())

    c.save()
    packet.seek(0)
    overlay_reader = PdfReader(packet)
    writer = PdfWriter(clone_from=DOVER_TEMPLATE)
    writer.pages[0].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream


# ========================================================
# 3. НАСТРОЙКИ ДОГОВОРА (PDF)
# ========================================================
CONTRACT_TEMPLATE = "contract_template.pdf"

# Координаты для Договора (шрифт изменен на Calibri 10.5)
CONTRACT_FIELDS = {
    0: [
        (216.11, 708.81, "number", "Calibri-Bold", 13.9),
        (466.15, 687.39, "date_start", "Calibri-Bold", 10.5),
        (57.60, 633.15, "company_header", "Calibri", 10.5),
        (57.60, 618.51, "fio_gen_dir", "Calibri", 10.5),
    ],
    4: [
        (57.60, 626.67, "date_end", "Calibri", 10.5),
    ],
    5: [
        (311.03, 672.99, "company", "Calibri-Bold", 10.5),
        (311.03, 648.27, "address", "Calibri", 10.5),
        (311.03, 608.91, "inn_kpp", "Calibri", 10.5),
        (311.03, 584.19, "bank_account", "Calibri", 10.5),
        (311.03, 559.47, "bank_name", "Calibri", 10.5),
        (311.03, 534.75, "corr_account", "Calibri", 10.5),
        (311.03, 510.03, "bik", "Calibri", 10.5),
        (311.03, 485.07, "phone", "Calibri", 10.5),
        (311.03, 391.47, "fio_short", "Calibri", 10.5),
    ],
    6: [
        (187.61, 701.31, "c_number", "Calibri-Bold", 10.5),
    ],
    7: [
        (57.60, 287.79, "fio_short", "Calibri", 10.5),
    ],
    8: [
        (187.61, 701.31, "c_number", "Calibri-Bold", 10.5),
        (57.60, 368.67, "fio_short", "Calibri", 10.5),
    ],
    9: [
        (187.61, 701.31, "c_number", "Calibri-Bold", 10.5),
    ],
    10: [
        (57.60, 300.99, "fio_short", "Calibri", 10.5),
    ]
}

def generate_contract(data: dict) -> io.BytesIO:
    if not os.path.exists(CONTRACT_TEMPLATE):
        raise FileNotFoundError(f"Файл {CONTRACT_TEMPLATE} не найден.")

    reader = PdfReader(CONTRACT_TEMPLATE)
    writer = PdfWriter(clone_from=CONTRACT_TEMPLATE)

    for page_idx, fields in CONTRACT_FIELDS.items():
        if page_idx >= len(reader.pages):
            continue
            
        page = reader.pages[page_idx]
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)
        
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_w, page_h))
        c.setFillColor(black)

        for fx, fy, key, font_name, font_size in fields:
            val = data.get(key, "")
            if not val:
                continue
                
            try:
                c.setFont(font_name, font_size)
            except:
                pass
                
            # Обработка многострочного адреса
            if key == "address" and "\n" in val:
                parts = val.split("\n")
                c.drawString(fx, fy, parts[0])
                c.drawString(fx, fy - (font_size * 1.2), parts[1])
            elif key == "fio_short" and page_idx in [7, 8, 10]:
                c.drawString(fx + 300, fy, val)
            else:
                c.drawString(fx, fy, val)

        c.save()
        packet.seek(0)
        
        overlay_reader = PdfReader(packet)
        writer.pages[page_idx].merge_page(overlay_reader.pages[0])

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream
