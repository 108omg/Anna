"""Thin wrapper around the Microsoft Graph API."""
from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - import is environment specific
    import msal  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully in GraphClient
    msal = None  # type: ignore[assignment]

GRAPH_API_ROOT = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


def _get_requests_module():  # pragma: no cover - trivial helper
    try:
        return importlib.import_module("requests")
    except ImportError as exc:  # pragma: no cover - import depends on env
        raise RuntimeError(
            "The 'requests' package is required to communicate with Microsoft Graph. "
            "Install it via 'pip install requests'."
        ) from exc


class GraphApiError(RuntimeError):
    """Raised when the Microsoft Graph API returns an error response."""

    def __init__(self, response: Any):
        self.response = response
        message = f"Graph API call failed with status {response.status_code}: {response.text}"
        super().__init__(message)


class GraphClient:
    """Client for interacting with the Microsoft Graph API."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str) -> None:
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        if msal is None:
            raise RuntimeError(
                "The 'msal' package is required to authenticate with Microsoft Graph. "
                "Install it via 'pip install msal'."
            )
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._client = msal.ConfidentialClientApplication(
            client_id, authority=authority, client_credential=client_secret
        )

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    def _acquire_token(self) -> str:
        result = self._client.acquire_token_silent(SCOPES, account=None)
        if not result:
            result = self._client.acquire_token_for_client(scopes=SCOPES)
        if "access_token" not in result:
            raise RuntimeError(f"Unable to obtain access token: {result.get('error_description')}")
        return result["access_token"]

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._acquire_token()}"}

    # ------------------------------------------------------------------
    # Mail helpers
    # ------------------------------------------------------------------
    def fetch_unread_emails(self, limit: int = 25) -> List[Dict]:
        """Return unread inbox emails ordered from newest to oldest."""

        url = f"{GRAPH_API_ROOT}/me/mailFolders/Inbox/messages"
        params = {
            "$top": limit,
            "$filter": "isRead eq false",
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,bodyPreview,webLink",
        }
        requests = _get_requests_module()
        response = requests.get(url, headers=self._auth_headers(), params=params, timeout=30)
        if not response.ok:
            raise GraphApiError(response)
        payload = response.json()
        return payload.get("value", [])

    def mark_email_as_read(self, message_id: str) -> None:
        """Mark a message as read."""

        url = f"{GRAPH_API_ROOT}/me/messages/{message_id}"
        requests = _get_requests_module()
        response = requests.patch(
            url,
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            json={"isRead": True},
            timeout=30,
        )
        if response.status_code not in (200, 204):
            raise GraphApiError(response)

    # ------------------------------------------------------------------
    # To-do helpers
    # ------------------------------------------------------------------
    @staticmethod
    def parse_graph_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def extract_sender(message: Dict) -> str:
        from_data = message.get("from") or {}
        email_address = from_data.get("emailAddress") or {}
        return email_address.get("name") or email_address.get("address") or "Unknown sender"

    @staticmethod
    def to_todo_payload(message: Dict, default_schedule: Optional[datetime] = None) -> Dict:
        received = GraphClient.parse_graph_datetime(message["receivedDateTime"])
        scheduled = default_schedule or received
        return {
            "message_id": message["id"],
            "subject": message.get("subject") or "(no subject)",
            "sender": GraphClient.extract_sender(message),
            "received_at": received,
            "scheduled_for": scheduled,
            "body_preview": message.get("bodyPreview", ""),
            "web_link": message.get("webLink"),
        }


class InMemoryGraphClient(GraphClient):  # pragma: no cover - used for demos/testing
    """Graph client used for tests or demos without network access."""

    def __init__(self, messages: Iterable[Dict]):
        self.messages = list(messages)

    def fetch_unread_emails(self, limit: int = 25) -> List[Dict]:
        return self.messages[:limit]

    def mark_email_as_read(self, message_id: str) -> None:
        for message in self.messages:
            if message.get("id") == message_id:
                message["isRead"] = True
                break
