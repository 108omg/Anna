"""Configuration utilities for the Outlook to-do synchroniser."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


class ConfigError(RuntimeError):
    """Raised when required configuration values are missing."""


@dataclass
class AppConfig:
    """Application configuration values.

    Attributes:
        tenant_id: Azure AD tenant id used for Microsoft Graph authentication.
        client_id: The client id of the Azure AD application registration.
        client_secret: The client secret of the Azure AD application registration.
        storage_path: File system path to the JSON file where to-do state is persisted.
    """

    tenant_id: str
    client_id: str
    client_secret: str
    storage_path: Path = Path("todo_state.json")

    @classmethod
    def from_env(cls, storage_path: Optional[Path] = None) -> "AppConfig":
        """Load configuration from the environment.

        Args:
            storage_path: Optional override for where the JSON data is stored.

        Raises:
            ConfigError: If a required environment variable is missing.
        """

        tenant_id = os.getenv("MS_TENANT_ID")
        client_id = os.getenv("MS_CLIENT_ID")
        client_secret = os.getenv("MS_CLIENT_SECRET")

        missing = [
            name
            for name, value in (
                ("MS_TENANT_ID", tenant_id),
                ("MS_CLIENT_ID", client_id),
                ("MS_CLIENT_SECRET", client_secret),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        if storage_path is None:
            storage_raw = os.getenv("OUTLOOK_TODO_STORAGE", "todo_state.json")
            storage_path = Path(storage_raw)

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            storage_path=storage_path.expanduser().resolve(),
        )
