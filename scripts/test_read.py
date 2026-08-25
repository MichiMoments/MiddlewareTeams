"""Quick smoke test: list chats and read recent messages."""
import logging
import sys

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.adapters.graph.reader import GraphMessageReader
from teams_core.config import TeamsConfig
from teams_core.domain.models import ConversationKind, ConversationRef

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
reader = GraphMessageReader(client)

print("\n=== Chats visibles para el service account ===\n")
chats = client.request("GET", "/me/chats", params={"$top": "10"})

if not chats.get("value"):
    print("No se encontraron chats. El service account debe ser miembro de al menos un chat.")
    sys.exit(1)

for i, c in enumerate(chats["value"]):
    topic = c.get("topic") or "(sin tema)"
    chat_type = c.get("chatType", "?")
    print(f"  [{i}] tipo={chat_type}  topic={topic}")
    print(f"      chat_id={c['id']}")

first = chats["value"][0]
print(f"\n=== Ultimos 5 mensajes del chat [{first.get('topic') or '(sin tema)'}] ===\n")

conv = ConversationRef(kind=ConversationKind.CHAT, chat_id=first["id"])
messages = reader.history(conv, limit=5)

if not messages:
    print("  (sin mensajes)")
else:
    for m in messages:
        author = m.author.display_name or m.author.id or "desconocido"
        text = m.text[:120] if m.text else "(vacio)"
        print(f"  [{m.created_at}] {author}: {text}")

print("\nLectura exitosa.")
