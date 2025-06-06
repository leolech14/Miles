from miles.storage import FileSeenStore


def test_file_store(tmp_path):
    f = tmp_path / "s.json"
    store = FileSeenStore(str(f))
    h = "abc"
    assert not store.has(h)
    store.add(h)
    assert store.has(h)
