"""Загрузка настроек из файла .env."""
import os
from dataclasses import dataclass

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
    )
