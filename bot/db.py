"""Работа с базой заявок (SQLite)."""
from datetime import datetime

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    name        TEXT NOT NULL,
    phone       TEXT NOT NULL,
    request     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(SCHEMA)
            await db.commit()

    async def add_lead(self, user_id: int, username: str | None,
                       name: str, phone: str, request: str) -> tuple[int, str]:
        """Сохраняет заявку и возвращает её номер и время создания."""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO leads (user_id, username, name, phone, request, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, name, phone, request, created_at),
            )
            await db.commit()
            return cursor.lastrowid, created_at
