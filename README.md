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
