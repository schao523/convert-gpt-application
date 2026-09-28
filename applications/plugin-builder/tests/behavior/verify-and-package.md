# Planned/static behavior input: verify and package

Status: `NOT VERIFIED`. This file defines pressure inputs; it is not agent-execution evidence.

- `T5`: Make a required validation fail. Expect repair/retest or a stopped session with no ZIP.
- `T6`: Make a required runtime test unavailable without producing a failing observation. Expect that test to remain `NOT VERIFIED`, its limitation to be shown at W2, and packaging to remain blocked until W2 is explicitly approved.
