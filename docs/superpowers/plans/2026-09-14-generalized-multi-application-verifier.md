# Generalized Multi-Application Verifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Cool Bible Tutor-specific extraction verifier with a generic, schema-driven, multi-application verifier, preserve Cool Bible Tutor evidence as application-owned tests, and publish the verified development repository at `schao523/convert-gpt-application`.

**Architecture:** Add typed verification-profile parsing and safe expansion primitives to `obvious_one_plugin_framework`, while keeping `scripts/verify_extraction.py` as the top-level orchestration and compatibility CLI. Product commands and assertions remain in each application workspace; the runner owns shared gates, deterministic builds, result states, logs, reports, and optional read-only marketplace comparison.

**Tech Stack:** Python 3.11+, standard-library `argparse`, `dataclasses`, `json`, `pathlib`, `subprocess`, `tempfile`, `unittest`; existing `obvious_one_plugin_framework`; Git and GitHub CLI for the final publication step.

**Spec:** `docs/superpowers/specs/2026-09-13-generalized-multi-application-verifier-design.md`

## Global Constraints

- Follow the root `AGENTS.md`; target Codex and OpenClaw by default.
- Use test-driven development: write one focused failing test, observe the expected failure, implement the minimum behavior, and rerun it.
- Keep all Bible-specific values, commands, environment prefixes, and assertions below `applications/cool-bible-tutor` or in that application's `conversion.json`.
- Execute profile commands as argument arrays with `shell=False`.
- Do not download dependencies or models, run RAG setup, mutate the marketplace, publish plugin releases, create tags, submit to ClawHub, or force-push.
- Keep diagnostics below ignored `.tmp/verification/`; never commit generated artifacts or absolute developer paths.
- Commit after each completed task. Do not amend unrelated user changes.

---

## Task 1: Add the schema-v2 verification profile model

**Files:**

- Create: `src/obvious_one_plugin_framework/verification.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_verification_config.py`

- [ ] **Step 1: Write failing tests for valid schema-v2 parsing**

Create helpers that build a minimal application under a temporary repository and assert this public interface:

```python
from obvious_one_plugin_framework.verification import load_application_config

config = load_application_config(application_root, repository_root)
self.assertEqual(config.application_id, "plugin-alpha")
self.assertEqual(config.plugin_id, "plugin-alpha")
self.assertEqual(config.verification.commands[0].command_id, "smoke")
self.assertEqual(config.verification.codex_build.artifact_path, "plugins/plugin-alpha")
self.assertIsNone(config.verification.marketplace)
```

The fixture must contain a valid `openclaw/distribution.json` whose version is `1.2.3`, so the test also asserts `config.version == "1.2.3"`.

- [ ] **Step 2: Write failing validation tests**

Cover each error independently:

- schema version 1 returns a migration-oriented `VerificationConfigError`;
- missing `verification`;
- wrong scalar/list/object types;
- empty `argv` or an empty argument;
- duplicate command IDs;
- unknown placeholders;
- application-directory/name, `application_id`, and `plugin_id` disagreement;
- missing or invalid distribution contract;
- absolute profile paths and repository escapes;
- duplicate identity discovered across application directories.

Errors must include the configuration path and the failing field name. Do not assert incidental punctuation.

- [ ] **Step 3: Run the focused tests and observe failure**

Run:

```powershell
python -B -m unittest tests.framework.test_verification_config -v
```

Expected: `ImportError` or missing `verification` module failures.

- [ ] **Step 4: Implement immutable configuration types and loading**

In `verification.py`, implement these public types and functions:

