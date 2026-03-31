from __future__ import annotations

import json
import os
from typing import Dict


class FeedbackService:
    """Stores user feedback per question.

    Feedback values:
    - like / dislike
    - too hard / too easy

    Used to bias future selection.
    """

    def __init__(self, feedback_path: str):
        self.feedback_path = feedback_path
        self._data = self._load()

    def get_user_feedback(self, username: str) -> Dict[str, str]:
        u = self._data.get(username, {})
        return u if isinstance(u, dict) else {}

    def record_feedback(self, username: str, question_id: str, feedback: str) -> None:
        self._data.setdefault(username, {})[question_id] = feedback
        self._save()

    def _load(self) -> Dict[str, Dict[str, str]]:
        if not os.path.exists(self.feedback_path):
            return {}
        try:
            with open(self.feedback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.feedback_path), exist_ok=True)
            with open(self.feedback_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            return
