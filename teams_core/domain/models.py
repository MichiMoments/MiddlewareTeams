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
class FileAttachment:
    """File sent in a Teams message (metadata only, no content)."""
    id: str
    name: str
    content_url: str


@dataclass(frozen=True)
class DownloadedFile:
    """File content fetched from SharePoint/OneDrive via Graph."""
    name: str
    content: bytes
    content_type: str


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
    attachments: tuple[FileAttachment, ...] = ()

    @property
    def dedup_key(self) -> str:
        return f"{self.conversation.key}:{self.message_id}"


@dataclass(frozen=True)
class BlobRef:
    """Reference to a blob in Azure Blob Storage."""
    name: str
    url: str


# --- Email domain models ---


@dataclass(frozen=True)
class EmailAddress:
    address: str
    name: str | None = None


@dataclass(frozen=True)
class EmailFileAttachment:
    """File to attach to an outgoing email. Max 3 MB for inline base64."""
    name: str
    content_bytes: bytes
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class OutboundEmail:
    subject: str
    body_html: str
    to: list[EmailAddress] = field(default_factory=list)
    cc: list[EmailAddress] = field(default_factory=list)
    bcc: list[EmailAddress] = field(default_factory=list)
    importance: str = "normal"
    attachments: list[EmailFileAttachment] = field(default_factory=list)
    save_to_sent: bool = True


@dataclass(frozen=True)
class InboundEmail:
    """Normalized representation of a Graph mail message."""
    message_id: str
    subject: str
    body_html: str
    body_preview: str
    from_address: EmailAddress
    to_recipients: tuple[EmailAddress, ...]
    cc_recipients: tuple[EmailAddress, ...] = ()
    received_at: datetime | None = None
    is_read: bool = False
    importance: str = "normal"
    has_attachments: bool = False
    conversation_id: str | None = None
    internet_message_id: str | None = None


@dataclass(frozen=True)
class MailFolder:
    """A mail folder (Inbox, Sent, Drafts, etc.)."""
    id: str
    display_name: str
    total_count: int = 0
    unread_count: int = 0