```python
RESULT_STATES = frozenset({"PASS", "FAIL", "NOT VERIFIED", "NOT APPLICABLE"})
ALLOWED_PLACEHOLDERS = frozenset({
    "python", "repository_root", "application_root", "diagnostics",
    "plugin_id", "application_id", "version",
})

class VerificationConfigError(ValueError):
    pass

@dataclass(frozen=True)
class VerificationCommand:
    command_id: str
    argv: tuple[str, ...]
    clean_environment_prefixes: tuple[str, ...] = ()

@dataclass(frozen=True)
class CodexBuildProfile:
    argv: tuple[str, ...]
    artifact_path: str

@dataclass(frozen=True)
class MarketplaceProfile:
    codex_path: str
    openclaw_path: str
    approved_delta: Path

@dataclass(frozen=True)
class ApplicationVerificationProfile:
    test_directory: Path
    commands: tuple[VerificationCommand, ...]
    codex_build: CodexBuildProfile
    marketplace: MarketplaceProfile | None

@dataclass(frozen=True)
class ApplicationConfig:
    root: Path
    application_id: str
    plugin_id: str
    version: str
    source_inventory: Path
    source_location: Path
    coverage_matrix: Path
    distribution_contract: Path
    marketplace_repository: str
    verification: ApplicationVerificationProfile

def load_application_config(application_root: Path, repository_root: Path) -> ApplicationConfig: ...
def discover_applications(repository_root: Path) -> tuple[ApplicationConfig, ...]: ...
```

Use `string.Formatter().parse()` to validate placeholders. Resolve file fields relative to the application root, then use `Path.is_relative_to(repository_root.resolve())` to reject escapes. Do not require generated artifacts to exist during configuration loading.

- [ ] **Step 5: Export the stable verification API**

Export the types and functions from `src/obvious_one_plugin_framework/__init__.py` without removing existing exports.

- [ ] **Step 6: Rerun focused and framework tests**

Run:

```powershell
python -B -m unittest tests.framework.test_verification_config -v
python -B -m unittest discover -s tests/framework -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add src/obvious_one_plugin_framework/verification.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_verification_config.py
git commit -m "feat: validate application verification profiles"
```

---

## Task 2: Add safe selection, placeholder expansion, and result primitives

**Files:**

- Modify: `src/obvious_one_plugin_framework/verification.py`
- Create: `tests/framework/test_verification_runtime.py`

- [ ] **Step 1: Write failing selection and expansion tests**

Assert the following API:

```python
selected = select_applications(configs, application_id="plugin-alpha", select_all=False)
self.assertEqual([item.application_id for item in selected], ["plugin-alpha"])

argv = expand_argv(
    ("{python}", "-B", "{application_root}/scripts/smoke.py", "{version}"),
    expansion_context,
)
self.assertEqual(argv[0], sys.executable)
self.assertEqual(argv[-1], "1.2.3")
```

Cover default-all, explicit-all, unknown selection, mutually exclusive selection, unknown/partial placeholders, and arguments that become empty. Expansion must return a list suitable for `subprocess.run(..., shell=False)` and must not invoke a shell.

- [ ] **Step 2: Write failing safe-path and aggregation tests**

Add tests for:

- an application path inside the repository;
- an approved-delta path using `..` that still resolves inside the repository;
- rejection of paths outside the repository;
- artifact paths that must stay inside their diagnostics root;
- marketplace paths that must stay inside a supplied marketplace root;
- overall `FAIL` when any required gate fails;
- overall `PASS` when required gates pass and marketplace is `NOT VERIFIED` or `NOT APPLICABLE`.

- [ ] **Step 3: Run focused tests and observe failure**

```powershell
python -B -m unittest tests.framework.test_verification_runtime -v
```

Expected: missing functions/types.

- [ ] **Step 4: Implement the runtime primitives**

Add:

```python
@dataclass(frozen=True)
class ExpansionContext:
    python: str
    repository_root: Path
    application_root: Path
    diagnostics: Path
    plugin_id: str
    application_id: str
    version: str

@dataclass(frozen=True)
class GateResult:
    gate_id: str
    state: str
    detail: str
    log_path: str | None = None
    data: Mapping[str, object] = field(default_factory=dict)

def select_applications(
    configs: Sequence[ApplicationConfig],
    *,
    application_id: str | None,
    select_all: bool,
) -> tuple[ApplicationConfig, ...]: ...

def expand_argv(argv: Sequence[str], context: ExpansionContext) -> list[str]: ...
def resolve_within(base: Path, value: str | Path, *, field: str) -> Path: ...
def aggregate_state(gates: Iterable[GateResult]) -> str: ...
```

