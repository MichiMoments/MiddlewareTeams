"""Azure Blob Storage adapter for uploading files and retrieving blob URLs."""
import logging
from urllib.parse import urlparse, urlunparse

from azure.storage.blob import ContainerClient

from teams_core.config import TeamsConfig
from teams_core.domain.models import BlobRef

log = logging.getLogger(__name__)


class BlobStorageUploader:
    """Implements FileUploader using Azure Blob Storage with a container SAS URL."""

    def __init__(self, cfg: TeamsConfig) -> None:
        self._container_url = cfg.storage_account_connection_string
        self._container_client = ContainerClient.from_container_url(self._container_url)

    def upload(self, file_content: bytes, file_name: str) -> BlobRef:
        blob_client = self._container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_content, overwrite=True)
        url = self._build_blob_url(file_name)
        log.info("Uploaded blob: %s (%d bytes)", file_name, len(file_content))
        return BlobRef(name=file_name, url=url)

    def get_blob_url(self, blob_name: str) -> str:
        return self._build_blob_url(blob_name)

    def _build_blob_url(self, blob_name: str) -> str:
        parsed = urlparse(self._container_url)
        blob_path = f"{parsed.path.rstrip('/')}/{blob_name}"
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            blob_path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
