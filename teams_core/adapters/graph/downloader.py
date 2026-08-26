"""Graph adapter for downloading file attachments via the Shares API."""
import base64
import logging

from teams_core.adapters.graph.client import GraphClient
from teams_core.domain.models import DownloadedFile, FileAttachment

log = logging.getLogger(__name__)


class GraphFileDownloader:

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    def download(self, attachment: FileAttachment) -> DownloadedFile:
        token = self._encode_sharing_url(attachment.content_url)
        resp = self._client.request_bytes(
            "GET", f"/shares/{token}/driveItem/content"
        )
        content_type = resp.headers.get("content-type", "application/octet-stream")
        return DownloadedFile(
            name=attachment.name,
            content=resp.content,
            content_type=content_type,
        )

    @staticmethod
    def _encode_sharing_url(url: str) -> str:
        encoded = base64.urlsafe_b64encode(url.encode()).decode()
        encoded = encoded.rstrip("=")
        return f"u!{encoded}"
