import re
from datetime import datetime
from typing import Sequence

from teams_core.adapters.graph.client import GraphClient
from teams_core.domain.models import (
    Author,
    ConversationKind,
    ConversationRef,
    FileAttachment,
    InboundMessage,
)

_TAG = re.compile(r"<[^>]+>")


class GraphMessageReader:
    def __init__(self, client: GraphClient) -> None:
        self._client = client

    @staticmethod
    def _base(conv: ConversationRef) -> str:
        if conv.kind is ConversationKind.CHAT:
            return f"/chats/{conv.chat_id}/messages"
        return f"/teams/{conv.team_id}/channels/{conv.channel_id}/messages"

    def history(
        self, conversation: ConversationRef, limit: int = 50
    ) -> Sequence[InboundMessage]:
        items = self._client.paged(
            self._base(conversation), params={"$top": min(limit, 50)}
        )
        out = []
        for raw in items:
            out.append(self._to_domain(raw, conversation))
            if len(out) >= limit:
                break
        return out

    def get_one(
        self, conversation: ConversationRef, message_id: str
    ) -> InboundMessage:
        raw = self._client.request(
            "GET", f"{self._base(conversation)}/{message_id}"
        )
        return self._to_domain(raw, conversation)

    @staticmethod
    def _parse_attachments(raw_attachments: list[dict]) -> tuple[FileAttachment, ...]:
        result = []
        for att in raw_attachments:
            if att.get("contentType") != "reference":
                continue
            content_url = att.get("contentUrl")
            name = att.get("name")
            if not content_url or not name:
                continue
            result.append(FileAttachment(
                id=att["id"],
                name=name,
                content_url=content_url,
            ))
        return tuple(result)

    @staticmethod
    def _to_domain(raw: dict, conv: ConversationRef) -> InboundMessage:
        body = raw.get("body") or {}
        html = body.get("content") or ""
        frm = raw.get("from") or {}
        user = frm.get("user") or {}
        app = frm.get("application") or {}

        return InboundMessage(
            message_id=raw["id"],
            conversation=conv,
            author=Author(
                id=user.get("id") or app.get("id"),
                display_name=user.get("displayName") or app.get("displayName"),
                is_application=bool(app),
            ),
            text=_TAG.sub("", html).strip(),
            body_html=html,
            created_at=datetime.fromisoformat(
                raw["createdDateTime"].replace("Z", "+00:00")
            ),
            etag=raw.get("etag"),
            reply_to_id=raw.get("replyToId"),
            attachments=GraphMessageReader._parse_attachments(
                raw.get("attachments") or []
            ),
        )
