"""Persistence helpers for to-do items."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from .models import TodoItem


class TodoStorage:
    """File-system backed storage for :class:`TodoItem` instances."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._items: Dict[str, TodoItem] = {}
        if self.path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self._items = {
            item_data["message_id"]: TodoItem.from_dict(item_data)
            for item_data in data
        }

    def save(self) -> None:
        """Persist the current state to disk."""

        serialised: List[Dict] = [item.to_dict() for item in self._items.values()]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(serialised, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add(self, item: TodoItem, overwrite: bool = False) -> None:
        """Store a new :class:`TodoItem`.

        Args:
            item: The to-do item to persist.
            overwrite: Whether to overwrite an existing entry with the same
                message id.
        """

        if not overwrite and item.message_id in self._items:
            raise KeyError(f"Item with id {item.message_id} already exists")
        self._items[item.message_id] = item

    def get(self, message_id: str) -> TodoItem | None:
        """Retrieve an item by its message id."""

        return self._items.get(message_id)

    def update(self, item: TodoItem) -> None:
        """Persist updates for an existing item."""

        if item.message_id not in self._items:
            raise KeyError(f"Cannot update missing item {item.message_id}")
        self._items[item.message_id] = item

    def remove(self, message_id: str) -> None:
        """Remove an item from storage."""

        if message_id in self._items:
            del self._items[message_id]

    def all(self) -> List[TodoItem]:
        """Return all stored items sorted by their scheduled time."""

        return sorted(self._items.values(), key=lambda item: item.scheduled_for)

    def extend(self, items: Iterable[TodoItem], overwrite: bool = False) -> None:
        """Store multiple items at once."""

        for item in items:
            self.add(item, overwrite=overwrite)

    def __contains__(self, message_id: str) -> bool:  # pragma: no cover - simple alias
        return message_id in self._items
