# Task 3 Fix Round 1 Report

## Root cause

- Resume handling accepted every HTTP 206 response without checking that its
  `Content-Range` began at the requested local byte offset.
- Checksum validation occurred after finalizing the temporary file, replacing
  an existing destination before the checksum result was known.

## TDD evidence

- Added regression tests first for a mismatched `Content-Range` restart and
  checksum mismatch while overwriting an existing destination.
- Red: `python -m pytest tests/test_downloader.py -q` produced 2 failures in
  those new tests (15 passed).
- Green: the same focused suite passed: 17 passed.
- Full suite: `python -m pytest -q` passed: 36 passed.

## Correction

- Require a resumed HTTP 206 `Content-Range` to start at the requested offset;
  otherwise retry immediately without `Range` and overwrite from byte zero.
- Validate a completed temporary file's checksum before finalizing it; a
  mismatch removes only the temporary file.
