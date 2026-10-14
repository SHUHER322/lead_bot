"""Точка входа: python -m bot.main"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from .config import load_config
from .db import Database
from .handlers import router
from .report import daily_report_loop
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


async def setup_commands(bot: Bot, config) -> None:
    """Список команд для кнопки «Меню». Менеджер видит ещё и /report."""
    common = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="cancel", description="Отменить заявку"),
    ]
    try:
        await bot.set_my_commands(common, scope=BotCommandScopeDefault())
        await bot.set_my_commands(
            common + [BotCommand(command="report", description="Отчёт за сегодня")],
            scope=BotCommandScopeChat(chat_id=config.manager_chat_id),
        )
    except Exception:
        # Не критично: без меню бот работает, команды и кнопки остаются
        log.exception("Не удалось установить список команд")


async def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()

    db = Database(config.db_path, config.timezone)
    await db.init()
    sheet = await setup_sheet(config)

    bot = Bot(config.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # db, config и sheet передаются в обработчики как аргументы
    dp = Dispatcher(storage=MemoryStorage(), db=db, config=config, sheet=sheet)
    dp.include_router(router)
    await setup_commands(bot, config)

    # Отчёт работает параллельно с приёмом сообщений
    report_task = asyncio.create_task(daily_report_loop(bot, db, config))
    try:
        await dp.start_polling(bot)
    finally:
        report_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Бот остановлен")
