"""Smoke test: list mail folders and read recent emails from inbox."""
import logging
import sys

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.adapters.graph.mail_reader import GraphEmailReader
from teams_core.config import TeamsConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
reader = GraphEmailReader(client)

print("\n=== Carpetas de correo ===\n")
folders = reader.list_folders()

if not folders:
    print("No se encontraron carpetas.")
    sys.exit(1)

for f in folders:
    print(f"  {f.display_name}: {f.unread_count} no leidos / {f.total_count} total")

print(f"\n=== Ultimos 5 correos del inbox ===\n")
messages = reader.list_messages(limit=5)

if not messages:
    print("  (sin correos)")
else:
    for m in messages:
        sender = m.from_address.name or m.from_address.address
        read_mark = " " if m.is_read else "*"
        preview = m.body_preview[:100] if m.body_preview else "(vacio)"
        print(f"  [{read_mark}] {m.received_at}  De: {sender}")
        print(f"      Asunto: {m.subject}")
        print(f"      Preview: {preview}")
        print()

print("Lectura de correo exitosa.")
