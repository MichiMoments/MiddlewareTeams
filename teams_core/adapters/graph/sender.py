from teams_core.adapters.graph.client import GraphClient
from teams_core.domain.models import (
    ConversationKind,
    ConversationRef,
    Mention,
    OutboundMessage,
)


class GraphMessageSender:
    """Implements MessageSender. Posts as the signed-in service account."""

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    def send(self, to: ConversationRef, message: OutboundMessage) -> str:
        payload = self._build_payload(message)
        created = self._client.request("POST", self._path(to, message), json=payload)
        return created["id"]

    @staticmethod
    def _path(to: ConversationRef, message: OutboundMessage) -> str:
        if to.kind is ConversationKind.CHAT:
            if message.reply_to_message_id:
                raise ValueError("Chats do not support threaded replies")
            return f"/chats/{to.chat_id}/messages"

        base = f"/teams/{to.team_id}/channels/{to.channel_id}/messages"
        if message.reply_to_message_id:
            return f"{base}/{message.reply_to_message_id}/replies"
        return base

    @staticmethod
    def _build_payload(message: OutboundMessage) -> dict:
        payload: dict = {
            "body": {"contentType": "html", "content": message.body_html},
            "importance": message.importance,
        }
        if message.subject:
            payload["subject"] = message.subject
        if message.mentions:
            payload["mentions"] = [
                {
                    "id": m.index,
                    "mentionText": m.text,
                    "mentioned": {
                        "user": {
                            "id": m.user_id,
                            "displayName": m.text,
                            "userIdentityType": "aadUser",
                        }
                    },
                }
                for m in message.mentions
            ]
        return payload


def mention_tag(mention: Mention) -> str:
    """Build the inline marker that must appear in body_html for a mention to render."""
    return f'<at id="{mention.index}">{mention.text}</at>'
