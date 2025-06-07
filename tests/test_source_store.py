from miles.source_store import SourceStore


def test_add_remove(tmp_path, monkeypatch):
    yaml_path = tmp_path / "src.yaml"
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    s = SourceStore(str(yaml_path))
    assert s.add("http://a.com")
    assert "http://a.com" in s.all()
    assert s.remove("1") == "http://a.com"
    assert not s.all()
