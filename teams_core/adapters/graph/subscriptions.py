from datetime import datetime, timedelta, timezone

from teams_core.adapters.graph.client import GraphClient
from teams_core.config import TeamsConfig
from teams_core.domain.models import ConversationKind, ConversationRef


class SubscriptionManager:
    def __init__(self, client: GraphClient, cfg: TeamsConfig) -> None:
        self._client = client
        self._cfg = cfg

    @staticmethod
    def _resource(conv: ConversationRef) -> str:
        if conv.kind is ConversationKind.CHAT:
            return f"/chats/{conv.chat_id}/messages"
        return f"/teams/{conv.team_id}/channels/{conv.channel_id}/messages"

    def create(self, conv: ConversationRef, minutes: int = 55) -> dict:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        payload = {
            "changeType": "created,updated,deleted",
            "notificationUrl": self._cfg.notification_url,
            "lifecycleNotificationUrl": self._cfg.lifecycle_url,
            "resource": self._resource(conv),
            "expirationDateTime": expiry.isoformat().replace("+00:00", "Z"),
            "clientState": self._cfg.client_state,
            "includeResourceData": False,
        }
        return self._client.request("POST", "/subscriptions", json=payload)

    def renew(self, subscription_id: str, minutes: int = 55) -> dict:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        return self._client.request(
            "PATCH",
            f"/subscriptions/{subscription_id}",
            json={"expirationDateTime": expiry.isoformat().replace("+00:00", "Z")},
        )

    def delete(self, subscription_id: str) -> None:
        self._client.request("DELETE", f"/subscriptions/{subscription_id}")

    def list_active(self) -> list[dict]:
        return list(self._client.paged("/subscriptions"))