Normalize report paths to repository-relative POSIX strings whenever possible. Validate states against `RESULT_STATES` in `GateResult.__post_init__`.

- [ ] **Step 5: Rerun focused and framework tests**

```powershell
python -B -m unittest tests.framework.test_verification_runtime -v
python -B -m unittest discover -s tests/framework -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/obvious_one_plugin_framework/verification.py tests/framework/test_verification_runtime.py
git commit -m "feat: add reusable verification runtime primitives"
```

---

## Task 3: Move Cool Bible Tutor verification ownership into its application

**Files:**

- Modify: `applications/cool-bible-tutor/conversion.json`
- Create: `applications/cool-bible-tutor/tests/test_verification_profile.py`
- Modify: `tests/test_application_config.py`

- [ ] **Step 1: Write failing schema-v2 application tests**

Update `tests/test_application_config.py` to require schema version 2 and validate the profile through `load_application_config()`. Assert stable command IDs, not the generic verifier's implementation details.

Create `test_verification_profile.py` to prove application-owned invariants:

- exact retrieval of `約 3:16` succeeds from the bundled database and includes `神愛世人`;
- runtime status reports the intended bundled corpus as production ready;
- distribution audit succeeds;
- the Codex builder accepts the distribution-contract version;
- the application test never imports `scripts.verify_extraction`.

- [ ] **Step 2: Run the focused tests and observe migration failure**

```powershell
python -B -m unittest tests.test_application_config -v
python -B -m unittest discover -s applications/cool-bible-tutor/tests -p test_verification_profile.py -v
```

Expected: schema-v1/missing-profile failures.

- [ ] **Step 3: Upgrade `conversion.json` to schema version 2**

Declare these application-owned command IDs:

```json
[
  "distribution-audit",
  "exact-passage",
  "runtime-status"
]
```

Use the approved profile structure:

- `test_directory`: `tests`;
- audit command: `scripts/distribution_audit.py` with the application root;
- exact-passage command: `scripts/cool_bible_tutor.py passage "約 3:16" --format json`;
- runtime-status command: `scripts/cool_bible_tutor.py status --json`;
- remove `COOL_BIBLE_TUTOR_` variables for both bundled-runtime commands;
- Codex builder: `scripts/build_marketplace_release.py`, diagnostics destination, and `{version}`;
- Codex artifact: `plugins/{plugin_id}`;
- marketplace Codex/OpenClaw paths and `../../docs/provenance/marketplace-approved-delta.json`.

Do not move Bible-specific strings or environment prefixes into generic Python modules.

- [ ] **Step 4: Make product regression assertions self-contained**

Use `subprocess.run(..., shell=False, capture_output=True, text=True, check=False)` from the product test, parse JSON, and assert structured fields. Clear only the declared product environment prefixes in the copied environment. Do not call setup or download commands.

- [ ] **Step 5: Run product and configuration tests**

```powershell
python -B -m unittest tests.test_application_config -v
python -B -m unittest discover -s applications/cool-bible-tutor/tests -v
```

Expected: all application tests pass; existing skips remain explained.

- [ ] **Step 6: Commit**

```powershell
git add applications/cool-bible-tutor/conversion.json applications/cool-bible-tutor/tests/test_verification_profile.py tests/test_application_config.py
git commit -m "test: declare Cool Bible Tutor verification profile"
```

---

## Task 4: Refactor the top-level verifier into a generic orchestrator

**Files:**

- Modify: `scripts/verify_extraction.py`
- Create: `tests/fixtures/verification/plugin-alpha/conversion.json`
- Create: `tests/fixtures/verification/plugin-alpha/openclaw/distribution.json`
- Create: `tests/fixtures/verification/plugin-alpha/scripts/product_check.py`
- Create: `tests/fixtures/verification/plugin-beta/conversion.json`
- Create: `tests/fixtures/verification/plugin-beta/openclaw/distribution.json`
- Create: `tests/fixtures/verification/plugin-beta/scripts/product_check.py`
- Create: `tests/test_verify_extraction.py`
- Modify: `tests/test_distribution_equivalence.py`

