import fakeredis
import redis
from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch
from miles.source_store import SourceStore


def test_add_remove(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    yaml_path = tmp_path / "src.yaml"
    monkeypatch.setattr(redis.Redis, "from_url", fakeredis.FakeRedis.from_url)
    # Use different DB number to avoid test collision
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/10")
    s = SourceStore(str(yaml_path))
    assert s.add("http://a.com")
    assert "http://a.com" in s.all()
    assert s.remove("1") == "http://a.com"
    assert not s.all()
