"""Hide a chat from the service account's chat list.

Change CHAT_ID below to the chat you want to hide, then run:
    python -m scripts.hide_chat
"""
import logging
import sys

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.config import TeamsConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

CHAT_ID = "19:57322257-4306-40d5-8d92-587a11101ce8_d3d87a46-9669-42a3-a3a4-dfa700d9a0db@unq.gbl.spaces"


cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)

me = client.request("GET", "/me")
user_id = me["id"]

print(f"\nHiding chat {CHAT_ID[:50]}... for user {user_id}\n")

client.request("POST", f"/chats/{CHAT_ID}/hideForUser", json={
    "user": {
        "id": user_id,
        "tenantId": cfg.tenant_id,
    }
})

print("Chat hidden successfully.")
