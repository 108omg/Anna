from datetime import datetime, timezone

from outlook_todo.graph import InMemoryGraphClient
from outlook_todo.todo_app import OutlookTodoApp
from outlook_todo.storage import TodoStorage


NOW = datetime(2023, 1, 1, 9, 0, tzinfo=timezone.utc)


class DummyGraph(InMemoryGraphClient):
    def __init__(self):
        messages = [
            {
                "id": "1",
                "subject": "Subject 1",
                "from": {"emailAddress": {"name": "Alice"}},
                "receivedDateTime": NOW.isoformat(),
                "bodyPreview": "Hello",
                "webLink": "https://outlook.example/1",
            }
        ]
        super().__init__(messages)


def create_app(tmp_path) -> OutlookTodoApp:
    graph = DummyGraph()
    storage = TodoStorage(tmp_path / "state.json")
    return OutlookTodoApp(graph, storage)


def test_sync_creates_items(tmp_path):
    app = create_app(tmp_path)
    created = app.sync_unread_emails()
    assert len(created) == 1
    stored = app.list_items()
    assert stored[0].subject == "Subject 1"


def test_mark_done_marks_email(tmp_path):
    app = create_app(tmp_path)
    app.sync_unread_emails()
    app.mark_done("1")
    assert app.list_items()[0].completed is True


def test_export_markdown(tmp_path):
    app = create_app(tmp_path)
    app.sync_unread_emails()
    output = tmp_path / "todo.md"
    path = app.export_markdown(output)
    assert path == output
    assert path.exists()


def test_export_active_markdown(tmp_path):
    app = create_app(tmp_path)
    app.sync_unread_emails()
    directory = tmp_path / "active"

    written = app.export_active_markdown(directory)
    assert len(written) == 1
    assert written[0].read_text(encoding="utf-8").startswith("# Subject 1")

    app.mark_done("1")
    written = app.export_active_markdown(directory)
    assert written == []
    assert list(directory.glob("*.md")) == []
