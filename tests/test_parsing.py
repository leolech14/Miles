import sys
from pathlib import Path

import pytest
import yaml

sys.path.append(str(Path(__file__).resolve().parents[1]))
import miles.bonus_alert_bot as bot


def test_parse_feed_produces_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    html = (Path(__file__).parent / "data" / "sample_feed.html").read_text()

    def fake_fetch(url: str) -> str | None:
        return html

    monkeypatch.setattr(bot, "fetch", fake_fetch)
    alerts: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    bot.parse_feed("Test", "https://example.com/feed", seen, alerts)
    assert len(alerts) == 1
    assert alerts[0][0] == 100


def test_sources_file_has_defaults() -> None:
    with open(Path(__file__).resolve().parents[1] / "sources.yaml") as f:
        urls = yaml.safe_load(f)
    required = {
        "https://passageirodeprimeira.com",
        "https://melhoresdestinos.com.br",
        "https://promo.millasemfronteiras.com",
        "https://promocao.smiles.com.br",
    }
    assert required.issubset(set(urls))
