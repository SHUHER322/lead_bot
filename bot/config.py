"""Загрузка настроек из файла .env."""
import os
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    manager_chat_id: int
    db_path: str
    # Google Таблица — необязательно: если ID пустой, выгрузка отключена
    google_credentials: str
    spreadsheet_id: str | None
    # Часовой пояс заказчика и время ежедневного отчёта по этому поясу
    timezone: ZoneInfo
    report_time: time
    # Категории заявок — кнопки при выборе, столбец в таблице, разбивка в отчёте
    categories: tuple[str, ...]


def _parse_time(value: str) -> time:
    try:
        hours, minutes = value.split(":")
        return time(int(hours), int(minutes))
    except ValueError:
        raise RuntimeError(f"REPORT_TIME должно быть в формате ЧЧ:ММ, сейчас: {value!r}")


def _parse_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise RuntimeError(f"Неизвестный часовой пояс TIMEZONE={name!r}. "
                           "Пример: Asia/Tomsk, Europe/Moscow")


DEFAULT_CATEGORIES = "Ремонт,Консультация,Сотрудничество,Другое"


def _parse_categories(value: str) -> tuple[str, ...]:
    categories = tuple(c.strip() for c in value.split(",") if c.strip())
    if not categories:
        raise RuntimeError("CATEGORIES пустой. Пример: Ремонт,Консультация,Другое")
    return categories


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    manager_id = os.getenv("MANAGER_CHAT_ID")
    if not token or not manager_id:
        raise RuntimeError("Заполни BOT_TOKEN и MANAGER_CHAT_ID в файле .env")
    return Config(
        bot_token=token,
        manager_chat_id=int(manager_id),
        db_path=os.getenv("DB_PATH", "leads.db"),
        google_credentials=os.getenv("GOOGLE_CREDENTIALS", "credentials.json"),
        spreadsheet_id=os.getenv("SPREADSHEET_ID") or None,
        timezone=_parse_timezone(os.getenv("TIMEZONE", "Asia/Tomsk")),
        report_time=_parse_time(os.getenv("REPORT_TIME", "20:00")),
        categories=_parse_categories(os.getenv("CATEGORIES", DEFAULT_CATEGORIES)),
    )
