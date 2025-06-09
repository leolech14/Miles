import sys
from pathlib import Path

import fakeredis
import redis
from _pytest.monkeypatch import MonkeyPatch

sys.path.append(str(Path(__file__).resolve().parents[1]))
from miles.bonus_alert_bot import scan_programs
from miles.source_store import SourceStore


def test_end_to_end_scan(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test complete scan workflow without external dependencies"""
    # Mock Redis
    monkeypatch.setattr(redis.Redis, "from_url", fakeredis.FakeRedis.from_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")

    # Mock external calls
    def mock_fetch(url: str) -> str:
        return '<article><a href="https://example.com">Transferência 100% bônus</a></article>'

    def mock_telegram(msg: str, chat_id: str | None = None) -> None:
        pass  # Don't actually send messages

    # Create test sources file
    sources_file = tmp_path / "test_sources.yaml"
    sources_file.write_text("- https://test.com\n")

    monkeypatch.setenv("SOURCES_PATH", str(sources_file))
    monkeypatch.setenv("MIN_BONUS", "50")

    # Import and patch after env vars are set
    import miles.bonus_alert_bot as bot
    from miles.source_store import SourceStore

    # Also patch the MIN_BONUS constant directly since module may have already loaded
    monkeypatch.setattr(bot, "MIN_BONUS", 50)
    # Create new STORE with test sources
    test_store = SourceStore(str(sources_file))
    monkeypatch.setattr(bot, "STORE", test_store)
    monkeypatch.setattr(bot, "fetch", mock_fetch)
    monkeypatch.setattr(bot, "send_telegram", mock_telegram)

    # Run the scan
    seen: set[str] = set()
    alerts = scan_programs(seen)

    # Verify we found the alert
    assert len(alerts) == 1
    assert alerts[0][0] == 100  # 100% bonus
    assert "test.com" in alerts[0][1]  # source name


def test_source_store_integration(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test SourceStore with Redis integration"""
    monkeypatch.setattr(redis.Redis, "from_url", fakeredis.FakeRedis.from_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")

    yaml_path = tmp_path / "integration_sources.yaml"
    yaml_path.write_text("- https://initial.com\n")

    store = SourceStore(str(yaml_path))

    # Test adding new source
    assert store.add("https://new.com")
    assert "https://new.com" in store.all()

    # Test removing source (sources are sorted alphabetically)
    all_sources = store.all()
    first_source = all_sources[0]  # Get the actual first source
    removed = store.remove("1")  # Remove first item
    assert removed == first_source
    assert first_source not in store.all()
