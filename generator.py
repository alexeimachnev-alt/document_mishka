import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

# ========================================================
# НАСТРОЙКИ СЕРТИФИКАТА (PILLOW)
# ========================================================
CERT_TEMPLATE = "cert_template.jpg"
FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

# ========================================================
# НАСТРОЙКИ ДОВЕРЕННОСТИ (REPORTLAB - PDF)
# ========================================================
DOVER_TEMPLATE = "МИШКА Доверенность м2 с печатями и подписью заполнять в середине-4.pdf"

try:
    pdfmetrics.registerFont(TTFont('Arial', FONT_FILE_SANS))
    pdfmetrics.registerFont(TTFont('Arial-Bold', FONT_FILE_BOLD))
except Exception as e:
    print(f"Ошибка загрузки шрифтов Arial для PDF: {e}")

DOVER_COORDS = {
    # --- ЛЕВЫЙ КОРЕШОК ---
    "k_number": (50, 720),
    "k_date_issue": (100, 695),
    "k_date_valid": (100, 680),
    "k_person": (50, 650),
    "k_supplier": (50, 580),
    "k_invoice": (50, 550),

    # --- ОСНОВНАЯ ЧАСТЬ ---
    "number": (440, 638),
    "date_issue": (150, 615),
    "date_valid": (430, 615),
    
    "position": (150, 525),
    "person_fio": (150, 508),
    
    "passport_series": (160, 485),
    "passport_num": (240, 485),
    "passport_issued": (150, 465),
    "passport_date": (150, 445),
    
    "supplier": (180, 425),
    "invoice": (250, 410),
}

DOVER_TABLE = {
    "start_y": 340,
    "step_y": 20,
    "cols": {
        "num": 40,
        "name": 100,
        "unit": 380,
        "qty": 450
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

    draw.text((width / 2, 242), clean_num, font=font_num, fill=color_num, anchor="mm")
    draw.text((width / 2, 445), company_name.strip(), font=font_company, fill=color_main, anchor="mm")
    draw.text((width / 2, 560), clean_inn, font=font_inn, fill=color_main, anchor="mm")
    draw.text((970, 893), valid_until.strip(), font=font_date, fill=color_main, anchor="lm")

    jpg_buffer, pdf_buffer = io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95)
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    
    jpg_buffer.seek(0)
    pdf_buffer.seek(0)
    return jpg_buffer, pdf_buffer


def generate_doverennost(data: dict, items: list) -> io.BytesIO:
    if not os.path.exists(DOVER_TEMPLATE):
         raise FileNotFoundError(f"Файл {DOVER_TEMPLATE} не найден.")
         
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(595.27, 841.89))
    c.setFont("Arial", 10)
    
    for key, coords in DOVER_COORDS.items():
        if key in data and data[key]:
            c.drawString(coords[0], coords[1], str(data[key]))
            
    current_y = DOVER_TABLE["start_y"]
    for i, item in enumerate(items[:3], start=1):
        c.drawString(DOVER_TABLE["cols"]["num"], current_y, str(i))
        c.drawString(DOVER_TABLE["cols"]["name"], current_y, item.get("name", ""))
        c.drawString(DOVER_TABLE["cols"]["unit"], current_y, item.get("unit", ""))
        c.drawString(DOVER_TABLE["cols"]["qty"], current_y, item.get("qty", ""))
        current_y -= DOVER_TABLE["step_y"]
            
    c.save()
    packet.seek(0)
    
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(DOVER_TEMPLATE, "rb"))
    output = PdfWriter()
    
    page1 = existing_pdf.pages[0]
    page1.merge_page(new_pdf.pages[0])
    output.add_page(page1)
    
    if len(existing_pdf.pages) > 1:
        output.add_page(existing_pdf.pages[1])
        
    output_stream = io.BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    
    return output_stream
