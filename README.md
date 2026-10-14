# Lead Bot — Telegram-бот для приёма заявок

Клиент проходит короткую анкету (имя → телефон → запрос), заявка сохраняется
в базу, менеджер мгновенно получает уведомление в Telegram.

**Стек:** Python 3.11+, aiogram 3, SQLite (aiosqlite).

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# заполнить BOT_TOKEN и MANAGER_CHAT_ID в .env
python -m bot.main
```

## Структура

```
bot/
  config.py    — настройки из .env
  db.py        — таблица заявок и запись в неё
  states.py    — шаги анкеты (FSM)
  handlers.py  — диалог с клиентом и уведомление менеджеру
  main.py      — запуск бота
```

## Дальше по плану

- Выгрузка заявок в Google Таблицу
- Ежедневный отчёт менеджеру
- Docker и деплой на VPS
