"""Command line interface for the Outlook to-do application."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .config import AppConfig, ConfigError
from .graph import GraphApiError, GraphClient
from .todo_app import OutlookTodoApp
from .storage import TodoStorage


def _parse_schedule(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Outlook unread mail to-do synchroniser")
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("sync", help="Import unread Outlook mails as tasks")
    sync_parser.add_argument("--limit", type=int, default=25, help="Maximum number of emails to fetch")
    sync_parser.add_argument(
        "--schedule",
        type=_parse_schedule,
        help="Override the scheduled time for all created tasks (ISO-8601 format)",
    )

    subparsers.add_parser("list", help="List all known tasks")

    done_parser = subparsers.add_parser("mark-done", help="Mark a task as complete")
    done_parser.add_argument("message_id", help="Identifier of the underlying Outlook message")

    export_parser = subparsers.add_parser("export-markdown", help="Write the current tasks to a Markdown file")
    export_parser.add_argument("output", type=Path, nargs="?", default=Path("todo.md"))

    active_md_parser = subparsers.add_parser(
        "export-active-markdown",
        help="Create individual Markdown files for each active task",
    )
    active_md_parser.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("active_tasks"),
        help="Destination directory for the per-task Markdown files",
    )

    return parser


def _create_app(config: AppConfig) -> OutlookTodoApp:
    storage = TodoStorage(config.storage_path)
    graph = GraphClient(config.tenant_id, config.client_id, config.client_secret)
    return OutlookTodoApp(graph, storage)


def handle_sync(app: OutlookTodoApp, limit: int, schedule: datetime | None) -> int:
    new_items = app.sync_unread_emails(limit=limit, schedule_for=schedule)
    if not new_items:
        print("No new unread mails were found.")
        return 0
    print(f"Imported {len(new_items)} mail(s) into the to-do list:")
    for item in new_items:
        print(f" - {item.subject} (scheduled for {item.scheduled_for.isoformat()})")
    return 0


def handle_list(app: OutlookTodoApp) -> int:
    items = app.list_items()
    if not items:
        print("No tasks available.")
        return 0
    for item in items:
        status = "Done" if item.completed else "Pending"
        print(f"[{status}] {item.subject} — scheduled for {item.scheduled_for.isoformat()}")
    return 0


def handle_mark_done(app: OutlookTodoApp, message_id: str) -> int:
    try:
        item = app.mark_done(message_id)
    except KeyError:
        print(f"No task with id {message_id} exists.")
        return 1
    print(f"Marked '{item.subject}' as complete and flagged the original e-mail as read.")
    return 0


def handle_export_markdown(app: OutlookTodoApp, output: Path) -> int:
    path = app.export_markdown(output)
    print(f"Wrote Markdown overview to {path}")
    return 0


def handle_export_active_markdown(app: OutlookTodoApp, directory: Path) -> int:
    paths = app.export_active_markdown(directory)
    if not paths:
        print(f"No active tasks found. Cleared Markdown directory at {directory.resolve()}.")
        return 0
    print(f"Wrote {len(paths)} Markdown file(s) to {directory.resolve()}:")
    for path in paths:
        print(f" - {path.name}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    try:
        config = AppConfig.from_env()
    except ConfigError as exc:  # pragma: no cover - configuration is validated in runtime
        print(str(exc))
        return 1

    app = _create_app(config)

    try:
        if args.command == "sync":
            return handle_sync(app, limit=args.limit, schedule=args.schedule)
        if args.command == "list":
            return handle_list(app)
        if args.command == "mark-done":
            return handle_mark_done(app, args.message_id)
        if args.command == "export-markdown":
            return handle_export_markdown(app, args.output)
        if args.command == "export-active-markdown":
            return handle_export_active_markdown(app, args.directory)
        parser.print_help()
        return 1
    except GraphApiError as exc:  # pragma: no cover - depends on network/API
        print(f"Graph API error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
