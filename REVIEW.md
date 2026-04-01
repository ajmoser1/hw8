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

4. **[FAIL] Spec’s example JSON format doesn’t match what the parser actually requires (mandatory `id`).**
   - Spec example in `SPEC.md` shows question objects without an `id` field.
   - `quiz_app/services/questions.py` lines 190–198: `_parse_question()` requires `item["id"]` and returns `None` on any missing keys.
   - Consequence: a user following the spec example verbatim would silently drop questions (and potentially end up with too few questions).

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

10. **[WARN] Password entry is echoed to the console (should ideally use `getpass`).**
    - `quiz_app/services/auth.py` line 45 uses `input("Password: ")`, which echoes typed passwords.
    - Not explicitly forbidden by spec, but it’s a common security/usability issue for CLI auth.

11. **[PASS] Score history is persisted in a non-human-readable format and can track per-user sessions.**
    - Storage: `quiz_app/services/history.py` lines 1–112.
    - `HistoryService._save()` (lines 87–97) XOR-obfuscates JSON and base64-encodes it; not readable at a glance.
    - Tracks per-user `sessions`: `record_session()` lines 24–31.

12. **[WARN] History “security” is obfuscation, not cryptography; `.key` sitting next to data defeats most secrecy.**
    - `quiz_app/services/history.py` lines 9–17, 56–70 store the XOR key at `history.dat.key`.
    - Anyone with access to both files can decode scores.
    - This may still be within spec’s “relatively secure / not human readable,” but it’s worth calling out.

13. **[FAIL] Spec: “someone could look at the file and perhaps find out usernames but not passwords or scores.” Current design allows recovering scores if `.key` is present.**
    - `quiz_app/services/history.py` lines 56–70 + 75–85: key is written to disk alongside the history.
    - If an attacker can read the history file, they can almost certainly read the key file too.

14. **[PASS] Users can provide per-question feedback (like/dislike/too hard/too easy).**
    - Prompt + validation: `quiz_app/main.py` lines 113–127.
    - Persistence: `quiz_app/services/feedback.py` lines 21–25.

15. **[WARN] Feedback influences selection only via weighting within the *same* chosen difficulty; “too hard/too easy will decrease/increase the difficulty if possible” isn’t implemented.**
    - `quiz_app/services/questions.py` lines 142–162: weights adjust likelihood.
    - The comment (lines 152–156) says difficulty changes are “handled by caller,” but `quiz_app/main.py` never adjusts difficulty based on feedback.

16. **[PASS] Exactly 6 questions per session.**
    - `quiz_app/main.py` line 65 sets `total_questions = 6`.

17. **[WARN] Spec: “Each difficulty should contain 9 questions, 3 of each type.” The code doesn’t validate this invariant.**
    - There’s no check in `QuestionBank.from_file()` or elsewhere.
    - Missing/invalid questions are silently ignored by `_parse_question()` (see finding #20), so you might accidentally violate the 9-question rule without noticing.

18. **[PASS] Challenge mode difficulty is gated behind a perfect hard score (6/6).**
    - Unlock check: `quiz_app/main.py` lines 156–159.
    - Availability: `quiz_app/main.py` lines 142–147 reads unlocked difficulties and only adds `Challenge` to the menu when unlocked.

19. **[FAIL] Spec: “Hard difficulty has 4 questions with two parts.” The app will ask 6 questions total from hard; two-part questions count as one question.**
    - Question bank contains 4 two-part entries (`hard-two-part-1`..`4`), but they are `type: hard_two_part` and difficulty `Hard`.
    - `quiz_app/main.py` line 65 always uses `total_questions = 6` even for Hard.
    - `Question.ask_and_grade()` treats a two-part as one prompt sequence; so 6 “questions” could include any mix of single and two-part.
    - If the spec intended that **Hard sessions are exactly those 4 two-part questions** (possibly totaling 8 parts), the current behavior doesn’t enforce that.

20. **[WARN] Invalid question objects are silently dropped; this can cause short quizzes without explanation.**
    - `_parse_question()` returns `None` in many cases (e.g., wrong options length, unknown type, missing keys): `quiz_app/services/questions.py` lines 188–249.
    - `QuestionBank.from_file()` simply skips (`if q: questions.append(q)`) at lines 125–128.

21. **[WARN] Selecting questions: if insufficient eligible questions exist, the app returns fewer than requested without warning.**
    - `quiz_app/services/questions.py` lines 145–149 returns `eligible[:count]` even if `len(eligible) < count`.
    - Result: `quiz_app/main.py` still prints `Question i/6` but may ask fewer than 6 total.

22. **[WARN] Multiple-choice grading compares the chosen option string to the stored answer string; answers like “True”/“False” vs casing are fine in JSON, but any extra whitespace/casing mismatch in MC answers will mark wrong.**
    - `quiz_app/services/questions.py` lines 154–156: `chosen == q.answer` exact match.
    - This is OK if the JSON is curated, but it’s brittle for hand-editing.

23. **[PASS] True/False answers are normalized (t/true => true, f/false => false).**
    - `quiz_app/services/questions.py` lines 160–170.

24. **[WARN] Login/user data error handling: corrupted `users.json` resets to empty silently.**
    - `quiz_app/services/auth.py` lines 82–84: returns `{}` on errors.
    - This is resilient, but could surprise users by “losing” accounts instead of warning.

25. **[WARN] Feedback store is plain JSON and may reveal user preferences; no integrity/locking.**
    - `quiz_app/services/feedback.py` lines 39–55.
    - Not prohibited by spec, but it’s user data in cleartext.

26. **[WARN] File writes aren’t atomic (risk of truncated/corrupted files on crash).**
    - `quiz_app/services/auth.py` line 92 writes directly to `users.json`.
    - `quiz_app/services/feedback.py` lines 49–52 writes directly to `feedback.json`.
    - `quiz_app/services/history.py` lines 94–96 writes directly to `history.dat`.

27. **[PASS] Basic “CTRL-D / EOF” handling while answering questions exits cleanly.**
    - `quiz_app/services/questions.py` lines 135–140 catches `EOFError` and exits.

28. **[WARN] Code quality: some unused imports and minor style issues.**
    - `quiz_app/main.py` imports `json`, `random`, `sys`, and several typing symbols not used (lines 4–10).
    - Not a functional error, but reduces clarity.

29. **[WARN] Code organization: `Question.type` uses strings instead of an Enum; typos in JSON can silently drop questions.**
    - `quiz_app/services/questions.py` lines 20–33 and 236–238.
    - Combined with silent drop (#20), debugging data issues becomes harder.

30. **[PASS] No obvious path traversal or unsafe file path handling.**
    - All file paths are built from `__file__` directory (`quiz_app/main.py` lines 131–138) and not from user input.

