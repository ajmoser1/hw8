from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any, Dict, List


class HistoryService:
    """Stores score history and stats in a non-human-readable format.

    Spec requirement:
    - file should not be human-readable; someone might learn usernames but not scores.

    Implementation:
    - JSON is XOR-obfuscated with a per-install key and then base64-encoded.
    - Not strong cryptography, but makes the file non-readable at a glance.
    """

    def __init__(self, history_path: str):
        self.history_path = history_path
        self.key_path = history_path + ".key"
        self._key = self._load_or_create_key()

    def record_session(self, username: str, difficulty: str, correct: int, total: int) -> None:
        data = self._load()
        user = data.setdefault(username, {"sessions": [], "unlocked": []})
        user["sessions"].append(
            {"difficulty": difficulty, "correct": correct, "total": total}
        )
        self._save(data)

    def get_unlocked_difficulties(self, username: str) -> List[str]:
        data = self._load()
        user = data.get(username)
        if not isinstance(user, dict):
            return []
        unlocked = user.get("unlocked", [])
        return unlocked if isinstance(unlocked, list) else []

    def unlock_difficulty(self, username: str, difficulty: str) -> None:
        data = self._load()
        user = data.setdefault(username, {"sessions": [], "unlocked": []})
        unlocked = user.setdefault("unlocked", [])
        if difficulty not in unlocked:
            unlocked.append(difficulty)
        self._save(data)

    def _load_or_create_key(self) -> bytes:
        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, "rb") as f:
                    key = f.read()
                if len(key) >= 16:
                    return key
            except OSError:
                pass
        key = secrets.token_bytes(32)
        try:
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)
        except OSError:
            # fallback in-memory only
            pass
        return key

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.history_path):
            return {}
        try:
            with open(self.history_path, "rb") as f:
                b64 = f.read()
            raw = base64.b64decode(b64)
            plain = self._xor(raw, self._key)
            data = json.loads(plain.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            # corrupted file => start fresh
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            plain = json.dumps(data, separators=(",", ":")).encode("utf-8")
            ob = self._xor(plain, self._key)
            b64 = base64.b64encode(ob)
            with open(self.history_path, "wb") as f:
                f.write(b64)
        except OSError:
            # best-effort
            return

    @staticmethod
    def _xor(data: bytes, key: bytes) -> bytes:
        out = bytearray(len(data))
        for i, b in enumerate(data):
            out[i] = b ^ key[i % len(key)]
        return bytes(out)
