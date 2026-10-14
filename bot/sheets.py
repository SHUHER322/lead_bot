"""Выгрузка заявок в Google Таблицу."""
import asyncio
import logging

import gspread

HEADER = ["№", "Дата", "Имя", "Телефон", "Telegram", "Запрос"]

log = logging.getLogger(__name__)


class LeadSheet:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self._ws: gspread.Worksheet | None = None

    def _connect(self) -> None:
        """Подключается к первому листу и добавляет заголовок, если лист пуст."""
        client = gspread.service_account(filename=self.credentials_path)
        ws = client.open_by_key(self.spreadsheet_id).sheet1
        if not ws.row_values(1):
            ws.append_row(HEADER)
        self._ws = ws

    async def init(self) -> None:
        # gspread работает синхронно, поэтому запускаем его в отдельном потоке,
        # чтобы не блокировать бота, пока идёт запрос к Google
        await asyncio.to_thread(self._connect)
        log.info("Google Таблица подключена")

    async def add_lead(self, row: list) -> None:
        if self._ws is None:
            return
        # RAW — записываем как есть, чтобы Google не превратил "+7..." в число
        await asyncio.to_thread(self._ws.append_row, row,
                                value_input_option="RAW")
