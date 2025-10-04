"""Entry point for ``python -m outlook_todo``."""
from .cli import main

if __name__ == "__main__":  # pragma: no cover - delegated to CLI
    raise SystemExit(main())