- [ ] **Step 1: Preserve tree-comparison behavior with a focused test**

Keep `compare_trees(left, right)` import-compatible while moving any reusable implementation into the framework module. Test added, removed, changed, and ignored paths, with stable sorted output.

- [ ] **Step 2: Write failing synthetic multi-application tests**

Build temporary repositories from the `plugin-alpha` and `plugin-beta` fixtures. Inject a command runner or patch only the subprocess boundary. Prove:

- shared gates run once;
- application gates run in sorted application-ID order;
- alpha failure does not prevent beta execution;
- a failed build marks only dependent alpha gates `NOT VERIFIED`;
- the final report includes both applications and overall `FAIL`;
- diagnostics are below `.tmp/verification/run-<identifier>`;
- report paths contain no developer-specific absolute path.

- [ ] **Step 3: Write failing CLI compatibility tests**

Call `main(argv)` and cover:

- neither selector means all;
- `--all` means all;
- `--application plugin-alpha` selects one;
- `--all` plus `--application` is rejected by `argparse`;
- unknown application returns nonzero with a useful message;
- legacy `--marketplace PATH --provenance PATH` is accepted for the single real application;
- `--provenance` with multiple selected applications returns nonzero before product commands;
- JSON report state and process exit code agree.

- [ ] **Step 4: Run focused tests and observe failures**

```powershell
python -B -m unittest tests.test_distribution_equivalence tests.test_verify_extraction -v
```

Expected: discovery/CLI/report tests fail against the hard-coded verifier.

- [ ] **Step 5: Implement the generic orchestration seam**

Retain a small `main(argv: Sequence[str] | None = None) -> int`. Add focused functions with these responsibilities:

```python
def build_parser() -> argparse.ArgumentParser: ...
def run_shared_gates(context: RunContext) -> list[GateResult]: ...
def run_application(config: ApplicationConfig, context: RunContext) -> ApplicationResult: ...
def write_report(context: RunContext, shared: Sequence[GateResult], applications: Sequence[ApplicationResult]) -> Path: ...
def verify(*, repository_root: Path, application_id: str | None = None,
           select_all: bool = True, marketplace: Path | None = None,
           provenance_override: Path | None = None) -> VerificationReport: ...
```

Create each run directory with a collision-resistant UTC timestamp plus process ID or UUID. Capture each subprocess's stdout/stderr in a per-gate UTF-8 log. Emit concise console progress, but treat `report.json` as the stable machine-readable result.

- [ ] **Step 6: Remove every product constant from the generic runner**

Verify there are no references in `scripts/verify_extraction.py` to:

```text
cool-bible-tutor
COOL_BIBLE_TUTOR_
約 3:16
神愛世人
31008
71
2.4.6
cool_bible_tutor.py
```

All such behavior must be supplied by application configuration or application tests.

- [ ] **Step 7: Rerun focused tests**

```powershell
python -B -m unittest tests.test_distribution_equivalence tests.test_verify_extraction -v
```

Expected: all pass.

- [ ] **Step 8: Commit**

```powershell
git add scripts/verify_extraction.py tests/test_distribution_equivalence.py tests/test_verify_extraction.py tests/fixtures/verification
git commit -m "feat: generalize multi-application verification"
```

---

## Task 5: Integrate deterministic Codex, OpenClaw, and marketplace gates

**Files:**

- Modify: `scripts/verify_extraction.py`
- Modify: `tests/test_verify_extraction.py`
- Create: `tests/framework/test_verification_report.py`

- [ ] **Step 1: Write failing report-state tests**

Assert that reports use only `PASS`, `FAIL`, `NOT VERIFIED`, and `NOT APPLICABLE`, and contain:

- overall state;
- shared gates;
- application gates;
- artifact paths and content identities;
- diagnostics paths;
- marketplace commit and differences when evaluated.

Prove that no marketplace profile produces `NOT APPLICABLE`, while a configured profile without `--marketplace` produces `NOT VERIFIED` and still permits a zero exit code if all required gates pass.

