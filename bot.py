import os
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from generator import generate_certificate, generate_doverennost, generate_contract

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

class CertForm(StatesGroup):
    number = State()
    company = State()
    inn = State()
    date = State()

class DoverForm(StatesGroup):
    number = State()
    position = State()
    person_fio = State()
    passport_series = State()
    passport_num = State()
    passport_issued = State()
    passport_date = State()
    supplier = State()
    invoice = State()
    items = State()

class ContractForm(StatesGroup):
    number = State()
    date_start = State()
    date_end = State()
    company = State()
    fio_gen_dir = State()
    fio_short = State()
    address = State()
    inn_kpp = State()
    bank_account = State()
    bank_name = State()
    corr_account = State()
    bik = State()
    phone = State()

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Сертификат дилера", callback_data="doc_cert")],
        [InlineKeyboardButton(text="📝 Доверенность (М-2)", callback_data="doc_dover")],
        [InlineKeyboardButton(text="🤝 Договор дилера", callback_data="doc_contract")]
    ])
    await message.answer("👋 **Бот генерации документов**\n\nВыберите документ, который нужно подготовить:", reply_markup=kb)

@dp.callback_query(F.data.startswith('doc_'))
async def process_doc_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    doc_type = callback.data.split('_')[1]
    
    if doc_type == "cert":
        await callback.message.answer("Шаг 1: Введите **номер сертификата** (например: `2708/25`):")
        await state.set_state(CertForm.number)
    elif doc_type == "dover":
        await callback.message.answer("Шаг 1: Введите **номер доверенности** (например: `15`):")
        await state.set_state(DoverForm.number)
    elif doc_type == "contract":
        await callback.message.answer("Шаг 1: Введите **номер договора** (например: `777`):")
        await state.set_state(ContractForm.number)

# ==========================================
# ВЕТКА: СЕРТИФИКАТ
# ==========================================
@dp.message(CertForm.number)
async def process_cert_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2: Введите **название юрлица** (например: `ООО \"Мосводопром\"`):")
    await state.set_state(CertForm.company)

@dp.message(CertForm.company)
async def process_cert_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text.strip())
    await message.answer("Шаг 3: Введите **ИНН** (например: `7721023832`):")
    await state.set_state(CertForm.inn)

@dp.message(CertForm.inn)
async def process_cert_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text.strip())
    await message.answer("Шаг 4: Введите **срок действия** (например: `27.08.2026`):")
    await state.set_state(CertForm.date)

@dp.message(CertForm.date)
async def process_cert_date(message: Message, state: FSMContext):
    data = await state.get_data()
    valid_until = message.text.strip()
    await state.clear()
    
    await message.answer("⏳ Создаю сертификат, подождите...")
    try:
        pdf_buf = generate_certificate(data["number"], data["company"], data["inn"], valid_until)
        await message.answer_document(
            BufferedInputFile(pdf_buf.getvalue(), filename=f"Сертификат_{data['number'].replace('/', '_')}.pdf"),
            caption=f"✅ Сертификат {data['number']} готов!\nГлавное меню — /start"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации сертификата: {e}")

# ==========================================
# ВЕТКА: ДОВЕРЕННОСТЬ
# ==========================================
@dp.message(DoverForm.number)
async def process_dover_num(message: Message, state: FSMContext):
    today = datetime.now()
    date_issue = today.strftime("%d.%m.%Y")
    date_valid = (today + timedelta(days=7)).strftime("%d.%m.%Y")
    
    await state.update_data(
        number=message.text.strip(),
        date_issue=date_issue,
        date_valid=date_valid,
        k_number=message.text.strip(),
        k_date_issue=date_issue,
        k_date_valid=date_valid
    )
    await message.answer("Шаг 2: Введите **должность** сотрудника (например: `Водитель`):")
    await state.set_state(DoverForm.position)

@dp.message(DoverForm.position)
async def process_dover_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text.strip())
    await message.answer("Шаг 3: Введите **ФИО** сотрудника полностью (например: `Мачнев Алексей Игоревич`):")
    await state.set_state(DoverForm.person_fio)

@dp.message(DoverForm.person_fio)
async def process_dover_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    await state.update_data(person_fio=fio, k_person=fio)
    await message.answer("Шаг 4: Введите **Серию** паспорта (только цифры):")
    await state.set_state(DoverForm.passport_series)

