# Outlook Mail To-Do Synchroniser

This project provides a command-line application that converts unread Outlook
messages into a local to-do list. Each task keeps track of when the work should
be carried out, whether it has been completed, and where to find the original
message. When a task is marked as done, the associated e-mail is also marked as
read within Outlook. The current task list can be exported to Markdown for
status reporting or sharing with a wider team.

## Features

- Fetch unread mails from the Outlook inbox via the Microsoft Graph API
- Persist the to-do list locally so that tasks survive between runs
- Mark tasks as completed and flag the original e-mail as read in Outlook
- Export the current tasks as a Markdown table
- Keep per-task Markdown notes for every active item
- Optional manual task entry for reminders that are not tied to a message

## Requirements

- Python 3.10+
- An Azure AD application registration with access to the Microsoft Graph API
  (client credentials flow)
- The following environment variables must be defined before running the tool:
  - `MS_TENANT_ID`
  - `MS_CLIENT_ID`
  - `MS_CLIENT_SECRET`
- Optional: set `OUTLOOK_TODO_STORAGE` to change where the local state file is
  stored (defaults to `todo_state.json` in the working directory)

Install the dependencies using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the CLI via `python -m outlook_todo` followed by one of the sub-commands.

### Synchronise unread e-mails

```bash
python -m outlook_todo sync --limit 50
```

By default, each task is scheduled for the time the message was received. To
override the planned execution time, provide the `--schedule` flag with an ISO
8601 timestamp:

```bash
python -m outlook_todo sync --schedule 2023-09-30T09:00
```

### List tasks

```bash
python -m outlook_todo list
```

### Mark a task as complete

```bash
python -m outlook_todo mark-done <message-id>
```

The message id is the Microsoft Graph identifier for the Outlook item. It is
printed during the synchronisation step and stored in the `todo_state.json`
file.

### Export tasks to Markdown

```bash
python -m outlook_todo export-markdown todo.md
```

The generated Markdown file contains a table summarising the current to-do
items. Completed tasks are annotated with ✅ while pending entries use ⬜.

### Export Markdown notes for active tasks

```bash
python -m outlook_todo export-active-markdown active_tasks/
```

This command maintains one Markdown file per active task inside the provided
directory. Files for tasks that have been completed are removed automatically so
the folder always reflects the current queue of work.

## Development

Run the automated test suite with:

```bash
pytest
```

The project uses a lightweight architecture of pure Python modules so it can be
easily extended or embedded into other tooling.
