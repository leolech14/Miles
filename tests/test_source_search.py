from pathlib import Path
import sys
from unittest.mock import Mock

sys.path.append(str(Path(__file__).resolve().parents[1]))
from miles import source_search
from miles.source_store import SourceStore


def test_update_sources(tmp_path, monkeypatch):
    src_file = tmp_path / "sources.yaml"
    src_file.write_text("- https://example.com\n")

    # Create a mock SourceStore that tracks added sources
    added_sources = []

    def mock_store():
        store = Mock(spec=SourceStore)
        store.all.return_value = ["https://example.com"]
        store.add.side_effect = lambda url: (added_sources.append(url), True)[1]
        return store

    def fake_search() -> list[str]:
        return ["https://milhas-test.com"]

    monkeypatch.setattr(source_search, "search_new_sources", fake_search)
    monkeypatch.setattr(source_search, "send_telegram", lambda msg: None)
    monkeypatch.setattr("miles.source_store.SourceStore", mock_store)

    added = source_search.update_sources()
    assert added == ["https://milhas-test.com"]
    assert "https://milhas-test.com" in added_sources
