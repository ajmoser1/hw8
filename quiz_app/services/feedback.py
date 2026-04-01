from __future__ import annotations

import json
import os
import base64
import tempfile
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
                wrapper = json.load(f)

            # New format: {"_encoded": true, "payload": "..."}
            if isinstance(wrapper, dict) and wrapper.get("_encoded") is True:
                payload = wrapper.get("payload")
                if isinstance(payload, str):
                    raw = base64.b64decode(payload.encode("utf-8"))
                    data = json.loads(raw.decode("utf-8"))
                    return data if isinstance(data, dict) else {}

            # Legacy format: plain JSON dict
            return wrapper if isinstance(wrapper, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
        except Exception:
            return {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.feedback_path), exist_ok=True)
            raw = json.dumps(self._data, separators=(",", ":")).encode("utf-8")
            wrapper = {
                "_encoded": True,
                "payload": base64.b64encode(raw).decode("utf-8"),
            }

            # Atomic write: write temp file then replace.
            dirpath = os.path.dirname(self.feedback_path)
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=dirpath,
                delete=False,
            ) as tf:
                json.dump(wrapper, tf, indent=2)
                tmp_name = tf.name
            os.replace(tmp_name, self.feedback_path)
        except OSError:
            return
