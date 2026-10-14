"""Точка входа: python -m bot.main"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import load_config
from .db import Database
from .handlers import router
from .sheets import LeadSheet

log = logging.getLogger(__name__)


async def setup_sheet(config) -> LeadSheet | None:
    """Подключает Google Таблицу. Если не вышло — бот работает без неё."""
    if not config.spreadsheet_id:
        log.info("SPREADSHEET_ID не задан — выгрузка в Google Таблицу отключена")
        return None
    sheet = LeadSheet(config.google_credentials, config.spreadsheet_id)
    try:
        await sheet.init()
    except Exception:
        log.exception("Не удалось подключить Google Таблицу — работаю без неё")
        return None
    return sheet


async def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()

    db = Database(config.db_path)
    await db.init()
    sheet = await setup_sheet(config)

    bot = Bot(config.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # db, config и sheet передаются в обработчики как аргументы
    dp = Dispatcher(storage=MemoryStorage(), db=db, config=config, sheet=sheet)
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Бот остановлен")
