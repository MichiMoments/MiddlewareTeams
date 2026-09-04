"""One-time interactive sign-in. Run: python -m scripts.bootstrap_auth"""
import http.server
import socketserver
import sys
import urllib.parse
import webbrowser

import msal

from teams_core.auth.cache import EncryptedTokenCache
from teams_core.auth.scopes import SCOPES
from teams_core.config import TeamsConfig

cfg = TeamsConfig.from_env()
cache = EncryptedTokenCache(cfg.token_cache_path, cfg.token_cache_key)

app = msal.ConfidentialClientApplication(
    client_id=cfg.client_id,
    authority=cfg.authority,
    client_credential=cfg.client_secret,
    token_cache=cache.load(),
)

flow = app.initiate_auth_code_flow(scopes=SCOPES, redirect_uri=cfg.redirect_uri)
print("Sign in as the SERVICE ACCOUNT:\n", flow["auth_uri"])
if "--no-browser" not in sys.argv:
    webbrowser.open(flow["auth_uri"])

captured: dict[str, str] = {}
port = int(urllib.parse.urlparse(cfg.redirect_uri).port or 8400)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        captured.update(
            {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Done. You can close this tab.")

    def log_message(self, *args):
        pass


with socketserver.TCPServer(("127.0.0.1", port), _Handler) as httpd:
    httpd.handle_request()

result = app.acquire_token_by_auth_code_flow(flow, captured)

if "access_token" not in result:
    raise SystemExit(
        f"Bootstrap failed: {result.get('error')} -- "
        f"{result.get('error_description')}"
    )

cache.save(app.token_cache)
print("Token cache written to", cfg.token_cache_path)
print("Signed in as:", result.get("id_token_claims", {}).get("preferred_username"))
