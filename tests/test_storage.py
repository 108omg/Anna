from datetime import datetime, timezone

from outlook_todo.models import TodoItem
from outlook_todo.storage import TodoStorage


def make_item(identifier: str) -> TodoItem:
    now = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    return TodoItem(
        message_id=identifier,
        subject="Subject",
        sender="sender@example.com",
        received_at=now,
        scheduled_for=now,
    )


def test_storage_roundtrip(tmp_path):
    storage_path = tmp_path / "state.json"
    storage = TodoStorage(storage_path)

    item = make_item("abc")
    storage.add(item)
    storage.save()

    loaded = TodoStorage(storage_path)
    assert loaded.get("abc").subject == "Subject"


def test_storage_prevents_duplicates(tmp_path):
    storage = TodoStorage(tmp_path / "state.json")
    item = make_item("dup")
    storage.add(item)
    try:
        storage.add(item)
    except KeyError:
        pass
    else:  # pragma: no cover - defensive programming
        raise AssertionError("Expected duplicate entry to raise KeyError")
