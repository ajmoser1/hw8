# Code Review vs SPEC.md (March 31, 2026)

Below are findings mapped to the acceptance criteria in `SPEC.md`, plus additional bug/error-handling/security/code-quality notes. Each item is marked **[PASS]**, **[FAIL]**, or **[WARN]** and references the relevant file + line(s).

> Line numbers are based on the current workspace contents.

1. **[PASS] App greets user and describes what it does.**
   - `quiz_app/main.py` lines 24–36: `_print_intro()` prints title + short description.

2. **[PASS] App prompts user to choose a difficulty and validates input.**
   - `quiz_app/main.py` lines 39–53: `_prompt_difficulty()` loops until the user enters an allowed difficulty (case-insensitive).

3. **[PASS] Questions are read from a human-readable JSON question bank file.**
   - `quiz_app/services/questions.py` lines 100–132: `QuestionBank.from_file()` loads `questions.json`.
   - `quiz_app/data/questions.json` is plain JSON and easy to edit.

4. **[PASS] Spec’s example JSON format works (question `id` is optional).**
    - `quiz_app/services/questions.py`: `_parse_question()` generates a stable fallback ID when `id` is missing.
    - Invalid question objects no longer fail silently during load (the app exits with a clear error listing invalid entries).

5. **[PASS] Supports 3 question types (true/false, multiple choice, short answer).**
   - `quiz_app/services/questions.py` lines 45–77 (`Question.ask_and_grade`) and 125–178 (`_grade_single`).

6. **[PASS] Valid response formats are made known to the user.**
   - `quiz_app/main.py` lines 78–88: prints the MC/TF/SA rules before starting.

7. **[PASS] Invalid responses for MC/TF re-prompt and show valid options; short-answer gets one attempt.**
   - Multiple choice: `quiz_app/services/questions.py` lines 141–156 (loop until valid A–D).
   - True/False: `quiz_app/services/questions.py` lines 160–171 (loop until valid true/false).
   - Short answer: `quiz_app/services/questions.py` lines 178–186 (no retry loop).

8. **[PASS] Correct answers print “Correct!” and incorrect answers reveal the answer.**
   - Correct message: `quiz_app/services/questions.py` lines 153, 169, 182.
   - Reveal answer after incorrect: `quiz_app/main.py` lines 101–103 calls `q.answer_display()`.

9. **[PASS] Local login system with create account + login, and passwords are not easily discoverable.**
   - Account flow: `quiz_app/services/auth.py` lines 25–74.
   - Password hashing: `quiz_app/services/auth.py` lines 97–103 uses PBKDF2-HMAC-SHA256 with per-user salt (200k iterations).
   - Constant-time compare: `quiz_app/services/auth.py` lines 117–118 uses `hmac.compare_digest`.

10. **[PASS] Password entry is not echoed (uses `getpass`).**
    - `quiz_app/services/auth.py`: password entry uses `getpass.getpass()` when running interactively.

11. **[PASS] Score history is persisted in a non-human-readable format and can track per-user sessions.**
    - Storage: `quiz_app/services/history.py`.
    - Data is encrypted (Fernet) and stored as opaque bytes; not human-readable at a glance.
    - Tracks per-user `sessions`: `record_session()`.

12. **[PASS] History storage does not rely on a co-located key file.**
    - `quiz_app/services/history.py`: history is encrypted (Fernet) with a key derived at login.
    - No `.key` file is required next to `history.dat`.

13. **[PASS] Spec’s intent met: scores are not recoverable from the history file alone.**
    - `quiz_app/services/history.py`: history is encrypted and not readable without the login-derived key.

14. **[PASS] Users can provide per-question feedback (like/dislike/too hard/too easy).**
    - Prompt + validation: `quiz_app/main.py` lines 113–127.
    - Persistence: `quiz_app/services/feedback.py` lines 21–25.

15. **[PASS] “Too hard/too easy” feedback adjusts difficulty when possible.**
    - `quiz_app/main.py`: after feedback is recorded, the next question’s difficulty shifts down/up when possible.

16. **[PASS] Exactly 6 questions per session.**
    - `quiz_app/main.py` line 65 sets `total_questions = 6`.

17. **[PASS] Question bank invariants are validated on load (9 per difficulty; 3 per type).**
    - `quiz_app/services/questions.py`: `QuestionBank.from_file()` validates that each difficulty contains exactly 3 MC, 3 TF, and 3 SA questions.

18. **[PASS] Challenge mode difficulty is gated behind a perfect hard score (6/6).**
    - Unlock check: `quiz_app/main.py` lines 156–159.
    - Availability: `quiz_app/main.py` lines 142–147 reads unlocked difficulties and only adds `Challenge` to the menu when unlocked.

19. **[PASS] Hard difficulty enforces inclusion of the 4 two-part questions.**
    - `quiz_app/services/questions.py`: Hard sessions are selected as 4 two-part questions plus 2 additional Hard questions (still 6 questions total per session).

20. **[PASS] Invalid question objects are not silently dropped.**
    - `quiz_app/services/questions.py`: invalid question objects cause a clear error during load listing which entries are invalid.

21. **[PASS] Question selection guarantees exactly 6 questions per session (or fails fast).**
    - `quiz_app/services/questions.py`: selection raises an error if the bank doesn’t contain enough eligible questions.

22. **[PASS] Multiple-choice grading is robust to whitespace/casing.**
    - `quiz_app/services/questions.py`: multiple-choice answers are normalized before comparison.

23. **[PASS] True/False answers are normalized (t/true => true, f/false => false).**
    - `quiz_app/services/questions.py` lines 160–170.

24. **[PASS] Corrupted `users.json` is handled robustly with a warning.**
    - `quiz_app/services/auth.py`: corrupted/invalid `users.json` results in an empty user set with a warning printed to stderr.

25. **[PASS] Feedback persistence is safer and less trivially readable.**
    - `quiz_app/services/feedback.py`: feedback is stored as an encoded payload and written atomically.

26. **[PASS] File writes are atomic for user/feedback/history stores.**
    - `quiz_app/services/auth.py`, `quiz_app/services/feedback.py`, `quiz_app/services/history.py`: writes use temp files + replace.

27. **[PASS] Basic “CTRL-D / EOF” handling while answering questions exits cleanly.**
    - `quiz_app/services/questions.py` lines 135–140 catches `EOFError` and exits.

28. **[PASS] Code quality: unused imports cleaned up.**
    - `quiz_app/main.py`: removed unused imports.

29. **[PASS] Question type values are validated (Enum-backed).**
    - `quiz_app/services/questions.py`: question type strings are validated against a `QuestionType` Enum during parsing.

30. **[PASS] No obvious path traversal or unsafe file path handling.**
    - All file paths are built from `__file__` directory (`quiz_app/main.py` lines 131–138) and not from user input.

