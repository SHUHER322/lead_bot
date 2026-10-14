"""Работа с базой заявок (SQLite)."""
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    request     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    category    TEXT
);
"""


@dataclass
class Lead:
    id: int
    created_at: str
    category: str | None  # у заявок, созданных до появления категорий, — None
    name: str
    phone: str
    username: str | None
    request: str


class Database:
    def __init__(self, path: str, tz: ZoneInfo):
        self.path = path
        self.tz = tz  # время заявок пишем по поясу заказчика, а не сервера

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(SCHEMA)
            # Миграция: в базах, созданных до категорий, этого столбца нет
            cursor = await db.execute("PRAGMA table_info(leads)")
            columns = {row[1] for row in await cursor.fetchall()}
            if "category" not in columns:
                await db.execute("ALTER TABLE leads ADD COLUMN category TEXT")
            await db.commit()

    async def add_lead(self, user_id: int, username: str | None, category: str,
                       name: str, phone: str, request: str) -> tuple[int, str]:
        """Сохраняет заявку и возвращает её номер и время создания."""
        created_at = datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO leads (user_id, username, category, name, phone, "
                "request, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, category, name, phone, request, created_at),
            )
            await db.commit()
            return cursor.lastrowid, created_at

    async def leads_for_day(self, day: date) -> list[Lead]:
        """Все заявки за указанный день (по поясу заказчика)."""
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT id, created_at, category, name, phone, username, request "
                "FROM leads WHERE created_at LIKE ? ORDER BY id",
                (f"{day.isoformat()}%",),  # created_at начинается с "ГГГГ-ММ-ДД"
            )
            return [Lead(*row) for row in await cursor.fetchall()]
