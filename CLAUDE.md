# teams_core

Framework-free Python package for Microsoft Teams integration via Microsoft Graph API.
Designed to be consumed by Django, Streamlit, or any other Python project.

> Referencia detallada de clases, métodos y firmas: ver [ARCHITECTURE.md](ARCHITECTURE.md) (local, no versionado).

## Architecture

```
teams_core/
  config.py              # TeamsConfig dataclass, loads .env via python-dotenv
  ports.py               # Protocol interfaces (TokenProvider, MessageSender, MessageReader, MessageAnalyzer)
  auth/
    scopes.py            # Delegated Graph scopes (7 scopes)
    cache.py             # EncryptedTokenCache (Fernet-encrypted MSAL cache at rest)
    provider.py          # MsalTokenProvider (delegated auth with Redis lock for safe refresh)
  domain/
    models.py            # ConversationRef, Author, Mention, OutboundMessage, InboundMessage
  adapters/
    fakes.py             # FakeSender, FakeReader, make_message() for testing
    graph/
      client.py          # GraphClient (httpx, retry on 429/503/504, error translation)
      sender.py          # GraphMessageSender + mention_tag() helper
      reader.py          # GraphMessageReader (history + get_one, HTML stripping)
      subscriptions.py   # SubscriptionManager (create, renew, delete, list_active)
scripts/
  bootstrap_auth.py      # One-time interactive sign-in to seed the token cache
  test_read.py           # Smoke test: list chats and read recent messages
  test_send.py           # Smoke test: send a message to a Teams chat
  test_poll.py           # Polling test: detect new messages and auto-reply
```

## Key design decisions

- **Delegated access model** (service account), not application-only. Graph has no app permission for normal message sending.
- **Auth flow**: Authorization code with confidential client. One interactive bootstrap, then silent refresh.
- **HTTP**: `msal` + `httpx` (sync). Avoids `msgraph-sdk` which is async-only.
- **Python 3.11+** required.
- **Graph v1.0 only** (`/beta` avoided in production).
- Nothing above the adapter layer imports `httpx`, `msal`, or knows about Graph. Ports are Protocol classes.

## Dependencies

- `msal` - Microsoft Authentication Library
- `httpx` - HTTP client
- `cryptography` - Fernet encryption for token cache
- `redis` - Distributed lock for token refresh
- `python-dotenv` - Loads `.env` automatically in `TeamsConfig.from_env()`

## Environment variables

All required, loaded via `TeamsConfig.from_env()`:

| Variable | Purpose |
|---|---|
| `TEAMS_TENANT_ID` | Entra tenant |
| `TEAMS_CLIENT_ID` | App registration client ID |
| `TEAMS_CLIENT_SECRET` | App registration secret (or use cert) |
| `TEAMS_REDIRECT_URI` | OAuth callback (e.g. `http://localhost:8400/callback`) |
| `TEAMS_TOKEN_CACHE_PATH` | File path for encrypted token cache |
| `TEAMS_TOKEN_CACHE_KEY` | Fernet key (32 url-safe base64 bytes) |
| `TEAMS_TOKEN_LOCK_URL` | Redis URL for refresh lock |
| `TEAMS_NOTIFICATION_URL` | Public HTTPS URL for Graph change notifications |
| `TEAMS_LIFECYCLE_URL` | Public HTTPS URL for Graph lifecycle events |
| `TEAMS_CLIENT_STATE` | Random secret echoed by Graph to verify notifications |

## Flujo de ejecución (setup completo)

El sistema requiere que los pasos se ejecuten en este orden. Cada paso depende del anterior.

```
1. Instalar dependencias
   pip install -e ".[dev]"

2. Configurar variables de entorno
   Copiar .env.example a .env y completar todos los valores.
   Ver tabla "Environment variables" arriba.

3. Levantar Redis (requerido por MsalTokenProvider)
   docker run -d -p 6379:6379 redis
   El provider usa un lock distribuido en Redis para evitar que
   múltiples procesos invaliden el refresh token al renovar
   simultáneamente. Sin Redis corriendo, cualquier operación
   que requiera un token falla con ConnectionError.

4. Bootstrap de autenticación (una sola vez, interactivo)
   python -m scripts.bootstrap_auth
   Abre el navegador para que el service account inicie sesión.
   Genera el archivo token_cache.enc cifrado con Fernet.
   Debe repetirse si el refresh token expira (~90 días de
   inactividad, verificar por tenant).

5. El sistema está listo para operar
   A partir de aquí, MsalTokenProvider renueva el access token
   silenciosamente usando el cache cifrado + el lock de Redis.
   GraphClient, GraphMessageSender y GraphMessageReader pueden
   instanciarse y usarse.
```


## Common commands

```bash
# Install in dev mode
pip install -e ".[dev]"

# Levantar Redis (prerequisito)
docker run -d -p 6379:6379 redis

# Bootstrap auth (run once, interactively, as the service account)
python -m scripts.bootstrap_auth

# Run tests
pytest

# Lint
ruff check teams_core/ tests/

# Type check
mypy teams_core/

# Smoke test: list chats and read messages (requires Redis + token cache)
python -m scripts.test_read

# Smoke test: send a message (requires Redis + token cache)
python -m scripts.test_send

# Polling test: auto-reply to new messages (requires Redis + token cache)
python -m scripts.test_poll
```

## Important constraints

- The service account must be a **member** of every target chat/team. No app permission bypasses this.
- `<at id="N">` tags in body_html must match the `mentions` array `id` values exactly.
- Stick to safe HTML tags: `<b>`, `<i>`, `<a>`, `<br>`, `<ul>`, `<code>`, `<blockquote>`.
- Change notifications are not guaranteed delivery; always have a backfill path via `history()`.
- Org limit: 10,000 total Teams change-notification subscriptions.
- Token refresh uses a Redis lock. Multiple processes refreshing without locking can invalidate each other's tokens permanently.
- `ReauthRequired` should trigger an alert; refresh tokens can silently expire.

## Items to verify per tenant

- Maximum `chatMessage` subscription lifetime (read from API response)
- Tenant refresh-token inactivity window (platform default ~90 days, can be overridden)
- Which non-`.All` scopes require admin consent under your user-consent policy
- Maximum client-secret lifetime
