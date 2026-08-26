"""Smoke test: find file attachments in recent chats and download the first one."""
import logging
import sys

from teams_core.adapters.graph.client import GraphClient, GraphError
from teams_core.adapters.graph.downloader import GraphFileDownloader
from teams_core.adapters.graph.reader import GraphMessageReader
from teams_core.auth.provider import MsalTokenProvider
from teams_core.config import TeamsConfig
from teams_core.domain.models import ConversationKind, ConversationRef

CHATS_TOP = 20
MESSAGES_PER_CHAT = 20

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("test_file")

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
reader = GraphMessageReader(client)
downloader = GraphFileDownloader(client)

print("\n=== File attachment download test ===\n")

chats = client.request("GET", "/me/chats", params={"$top": str(CHATS_TOP)})
chat_list = chats.get("value", [])

if not chat_list:
    print("No chats found. The service account must be a member of at least one chat.")
    sys.exit(1)

print(f"Scanning {len(chat_list)} chats for file attachments...\n")

found_attachment = None
found_message = None

for chat in chat_list:
    chat_id = chat["id"]
    topic = chat.get("topic") or "(no topic)"
    conv = ConversationRef(kind=ConversationKind.CHAT, chat_id=chat_id)

    try:
        messages = reader.history(conv, limit=MESSAGES_PER_CHAT)
    except GraphError as exc:
        log.warning("Failed to read chat %s: %s", chat_id[:40], exc)
        continue

    for m in messages:
        if m.attachments:
            found_message = m
            found_attachment = m.attachments[0]
            print(f"  Found file in chat: {topic}")
            print(f"  Message from: {m.author.display_name or m.author.id}")
            print(f"  Message text: {m.text[:80] if m.text else '(empty)'}")
            print(f"  Attachments: {len(m.attachments)} file(s)")
            for att in m.attachments:
                print(f"    - {att.name} (id={att.id})")
                print(f"      url={att.content_url[:80]}...")
            break

    if found_attachment:
        break

if not found_attachment:
    print("No file attachments found in any recent messages.")
    print("Send a file in a Teams chat and run this script again.")
    sys.exit(0)

print(f"\n--- Downloading: {found_attachment.name} ---\n")

try:
    result = downloader.download(found_attachment)
    print(f"  Name:         {result.name}")
    print(f"  Content-Type: {result.content_type}")
    print(f"  Size:         {len(result.content)} bytes")

    out_path = found_attachment.name
    with open(out_path, "wb") as f:
        f.write(result.content)
    print(f"  Saved to:     {out_path}")

except GraphError as exc:
    log.error("Download failed: %s", exc)
    sys.exit(1)

print("\nDownload test complete.")
