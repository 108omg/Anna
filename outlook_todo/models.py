"""Data models for Outlook-derived to-do items."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def _ensure_tz(value: datetime) -> datetime:
    """Ensure a datetime instance is timezone aware."""
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone aware")
    return value


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


@dataclass
class TodoItem:
    """Represents a to-do entry created from an Outlook e-mail."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime
    scheduled_for: datetime
    body_preview: str = ""
    web_link: str | None = None
    completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.received_at = _ensure_tz(self.received_at)
        self.scheduled_for = _ensure_tz(self.scheduled_for)
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the item to a JSON-compatible dictionary."""

        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "sender": self.sender,
            "received_at": self.received_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat(),
            "body_preview": self.body_preview,
            "web_link": self.web_link,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TodoItem":
        """Reconstruct a :class:`TodoItem` from persisted data."""

        created_raw = payload.get("created_at", datetime.now(timezone.utc).isoformat())
        return cls(
            message_id=payload["message_id"],
            subject=payload["subject"],
            sender=payload["sender"],
            received_at=_parse_datetime(payload["received_at"]),
            scheduled_for=_parse_datetime(payload["scheduled_for"]),
            body_preview=payload.get("body_preview", ""),
            web_link=payload.get("web_link"),
            completed=payload.get("completed", False),
            created_at=_parse_datetime(created_raw),
        )

    @property
    def status(self) -> str:
        """Return the textual representation of the completion status."""

        return "Done" if self.completed else "Pending"