@dp.message(DoverForm.passport_series)
async def process_dover_pass_series(message: Message, state: FSMContext):
    await state.update_data(passport_series=message.text.strip())
    await message.answer("Шаг 5: Введите **Номер** паспорта (только цифры):")
    await state.set_state(DoverForm.passport_num)

@dp.message(DoverForm.passport_num)
async def process_dover_pass_num(message: Message, state: FSMContext):
    await state.update_data(passport_num=message.text.strip())
    await message.answer("Шаг 6: **Кем выдан** паспорт? (например: `ГУ МВД РОССИИ ПО Г.МОСКВЕ`):")
    await state.set_state(DoverForm.passport_issued)

@dp.message(DoverForm.passport_issued)
async def process_dover_pass_issued(message: Message, state: FSMContext):
    await state.update_data(passport_issued=message.text.strip())
    await message.answer("Шаг 7: **Дата выдачи** паспорта (например: `24.02.2024`):")
    await state.set_state(DoverForm.passport_date)

@dp.message(DoverForm.passport_date)
async def process_dover_pass_date(message: Message, state: FSMContext):
    await state.update_data(passport_date=message.text.strip())
    await message.answer("Шаг 8: Введите **название поставщика** (например: `ООО ОТГРУЗКА`):")
    await state.set_state(DoverForm.supplier)

@dp.message(DoverForm.supplier)
async def process_dover_supplier(message: Message, state: FSMContext):
    supplier = message.text.strip()
    await state.update_data(supplier=supplier, k_supplier=supplier)
    await message.answer("Шаг 9: Введите **Основание / счет** (например: `счету №777 от 12.12.2025`):")
    await state.set_state(DoverForm.invoice)

@dp.message(DoverForm.invoice)
async def process_dover_invoice(message: Message, state: FSMContext):
    await state.update_data(invoice=message.text.strip(), k_invoice="")
    await message.answer(
        "Шаг 10 (ФИНАЛ): Введите **список ТМЦ** (до 3 позиций).\n"
        "Пишите каждый товар с новой строки через знак `|`.\n\n"
        "Пример:\nЛестница 4односекционная 08 | Шт | 100"
    )
    await state.set_state(DoverForm.items)

@dp.message(DoverForm.items)
async def process_dover_items(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    items = []
    lines = message.text.strip().split("\n")
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            items.append({"name": parts[0], "unit": parts[1], "qty": parts[2]})
        elif len(parts) == 2:
            items.append({"name": parts[0], "unit": "Шт", "qty": parts[1]})
            
    await message.answer("⏳ Генерирую доверенность...")
    try:
        pdf_buf = generate_doverennost(data, items)
        file_name = f"Доверенность_№{data.get('number', '0')}.pdf"
        await message.answer_document(BufferedInputFile(pdf_buf.getvalue(), filename=file_name), caption="✅ Доверенность готова!\nГлавное меню — /start")
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации: {e}")

# ==========================================
# ВЕТКА: ДОГОВОР ДИЛЕРА
# ==========================================
def get_month_name(month_num):
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return months[month_num - 1]

@dp.message(ContractForm.number)
async def process_contract_num(message: Message, state: FSMContext):
    today = datetime.now()
    end_of_year = datetime(today.year, 12, 31)
    
    date_start = f"«{today.day}» {get_month_name(today.month)} {today.year}"
    date_end = f"«{end_of_year.day}» {get_month_name(end_of_year.month)} {end_of_year.year} г."
    
    await state.update_data(
        number=f"ДИЛЕРСКИЙ ДОГОВОР № {message.text.strip()}",
        c_number=f"к Дилерскому договору № {message.text.strip()} от {date_start}",
        date_start=date_start,
        date_end=date_end
    )
    await message.answer("Шаг 2: Введите **название юрлица** (например: `ООО МАЧНЕВ И КОШКИ`):")
    await state.set_state(ContractForm.company)

@dp.message(ContractForm.company)
async def process_contract_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text.strip())
    await message.answer("Шаг 3: Введите **ФИО Директора (в Род. падеже)** (например: `Мачнева А.И.`):")
    await state.set_state(ContractForm.fio_gen_dir)

