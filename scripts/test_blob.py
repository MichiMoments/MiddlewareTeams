"""Smoke test: upload a file to Azure Blob Storage and retrieve its URL."""
import logging
import sys
from pathlib import Path

from teams_core.adapters.blob.storage import BlobStorageUploader
from teams_core.config import TeamsConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

cfg = TeamsConfig.from_env()
uploader = BlobStorageUploader(cfg)

FILE_PATH = Path(__file__).resolve().parent.parent / "otrosi_teletrabajo_20260818.zip"

if not FILE_PATH.exists():
    print(f"File not found: {FILE_PATH}")
    sys.exit(1)

TEST_CONTENT = FILE_PATH.read_bytes()
TEST_NAME = FILE_PATH.name

print(f"\n=== Azure Blob Storage upload test ===")
print(f"  File: {TEST_NAME} ({len(TEST_CONTENT)} bytes)\n")

try:
    ref = uploader.upload(TEST_CONTENT, TEST_NAME)
    print(f"  Blob name:  {ref.name}")
    print(f"  Blob URL:   {ref.url}")
except Exception as exc:
    logging.error("Upload failed: %s", exc)
    sys.exit(1)

print("\n--- Retrieving URL for existing blob ---\n")

url = uploader.get_blob_url(TEST_NAME)
print(f"  URL: {url}")

print("\nBlob test complete.")
