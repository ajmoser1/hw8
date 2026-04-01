from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from typing import Any, Dict, List

from cryptography.fernet import Fernet, InvalidToken


class HistoryService:
    """Stores score history and stats in a non-human-readable format.

    Spec requirement:
    - file should not be human-readable; someone might learn usernames but not scores.

    Implementation:
    - JSON is encrypted using Fernet (AES-CBC + HMAC, via the cryptography package).
    - The encryption key is derived from the user's password at login time.
    - No on-disk key file is stored next to the history file.
    """

    def __init__(self, history_path: str):
        self.history_path = history_path
        self._fernet: Fernet | None = None

    def set_password(self, username: str, password: str) -> None:
        # Derive a per-user key (users can still be discoverable in the file, as spec allows).
        # Note: This isn't meant to be enterprise-grade KDF management; it's a reasonable
        # improvement over the previous XOR+keyfile approach while keeping dependencies low.
        key = _derive_fernet_key(username=username, password=password)
        self._fernet = Fernet(key)

    def record_session(self, username: str, difficulty: str, correct: int, total: int) -> None:
        self._ensure_ready()
        data = self._load()
        user = data.setdefault(username, {"sessions": [], "unlocked": []})
        user["sessions"].append({"difficulty": difficulty, "correct": correct, "total": total})
        self._save(data)

    def get_unlocked_difficulties(self, username: str) -> List[str]:
        self._ensure_ready()
        data = self._load()
        user = data.get(username)
        if not isinstance(user, dict):
            return []
        unlocked = user.get("unlocked", [])
        return unlocked if isinstance(unlocked, list) else []

    def unlock_difficulty(self, username: str, difficulty: str) -> None:
        self._ensure_ready()
        data = self._load()
        user = data.setdefault(username, {"sessions": [], "unlocked": []})
        unlocked = user.setdefault("unlocked", [])
        if difficulty not in unlocked:
            unlocked.append(difficulty)
        self._save(data)

    def _ensure_ready(self) -> None:
        if self._fernet is None:
            raise SystemExit(
                "HistoryService isn't initialized with a password. Call history.set_password(...) after login."
            )

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.history_path):
            return {}
        try:
            with open(self.history_path, "rb") as f:
                token = f.read()

            # New format: Fernet token bytes.
            if self._fernet is not None:
                try:
                    plain = self._fernet.decrypt(token)
                    data = json.loads(plain.decode("utf-8"))
                    return data if isinstance(data, dict) else {}
                except InvalidToken:
                    # Might be legacy file; fall through.
                    pass

            # Legacy format (best-effort): base64(XOR(json, key_from_keyfile)).
            legacy = _try_load_legacy_xor_history(self.history_path)
            if legacy is not None:
                return legacy

            return {}
        except Exception:
            # corrupted file => start fresh
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            plain = json.dumps(data, separators=(",", ":")).encode("utf-8")
            self._ensure_ready()
            assert self._fernet is not None
            b64 = self._fernet.encrypt(plain)
            dirpath = os.path.dirname(self.history_path)
            with tempfile.NamedTemporaryFile(
                "wb",
                dir=dirpath,
                delete=False,
            ) as tf:
                tf.write(b64)
                tmp_name = tf.name
            os.replace(tmp_name, self.history_path)
        except OSError:
            # best-effort
            return


def _derive_fernet_key(*, username: str, password: str) -> bytes:
    # Fernet expects a 32-byte key, urlsafe-base64 encoded.
    # We derive bytes using SHA256(password + username). For the scope of this assignment
    # it's sufficient and avoids storing a separate key file.
    digest = hashlib.sha256((password + "::" + username).encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _try_load_legacy_xor_history(history_path: str) -> Dict[str, Any] | None:
    key_path = history_path + ".key"
    if not os.path.exists(key_path):
        return None
    try:
        with open(key_path, "rb") as f:
            key = f.read()
        if len(key) < 16:
            return None
        with open(history_path, "rb") as f:
            b64 = f.read()
        raw = base64.b64decode(b64)
        plain = _xor(raw, key)
        data = json.loads(plain.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return None


def _xor(data: bytes, key: bytes) -> bytes:
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ key[i % len(key)]
    return bytes(out)
