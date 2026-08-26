"""Polling test: detect new messages across all chats and auto-reply."""
import logging
import time

from teams_core.adapters.graph.client import GraphClient, GraphError
from teams_core.adapters.graph.reader import GraphMessageReader
from teams_core.adapters.graph.sender import GraphMessageSender
from teams_core.auth.provider import MsalTokenProvider
from teams_core.config import TeamsConfig
from teams_core.domain.models import ConversationKind, ConversationRef, OutboundMessage

POLL_INTERVAL = 5
CHATS_TOP = 50
MESSAGES_PER_CHAT = 10
REPLY_HTML = "<p>Hello, testing messaging</p>"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("test_poll")

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
reader = GraphMessageReader(client)
sender = GraphMessageSender(client)

me = client.request("GET", "/me")
my_id = me["id"]
log.info("Service account user ID: %s", my_id)


def list_chats():
    resp = client.request("GET", "/me/chats", params={"$top": str(CHATS_TOP)})
    return resp.get("value", [])


def read_recent(chat_id):
    conv = ConversationRef(kind=ConversationKind.CHAT, chat_id=chat_id)
    return list(reader.history(conv, limit=MESSAGES_PER_CHAT))


def send_reply(chat_id):
    conv = ConversationRef(kind=ConversationKind.CHAT, chat_id=chat_id)
    msg = OutboundMessage(body_html=REPLY_HTML)
    return sender.send(conv, msg)


def seed_seen_ids():
    seen = set()
    chats = list_chats()
    log.info("Seed phase: found %d chats", len(chats))

    for chat in chats:
        chat_id = chat["id"]
        try:
            messages = read_recent(chat_id)
            for m in messages:
                seen.add(m.message_id)
            log.info("  Chat %s: seeded %d messages", chat_id[:40], len(messages))
        except GraphError as exc:
            log.warning("  Chat %s: failed to read (%s)", chat_id[:40], exc)

    log.info("Seed complete: %d message IDs tracked", len(seen))
    return seen


def poll_cycle(seen_ids):
    chats = list_chats()

    for chat in chats:
        chat_id = chat["id"]
        try:
            messages = read_recent(chat_id)
        except GraphError as exc:
            log.warning("Failed to read chat %s: %s", chat_id[:40], exc)
            continue

        for m in messages:
            if m.message_id in seen_ids:
                continue

            seen_ids.add(m.message_id)

            if m.author.id is None:
                continue

            if m.author.is_application:
                continue

            if m.author.id == my_id:
                continue

            author_name = m.author.display_name or m.author.id
            preview = m.text[:80] if m.text else "(empty)"
            print(f"  [NEW] from={author_name} chat={chat_id[:40]} text={preview!r}")

            try:
                reply_id = send_reply(chat_id)
                seen_ids.add(reply_id)
                print(f"  [REPLIED] msg_id={reply_id}")
            except GraphError as exc:
                log.error("  Failed to reply in chat %s: %s", chat_id[:40], exc)


def main():
    print("\n=== Polling test: auto-reply to new messages ===\n")

    seen_ids = seed_seen_ids()

    print(f"\nPolling every {POLL_INTERVAL}s. Press Ctrl+C to stop.\n")
    try:
        while True:
            poll_cycle(seen_ids)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        log.info("Seen set size at exit: %d", len(seen_ids))


main()
