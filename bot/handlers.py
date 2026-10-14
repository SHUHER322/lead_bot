"""Обработчики сообщений: анкета заявки."""
import html
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

from .config import Config
from .db import Database
from .states import LeadForm

router = Router()

PHONE_RE = re.compile(r"^\+?[\d\s\-()]{10,18}$")

phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте! Оставьте заявку — менеджер свяжется с вами.\n\n"
        "Как вас зовут?\n\n/cancel — отменить"
    )
    await state.set_state(LeadForm.name)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Заявка отменена. /start — начать заново.",
                         reply_markup=ReplyKeyboardRemove())


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
    if not PHONE_RE.match(phone):
        await message.answer("Не похоже на номер. Пример: +7 913 123-45-67")
        return
    await _save_phone(message, state, phone)


async def _save_phone(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    await message.answer("Коротко опишите, что вам нужно.",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(LeadForm.request)


@router.message(LeadForm.request, F.text)
async def get_request(message: Message, state: FSMContext,
                      bot: Bot, db: Database, config: Config):
    data = await state.update_data(request=message.text.strip())
    user = message.from_user
    lead_id = await db.add_lead(user.id, user.username,
                                data["name"], data["phone"], data["request"])
    await state.clear()

    await message.answer(f"Спасибо! Заявка №{lead_id} принята. "
                         "Мы скоро свяжемся с вами.")

    username = f"@{user.username}" if user.username else "—"
    await bot.send_message(
        config.manager_chat_id,
        f"🆕 <b>Заявка №{lead_id}</b>\n"
        f"Имя: {html.escape(data['name'])}\n"
        f"Телефон: {html.escape(data['phone'])}\n"
        f"Telegram: {html.escape(username)}\n"
        f"Запрос: {html.escape(data['request'])}",
    )


@router.message(LeadForm.name)
@router.message(LeadForm.request)
async def wrong_input(message: Message):
    await message.answer("Пожалуйста, отправьте текстом.")
