from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ConversationKind(str, Enum):
    CHAT = "chat"
    CHANNEL = "channel"


@dataclass(frozen=True)
class ConversationRef:
    kind: ConversationKind
    chat_id: str | None = None
    team_id: str | None = None
    channel_id: str | None = None

    def __post_init__(self) -> None:
        if self.kind is ConversationKind.CHAT and not self.chat_id:
            raise ValueError("chat_id required for CHAT")
        if self.kind is ConversationKind.CHANNEL and not (
            self.team_id and self.channel_id
        ):
            raise ValueError("team_id and channel_id required for CHANNEL")

    @property
    def key(self) -> str:
        """Stable identifier for storage and dedup."""
        if self.kind is ConversationKind.CHAT:
            return f"chat:{self.chat_id}"
        return f"channel:{self.team_id}:{self.channel_id}"


@dataclass(frozen=True)
class Author:
    id: str | None
    display_name: str | None
    is_application: bool = False


@dataclass(frozen=True)
class Mention:
    index: int
    text: str
    user_id: str


@dataclass(frozen=True)
class OutboundMessage:
    body_html: str
    mentions: list[Mention] = field(default_factory=list)
    subject: str | None = None
    reply_to_message_id: str | None = None
    importance: str = "normal"


@dataclass(frozen=True)
class InboundMessage:
    """Normalized representation of a Graph chatMessage."""
    message_id: str
    conversation: ConversationRef
    author: Author
    text: str
    body_html: str
    created_at: datetime
    etag: str | None = None
    reply_to_id: str | None = None

    @property
    def dedup_key(self) -> str:
        return f"{self.conversation.key}:{self.message_id}"
