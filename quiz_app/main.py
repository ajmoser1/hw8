from __future__ import annotations

from dataclasses import dataclass
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

from .services.auth import AuthService, User
from .services.feedback import FeedbackService
from .services.history import HistoryService
from .services.questions import Question, QuestionBank


APP_TITLE = "hw8 Quiz App"


@dataclass
class SessionResult:
    difficulty: str
    total: int
    correct: int


def _print_intro() -> None:
    print(f"{APP_TITLE}")
    print(
        "A command-line quiz app with accounts, persistent stats, and a JSON question bank."
    )
    print()


def _prompt_difficulty(available: List[str]) -> str:
    available_lower = [d.lower() for d in available]
    while True:
        print("Choose a difficulty:")
        for d in available:
            print(f"- {d}")
        choice = input("> ").strip()
        if choice.lower() in available_lower:
            return available[available_lower.index(choice.lower())]
        print(f"Invalid difficulty. Valid: {', '.join(available)}")


def _run_quiz(
    bank: QuestionBank,
    feedback: FeedbackService,
    user: User,
    difficulty: str,
) -> SessionResult:
    # Per spec: 6 questions per session
    total_questions = 6

    questions = bank.select_questions(
        difficulty=difficulty,
        count=total_questions,
        user_feedback=feedback.get_user_feedback(user.username),
    )

    print("\nAnswer format rules:")
    print("- Multiple choice: A/a, B/b, C/c, D/d")
    print("- True/False: True/true/t, False/false/f")
    print(
        "- Short answer: case-sensitive as required by the question (some require lowercase/camelCase)"
    )
    print()

    correct = 0
    for idx, q in enumerate(questions, start=1):
        print(f"Question {idx}/{total_questions} ({q.type}, {q.category}):")
        is_correct = q.ask_and_grade()
        if is_correct:
            correct += 1
        else:
            print(f"Answer: {q.answer_display()}")

        # feedback influences future selection
        fb = _prompt_feedback()
        if fb is not None:
            feedback.record_feedback(user.username, q.id, fb)

        print()

    print(f"Session complete. Score: {correct}/{total_questions}")
    return SessionResult(difficulty=difficulty, total=total_questions, correct=correct)


def _prompt_feedback() -> Optional[str]:
    print("Feedback? (like/dislike/too hard/too easy or press Enter to skip)")
    val = input("> ").strip().lower()
    if val == "":
        return None
    allowed = {"like", "dislike", "too hard", "too easy"}
    if val not in allowed:
        print("Invalid feedback; skipping.")
        return None
    return val


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    bank_path = os.path.join(data_dir, "questions.json")
    users_path = os.path.join(data_dir, "users.json")
    history_path = os.path.join(data_dir, "history.dat")
    feedback_path = os.path.join(data_dir, "feedback.json")

    _print_intro()

    bank = QuestionBank.from_file(bank_path)
    auth = AuthService(users_path)
    history = HistoryService(history_path)
    feedback = FeedbackService(feedback_path)

    user = auth.login_flow()

    # challenge mode is unlocked only after perfect 6/6 on hard
    unlocked = history.get_unlocked_difficulties(user.username)
    available = ["Easy", "Medium", "Hard"]
    if "Challenge" in unlocked:
        available.append("Challenge")

    difficulty = _prompt_difficulty(available)

    result = _run_quiz(bank, feedback, user, difficulty)

    history.record_session(user.username, result.difficulty, result.correct, result.total)

    # Unlock challenge mode condition from spec
    if result.difficulty.lower() == "hard" and result.correct == result.total:
        history.unlock_difficulty(user.username, "Challenge")
        print("Challenge mode unlocked! It will appear next time you choose difficulty.")


if __name__ == "__main__":
    main()
