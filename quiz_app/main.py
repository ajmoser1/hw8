from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List, Optional

from .services.auth import AuthService, User
from .services.feedback import FeedbackService
from .services.history import HistoryService
from .services.questions import QuestionBank


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

    user_fb = feedback.get_user_feedback(user.username)

    def shift_difficulty(cur: str, direction: str) -> str:
        order = ["Easy", "Medium", "Hard", "Challenge"]
        cur_norm = cur.lower()
        order_norm = [d.lower() for d in order]
        if cur_norm not in order_norm:
            return cur
        i = order_norm.index(cur_norm)
        if direction == "up" and i + 1 < len(order):
            return order[i + 1]
        if direction == "down" and i - 1 >= 0:
            return order[i - 1]
        return cur

    print("\nAnswer format rules:")
    print("- Multiple choice: A/a, B/b, C/c, D/d")
    print("- True/False: True/true/t, False/false/f")
    print(
        "- Short answer: case-sensitive as required by the question (some require lowercase/camelCase)"
    )
    print()

    correct = 0
    current_difficulty = difficulty
    asked_ids: set[str] = set()
    for idx in range(1, total_questions + 1):
        # Select one question at a time so feedback can influence difficulty changes.
        candidates = [
            q
            for q in bank.select_questions(
                difficulty=current_difficulty,
                count=20,
                user_feedback=user_fb,
            )
            if q.id not in asked_ids
        ]
        if not candidates:
            # Fallback: ignore asked_ids constraint.
            candidates = bank.select_questions(
                difficulty=current_difficulty,
                count=1,
                user_feedback=user_fb,
            )
        if not candidates:
            print(f"Not enough questions available for difficulty '{current_difficulty}'.")
            break
        q = candidates[0]
        asked_ids.add(q.id)
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
            user_fb[q.id] = fb

            # Per spec: too hard/too easy shifts difficulty if possible.
            if fb == "too hard":
                current_difficulty = shift_difficulty(current_difficulty, "down")
            elif fb == "too easy":
                current_difficulty = shift_difficulty(current_difficulty, "up")

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

    user, password = auth.login_flow()
    history.set_password(user.username, password)

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
