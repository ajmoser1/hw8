from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import random
from enum import Enum
from typing import Any, Dict, List, Optional
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    HARD_TWO_PART = "hard_two_part"



VALID_MC = {"a", "b", "c", "d"}
VALID_TF = {"true", "t", "false", "f"}


@dataclass
class Question:
    id: str
    question: str
    type: str  # stored as the JSON string value; validated against QuestionType
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
            if _normalize_answer(chosen) == _normalize_answer(q.answer):
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


def _normalize_answer(s: str) -> str:
    return str(s).strip().casefold()


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
        errors: List[str] = []
        for idx, item in enumerate(raw):
            q = _parse_question(item)
            if q is None:
                preview = "<unprintable>"
                try:
                    preview = json.dumps(item, ensure_ascii=False)
                except Exception:
                    pass
                errors.append(f"- questions[{idx}] is invalid: {preview}")
                continue
            questions.append(q)

        if errors:
            joined = "\n".join(errors[:10])
            more = "" if len(errors) <= 10 else f"\n...and {len(errors) - 10} more"
            raise SystemExit(
                "Question bank contains invalid question objects. Fix them in questions.json:\n"
                + joined
                + more
            )

        _validate_question_bank(questions)
        return cls(questions)

    def select_questions(
        self,
        difficulty: str,
        count: int,
        user_feedback: Dict[str, str],
    ) -> List[Question]:
        # Spec special-case: Hard difficulty includes 4 two-part questions.
        if difficulty.lower() == "hard":
            return self._select_hard_session(count=count, user_feedback=user_feedback)

        eligible = [q for q in self.questions if q.difficulty.lower() == difficulty.lower()]
        if len(eligible) < count:
            raise SystemExit(
                f"Not enough questions for difficulty '{difficulty}'. Need {count}, found {len(eligible)}. "
                "Fix questions.json to meet the SPEC requirements."
            )

        def weight(q: Question) -> float:
            fb = user_feedback.get(q.id)
            if fb == "like":
                return 2.0
            if fb == "dislike":
                return 0.2
            if fb in {"too easy", "too hard"}:
                return 0.5
            return 1.0

        pool = eligible[:]
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
        if len(chosen) != count:
            raise SystemExit(
                f"Internal error selecting questions: requested {count}, got {len(chosen)}"
            )
        return chosen

    def _select_hard_session(self, *, count: int, user_feedback: Dict[str, str]) -> List[Question]:
        """Hard sessions are 6 questions: 4 two-part + 2 regular Hard questions."""

        hard = [q for q in self.questions if q.difficulty.lower() == "hard"]
        two_part = [q for q in hard if q.type == "hard_two_part"]
        regular = [q for q in hard if q.type != "hard_two_part"]

        if len(two_part) < 4:
            raise SystemExit(
                f"Hard difficulty requires 4 two-part questions; found {len(two_part)}. Fix questions.json."
            )

        random.shuffle(two_part)
        chosen: List[Question] = two_part[: min(4, len(two_part))]

        remaining = max(0, count - len(chosen))
        if remaining == 0:
            return chosen[:count]

        def weight(q: Question) -> float:
            fb = user_feedback.get(q.id)
            if fb == "like":
                return 2.0
            if fb == "dislike":
                return 0.2
            if fb in {"too easy", "too hard"}:
                return 0.5
            return 1.0

        pool = regular[:]
        if len(pool) < remaining:
            raise SystemExit(
                f"Hard difficulty needs {remaining} additional regular questions but only has {len(pool)}. Fix questions.json."
            )

        for _ in range(remaining):
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

        if len(chosen) != count:
            raise SystemExit(
                f"Internal error selecting hard session: requested {count}, got {len(chosen)}"
            )
        return chosen


def _validate_question_bank(questions: List[Question]) -> None:
    """Validate key SPEC invariants with helpful errors."""

    # Count per difficulty for base question types.
    base_types = {"multiple_choice", "true_false", "short_answer"}
    counts: Dict[str, Dict[str, int]] = {}
    two_part_counts: Dict[str, int] = {}
    for q in questions:
        d = q.difficulty
        if q.type == "hard_two_part":
            two_part_counts[d] = two_part_counts.get(d, 0) + 1
            continue
        if q.type not in base_types:
            continue
        counts.setdefault(d, {})[q.type] = counts.setdefault(d, {}).get(q.type, 0) + 1

    problems: List[str] = []

    # Spec: Each difficulty should contain 9 questions, 3 of each type.
    for diff in ["Easy", "Medium", "Hard", "Challenge"]:
        c = counts.get(diff, {})
        for t in ["multiple_choice", "true_false", "short_answer"]:
            if c.get(t, 0) != 3:
                problems.append(
                    f"- Difficulty '{diff}' must have exactly 3 '{t}' questions, found {c.get(t, 0)}"
                )

    # Spec: Hard difficulty has 4 questions with two parts.
    if two_part_counts.get("Hard", 0) != 4:
        problems.append(
            f"- Difficulty 'Hard' must have exactly 4 'hard_two_part' questions, found {two_part_counts.get('Hard', 0)}"
        )

    if problems:
        raise SystemExit(
            "Question bank doesn't meet SPEC invariants. Fix quiz_app/data/questions.json:\n"
            + "\n".join(problems)
        )


def _parse_question(item: Dict[str, Any]) -> Optional[Question]:
    try:
        qtext = str(item["question"])
        qtype = str(item["type"])
        category = str(item.get("category", "General"))
        difficulty = str(item.get("difficulty", "Easy"))

        # Validate early so typos don't silently change behavior.
        if qtype not in {t.value for t in QuestionType}:
            return None

        # Spec example omits an explicit `id`. If it's absent, generate a stable ID
        # from question content so feedback/history can still key off it.
        raw_id = item.get("id")
        if raw_id is None or str(raw_id).strip() == "":
            qid_source = json.dumps(
                {
                    "question": qtext,
                    "type": qtype,
                    "category": category,
                    "difficulty": difficulty,
                    "options": item.get("options"),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            qid = "q_" + hashlib.sha1(qid_source.encode("utf-8")).hexdigest()[:12]
        else:
            qid = str(raw_id)

        if qtype == QuestionType.HARD_TWO_PART.value:
            parts_raw = item.get("parts")
            if not isinstance(parts_raw, list) or len(parts_raw) != 2:
                return None
            parts: List[Question] = []
            for pi, pr in enumerate(parts_raw):
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
                type=QuestionType.HARD_TWO_PART.value,
                answer="",
                category=category,
                difficulty=difficulty,
                parts=parts,
            )

        answer = str(item["answer"])
        options = item.get("options")
        if qtype == QuestionType.MULTIPLE_CHOICE.value:
            if not isinstance(options, list) or len(options) != 4:
                return None
            options = [str(x) for x in options]
        else:
            options = None

        if qtype not in {
            QuestionType.MULTIPLE_CHOICE.value,
            QuestionType.TRUE_FALSE.value,
            QuestionType.SHORT_ANSWER.value,
        }:
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
