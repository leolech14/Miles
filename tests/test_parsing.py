import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import bonus_alert_bot as bot


def test_handle_text_detects_percentage():
    alerts = []
    seen = set()
    text = "Promo: 120% bônus transferência"
    bot.handle_text("Test", text, "https://example.com", seen, alerts)
    assert alerts and alerts[0][0] == 120


def test_handle_text_dobro_triggers_default():
    alerts = []
    seen = set()
    text = "promo dobrar seus pontos na transferência"
    bot.handle_text("Test", text, "https://example.com/2", seen, alerts)
    assert alerts and alerts[0][0] == 100


def test_programs_include_new_sources():
    required = {
        "Promoção Aérea",
        "Pontos pra Voar",
        "Melhores Destinos",
        "Promomilhas",
    }
    assert required.issubset(bot.PROGRAMS.keys())
