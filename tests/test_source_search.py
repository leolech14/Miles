from pathlib import Path
import sys
import yaml

sys.path.append(str(Path(__file__).resolve().parents[1]))
from miles import source_search


def test_update_sources(tmp_path, monkeypatch):
    src_file = tmp_path / "sources.yaml"
    src_file.write_text("- https://example.com\n")
    monkeypatch.setattr(source_search, "SOURCES_PATH", str(src_file))

    def fake_search() -> list[str]:
        return ["https://newsite.com"]

    monkeypatch.setattr(source_search, "search_new_sources", fake_search)
    monkeypatch.setattr(source_search, "send_telegram", lambda msg: None)
    added = source_search.update_sources()
    assert added == ["https://newsite.com"]
    urls = yaml.safe_load(src_file.read_text())
    assert "https://newsite.com" in urls
