from typing import Protocol, Sequence

from teams_core.domain.models import (
    ConversationRef,
    DownloadedFile,
    FileAttachment,
    InboundMessage,
    OutboundMessage,
)


class TokenProvider(Protocol):
    def get_token(self) -> str: ...


class MessageSender(Protocol):
    def send(self, to: ConversationRef, message: OutboundMessage) -> str:
        """Returns the created message id."""
        ...


class MessageReader(Protocol):
    def history(
        self, conversation: ConversationRef, limit: int = 50
    ) -> Sequence[InboundMessage]: ...

    def get_one(
        self, conversation: ConversationRef, message_id: str
    ) -> InboundMessage: ...


class FileDownloader(Protocol):
    def download(self, attachment: FileAttachment) -> DownloadedFile: ...


class MessageAnalyzer(Protocol):
    def analyze(self, message: InboundMessage) -> dict: ...
