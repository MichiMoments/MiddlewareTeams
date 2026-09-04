from typing import Protocol, Sequence

from teams_core.domain.models import (
    BlobRef,
    ConversationRef,
    DownloadedFile,
    FileAttachment,
    InboundEmail,
    InboundMessage,
    MailFolder,
    OutboundEmail,
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


class FileUploader(Protocol):
    def upload(self, file_content: bytes, file_name: str) -> BlobRef: ...
    def get_blob_url(self, blob_name: str) -> str: ...


class EmailSender(Protocol):
    def send(self, email: OutboundEmail) -> None: ...
    def reply(self, message_id: str, body_html: str) -> None: ...


class EmailReader(Protocol):
    def list_messages(
        self, *, folder_id: str | None = None, limit: int = 25
    ) -> Sequence[InboundEmail]: ...

    def get_message(self, message_id: str) -> InboundEmail: ...

    def list_folders(self) -> Sequence[MailFolder]: ...


class MessageAnalyzer(Protocol):
    def analyze(self, message: InboundMessage) -> dict: ...
