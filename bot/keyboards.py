"""Кнопки бота: под полем ввода (reply) и под сообщением (inline)."""
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

# Тексты кнопок вынесены в константы: по ним же обработчики узнают нажатия
BTN_NEW_LEAD = "📝 Оставить заявку"
BTN_REPORT = "📊 Отчёт за сегодня"
BTN_CANCEL = "❌ Отменить"
BTN_PHONE = "📱 Отправить номер"


def main_kb(is_manager: bool) -> ReplyKeyboardMarkup:
    """Главное меню. Кнопку отчёта видит только менеджер."""
    rows = [[KeyboardButton(text=BTN_NEW_LEAD)]]
    if is_manager:
        rows.append([KeyboardButton(text=BTN_REPORT)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
    resize_keyboard=True,
)

phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_PHONE, request_contact=True)],
        [KeyboardButton(text=BTN_CANCEL)],
    ],
    resize_keyboard=True,
)


# --- Inline-кнопки (под сообщением) ---

CATEGORY_PREFIX = "cat:"


def categories_kb(categories: tuple[str, ...]) -> InlineKeyboardMarkup:
    """Кнопки выбора категории. В callback_data — номер категории, а не текст:
    у Telegram лимит 64 байта, а длинное русское название может не влезть."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"{CATEGORY_PREFIX}{i}")]
        for i, name in enumerate(categories)
    ])
