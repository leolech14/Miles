import sys
from pathlib import Path
import yaml

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
    text = "promo com dobro de pontos na transferência"
    bot.handle_text("Test", text, "https://example.com/2", seen, alerts)
    assert alerts and alerts[0][0] == 100


def test_sources_file_has_defaults():
    with open(Path(__file__).resolve().parents[1] / "sources.yaml") as f:
        urls = yaml.safe_load(f)
    required = {
        "https://passageirodeprimeira.com",
        "https://melhoresdestinos.com.br",
        "https://promo.millasemfronteiras.com",
        "https://promocao.smiles.com.br",
    }
    assert required.issubset(set(urls))
