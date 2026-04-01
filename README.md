# hw8 – CLI Quiz App

A command-line Python quiz app with a local login system, question bank in JSON, score history stored in a non-human-readable format, and feedback that influences future question selection.

## Requirements
- Python 3.10+ recommended (works on 3.8+).

## Run
```bash
python3 -m quiz_app
```

## Files
- `quiz_app/` – application package
- `quiz_app/data/questions.json` – human-readable question bank
- `quiz_app/data/users.json` – user database (salted password hashes)
- `quiz_app/data/history.dat` – score history + stats (base64-encoded, obfuscated JSON)
- `quiz_app/data/feedback.json` – per-user question feedback

## Notes on “secure/non-human-readable” storage
This project:
- stores passwords as salted PBKDF2-HMAC hashes (not reversible)
- stores score history in an obfuscated, base64-encoded blob to make it non-human-readable

This is **not** cryptographic encryption, but it matches the spec’s stated goal: someone inspecting files shouldn’t easily see passwords or scores.

## Acceptance criteria (review checklist)

- [ ] **App starts cleanly**: Running `python3 -m quiz_app` shows the intro text, then prompts for login (no stack traces on startup).
- [ ] **Login system works**: A reviewer can create a new account and then log in with it on a subsequent run; `quiz_app/data/users.json` contains salted password hashes (no plaintext passwords).
- [ ] **Question bank meets spec**: `quiz_app/data/questions.json` is human-readable, contains the sample questions from `SPEC.md`, and each difficulty has **exactly 9 questions (3 multiple choice, 3 true/false, 3 short answer)**.
- [ ] **Session rules match spec**: After choosing difficulty, the user gets **exactly 6 questions** and sees the valid response formats before the quiz starts.
- [ ] **Validation + messaging are correct**:
	- Multiple choice + true/false: invalid input prints the valid responses for that type and re-prompts.
	- Short answer: one attempt only (no invalid-response list behavior).
	- Correct answers print `Correct!`; incorrect answers reveal the correct answer before moving on.
- [ ] **Non-human-readable score history**: After a session completes, `quiz_app/data/history.dat` is updated and is not plainly readable while still tracking per-user sessions and unlocked difficulties.
- [ ] **Feedback affects selection**: After each question the app accepts `like`, `dislike`, `too hard`, or `too easy` (or skip) and persists to `quiz_app/data/feedback.json`; repeated sessions show a noticeable bias toward liked questions and away from disliked ones.
- [ ] **Challenge unlock behavior**: “Challenge” difficulty doesn’t appear until the user scores **6/6 on Hard**, after which it appears on the next run.
