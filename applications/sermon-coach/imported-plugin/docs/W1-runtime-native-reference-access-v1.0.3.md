# v1.0.3 Runtime-native reference access fix

State: W1 APPROVED by owner instruction to proceed with the proposed fix.

## Finding
Installed ChatGPT Work loaded the Skills but did not expose bundled Python scripts as callable tools. As a result, the v1.0.2 requirement to call `packaged-reference-access` forced otherwise-available reference-grounded review into LIMITED state.

## Fix
- Normal installed-runtime consultation uses direct Skill-relative packaged resources and host-native file reading.
- Each Skill carries hash-identical mirrors of approved Reference Materials under `assets/references/`.
- `assets/reference-mirrors.json` binds every mirror to the canonical RM ID, source path, and SHA-256.
- Python scripts remain optional offline/package validators and are not required runtime tools.
- No approved WF/IM/UIP, sermon behavior, reference authority, or user-agency rule is changed.
