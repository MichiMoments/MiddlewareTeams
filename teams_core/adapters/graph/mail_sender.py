"""Graph adapter for sending emails via /me/sendMail."""
import base64
import logging

from teams_core.adapters.graph.client import GraphClient
from teams_core.domain.models import EmailAddress, OutboundEmail

log = logging.getLogger(__name__)


class GraphEmailSender:
    """Implements EmailSender. Sends as the signed-in service account."""

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    def send(self, email: OutboundEmail) -> None:
        payload = self._build_send_payload(email)
        self._client.request("POST", "/me/sendMail", json=payload)

    def reply(self, message_id: str, body_html: str) -> None:
        payload = {
            "message": {
                "body": {"contentType": "html", "content": body_html},
            },
        }
        self._client.request(
            "POST", f"/me/messages/{message_id}/reply", json=payload
        )

    @staticmethod
    def _build_send_payload(email: OutboundEmail) -> dict:
        message: dict = {
            "subject": email.subject,
            "body": {"contentType": "html", "content": email.body_html},
            "toRecipients": [GraphEmailSender._fmt_recipient(a) for a in email.to],
        }
        if email.cc:
            message["ccRecipients"] = [
                GraphEmailSender._fmt_recipient(a) for a in email.cc
            ]
        if email.bcc:
            message["bccRecipients"] = [
                GraphEmailSender._fmt_recipient(a) for a in email.bcc
            ]
        if email.importance != "normal":
            message["importance"] = email.importance
        if email.attachments:
            message["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att.name,
                    "contentType": att.content_type,
                    "contentBytes": base64.b64encode(att.content_bytes).decode(),
                }
                for att in email.attachments
            ]
        return {
            "message": message,
            "saveToSentItems": email.save_to_sent,
        }

    @staticmethod
    def _fmt_recipient(addr: EmailAddress) -> dict:
        r: dict = {"emailAddress": {"address": addr.address}}
        if addr.name:
            r["emailAddress"]["name"] = addr.name
        return r
