from pathlib import Path
import sys
from miles.storage import FileSeenStore

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_file_store(tmp_path: Path) -> None:
    f = tmp_path / "s.json"
    store = FileSeenStore(str(f))
    h = "abc"
    assert not store.has(h)
    store.add(h)
    assert store.has(h)


def test_file_store_empty_initialization(tmp_path: Path) -> None:
    f = tmp_path / "empty.json"
    store = FileSeenStore(str(f))
    assert not store.has("any_hash")
    assert not f.exists()  # File should be created only when needed


def test_file_store_multiple_items(tmp_path: Path) -> None:
    f = tmp_path / "multiple.json"
    store = FileSeenStore(str(f))

    hashes = ["abc", "def", "123"]
    for h in hashes:
        assert not store.has(h)
        store.add(h)
        assert store.has(h)

    # Verify all items are still there
    for h in hashes:
        assert store.has(h)


def test_file_store_persistence(tmp_path: Path) -> None:
    f = tmp_path / "persist.json"

    # Add items with first instance
    store1 = FileSeenStore(str(f))
    store1.add("item1")
    store1.add("item2")

    # Create new instance pointing to same file
    store2 = FileSeenStore(str(f))
    assert store2.has("item1")
    assert store2.has("item2")
    assert not store2.has("item3")
