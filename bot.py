import os
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.web_app_info import WebAppInfo
import urllib.request
import threading
import time

from generator import generate_certificate, generate_doverennost, generate_contract

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://mishka-doc-bot.onrender.com/app")
PING_URL = os.getenv("PING_URL", "https://mishka-doc-bot.onrender.com")

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

# --- Автопингер (чтобы Render не засыпал) ---
def pinger():
    while True:
        time.sleep(600)  # Пинг каждые 10 минут
        try:
            url = PING_URL if PING_URL.startswith('http') else 'https://' + PING_URL
            urllib.request.urlopen(url)
            print(f"Pinged {url} successfully.")
        except Exception as e:
            print(f"Ping error: {e}")

# --- Обработчик команды /start ---
@dp.message(CommandStart())
async def start_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ МАГИЯ ДОКУМЕНТОВ ✨", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "👋 **Генератор документов МИШКА**\n\n"
        "Нажми на кнопку «✨ МАГИЯ ДОКУМЕНТОВ ✨», чтобы открыть приложение и сгенерировать Сертификат, Доверенность или Договор в 1 клик!",
        reply_markup=kb
    )

# --- Web Server Endpoints ---
async def healthcheck(request):
    return web.Response(text="Doc Bot is running 24/7!")

async def index_html(request):
    # Отдаем HTML страницу нашего Mini App
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def api_generate(request):
    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        doc_type = data.get("doc_type")
        form = data.get("form", {})

        if not chat_id:
            return web.json_response({"error": "No chat_id provided"}, status=400)

        # Отправляем сообщение о начале генерации
        await bot.send_message(chat_id, "⏳ Творим магию... Документ скоро будет готов!")

        # --- СЕРТИФИКАТ ---
        if doc_type == "cert":
            pdf_buf = generate_certificate(
                form.get("number", ""),
                form.get("company", ""),
                form.get("inn", ""),
                form.get("date", "")
            )
            await bot.send_document(
                chat_id,
                BufferedInputFile(pdf_buf.getvalue(), filename=f"Сертификат_{form.get('number', '0').replace('/', '_')}.pdf"),
                caption="✅ Сертификат дилера успешно сгенерирован!"
            )

        # --- ДОВЕРЕННОСТЬ ---
        elif doc_type == "dover":
            today = datetime.now()
            date_issue = today.strftime("%d.%m.%Y")
            date_valid = (today + timedelta(days=7)).strftime("%d.%m.%Y")
            
            form["date_issue"] = date_issue
            form["date_valid"] = date_valid
            form["k_number"] = form.get("number", "")
            form["k_date_issue"] = date_issue
            form["k_date_valid"] = date_valid
            form["k_person"] = form.get("person_fio", "")
            form["k_supplier"] = form.get("supplier", "")

            # Парсинг ТМЦ
            items = []
            lines = form.get("items_text", "").strip().split("\n")
            for line in lines:
                if not line.strip(): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    items.append({"name": parts[0], "unit": parts[1], "qty": parts[2]})
                elif len(parts) == 2:
                    items.append({"name": parts[0], "unit": "Шт", "qty": parts[1]})

            pdf_buf = generate_doverennost(form, items)
            await bot.send_document(
                chat_id,
                BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_№{form.get('number', '0')}.pdf"),
                caption="✅ Доверенность М-2 успешно сгенерирована!"
            )

        # --- ДОГОВОР ---
        elif doc_type == "contract":
            today = datetime.now()
            end_of_year = datetime(today.year, 12, 31)
            months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            
            date_start = f"«{today.day}» {months[today.month - 1]} {today.year}"
            date_end = f"«{end_of_year.day}» {months[end_of_year.month - 1]} {end_of_year.year} г."

            # Подготавливаем поля
            num_only = form.get('num_only', '')
            form["number"] = f"ДИЛЕРСКИЙ ДОГОВОР № {num_only}"
            form["c_number"] = f"к Дилерскому договору № {num_only} от {date_start}"
            form["date_start"] = date_start
            form["date_end"] = date_end
            
            comp = form.get('company', '')
            form["company_header"] = f"действующего на основании Устава, с одной стороны, и {comp}, в лице Генерального"
            form["fio_gen_dir"] = f"директора {form.get('fio_gen_dir', '')}, действующего на основании Устава, именуемый в дальнейшем «Дилер», с другой"
            form["fio_short"] = f"___________ / {form.get('fio_short', '')} /"
            
            addr = form.get("address", "")
            if len(addr) > 40:
                split_idx = addr.find(',', 35)
                if split_idx != -1:
                    addr = f"Юр. адрес: {addr[:split_idx+1]}\n{addr[split_idx+1:].strip()}"
                else:
                    addr = f"Юр. адрес: {addr}"
            else:
                addr = f"Юр. адрес: {addr}"
            form["address"] = addr
            
            form["inn_kpp"] = f"ИНН/КПП: {form.get('inn_kpp', '')}"
            form["bank_account"] = f"Р/с: {form.get('bank_account', '')}"
            form["bank_name"] = f"Банк: {form.get('bank_name', '')}"
            form["corr_account"] = f"К/с: {form.get('corr_account', '')}"
            form["bik"] = f"БИК: {form.get('bik', '')}"
            form["phone"] = f"Тел.: {form.get('phone', '')}"
            
            pdf_buf = generate_contract(form)
            await bot.send_document(
                chat_id,
                BufferedInputFile(pdf_buf.getvalue(), filename=f"Договор_{comp}.pdf"),
                caption="✅ Дилерский договор (11 стр.) успешно сгенерирован!"
            )

        return web.json_response({"success": True})
        
    except Exception as e:
        print(f"API Error: {e}")
        if 'chat_id' in locals() and chat_id:
            await bot.send_message(chat_id, f"❌ Ошибка генерации: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def main():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/app", index_html)
    app.router.add_post("/api/generate", api_generate)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    # Запускаем автопингер в отдельном потоке
    threading.Thread(target=pinger, daemon=True).start()
    
    print("Бот, WebApp и автопингер запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
