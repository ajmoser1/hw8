from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import os
from typing import Dict, Optional


@dataclass(frozen=True)
class User:
    username: str


class AuthService:
    """Local login system.

    - Allows creating a new username/password or logging in.
    - Stores passwords securely as salted PBKDF2-HMAC hashes.
    """

    def __init__(self, users_path: str):
        self.users_path = users_path
        self._users = self._load_users()

    def login_flow(self) -> User:
        while True:
            print("Login")
            print("1) Login")
            print("2) Create new account")
            choice = input("> ").strip()
            if choice not in {"1", "2"}:
                print("Invalid choice. Enter 1 or 2.\n")
                continue

            username = input("Username: ").strip()
            if not username:
                print("Username cannot be empty.\n")
                continue

            password = input("Password: ").strip()
            if not password:
                print("Password cannot be empty.\n")
                continue

            if choice == "2":
                if username in self._users:
                    print("That username already exists.\n")
                    continue
                self._users[username] = self._hash_password(password)
                self._save_users()
                print("Account created.\n")
                return User(username=username)

            # choice == "1"
            if username not in self._users:
                print("Unknown username.\n")
                continue
            if not self._verify_password(password, self._users[username]):
                print("Incorrect password.\n")
                continue

            print("Login successful.\n")
            return User(username=username)

    def _load_users(self) -> Dict[str, str]:
        if not os.path.exists(self.users_path):
            return {}
        try:
            with open(self.users_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            users = data.get("users", {})
            return users if isinstance(users, dict) else {}
        except (OSError, json.JSONDecodeError):
            # Spec emphasizes robust behavior; corrupted file => start fresh
            return {}

    def _save_users(self) -> None:
        os.makedirs(os.path.dirname(self.users_path), exist_ok=True)
        tmp = {"users": self._users}
        with open(self.users_path, "w", encoding="utf-8") as f:
            json.dump(tmp, f, indent=2)

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return "pbkdf2_sha256$200000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        try:
            scheme, iters_s, salt_b64, dk_b64 = stored.split("$")
            if scheme != "pbkdf2_sha256":
                return False
            iters = int(iters_s)
            salt = base64.b64decode(salt_b64.encode())
            expected = base64.b64decode(dk_b64.encode())
            got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
            return hmac.compare_digest(got, expected)
        except Exception:
            return False
