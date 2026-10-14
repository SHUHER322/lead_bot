# Lead Bot — Telegram-бот для приёма заявок

Клиент проходит короткую анкету (имя → телефон → запрос), заявка сохраняется
в базу и дублируется в Google Таблицу, менеджер мгновенно получает уведомление
в Telegram.

**Стек:** Python 3.11–3.14, aiogram 3, SQLite (aiosqlite), Google Sheets API (gspread).

## Запуск

```bash
python -m venv .venv             # на Windows с несколькими Python: py -V:3.14 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# заполнить BOT_TOKEN и MANAGER_CHAT_ID в .env
python -m bot.main
```

## Google Таблица (необязательно)

1. В Google Cloud Console создать проект и включить Google Sheets API.
2. Создать сервисный аккаунт, скачать JSON-ключ и положить его в корень
   проекта как `credentials.json`.
3. Создать таблицу и выдать почте сервисного аккаунта (`client_email`
   из ключа) права редактора.
4. Вписать ID таблицы в `.env` → `SPREADSHEET_ID`.

Заголовки столбцов бот добавит сам. Если таблица недоступна, заявки всё равно
сохраняются в базу.

## Структура

```
bot/
  config.py    — настройки из .env
  db.py        — таблица заявок и запись в неё
  states.py    — шаги анкеты (FSM)
  sheets.py    — выгрузка заявок в Google Таблицу
  handlers.py  — диалог с клиентом и уведомление менеджеру
  main.py      — запуск бота
```

## Дальше по плану

- Ежедневный отчёт менеджеру
- Docker и деплой на VPS
