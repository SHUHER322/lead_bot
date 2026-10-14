"""Обработчики сообщений: меню, анкета заявки, отчёт."""
import html
import logging
import re
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .config import Config
from .db import Database
from .keyboards import (BTN_CANCEL, BTN_NEW_LEAD, BTN_REPORT, CATEGORY_PREFIX,
                        cancel_kb, categories_kb, main_kb, phone_kb)
from .report import build_report
from .sheets import LeadSheet
from .states import LeadForm

router = Router()
log = logging.getLogger(__name__)

# Какие символы можно вводить. re.ASCII — чтобы \d был только 0–9, без цифр других алфавитов
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{10,18}$", re.ASCII)


def is_valid_phone(phone: str) -> bool:
    """Номер в свободном формате, но с разумным количеством цифр."""
    if not PHONE_RE.match(phone):
        return False
    # Регулярка проверяет только символы — без этого прошло бы «----------»
    digits = sum(c.isdigit() for c in phone)
    return 10 <= digits <= 15  # 15 — максимум для международного номера


def is_manager(message: Message, config: Config) -> bool:
    """Фильтр: действие доступно только менеджеру."""
    return message.from_user.id == config.manager_chat_id


# --- Меню. Эти обработчики стоят первыми, чтобы нажатие кнопки посреди
# анкеты не приняли за ответ (например, «❌ Отменить» — за имя) ---

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, config: Config):
    await state.clear()
    await message.answer(
        "Здравствуйте! Здесь можно оставить заявку — менеджер свяжется с вами.\n\n"
        f"Нажмите «{BTN_NEW_LEAD}», чтобы начать.",
        reply_markup=main_kb(is_manager(message, config)),
    )


@router.message(or_f(Command("cancel"), F.text == BTN_CANCEL))
async def cancel(message: Message, state: FSMContext, config: Config):
    await state.clear()
    await message.answer("Заявка отменена.",
                         reply_markup=main_kb(is_manager(message, config)))


@router.message(or_f(Command("report"), F.text == BTN_REPORT), is_manager)
async def report(message: Message, db: Database, config: Config):
    today = datetime.now(config.timezone).date()
    leads = await db.leads_for_day(today)
    await message.answer(build_report(today, leads))


@router.message(F.text == BTN_NEW_LEAD)
async def new_lead(message: Message, state: FSMContext, config: Config):
    await state.clear()
    # Два сообщения: у одного сообщения может быть только одна клавиатура,
    # а нам нужны и кнопка «Отменить» внизу, и категории под вопросом
    await message.answer("Новая заявка. Отменить можно в любой момент.",
                         reply_markup=cancel_kb)
    await message.answer("Что вас интересует?",
                         reply_markup=categories_kb(config.categories))
    await state.set_state(LeadForm.category)


# --- Анкета ---

@router.callback_query(LeadForm.category, F.data.startswith(CATEGORY_PREFIX))
async def get_category(callback: CallbackQuery, state: FSMContext, config: Config):
    index = int(callback.data.removeprefix(CATEGORY_PREFIX))
    if not 0 <= index < len(config.categories):
        # Список категорий поменяли, а кнопка осталась от старого
        await callback.answer("Этот вариант больше недоступен", show_alert=True)
        return
    category = config.categories[index]
    await state.update_data(category=category)
    # Убираем кнопки и оставляем в чате выбранный вариант
    await callback.message.edit_text(f"Категория: <b>{html.escape(category)}</b>")
    await callback.answer()  # убирает «часики» на кнопке
    await callback.message.answer("Как вас зовут?")
    await state.set_state(LeadForm.name)


@router.callback_query(F.data.startswith(CATEGORY_PREFIX))
async def stale_category(callback: CallbackQuery):
    """Нажатие на кнопку категории из старой или отменённой заявки."""
    await callback.answer("Эта заявка уже закрыта. Начните новую через меню.",
                          show_alert=True)


@router.message(LeadForm.category)
async def category_not_chosen(message: Message):
    await message.answer("Выберите вариант кнопкой под вопросом «Что вас интересует?».")


@router.message(LeadForm.name, F.text)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not 2 <= len(name) <= 50:
        await message.answer("Введите имя от 2 до 50 символов.")
        return
    await state.update_data(name=name)
    await message.answer("Укажите телефон или нажмите кнопку ниже.",
                         reply_markup=phone_kb)
    await state.set_state(LeadForm.phone)


@router.message(LeadForm.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    await _save_phone(message, state, message.contact.phone_number)


@router.message(LeadForm.phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer("Не похоже на номер. Пример: +7 913 123-45-67")
        return
    await _save_phone(message, state, phone)


async def _save_phone(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    await message.answer("Коротко опишите, что вам нужно.", reply_markup=cancel_kb)
    await state.set_state(LeadForm.request)


@router.message(LeadForm.request, F.text)
async def get_request(message: Message, state: FSMContext,
                      bot: Bot, db: Database, config: Config,
                      sheet: LeadSheet | None):
    data = await state.update_data(request=message.text.strip())
    user = message.from_user
    lead_id, created_at = await db.add_lead(
        user.id, user.username, data["category"],
        data["name"], data["phone"], data["request"])
    await state.clear()

    await message.answer(f"Спасибо! Заявка №{lead_id} принята. "
                         "Мы скоро свяжемся с вами.",
                         reply_markup=main_kb(is_manager(message, config)))

    username = f"@{user.username}" if user.username else "—"

    # Ошибка Google не должна мешать: заявка уже в базе, менеджер получит уведомление
    if sheet:
        try:
            await sheet.add_lead([lead_id, created_at, data["category"], data["name"],
                                  data["phone"], username, data["request"]])
        except Exception:
            log.exception("Не удалось записать заявку №%s в Google Таблицу", lead_id)

    await bot.send_message(
        config.manager_chat_id,
        f"🆕 <b>Заявка №{lead_id}</b>\n"
        f"Категория: <b>{html.escape(data['category'])}</b>\n"
        f"Имя: {html.escape(data['name'])}\n"
        f"Телефон: {html.escape(data['phone'])}\n"
        f"Telegram: {html.escape(username)}\n"
        f"Запрос: {html.escape(data['request'])}",
    )


@router.message(LeadForm.name)
@router.message(LeadForm.phone)
@router.message(LeadForm.request)
async def wrong_input(message: Message):
    await message.answer("Пожалуйста, отправьте текстом.")


# --- Всё остальное вне анкеты ---

@router.message()
async def fallback(message: Message, config: Config):
    await message.answer(f"Чтобы оставить заявку, нажмите «{BTN_NEW_LEAD}».",
                         reply_markup=main_kb(is_manager(message, config)))
