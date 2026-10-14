"""Шаги анкеты (машина состояний)."""
from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    name = State()
    phone = State()
    request = State()
