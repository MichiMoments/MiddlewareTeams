from datetime import datetime, timezone
from typing import Sequence

from teams_core.domain.models import (
    Author,
    ConversationRef,
    InboundMessage,
    OutboundMessage,
)


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[tuple[ConversationRef, OutboundMessage]] = []

    def send(self, to: ConversationRef, message: OutboundMessage) -> str:
        self.sent.append((to, message))
        return f"fake-{len(self.sent)}"


class FakeReader:
    def __init__(self, messages: Sequence[InboundMessage] = ()) -> None:
        self._messages = list(messages)

    def history(self, conversation: ConversationRef, limit: int = 50):
        return self._messages[:limit]

    def get_one(self, conversation: ConversationRef, message_id: str):
        for m in self._messages:
            if m.message_id == message_id:
                return m
        raise KeyError(message_id)


def make_message(text: str = "hello", **kw) -> InboundMessage:
    defaults = dict(
        message_id="1",
        author=Author(id="u1", display_name="Test User"),
        text=text,
        body_html=f"<p>{text}</p>",
        created_at=datetime.now(timezone.utc),
    )
    return InboundMessage(**{**defaults, **kw})
