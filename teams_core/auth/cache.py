import os
from pathlib import Path

import msal
from cryptography.fernet import Fernet


class EncryptedTokenCache:
    """MSAL SerializableTokenCache persisted encrypted at rest."""

    def __init__(self, path: str, key: str) -> None:
        self._path = Path(path)
        self._fernet = Fernet(key.encode())

    def load(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if self._path.exists():
            blob = self._fernet.decrypt(self._path.read_bytes())
            cache.deserialize(blob.decode())
        return cache

    def save(self, cache: msal.SerializableTokenCache) -> None:
        if not cache.has_state_changed:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        blob = self._fernet.encrypt(cache.serialize().encode())
        tmp = self._path.with_suffix(".tmp")
        tmp.write_bytes(blob)
        os.replace(tmp, self._path)
