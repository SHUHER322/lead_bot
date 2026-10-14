"""Ежедневный отчёт по заявкам для менеджера."""
import asyncio
import html
import logging
from datetime import date, datetime, timedelta

from .db import Database, Lead

log = logging.getLogger(__name__)

MAX_MESSAGE_LEN = 4000  # лимит Telegram — 4096 символов на сообщение


def build_report(day: date, leads: list[Lead]) -> str:
    """Собирает текст отчёта за день."""
    title = f"📊 <b>Отчёт за {day.strftime('%d.%m.%Y')}</b>\n"
    if not leads:
        return title + "Заявок не было."

    text = title + f"Заявок: <b>{len(leads)}</b>\n"
    for i, lead in enumerate(leads):
        time_part = lead.created_at[11:16]  # "ГГГГ-ММ-ДД ЧЧ:ММ:СС" → "ЧЧ:ММ"
        line = (f"\n№{lead.id} · {time_part} · {html.escape(lead.name)} · "
                f"{html.escape(lead.phone)}\n{html.escape(lead.request)}\n")
        if len(text) + len(line) > MAX_MESSAGE_LEN:
            text += f"\n…и ещё {len(leads) - i}. Полный список — в базе или таблице."
            break
        text += line
    return text


def next_run(now: datetime, report_time) -> datetime:
    """Ближайший момент отправки отчёта: сегодня или завтра."""
    run = now.replace(hour=report_time.hour, minute=report_time.minute,
                      second=0, microsecond=0)
    if run <= now:
        run += timedelta(days=1)
    return run


async def daily_report_loop(bot, db: Database, config) -> None:
    """Бесконечный цикл: ждёт времени отчёта и отправляет его менеджеру."""
    tz = config.timezone
    while True:
        run_at = next_run(datetime.now(tz), config.report_time)
        log.info("Следующий отчёт: %s", run_at.strftime("%d.%m.%Y %H:%M %Z"))

        # Спим короткими отрезками и сверяемся с часами: так отчёт не «уплывёт»,
        # если компьютер уходил в сон или перевели время
        while (remaining := (run_at - datetime.now(tz)).total_seconds()) > 0:
            await asyncio.sleep(min(remaining, 60))

        try:
            leads = await db.leads_for_day(run_at.date())
            await bot.send_message(config.manager_chat_id,
                                   build_report(run_at.date(), leads))
        except Exception:
            log.exception("Не удалось отправить ежедневный отчёт")
