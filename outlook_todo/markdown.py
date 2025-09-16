"""Utilities for exporting the to-do list as Markdown."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .models import TodoItem


def format_datetime(value: datetime) -> str:
    """Format the datetime for human-friendly display."""

    return value.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def to_markdown(items: Iterable[TodoItem]) -> str:
    """Produce a Markdown table representation of todo items."""

    rows = [
        "| Subject | Sender | Scheduled | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        subject = item.subject.replace("|", r"\|")
        sender = item.sender.replace("|", r"\|")
        scheduled = format_datetime(item.scheduled_for)
        status = "✅" if item.completed else "⬜"
        rows.append(f"| {subject} | {sender} | {scheduled} | {status} |")
    if len(rows) == 2:
        rows.append("| _No tasks available_ |  |  |  |")
    return "\n".join(rows)


def item_to_markdown(item: TodoItem) -> str:
    """Return a Markdown document describing a single to-do item."""

    status_label = "✅ Done" if item.completed else "⬜ Pending"
    lines = [
        f"# {item.subject or '(no subject)'}",
        "",
        f"- **Sender:** {item.sender}",
        f"- **Received:** {format_datetime(item.received_at)}",
        f"- **Scheduled:** {format_datetime(item.scheduled_for)}",
        f"- **Status:** {status_label}",
    ]
    if item.web_link:
        lines.append(f"- **Link:** {item.web_link}")
    if item.body_preview:
        lines.extend(["", "## Preview", "", item.body_preview])
    return "\n".join(lines).strip() + "\n"
