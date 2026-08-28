from datetime import datetime, timezone
from typing import Sequence

from teams_core.domain.models import (
    Author,
    BlobRef,
    ConversationRef,
    DownloadedFile,
    FileAttachment,
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


class FakeFileDownloader:
    def __init__(self, content: bytes = b"fake file content") -> None:
        self.downloaded: list[FileAttachment] = []
        self._content = content

    def download(self, attachment: FileAttachment) -> DownloadedFile:
        self.downloaded.append(attachment)
        return DownloadedFile(
            name=attachment.name,
            content=self._content,
            content_type="application/octet-stream",
        )


def make_attachment(
    name: str = "test.pdf",
    content_url: str = "https://tenant.sharepoint.com/sites/Test/Shared%20Documents/test.pdf",
    **kw,
) -> FileAttachment:
    defaults = dict(id="att-1", name=name, content_url=content_url)
    return FileAttachment(**{**defaults, **kw})


class FakeFileUploader:
    def __init__(self) -> None:
        self.uploaded: list[tuple[bytes, str]] = []

    def upload(self, file_content: bytes, file_name: str) -> BlobRef:
        self.uploaded.append((file_content, file_name))
        return BlobRef(
            name=file_name,
            url=f"https://fake.blob.core.windows.net/test-container/{file_name}",
        )

    def get_blob_url(self, blob_name: str) -> str:
        return f"https://fake.blob.core.windows.net/test-container/{blob_name}"


def make_message(text: str = "hello", **kw) -> InboundMessage:
    defaults = dict(
        message_id="1",
        author=Author(id="u1", display_name="Test User"),
        text=text,
        body_html=f"<p>{text}</p>",
        created_at=datetime.now(timezone.utc),
    )
    return InboundMessage(**{**defaults, **kw})


def make_blob_ref(
    name: str = "test.pdf",
    url: str = "https://fake.blob.core.windows.net/test-container/test.pdf",
) -> BlobRef:
    return BlobRef(name=name, url=url)
