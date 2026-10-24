"""Несколько менеджеров: разбор MANAGER_CHAT_ID и рассылка всем."""
import asyncio

import pytest

from bot.config import parse_manager_ids
from bot.notify import send_to_managers


def test_one_id():
    assert parse_manager_ids("123456789") == (123456789,)


def test_several_ids_with_spaces_and_duplicates():
    assert parse_manager_ids("574340592, 6592299831,574340592") == (574340592, 6592299831)


def test_group_id_is_negative():
    assert parse_manager_ids("-1001234567890") == (-1001234567890,)


@pytest.mark.parametrize("value", ["", " , ", "abc", "123;456"])
def test_bad_ids(value):
    with pytest.raises(RuntimeError, match="MANAGER_CHAT_ID"):
        parse_manager_ids(value)


class FakeBot:
    """Запоминает отправленное; одному из менеджеров «не доставляется»."""
    def __init__(self, broken=()):
        self.sent, self.broken = [], set(broken)

    async def send_message(self, chat_id, text):
        if chat_id in self.broken:
            raise RuntimeError("Forbidden: bot was blocked by the user")
        self.sent.append((chat_id, text))


def test_send_to_all_managers():
    bot = FakeBot()
    assert asyncio.run(send_to_managers(bot, (1, 2), "Заявка")) == 2
    assert bot.sent == [(1, "Заявка"), (2, "Заявка")]


def test_one_blocked_manager_does_not_stop_others():
    bot = FakeBot(broken={1})
    assert asyncio.run(send_to_managers(bot, (1, 2), "Заявка")) == 1
    assert bot.sent == [(2, "Заявка")]
