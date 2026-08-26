import logging
import random
import time
from typing import Any

import httpx

from teams_core.config import TeamsConfig
from teams_core.ports import TokenProvider

log = logging.getLogger(__name__)


class GraphError(RuntimeError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"[{status}] {code}: {message}")
        self.status = status
        self.code = code


class GraphPermissionError(GraphError):
    """403 -- scope, membership, or Protected API problem. Not retryable."""


class GraphThrottled(GraphError):
    """429 or 503 after retries are exhausted."""


class GraphClient:
    MAX_ATTEMPTS = 5

    def __init__(self, cfg: TeamsConfig, tokens: TokenProvider) -> None:
        self._cfg = cfg
        self._tokens = tokens
        self._http = httpx.Client(timeout=30.0)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{self._cfg.graph_base}{path}"

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            resp = self._http.request(
                method,
                url,
                json=json,
                params=params,
                headers={
                    "Authorization": f"Bearer {self._tokens.get_token()}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code in (429, 503, 504):
                if attempt == self.MAX_ATTEMPTS:
                    raise GraphThrottled(resp.status_code, "throttled", resp.text)
                delay = float(
                    resp.headers.get("Retry-After", 2 ** attempt)
                ) + random.uniform(0, 0.5)
                log.warning(
                    "Graph throttled, sleeping %.1fs (attempt %s)", delay, attempt
                )
                time.sleep(delay)
                continue

            if resp.status_code >= 400:
                self._raise(resp)

            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()

        raise GraphThrottled(429, "throttled", "retries exhausted")

    @staticmethod
    def _raise(resp: httpx.Response) -> None:
        try:
            err = resp.json().get("error", {})
            code = err.get("code", "Unknown")
            message = err.get("message", resp.text)
        except Exception:
            code, message = "Unparseable", resp.text[:500]

        if resp.status_code == 403:
            raise GraphPermissionError(403, code, message)
        raise GraphError(resp.status_code, code, message)

    def request_bytes(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = path if path.startswith("http") else f"{self._cfg.graph_base}{path}"

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            resp = self._http.request(
                method,
                url,
                params=params,
                headers={
                    "Authorization": f"Bearer {self._tokens.get_token()}",
                },
                follow_redirects=True,
            )

            if resp.status_code in (429, 503, 504):
                if attempt == self.MAX_ATTEMPTS:
                    raise GraphThrottled(resp.status_code, "throttled", resp.text)
                delay = float(
                    resp.headers.get("Retry-After", 2 ** attempt)
                ) + random.uniform(0, 0.5)
                log.warning(
                    "Graph throttled, sleeping %.1fs (attempt %s)", delay, attempt
                )
                time.sleep(delay)
                continue

            if resp.status_code >= 400:
                self._raise(resp)

            return resp

        raise GraphThrottled(429, "throttled", "retries exhausted")

    def paged(self, path: str, *, params: dict | None = None):
        """Follows @odata.nextLink. Yields raw items."""
        page = self.request("GET", path, params=params)
        while True:
            yield from page.get("value", [])
            next_link = page.get("@odata.nextLink")
            if not next_link:
                return
            page = self.request("GET", next_link)
