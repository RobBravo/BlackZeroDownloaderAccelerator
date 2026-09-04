# Task 2 Fix Round 1 Report

## Scope

Corrected the two review findings from Task 2 in the isolated worktree:

- `finalize_part` now defaults to non-overwriting publication and preserves an existing destination by raising a clear `FileExistsError`. Passing `overwrite=True` is the explicit authorization required to replace a destination.
- RFC 5987 `filename*` values now parse the `charset'language'encoded-payload` form, decode percent-encoded bytes using the declared charset, and safely fall back to URL-derived naming when the value is malformed or undecodable.

## TDD evidence

Added regression tests before the production correction. The focused suite initially failed with four expected failures: language-tagged `filename*`, invalid RFC 5987 fallback, rejection of an existing destination, and the new explicit overwrite argument.

## Validation

- Focused: `python -m pytest tests/test_files.py -q` — 15 passed.
- Full: `python -m pytest -q` — 19 passed.

The Windows `python.exe` app alias was unavailable to the shell, so validation used the installed Python 3.12 interpreter at `C:\Users\ingmo\AppData\Local\Programs\Python\Python312\python.exe`.

## Files changed

- `blackzero/files.py`
- `tests/test_files.py`

## Remaining concerns

- The downloader call site will need to pass its overwrite decision explicitly in a later task, as planned.
- The existing plan document still shows the old `finalize_part` signature; it was intentionally left unchanged because this round is restricted to the two code/test files plus this report.