@dp.message(ContractForm.fio_gen_dir)
async def process_contract_fio_gen(message: Message, state: FSMContext):
    fio = message.text.strip()
    await state.update_data(
        fio_gen_dir=f"директора {fio}, действующего на основании Устава, именуемый в дальнейшем «Дилер», с другой",
    )
    await message.answer("Шаг 4: Введите **короткое ФИО для подписи** (например: `Мачнев А.И.`):")
    await state.set_state(ContractForm.fio_short)

@dp.message(ContractForm.fio_short)
async def process_contract_fio_short(message: Message, state: FSMContext):
    fio = message.text.strip()
    await state.update_data(fio_short=f"___________ / {fio} /")
    await message.answer("Шаг 5: Введите **Юр. адрес** (например: `111531, г. Москва, ул. шоссе Энтузиастов, д. 100`):")
    await state.set_state(ContractForm.address)

@dp.message(ContractForm.address)
async def process_contract_address(message: Message, state: FSMContext):
    addr = message.text.strip()
    if len(addr) > 40:
        split_idx = addr.find(',', 35)
        if split_idx != -1:
            addr = f"Юр. адрес: {addr[:split_idx+1]}\n{addr[split_idx+1:].strip()}"
        else:
            addr = f"Юр. адрес: {addr}"
    else:
        addr = f"Юр. адрес: {addr}"
        
    await state.update_data(address=addr)
    await message.answer("Шаг 6: Введите **ИНН / КПП** (например: `4953077739 / 4953088974`):")
    await state.set_state(ContractForm.inn_kpp)

@dp.message(ContractForm.inn_kpp)
async def process_contract_inn(message: Message, state: FSMContext):
    await state.update_data(inn_kpp=f"ИНН/КПП: {message.text.strip()}")
    await message.answer("Шаг 7: Введите **Расчетный счет** (например: `40040040040040040044`):")
    await state.set_state(ContractForm.bank_account)

@dp.message(ContractForm.bank_account)
async def process_contract_acc(message: Message, state: FSMContext):
    await state.update_data(bank_account=f"Р/с: {message.text.strip()}")
    await message.answer("Шаг 8: Введите **Название Банка** (например: `ПАО Альфа-банк`):")
    await state.set_state(ContractForm.bank_name)

@dp.message(ContractForm.bank_name)
async def process_contract_bank(message: Message, state: FSMContext):
    await state.update_data(bank_name=f"Банк: {message.text.strip()}")
    await message.answer("Шаг 9: Введите **Корр. счет** (например: `50050050050050050055`):")
    await state.set_state(ContractForm.corr_account)

@dp.message(ContractForm.corr_account)
async def process_contract_corr(message: Message, state: FSMContext):
    await state.update_data(corr_account=f"К/с: {message.text.strip()}")
    await message.answer("Шаг 10: Введите **БИК** (например: `01020304`):")
    await state.set_state(ContractForm.bik)

@dp.message(ContractForm.bik)
async def process_contract_bik(message: Message, state: FSMContext):
    await state.update_data(bik=f"БИК: {message.text.strip()}")
    await message.answer("Шаг 11 (ФИНАЛ): Введите **Номер телефона** (например: `+79060400043`):")
    await state.set_state(ContractForm.phone)

@dp.message(ContractForm.phone)
async def process_contract_phone(message: Message, state: FSMContext):
    await state.update_data(phone=f"Тел.: {message.text.strip()}")
    data = await state.get_data()
    await state.clear()
    
    data['company_header'] = f"действующего на основании Устава, с одной стороны, и {data['company']}, в лице Генерального"
    
    await message.answer("⏳ Генерирую договор (11 страниц), заполняю реквизиты...")
    try:
        from generator import generate_contract
        pdf_buf = generate_contract(data)
        file_name = f"Договор_{data.get('company', 'Дилер')}.pdf"
        await message.answer_document(BufferedInputFile(pdf_buf.getvalue(), filename=file_name), caption="✅ Договор готов!\nГлавное меню — /start")
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации договора: {e}")


# --- Web Server для Render ---
async def healthcheck(request):
    return web.Response(text="Doc Bot is running 24/7!")

async def main():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
