"""Quick smoke test: send a message to a Teams chat."""
import logging

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.adapters.graph.sender import GraphMessageSender
from teams_core.config import TeamsConfig
from teams_core.domain.models import ConversationKind, ConversationRef, OutboundMessage

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

TARGET_CHAT = "19:6eab630b-a1e3-4814-b0d2-11e448af2ec4_d3d87a46-9669-42a3-a3a4-dfa700d9a0db@unq.gbl.spaces"

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
sender = GraphMessageSender(client)

conv = ConversationRef(kind=ConversationKind.CHAT, chat_id=TARGET_CHAT)
msg = OutboundMessage(body_html="<p>Hola, soy un bot</p>")

print(f"\n=== Enviando mensaje al chat {TARGET_CHAT[:40]}... ===\n")

message_id = sender.send(conv, msg)

print(f"  Mensaje enviado. ID: {message_id}")
print("\nEnvio exitoso.")