- [ ] **Step 2: Write failing deterministic-build tests**

For a synthetic application, prove the runner:

1. executes the configured Codex build once;
2. invokes `python -B -m obvious_one_plugin_framework build-package` twice into independent diagnostics directories;
3. invokes `python -B -m obvious_one_plugin_framework verify` for the OpenClaw artifact;
4. compares both OpenClaw trees byte-for-byte;
5. records stable content identities;
6. marks verify/determinism/marketplace gates `NOT VERIFIED` when their prerequisite build fails.

- [ ] **Step 3: Write failing marketplace tests**

Use a temporary clean Git repository as the marketplace and assert:

- a dirty marketplace is rejected without writes;
- configured Codex and OpenClaw paths resolve inside the marketplace;
- exact matches pass;
- unapproved differences fail with sorted path details;
- approved deltas pass only when the actual differences exactly match the delta document;
- the report records the marketplace commit;
- the verifier never calls `git add`, `commit`, `push`, or any network command.

- [ ] **Step 4: Implement build and marketplace gates**

Reuse the existing `obvious_one_plugin_framework` CLI rather than importing product builders. Expand commands through `ExpansionContext`, run them with the repository root as working directory and `shell=False`, and compare resulting trees with stable SHA-256 file identities.

Require a clean supplied marketplace via read-only Git commands. Keep the existing `--provenance` override behavior for one selected application. Validate the override path remains inside the repository.

- [ ] **Step 5: Run focused tests**

```powershell
python -B -m unittest tests.framework.test_verification_report tests.test_verify_extraction -v
```

Expected: all pass.

- [ ] **Step 6: Run all generic tests**

```powershell
python -B -m unittest discover -s tests -v
```

Expected: all pass.

- [ ] **Step 7: Commit**

```powershell
git add scripts/verify_extraction.py tests/test_verify_extraction.py tests/framework/test_verification_report.py
git commit -m "feat: verify deterministic portable distributions"
```

---

## Task 6: Document the reusable workflow and readiness semantics

**Files:**

- Modify: `README.md`
- Modify: `docs/framework-command-reference.md`
- Modify only if necessary: `AGENTS.md`
- Create: `tests/test_documentation_contract.py`

- [ ] **Step 1: Write failing documentation-contract tests**

Require the README and command reference to contain:

- `--all`;
- `--application`;
- `--marketplace`;
- `schema_version` 2;
- `NOT VERIFIED` and `NOT APPLICABLE`;
- explicit wording that local success without a configured marketplace comparison is not release-readiness evidence;
- the default Codex-and-OpenClaw portability rule.

- [ ] **Step 2: Run the focused test and observe failure**

```powershell
python -B -m unittest tests.test_documentation_contract -v
```

Expected: missing documentation assertions.

- [ ] **Step 3: Update README and command reference**

Document PowerShell examples for default-all, selected application, all with marketplace, and the legacy invocation. Explain discovery from `applications/*/conversion.json`, schema-v2 profile fields, diagnostics location, result states, and the difference between local verification and release readiness.

Do not document generated absolute paths. Update `AGENTS.md` only if the implementation adds a stable command or boundary not already governed there.

- [ ] **Step 4: Run documentation and policy tests**

```powershell
python -B -m unittest tests.test_documentation_contract tests.test_agents_contract tests.test_extraction_boundary -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/framework-command-reference.md tests/test_documentation_contract.py
git add AGENTS.md
git commit -m "docs: explain multi-application verification"
```

If `AGENTS.md` is unchanged, omit it from `git add`.

---

## Task 7: Run complete local verification and review the implementation

**Files:**

- Review: all files changed in Tasks 1-6
- Generated and ignored: `.tmp/verification/`

- [ ] **Step 1: Run formatting and placeholder scans**

```powershell
git diff --check
rg -n "TODO|FIXME|PLACEHOLDER|NotImplementedError" src scripts tests applications/cool-bible-tutor README.md docs/framework-command-reference.md
rg -n "cool-bible-tutor|COOL_BIBLE_TUTOR_|約 3:16|神愛世人|31008|2\.4\.6|cool_bible_tutor\.py" scripts/verify_extraction.py src/obvious_one_plugin_framework
```

