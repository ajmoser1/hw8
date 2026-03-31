from __future__ import annotations

from dataclasses import dataclass
import json
import os
import random
from typing import Any, Dict, List, Optional


VALID_MC = {"a", "b", "c", "d"}
VALID_TF = {"true", "t", "false", "f"}


@dataclass
class Question:
    id: str
    question: str
    type: str  # multiple_choice | true_false | short_answer
    answer: str
    category: str
    difficulty: str
    options: Optional[List[str]] = None
    # for hard two-part questions
    parts: Optional[List["Question"]] = None

    def ask_and_grade(self) -> bool:
        if self.parts:
            all_correct = True
            for part_idx, part in enumerate(self.parts, start=1):
                print(f"Part {part_idx}: {part.question}")
                if part.type == "multiple_choice":
                    _print_options(part.options or [])
                ok = _grade_single(part)
                all_correct = all_correct and ok
            return all_correct

        print(self.question)
        if self.type == "multiple_choice":
            _print_options(self.options or [])
        return _grade_single(self)

    def answer_display(self) -> str:
        if self.parts:
            return " / ".join([p.answer for p in self.parts])
        return self.answer


def _print_options(options: List[str]) -> None:
    labels = ["A", "B", "C", "D"]
    for i, opt in enumerate(options[:4]):
        print(f"  {labels[i]}. {opt}")


def _grade_single(q: Question) -> bool:
    def safe_input(prompt: str) -> str:
        try:
            return input(prompt)
        except EOFError:
            print("\nInput ended. Exiting quiz.")
            raise SystemExit(0)

    if q.type == "multiple_choice":
        allowed = "A/a, B/b, C/c, D/d"
        while True:
            ans = safe_input("> ").strip()
            if ans.lower() not in VALID_MC:
                print(f"Invalid response. Valid responses: {allowed}")
                continue
            idx = {"a": 0, "b": 1, "c": 2, "d": 3}[ans.lower()]
            chosen = (q.options or [""] * 4)[idx]
            if chosen == q.answer:
                print("Correct!")
                return True
            print("Incorrect.")
            return False

    if q.type == "true_false":
        allowed = "True/true/t, False/false/f"
        while True:
            ans = safe_input("> ").strip().lower()
            if ans not in VALID_TF:
                print(f"Invalid response. Valid responses: {allowed}")
                continue
            normalized = "true" if ans in {"true", "t"} else "false"
            if normalized == q.answer.lower():
                print("Correct!")
                return True
            print("Incorrect.")
            return False

    # short_answer: one chance, no invalid list per spec
    ans = safe_input("> ").strip()
    if ans == q.answer:
        print("Correct!")
        return True
    print("Incorrect.")
    return False


class QuestionBank:
    def __init__(self, questions: List[Question]):
        self.questions = questions

    @classmethod
    def from_file(cls, path: str) -> "QuestionBank":
        if not os.path.exists(path):
            raise SystemExit(
                f"Missing question bank file at {path}. Expected quiz_app/data/questions.json"
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Invalid JSON in question bank: {e}")

        raw = data.get("questions")
        if not isinstance(raw, list):
            raise SystemExit("Question bank JSON must contain a 'questions' list")

        questions: List[Question] = []
        for item in raw:
            q = _parse_question(item)
            if q:
                questions.append(q)

        return cls(questions)

    def select_questions(
        self,
        difficulty: str,
        count: int,
        user_feedback: Dict[str, str],
    ) -> List[Question]:
        eligible = [q for q in self.questions if q.difficulty.lower() == difficulty.lower()]
        if len(eligible) < count:
            # fall back: if challenge not ready etc.
            random.shuffle(eligible)
            return eligible[:count]

        # Weighting based on feedback
        def weight(q: Question) -> float:
            fb = user_feedback.get(q.id)
            if fb == "like":
                return 2.0
            if fb == "dislike":
                return 0.2
            if fb == "too easy":
                # bias upward in difficulty if possible: handled by caller by picking difficulty.
                # Here we just de-prioritize.
                return 0.5
            if fb == "too hard":
                return 0.5
            return 1.0

        pool = eligible[:]
        # sample without replacement using weights
        chosen: List[Question] = []
        for _ in range(count):
            total_w = sum(weight(q) for q in pool)
            r = random.random() * total_w
            upto = 0.0
            pick_idx = 0
            for i, q in enumerate(pool):
                upto += weight(q)
                if upto >= r:
                    pick_idx = i
                    break
            chosen.append(pool.pop(pick_idx))
        return chosen


def _parse_question(item: Dict[str, Any]) -> Optional[Question]:
    try:
        qid = str(item["id"])
        qtext = str(item["question"])
        qtype = str(item["type"])
        category = str(item.get("category", "General"))
        difficulty = str(item.get("difficulty", "Easy"))

        if qtype == "hard_two_part":
            parts_raw = item.get("parts")
            if not isinstance(parts_raw, list) or len(parts_raw) != 2:
                return None
            parts: List[Question] = []
            for pi, pr in enumerate(parts_raw):
                # each part is a normal question style
                part_item = dict(pr)
                part_item.setdefault("id", f"{qid}.p{pi+1}")
                part_item.setdefault("category", category)
                part_item.setdefault("difficulty", difficulty)
                part_q = _parse_question(part_item)
                if part_q is None:
                    return None
                parts.append(part_q)
            return Question(
                id=qid,
                question=qtext,
                type="hard_two_part",
                answer="",
                category=category,
                difficulty=difficulty,
                parts=parts,
            )

        answer = str(item["answer"])
        options = item.get("options")
        if qtype == "multiple_choice":
            if not isinstance(options, list) or len(options) != 4:
                return None
            options = [str(x) for x in options]
        else:
            options = None

        if qtype not in {"multiple_choice", "true_false", "short_answer"}:
            return None

        return Question(
            id=qid,
            question=qtext,
            type=qtype,
            options=options,
            answer=answer,
            category=category,
            difficulty=difficulty,
        )
    except Exception:
        return None
