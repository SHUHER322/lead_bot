"""Тексты ежедневного отчёта (build_report)."""
from datetime import date

from bot.db import Lead
from bot.report import MAX_MESSAGE_LEN, NO_CATEGORY, build_report

DAY = date(2026, 10, 15)


def make_lead(id=1, category="Ремонт", time="14:30", name="Иван",
              phone="+79131234567", request="Покрасить стены") -> Lead:
    return Lead(id=id, created_at=f"2026-10-15 {time}:00", category=category,
                name=name, phone=phone, username=None, request=request)


def test_empty_day():
    text = build_report(DAY, [])
    assert "Отчёт за 15.10.2026" in text
    assert "Заявок не было." in text


def test_lead_line():
    text = build_report(DAY, [make_lead(id=7)])
    assert "Заявок: <b>1</b>" in text
    assert "№7 · 14:30 · <b>Ремонт</b>" in text
    assert "Иван · +79131234567" in text
    assert "Покрасить стены" in text


def test_categories_sorted_by_count():
    leads = [make_lead(id=1, category="Другое"),
             make_lead(id=2, category="Ремонт"),
             make_lead(id=3, category="Ремонт")]
    text = build_report(DAY, leads)
    assert "Заявок: <b>3</b>" in text
    assert "• Ремонт — 2" in text
    assert "• Другое — 1" in text
    # Самая частая категория идёт первой
    assert text.index("• Ремонт") < text.index("• Другое")


def test_lead_without_category():
    """Старые заявки (до появления категорий) не должны ломать отчёт."""
    text = build_report(DAY, [make_lead(category=None)])
    assert f"• {NO_CATEGORY} — 1" in text
    assert f"<b>{NO_CATEGORY}</b>" in text


def test_html_is_escaped():
    """Ввод пользователя не должен ломать HTML-разметку Telegram."""
    text = build_report(DAY, [make_lead(name="<b>Хакер</b>",
                                        request="Цена < 1000 & быстро")])
    assert "<b>Хакер</b>" not in text
    assert "&lt;b&gt;Хакер&lt;/b&gt;" in text
    assert "Цена &lt; 1000 &amp; быстро" in text


def test_long_report_is_truncated():
    leads = [make_lead(id=i, request="Очень длинный запрос " * 10)
             for i in range(1, 101)]
    text = build_report(DAY, leads)
    assert len(text) <= 4096  # жёсткий лимит Telegram
    assert "Заявок: <b>100</b>" in text  # итог считается по всем заявкам

    shown = text.count("\n№")
    assert 0 < shown < 100
    assert f"…и ещё {100 - shown}." in text


def test_short_report_is_not_truncated():
    leads = [make_lead(id=i) for i in range(1, 6)]
    text = build_report(DAY, leads)
    assert len(text) < MAX_MESSAGE_LEN
    assert "…и ещё" not in text
    assert text.count("\n№") == 5