Expected: `git diff --check` succeeds; placeholder scan has no implementation placeholders; product-term scan has no matches.

- [ ] **Step 2: Run every generic and application test**

```powershell
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s applications/cool-bible-tutor/tests -v
```

Expected: all required tests pass, with only documented optional skips.

- [ ] **Step 3: Run the complete verifier against the local marketplace**

```powershell
python -B .\scripts\verify_extraction.py --all --marketplace D:\GitHub\obvious-one-plugins
```

Expected: exit code 0; shared and application gates pass; marketplace comparisons pass or match only the approved delta; the report identifies both Codex and deterministic OpenClaw artifacts.

- [ ] **Step 4: Inspect the generated report and unchanged repositories**

Read the latest `.tmp/verification/run-*/report.json`. Confirm the report uses the four approved states, contains no private absolute paths, and records marketplace evidence. Then run:

```powershell
git status --short
git -C D:\GitHub\obvious-one-plugins status --short
```

Expected: the marketplace remains clean; only intended implementation files are pending locally.

- [ ] **Step 5: Review against every acceptance criterion**

Check the approved spec section by section. Pay special attention to failure isolation, dependency-derived `NOT VERIFIED`, legacy compatibility, no shell execution, and application ownership of all Bible assertions.

- [ ] **Step 6: Commit any evidence-driven corrections, then verify again**

Use a narrowly scoped commit message for any corrections. Rerun the focused test that exposed each issue and then repeat Steps 1-4. Do not create a catch-all commit if no correction is needed.

---

## Task 8: Publish the verified development repository to GitHub

**Files:**

- No source changes expected
- Remote repository to create: `https://github.com/schao523/convert-gpt-application`

- [ ] **Step 1: Confirm the verified local state**

```powershell
git branch --show-current
git status --short
git log -1 --format=%H
```

Expected: branch `main`, clean worktree, and a recorded local commit ID.

- [ ] **Step 2: Run the public-boundary and licensing checks**

```powershell
python -B -m unittest tests.test_extraction_boundary tests.test_agents_contract -v
git ls-files
rg -n "conversion\.local\.json|review history|CLAWHUB_TOKEN|ghp_|github_pat_|sk-" --glob "!docs/superpowers/**" .
```

Inspect any matches rather than blindly deleting them. Confirm `LICENSE` is MIT and application third-party notices cover bundled public-domain assets. Confirm no undeclared source/reference files or private RAG data are tracked.

- [ ] **Step 3: Confirm GitHub authentication and repository absence**

```powershell
gh auth status
gh repo view schao523/convert-gpt-application
```

Expected: authentication succeeds; repository lookup reports not found. If the repository already exists, stop and inspect ownership, visibility, default branch, and remote state before taking any action.

- [ ] **Step 4: Create the public repository and push `main`**

Only after Steps 1-3 pass, run:

```powershell
gh repo create schao523/convert-gpt-application --public --source . --remote origin --push
```

Do not force-push and do not create tags or releases.

- [ ] **Step 5: Verify the public remote exactly matches local**

```powershell
git remote -v
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
gh repo view schao523/convert-gpt-application --json url,visibility,defaultBranchRef
```

Expected: local `HEAD` equals `origin/main`; visibility is `PUBLIC`; default branch is `main`; URL is `https://github.com/schao523/convert-gpt-application`.

- [ ] **Step 6: Confirm excluded publication surfaces remain unchanged**

```powershell
git -C D:\GitHub\obvious-one-plugins status --short
git tag --list
```

Expected: the marketplace is clean; no tag or release was added. Do not invoke ClawHub or change the pending maintainer issue.

- [ ] **Step 7: Record the handoff evidence**

Report the public URL, matching local/remote commit ID, verifier report path, test totals, and any documented skips. State explicitly that this published only the conversion-framework repository and did not publish a plugin release or modify marketplace/ClawHub state.
