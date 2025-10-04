from datetime import datetime, timezone

from outlook_todo.markdown import item_to_markdown, to_markdown
from outlook_todo.models import TodoItem


def make_item(subject: str, completed: bool = False) -> TodoItem:
    now = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    return TodoItem(
        message_id=f"id-{subject}",
        subject=subject,
        sender="sender@example.com",
        received_at=now,
        scheduled_for=now,
        completed=completed,
    )


def test_to_markdown_with_items():
    items = [make_item("Task A"), make_item("Task B", completed=True)]
    markdown = to_markdown(items)
    assert "Task A" in markdown
    assert "Task B" in markdown
    assert "⬜" in markdown
    assert "✅" in markdown


def test_to_markdown_empty_list():
    markdown = to_markdown([])
    assert "No tasks available" in markdown


def test_item_to_markdown_includes_details():
    item = make_item("Important", completed=True)
    item.body_preview = "Details go here"
    item.web_link = "https://example.com"
    markdown = item_to_markdown(item)
    assert "# Important" in markdown
    assert "✅ Done" in markdown
    assert "Details go here" in markdown
    assert "https://example.com" in markdown
