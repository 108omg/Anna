"""Core orchestration logic for syncing Outlook emails to to-do items."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from .graph import GraphClient
from .markdown import item_to_markdown, to_markdown
from .models import TodoItem
from .storage import TodoStorage


class OutlookTodoApp:
    """High level interface for the Outlook to-do synchroniser."""

    def __init__(self, graph_client: GraphClient, storage: TodoStorage) -> None:
        self.graph_client = graph_client
        self.storage = storage

    # ------------------------------------------------------------------
    # Synchronisation
    # ------------------------------------------------------------------
    def sync_unread_emails(self, limit: int = 25, schedule_for: datetime | None = None) -> List[TodoItem]:
        """Convert unread emails to to-do entries.

        Args:
            limit: Maximum number of unread messages to fetch.
            schedule_for: Optional datetime indicating when the tasks should be
                executed. Defaults to the received time of the message.
        """

        messages = self.graph_client.fetch_unread_emails(limit=limit)
        new_items: List[TodoItem] = []
        for message in messages:
            message_id = message["id"]
            if message_id in self.storage:
                continue
            payload = self.graph_client.to_todo_payload(message, default_schedule=schedule_for)
            todo = TodoItem(**payload)
            self.storage.add(todo, overwrite=True)
            new_items.append(todo)
        if new_items:
            self.storage.save()
        return new_items

    def list_items(self) -> Sequence[TodoItem]:
        """Return all known to-do entries."""

        return self.storage.all()

    def mark_done(self, message_id: str) -> TodoItem:
        """Mark the matching to-do item as completed and flag the email as read."""

        item = self.storage.get(message_id)
        if item is None:
            raise KeyError(f"No todo item found with id {message_id}")
        if item.completed:
            return item
        self.graph_client.mark_email_as_read(message_id)
        item.completed = True
        self.storage.update(item)
        self.storage.save()
        return item

    def export_markdown(self, output_path: Path) -> Path:
        """Write the current to-do list to *output_path* in Markdown format."""

        markdown = to_markdown(self.storage.all())
        output_path = output_path.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return output_path

    def export_active_markdown(self, output_dir: Path) -> List[Path]:
        """Write individual Markdown files for each active (pending) task."""

        output_dir = output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        def _safe_component(value: str) -> str:
            value = value.strip() or "task"
            return re.sub(r"[^A-Za-z0-9._-]", "_", value)

        def _filename_for(item: TodoItem) -> str:
            subject_slug = _safe_component(item.subject)
            id_slug = _safe_component(item.message_id)
            return f"{subject_slug}-{id_slug}.md"

        active_items = [item for item in self.storage.all() if not item.completed]
        written_paths: List[Path] = []
        for item in active_items:
            filename = _filename_for(item)
            path = output_dir / filename
            path.write_text(item_to_markdown(item), encoding="utf-8")
            written_paths.append(path)

        existing_files = {p for p in output_dir.glob("*.md")}
        for path in existing_files - set(written_paths):
            path.unlink()

        return sorted(written_paths)

    def add_manual_item(
        self,
        subject: str,
        sender: str,
        scheduled_for: datetime,
        body_preview: str = "",
        web_link: str | None = None,
    ) -> TodoItem:
        """Add an ad-hoc task to the to-do list."""

        message_id = f"manual-{len(self.storage.all())+1}"
        todo = TodoItem(
            message_id=message_id,
            subject=subject,
            sender=sender,
            received_at=scheduled_for,
            scheduled_for=scheduled_for,
            body_preview=body_preview,
            web_link=web_link,
        )
        self.storage.add(todo, overwrite=True)
        self.storage.save()
        return todo

    def export_markdown_string(self) -> str:
        """Return the Markdown representation without touching disk."""

        return to_markdown(self.storage.all())
