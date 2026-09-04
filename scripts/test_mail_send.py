"""Smoke test: send a test email via Graph."""
import logging

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.adapters.graph.mail_sender import GraphEmailSender
from teams_core.config import TeamsConfig
from teams_core.domain.models import EmailAddress, OutboundEmail

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# ---- Edit this value ----
TARGET_EMAIL = "d.perezc23@uniandes.edu.co"
# --------------------------

if TARGET_EMAIL == "PASTE_EMAIL_HERE":
    print("Edit TARGET_EMAIL in this script before running it.")
    import sys
    sys.exit(1)

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)
sender = GraphEmailSender(client)

email = OutboundEmail(
    subject="Test desde teams_core",
    body_html="<p>Este es un correo de prueba enviado por el middleware.</p>",
    to=[EmailAddress(address=TARGET_EMAIL)],
)

print(f"\n=== Enviando correo a {TARGET_EMAIL} ===\n")

sender.send(email)

print("  Correo enviado exitosamente (202 Accepted).")
print("\nEnvio de correo exitoso.")
