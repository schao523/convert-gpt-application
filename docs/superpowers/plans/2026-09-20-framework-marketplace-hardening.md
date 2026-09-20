# Framework and Marketplace Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add schema-v3 deterministic distribution contracts, machine-readable recovery, transactional marketplace preparation, Git-byte verification, and catalog-driven cross-platform CI while preserving v1/v2 as read-only legacy formats.

**Architecture:** Extend the existing Python framework through focused contract, result, content-policy, marketplace, and Git-evidence modules. The existing package builder consumes the new canonical-content boundary; marketplace orchestration composes public framework APIs and application-owned commands, while generated marketplace verification remains self-contained. Vibe Coding Designer becomes the schema-v3 build canary, and Cool Bible Tutor remains a byte-preserved `verify_existing` entry.

**Tech Stack:** Python 3.11+, standard library only, `unittest`, Git CLI, deterministic JSON, GitHub Actions YAML.

**Spec:** `docs/superpowers/specs/2026-09-20-framework-marketplace-hardening-design.md`

## Global Constraints

- New package builds require distribution-contract schema v3; schema v1/v2 remain inspection and legacy-verification inputs only.
- Framework APIs and CLI commands are non-interactive and machine-readable; callers may be agents, scripts, CI jobs, clients, or humans.
- The framework validates recorded decision evidence but never invents file classifications, rights, scope, runtime, or publication decisions.
- Application text is strict UTF-8 without BOM and is normalized to LF; binary files are copied byte-for-byte; generated JSON is sorted UTF-8/LF with one final newline.
- All source, output, marketplace, and Git paths must remain inside explicit validated roots; links, junctions, reparse points, and case-folded destination collisions are rejected.
- Build and marketplace preparation are transactional and cannot replace the last valid artifact after a failed gate.
- `prepare-marketplace` writes only to a separate staging root; it never applies, commits, pushes, tags, releases, or publishes.
- `build` catalog entries require schema v3; `verify_existing` accepts v1/v2/v3 read-only and cannot rebuild or alter that plugin's bytes, version, identity, or catalog entry.
- GitHub marketplace and ClawHub are independent publication contracts; ClawHub is disabled unless a compatible native manifest is explicitly declared.
- Python 3.11 is the minimum runtime. Add no required third-party runtime dependency and perform no network or model download.
- Generic production code must contain no Cool Bible Tutor domain behavior or Vibe Coding Designer acceptance logic.

## File Structure

- Create `src/obvious_one_plugin_framework/results.py` for immutable operation-result, diagnostic, artifact, mutation, and JSON-envelope models.
- Modify `src/obvious_one_plugin_framework/contract.py` for strict version routing and schema-v3 content/publication models.
- Create `src/obvious_one_plugin_framework/contract_migration.py` for non-overwriting v1/v2-to-v3 proposal generation.
- Create `src/obvious_one_plugin_framework/content_policy.py` for classification, canonical byte writing, path collision checks, and manifest records.
- Modify `src/obvious_one_plugin_framework/package_builder.py` to require v3 builds and emit content-manifest schema v2.
- Create `src/obvious_one_plugin_framework/marketplace.py` for preparation-catalog loading and staged marketplace composition.
- Create `src/obvious_one_plugin_framework/git_evidence.py` for attributes, index, commit, and fresh-checkout byte verification.
- Create `src/obvious_one_plugin_framework/marketplace_ci.py` for validation-registry, self-contained verifier, and matrix workflow generation.
- Modify `src/obvious_one_plugin_framework/cli.py` and `__init__.py` to expose the public operations and stable result envelopes.
- Create focused tests in `tests/framework/test_results.py`, `test_contract_migration.py`, `test_content_policy.py`, `test_marketplace.py`, `test_git_evidence.py`, and `test_marketplace_ci.py`; extend existing contract, package, CLI, template, documentation, and Vibe tests.
- Create `tests/framework/fixtures/plugin-v3/` and Git marketplace fixtures entirely through temporary test roots.
- Create `marketplaces/obvious-one.json` as the application-neutral preparation catalog.
- Migrate `applications/vibe-coding-designer/openclaw/distribution.json` to schema v3 and add its marketplace mapping to `conversion.json`.
- Update `templates/github-workflows/validate.yml.template`; package the self-contained verifier template below `src/obvious_one_plugin_framework/templates/marketplace/` so installed wheels retain it.
- Update `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`, `docs/GPT_TO_PLUGIN_USER_GUIDE.md`, and applicable repository contract tests.

## Review Focus

- A pair of artifact paths that differ only by case must fail before staging because the resulting checkout is unsafe on case-insensitive filesystems; Task 4 pins this behavior.
- A text-classified file containing a UTF-8 BOM or invalid UTF-8 must return a stable failure instead of being copied or silently treated as binary; Task 4 pins this behavior.
- Identical, nested, repository-root, or marketplace-inside-output paths must be rejected without deleting or replacing content; Task 6 pins this behavior.
- A `verify_existing` entry whose baseline catalog identity/version or artifact bytes drift must fail while leaving the baseline and staged copy untouched; Tasks 6 and 8 pin this behavior.
- Git evidence must distinguish unstaged working-tree bytes, staged index blobs, committed blobs, untracked files, and checkout conversion; Task 7 pins each state.

## Requirement Coverage

- FRH-001: Tasks 2, 3, 4, 6, and 10.
- FRH-002 and FRH-003: Task 4, with CLI recovery evidence in Task 5.
- FRH-004: Tasks 1, 5, and 9.
- FRH-005: Task 6, exercised against the real baseline in Task 11.
- FRH-006: Tasks 4 and 7, with cross-checkout verification in Task 11.
- FRH-007: Task 8, with the real two-plugin catalog in Tasks 10 and 11.
- FRH-008: Tasks 2 and 8.
- FRH-009: Tasks 6, 8, and 10.
- FRH-010: packaged resources and layout-independent loading in Tasks 6, 8, and 11.
- FRH-011: Task 5, preserved by all later CLI operations.

---

### Task 1: Stable operation-result contracts

**Files:**
- Create: `src/obvious_one_plugin_framework/results.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_results.py`

**Interfaces:**
- Consumes: no new project interface.
- Produces: `Diagnostic`, `ArtifactRecord`, `MutationRecord`, `OperationResult`, `result_payload(result: OperationResult) -> dict[str, object]`, `operation_result_from_payload(payload: Mapping[str, object]) -> OperationResult`, `result_json(result: OperationResult) -> str`, `load_result(path: Path) -> OperationResult`, and `ResultStatus = Literal["PASS", "BLOCKED", "FAIL"]`.

- [ ] **Step 1: Write failing result-model tests**

```python
from obvious_one_plugin_framework.results import Diagnostic, OperationResult, result_json

def test_result_json_is_stable_and_path_safe(self) -> None:
    result = OperationResult(
        operation="validate-contract",
        status="BLOCKED",
        code="unclassified_files",
        diagnostics=(Diagnostic("unclassified_file", "skills/demo/SKILL.md", "classification required", ("text", "binary")),),
    )
    first = result_json(result)
    self.assertEqual(first, result_json(result))
    self.assertTrue(first.endswith("\n"))
    self.assertNotIn("C:\\\\Users", first)

def test_result_rejects_unknown_status(self) -> None:
    with self.assertRaisesRegex(ValueError, "invalid_result_status"):
        OperationResult(operation="verify", status="OK", code="ok")

def test_result_rejects_private_absolute_path_in_evidence(self) -> None:
    result = OperationResult(operation="verify", status="FAIL", code="io_failure", evidence={"source": "C:\\Users\\person\\private"})
    with self.assertRaisesRegex(ValueError, "private_absolute_path"):
        result_payload(result)
```

- [ ] **Step 2: Run the focused tests and confirm the missing-module failure**

Run: `python -B -m unittest tests.framework.test_results -v`

Expected: `FAIL` because `obvious_one_plugin_framework.results` does not exist.

- [ ] **Step 3: Implement immutable result models and canonical serialization**

```python
@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str | None
    message: str
    candidates: tuple[str, ...] = ()

@dataclass(frozen=True)
class OperationResult:
    operation: str
    status: Literal["PASS", "BLOCKED", "FAIL"]
    code: str
    diagnostics: tuple[Diagnostic, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    mutations: tuple[MutationRecord, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "BLOCKED", "FAIL"}:
            raise ValueError("invalid_result_status")

def result_payload(result: OperationResult) -> dict[str, object]:
    payload = {"result_schema_version": 1, **asdict(result)}
    _reject_private_absolute_paths(payload)
    return payload

def result_json(result: OperationResult) -> str:
    return json.dumps(result_payload(result), ensure_ascii=True, indent=2, sort_keys=True) + "\n"

def load_result(path: Path) -> OperationResult:
    return operation_result_from_payload(json.loads(path.read_text(encoding="utf-8")))
```

Implement `ArtifactRecord` with `path`, `kind`, `sha256`, and `size`; implement `MutationRecord` with `path` and `action`. Reject absolute diagnostic/artifact/mutation paths before serialization.

- [ ] **Step 4: Run result and export tests**

Run: `python -B -m unittest tests.framework.test_results tests.test_repository_layout -v`

Expected: `PASS`.

- [ ] **Step 5: Commit the result contract**

```powershell
git add src/obvious_one_plugin_framework/results.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_results.py
git commit -m "feat: add machine-readable operation results"
```

### Task 2: Distribution-contract schema v3 and legacy routing

**Files:**
- Modify: `src/obvious_one_plugin_framework/contract.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Modify: `tests/framework/test_contract.py`
- Create: `tests/framework/fixtures/plugin-v3/distribution.json`
- Create: `tests/framework/fixtures/plugin-v3/source/.codex-plugin/plugin.json`
- Create: `tests/framework/fixtures/plugin-v3/source/README.md`
- Create: `tests/framework/fixtures/plugin-v3/source/assets/logo.bin`
- Create: `tests/framework/fixtures/plugin-v3/source/docs/source-decisions.md`

**Interfaces:**
- Consumes: existing `ContractError` and `DistributionContract` loaders.
- Produces: `ContentRule`, `RedistributionEvidence`, `PublicationProfile`, `PublicationTarget`, `require_buildable_contract(contract: DistributionContract) -> None`, and v3 fields `content_rules` and `publication` on `DistributionContract`.

- [ ] **Step 1: Add failing schema-v3 and legacy-routing tests**

```python
def test_schema_v3_loads_content_and_publication_rules(self) -> None:
    contract = load_contract(FIXTURES / "plugin-v3/distribution.json")
    self.assertEqual(contract.schema_version, 3)
    self.assertEqual(contract.content_rules[0].classification, "text")
    self.assertTrue(contract.publication.github_marketplace.enabled)
    self.assertFalse(contract.publication.clawhub.enabled)

def test_legacy_contract_is_read_only_for_builds(self) -> None:
    contract = load_contract(FIXTURES / "plugin-alpha/distribution.json")
    with self.assertRaisesRegex(ContractError, "legacy_contract_read_only"):
        require_buildable_contract(contract)
```

Also test unknown v3 keys, empty rule selectors, duplicate rule IDs, unsafe provenance paths, disabled ClawHub with non-null fields, enabled ClawHub without a native manifest, and a non-existent provenance file.

- [ ] **Step 2: Run contract tests and confirm v3 is unsupported**

Run: `python -B -m unittest tests.framework.test_contract -v`

Expected: `FAIL` with `unsupported_schema` or missing v3 symbols.

- [ ] **Step 3: Add strict v3 dataclasses and parsing**

```python
@dataclass(frozen=True)
class RedistributionEvidence:
    status: str
    provenance: str

@dataclass(frozen=True)
class ContentRule:
    rule_id: str
    paths: tuple[str, ...]
    prefixes: tuple[str, ...]
    classification: Literal["text", "binary"]
    redistribution: RedistributionEvidence

@dataclass(frozen=True)
class PublicationTarget:
    enabled: bool
    family: str | None = None
    native_manifest: str | None = None

def require_buildable_contract(contract: DistributionContract) -> None:
    if contract.schema_version != 3:
        raise ContractError("legacy_contract_read_only", str(contract.schema_version))
```

Route versions 1 and 2 through their existing parser and validation semantics. Require the exact schema-v3 root additions `content_rules` and `publication`; retain existing root fields. Validate all relative paths with `_relative`, require `redistribution.status == "approved"`, and require the provenance file below `source_root`.

- [ ] **Step 4: Run contract and existing framework compatibility tests**

Run: `python -B -m unittest tests.framework.test_contract tests.framework.test_verification_config tests.framework.test_release_assets -v`

Expected: `PASS`; legacy configuration still loads for inspection.

- [ ] **Step 5: Commit schema-v3 parsing**

```powershell
git add src/obvious_one_plugin_framework/contract.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_contract.py tests/framework/fixtures/plugin-v3
git commit -m "feat: add distribution contract schema v3"
```

### Task 3: Read-only legacy migration proposals

**Files:**
- Create: `src/obvious_one_plugin_framework/contract_migration.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_contract_migration.py`

**Interfaces:**
- Consumes: `load_contract`, safe relative-path helpers, and `OperationResult`.
- Produces: `MigrationProposal`, `build_migration_proposal(contract_path: Path) -> MigrationProposal`, and `write_migration_proposal(contract_path: Path, output_path: Path) -> OperationResult`.

- [ ] **Step 1: Write failing proposal and non-overwrite tests**

```python
def test_legacy_migration_writes_unresolved_proposal_not_valid_contract(self) -> None:
    result = write_migration_proposal(LEGACY, self.root / "proposal.json")
    payload = json.loads((self.root / "proposal.json").read_text(encoding="utf-8"))
    self.assertEqual(result.status, "BLOCKED")
    self.assertEqual(payload["proposal_schema_version"], 1)
    self.assertEqual(payload["target_schema_version"], 3)
    self.assertEqual(payload["contract_draft"]["schema_version"], 3)
    self.assertTrue(payload["diagnostics"])

def test_migration_refuses_existing_destination(self) -> None:
    destination = self.root / "proposal.json"
    destination.write_text("keep", encoding="utf-8")
    with self.assertRaisesRegex(ContractError, "migration_destination_exists"):
        write_migration_proposal(LEGACY, destination)
    self.assertEqual(destination.read_text(encoding="utf-8"), "keep")
```

- [ ] **Step 2: Run the migration tests and confirm the missing-module failure**

Run: `python -B -m unittest tests.framework.test_contract_migration -v`

Expected: `FAIL` because the migration module does not exist.

- [ ] **Step 3: Implement deterministic proposal generation**

Build `contract_draft` by copying the legacy identity, selection, size, release, overlay, audit, and RAG fields. Set unresolved publication booleans and file classifications to JSON `null`, which makes the proposal intentionally non-buildable, and emit `publication_decision_required` plus one diagnostic per selected path with detected characteristics and candidates `text`, `binary`, `exclude`, `external_asset`, and `private_local`. Never put an affirmative publication decision or content classification into a draft without recorded evidence.

Write with:

```python
encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
output_path.write_text(encoded, encoding="utf-8", newline="\n")
```

- [ ] **Step 4: Run proposal tests twice and compare bytes**

Run: `python -B -m unittest tests.framework.test_contract_migration -v`

Expected: `PASS`, including identical proposals in two independent temporary roots.

- [ ] **Step 5: Commit the migration proposal API**

```powershell
git add src/obvious_one_plugin_framework/contract_migration.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_contract_migration.py
git commit -m "feat: generate safe schema v3 migration proposals"
```

### Task 4: Canonical content policies and deterministic package manifests

**Files:**
- Create: `src/obvious_one_plugin_framework/content_policy.py`
- Modify: `src/obvious_one_plugin_framework/package_builder.py`
- Modify: `src/obvious_one_plugin_framework/release_assets.py`
- Create: `tests/framework/test_content_policy.py`
- Modify: `tests/framework/test_package_builder.py`
- Modify: `tests/framework/test_release_assets.py`

**Interfaces:**
- Consumes: `DistributionContract`, `ContentRule`, and `require_buildable_contract`.
- Produces: `ResolvedContentPolicy`, `resolve_content_policies(contract, paths) -> Mapping[str, ResolvedContentPolicy]`, `write_canonical_file(source, destination, policy) -> None`, and content-manifest schema v2 records.

- [ ] **Step 1: Write failing classification and canonical-byte tests**

```python
def test_unclassified_and_ambiguous_paths_block_before_write(self) -> None:
    with self.assertRaisesRegex(ContentPolicyError, "unclassified_files"):
        resolve_content_policies(contract, ("README.md", "new.txt"))
    with self.assertRaisesRegex(ContentPolicyError, "ambiguous_file_classification"):
        resolve_content_policies(overlapping_contract, ("README.md",))

def test_text_is_lf_binary_is_exact_and_bom_is_rejected(self) -> None:
    text_source.write_bytes(b"one\r\ntwo\rthree")
    write_canonical_file(text_source, text_output, text_policy)
    self.assertEqual(text_output.read_bytes(), b"one\ntwo\nthree")
    write_canonical_file(binary_source, binary_output, binary_policy)
    self.assertEqual(binary_output.read_bytes(), binary_source.read_bytes())
    bom_source.write_bytes(b"\xef\xbb\xbfunsafe")
    with self.assertRaisesRegex(ContentPolicyError, "text_bom_forbidden"):
        write_canonical_file(bom_source, bom_output, text_policy)
```

Add tests for invalid UTF-8, `Readme.md` versus `README.md` collision, prefix segment boundaries, preservation of final-newline presence, and no output directory creation after policy failure.

- [ ] **Step 2: Run content-policy tests and confirm missing symbols**

Run: `python -B -m unittest tests.framework.test_content_policy -v`

Expected: `FAIL` because the content-policy module does not exist.

- [ ] **Step 3: Implement exact rule matching and canonical writers**

```python
def _matches(rule: ContentRule, relative: str) -> bool:
    return relative in rule.paths or any(
        relative.startswith(prefix.rstrip("/") + "/") for prefix in rule.prefixes
    )

def write_canonical_file(source: Path, destination: Path, policy: ResolvedContentPolicy) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if policy.classification == "binary":
        shutil.copyfile(source, destination)
        return
    raw = source.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContentPolicyError("text_bom_forbidden", policy.path)
    text = raw.decode("utf-8")
    destination.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")
```

Resolve all policies and case-folded collisions before creating the staging directory. Give framework-generated `package.json` and `CONTENT-MANIFEST.json` the built-in `generated-json` policy and vendored runtime files versioned built-in policies.

- [ ] **Step 4: Make package building v3-only and manifest schema v2**

Call `require_buildable_contract` before output-parent creation. Replace `_copy_file` for application files with `write_canonical_file`. Manifest records must contain `path`, `classification`, `canonicalization`, `size`, and `sha256`; calculate aggregate identity from compact sorted JSON of ordered records.

```python
def _manifest_data(stage: Path, contract: DistributionContract) -> dict[str, object]:
    records = _records_with_policies(stage, contract)
    identity = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "schema_version": 2,
        "plugin_id": contract.plugin_id,
        "version": contract.version,
        "file_count": len(records),
        "total_bytes": sum(record["size"] for record in records),
        "content_sha256": sha256(identity).hexdigest(),
        "files": records,
    }
```

Call `require_buildable_contract` at the start of `build_asset_groups` before
creating its output root. Legacy remote-asset manifests remain readable, but no
v1/v2 contract may generate a new archive.

- [ ] **Step 5: Run package, content, asset, and determinism tests**

Run: `python -B -m unittest tests.framework.test_content_policy tests.framework.test_package_builder tests.framework.test_release_assets -v`

Expected: `PASS`; legacy `verify_package` continues to verify legacy manifest schema without rebuilding, while `build_package` and `build_asset_groups` reject legacy contracts before mutation.

- [ ] **Step 6: Commit canonical package generation**

```powershell
git add src/obvious_one_plugin_framework/content_policy.py src/obvious_one_plugin_framework/package_builder.py src/obvious_one_plugin_framework/release_assets.py tests/framework/test_content_policy.py tests/framework/test_package_builder.py tests/framework/test_release_assets.py
git commit -m "feat: canonicalize schema v3 package content"
```

### Task 5: Non-interactive CLI result envelopes

**Files:**
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_cli.py`

**Interfaces:**
- Consumes: Tasks 1-4 public APIs.
- Produces: CLI commands `validate-contract`, `migrate-contract`, hardened `build-package` and `verify`, and `emit_result(result: OperationResult) -> None`.

- [ ] **Step 1: Write failing CLI-envelope tests**

```python
def test_cli_reports_blocked_legacy_build(self) -> None:
    code, payload = self.invoke("build-package", "--contract", str(LEGACY), "--output", str(self.output / "legacy"))
    self.assertEqual(code, 2)
    self.assertEqual(payload["status"], "BLOCKED")
    self.assertEqual(payload["code"], "legacy_contract_read_only")
    self.assertEqual(payload["mutations"], [])

def test_validate_contract_requires_no_interaction(self) -> None:
    with patch("builtins.input", side_effect=AssertionError("interactive input forbidden")):
        code, payload = self.invoke("validate-contract", "--contract", str(V3))
    self.assertEqual((code, payload["status"]), (0, "PASS"))
```

Test malformed CLI syntax through a parser subclass that returns the result envelope with exit code 2, legacy Windows console ASCII-safe output, invalid JSON, migration destination collision, and stable exit-code mappings.

- [ ] **Step 2: Run CLI tests and observe old payload failures**

Run: `python -B -m unittest tests.framework.test_cli -v`

Expected: `FAIL` because current payloads use `status: ok/error` and new commands are absent.

- [ ] **Step 3: Implement command dispatch through `OperationResult`**

Create one handler per command. Convert `ContractError` codes `legacy_contract_read_only`, `unclassified_files`, `ambiguous_file_classification`, and `rights_unresolved` to `BLOCKED`; malformed or unsafe contracts remain `FAIL`. Preserve exit codes 0/2/3/4. Emit exactly one `result_json` document to stdout for every path, including parser errors.

```python
BLOCKING_CODES = frozenset({
    "legacy_contract_read_only",
    "unclassified_files",
    "ambiguous_file_classification",
    "rights_unresolved",
})

def _contract_failure(operation: str, error: ContractError) -> OperationResult:
    status = "BLOCKED" if error.code in BLOCKING_CODES else "FAIL"
    return OperationResult(operation=operation, status=status, code=error.code)
```

- [ ] **Step 4: Run CLI and result suites**

Run: `python -B -m unittest tests.framework.test_results tests.framework.test_cli -v`

Expected: `PASS`.

- [ ] **Step 5: Commit the CLI contract**

```powershell
git add src/obvious_one_plugin_framework/cli.py tests/framework/test_cli.py
git commit -m "feat: expose noninteractive framework commands"
```

### Task 6: Preparation catalog and transactional marketplace staging

**Files:**
- Create: `src/obvious_one_plugin_framework/marketplace.py`
- Modify: `src/obvious_one_plugin_framework/verification.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_marketplace.py`
- Modify: `tests/framework/test_verification_config.py`
- Create: `tests/framework/fixtures/marketplace-plan.json`

**Interfaces:**
- Consumes: `ApplicationConfig`, `load_application_config`, `build_package`, `OperationResult`, and direct argv expansion.
- Produces: `PreparationEntry`, `PreparationCatalog`, `load_preparation_catalog(path: Path, repository_root: Path) -> PreparationCatalog`, `prepare_marketplace(catalog, baseline: Path, output: Path) -> OperationResult`, `load_application_config_path(config_path: Path, boundary_root: Path) -> ApplicationConfig`, and optional `marketplace_targets: tuple[Literal["codex", "openclaw"], ...]` on `VerificationCommand`.

- [ ] **Step 1: Write failing catalog-validation tests**

```python
def test_build_requires_v3_and_verify_existing_accepts_legacy(self) -> None:
    catalog = load_preparation_catalog(CATALOG, REPOSITORY)
    self.assertEqual([entry.mode for entry in catalog.applications], ["verify_existing", "build"])
    with self.assertRaisesRegex(MarketplaceError, "legacy_contract_read_only"):
        load_preparation_catalog(LEGACY_AS_BUILD, REPOSITORY)

def test_duplicate_destination_and_path_escape_are_rejected(self) -> None:
    with self.assertRaisesRegex(MarketplaceError, "duplicate_marketplace_destination"):
        load_preparation_catalog(DUPLICATE, REPOSITORY)
    with self.assertRaisesRegex(MarketplaceError, "catalog_path_escape"):
        load_preparation_catalog(ESCAPE, REPOSITORY)
```

Add a fixture whose `conversion.json` lives below `workspace/products/demo`
rather than `applications/demo`; assert `load_application_config_path` accepts
it under the supplied workspace boundary while the repository discovery
wrapper continues to enforce immediate `applications/*` children.

- [ ] **Step 2: Write failing transactional-staging tests**

Use temporary source and baseline Git trees. Assert that a schema-v3 `build` entry changes only its two declared staged destinations; a legacy `verify_existing` entry is byte-identical; failed product audit preserves an existing output; and baseline, output, nested, repository-root, and output-inside-baseline path combinations return `unsafe_marketplace_path` without mutation.

- [ ] **Step 3: Run marketplace tests and confirm missing-module failures**

Run: `python -B -m unittest tests.framework.test_marketplace -v`

Expected: `FAIL` because `marketplace.py` does not exist.

- [ ] **Step 4: Implement strict preparation-catalog loading**

Use schema:

```json
{
  "schema_version": 1,
  "marketplace_id": "obvious-one",
  "applications": [
    {
      "application_config": "applications/cool-bible-tutor/conversion.json",
      "distribution_contract": "applications/cool-bible-tutor/openclaw/distribution.json",
      "codex_destination": "plugins/cool-bible-tutor",
      "openclaw_destination": "openclaw/cool-bible-tutor",
      "mode": "verify_existing"
    }
  ]
}
```

Resolve catalog paths below `repository_root`; reject unknown keys, duplicate IDs/destinations, invalid modes, application/contract identity mismatches, and legacy `build` entries.

- [ ] **Step 5: Add explicit application-owned marketplace command targets**

Permit each existing `verification.commands[]` object to declare optional `marketplace_targets` containing only `codex` and/or `openclaw`; default to an empty tuple. Reject duplicates and reject opted-in argv containing `{repository_root}` or `{diagnostics}` because those roots do not exist in a redistributable marketplace. The CI generator may translate `{application_root}` to `{artifact_root}` only for commands explicitly opted into a target.

```python
targets = tuple(command.get("marketplace_targets", ()))
if len(targets) != len(set(targets)) or not set(targets) <= {"codex", "openclaw"}:
    raise _error(config_path, f"{field}.marketplace_targets", "invalid marketplace target")
if targets and any(token in argument for argument in argv for token in ("{repository_root}", "{diagnostics}")):
    raise _error(config_path, f"{field}.argv", "marketplace command uses development-only root")
```

Add `load_application_config_path` so catalog callers can load a configuration anywhere below an explicitly supplied boundary rather than requiring this repository's `applications/<id>` layout. Keep `load_application_config(application_root, repository_root)` as the discovery-compatible wrapper and test both paths:

```python
def load_application_config_path(config_path: Path, boundary_root: Path) -> ApplicationConfig:
    boundary = Path(boundary_root).resolve()
    path = Path(config_path).resolve()
    if path.name != "conversion.json" or not path.is_relative_to(boundary):
        raise _error(path, "config_path", "path escapes declared boundary")
    return _load_application_config(path, boundary)
```

- [ ] **Step 6: Implement isolated marketplace preparation**

Copy the clean baseline into a new temporary sibling stage. For `build`, invoke the application-owned Codex argv into a temporary Codex build root and `build_package` for OpenClaw, then replace only staged destinations. For `verify_existing`, compare baseline catalogs, plugin identities, and existing content manifests without invoking either builder. Generate a sorted delta from baseline-relative hashes, then atomically replace only the requested staging output.

```python
def prepare_marketplace(catalog: PreparationCatalog, baseline: Path, output: Path) -> OperationResult:
    _validate_separate_roots(catalog.repository_root, baseline, output)
    with TemporaryDirectory(prefix=".marketplace-", dir=output.parent) as temporary:
        stage = Path(temporary) / "marketplace"
        shutil.copytree(baseline, stage)
        for entry in catalog.applications:
            if entry.mode == "build":
                _build_entry(entry, stage)
            else:
                _verify_existing_entry(entry, baseline, stage)
        _write_generated_controls(catalog, stage)
        result = _marketplace_result(baseline, stage)
        _replace_tree_transactionally(stage, output)
        return result
```

- [ ] **Step 7: Run marketplace and verification-config tests**

Run: `python -B -m unittest tests.framework.test_marketplace tests.framework.test_verification_config -v`

Expected: `PASS`, including byte-identical legacy artifacts and no baseline writes.

- [ ] **Step 8: Commit marketplace staging**

```powershell
git add src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/verification.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_marketplace.py tests/framework/test_verification_config.py tests/framework/fixtures/marketplace-plan.json
git commit -m "feat: prepare transactional marketplace deltas"
```

### Task 7: Git attributes and exact-byte evidence

**Files:**
- Create: `src/obvious_one_plugin_framework/git_evidence.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Create: `tests/framework/test_git_evidence.py`

**Interfaces:**
- Consumes: package content manifests and marketplace destinations.
- Produces: `GitEvidenceReport`, `verify_git_evidence(marketplace: Path, scopes: Sequence[str], *, commit: str | None = None, fresh_checkout: bool = False) -> GitEvidenceReport`, and `exact_byte_attributes(scopes: Sequence[str]) -> str`.

- [ ] **Step 1: Write failing Git-state tests**

Create temporary Git repositories with `core.autocrlf=true` and assert:

```python
def test_index_commit_and_fresh_checkout_keep_exact_bytes(self) -> None:
    attributes = exact_byte_attributes(("plugins/demo", "openclaw/demo"))
    (repo / ".gitattributes").write_text(attributes, encoding="utf-8", newline="\n")
    commit_all(repo)
    report = verify_git_evidence(repo, ("plugins/demo", "openclaw/demo"), commit="HEAD", fresh_checkout=True)
    self.assertEqual(report.status, "PASS")

def test_staged_and_unstaged_differences_are_distinct(self) -> None:
    staged = verify_git_evidence(repo, scopes, commit="HEAD")
    self.assertIn("index_blob_mismatch", staged.codes)
    self.assertIn("working_tree_mismatch", staged.codes)
```

Also test untracked artifact files, missing `-text`, path names with spaces/Unicode, incomplete index entries, and no modification of the supplied repository.

- [ ] **Step 2: Run Git evidence tests and confirm the missing-module failure**

Run: `python -B -m unittest tests.framework.test_git_evidence -v`

Expected: `FAIL` because `git_evidence.py` does not exist.

- [ ] **Step 3: Implement shell-free Git inspection**

Use `subprocess.run([...], shell=False, timeout=30, check=False, capture_output=True)`. Read index object IDs from `git ls-files --stage -z`, bytes from `git cat-file blob <oid>`, commit bytes from `git show <ref>:<path>`, and attributes from `git check-attr -z text -- <path>`. For fresh checkout, create a `TemporaryDirectory`, run `git clone --no-hardlinks --no-checkout <local-path> <temp>`, then `git checkout --detach <ref>`; never fetch.

- [ ] **Step 4: Emit scoped exact-byte attributes**

```python
def exact_byte_attributes(scopes: Sequence[str]) -> str:
    lines = [f"/{scope.rstrip('/')}/** -text whitespace=cr-at-eol" for scope in sorted(set(scopes))]
    return "\n".join(lines) + "\n"
```

Merge only generated plugin-scope lines while preserving unrelated `.gitattributes` lines.

- [ ] **Step 5: Run Git and package determinism tests**

Run: `python -B -m unittest tests.framework.test_git_evidence tests.framework.test_package_builder -v`

Expected: `PASS` with `core.autocrlf=true` fixtures.

- [ ] **Step 6: Commit Git evidence verification**

```powershell
git add src/obvious_one_plugin_framework/git_evidence.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_git_evidence.py
git commit -m "feat: verify marketplace git bytes"
```

### Task 8: Self-contained marketplace verifier and catalog-driven CI

**Files:**
- Create: `src/obvious_one_plugin_framework/marketplace_ci.py`
- Modify: `src/obvious_one_plugin_framework/marketplace.py`
- Create: `src/obvious_one_plugin_framework/templates/marketplace/verify_marketplace.py.template`
- Modify: `pyproject.toml`
- Modify: `templates/github-workflows/validate.yml.template`
- Create: `tests/framework/test_marketplace_ci.py`
- Modify: `tests/test_templates.py`

**Interfaces:**
- Consumes: `PreparationCatalog`, runtime marketplace catalogs, application validation commands, and exact-byte scopes.
- Produces: `build_validation_registry(...) -> dict[str, object]`, `render_marketplace_verifier() -> str`, and `render_validation_workflow() -> str`; staged files `.obvious-one-validation.json`, `tools/verify_marketplace.py`, and `.github/workflows/validate.yml`.

- [ ] **Step 1: Write failing registry and matrix tests**

```python
def test_registry_contains_every_runtime_catalog_plugin_once(self) -> None:
    registry = build_validation_registry(codex_catalog, openclaw_catalog, preparation_catalog)
    self.assertEqual([item["plugin_id"] for item in registry["plugins"]], ["cool-bible-tutor", "vibe-coding-designer"])
    self.assertEqual(registry["plugins"][0]["mode"], "verify_existing")
    self.assertEqual(registry["plugins"][1]["mode"], "build")

def test_adding_plugin_expands_matrix_without_workflow_edit(self) -> None:
    registry = build_validation_registry(with_synthetic_plugin, openclaw_with_synthetic, plan_with_synthetic)
    self.assertEqual(len(registry["plugins"]), 3)
    self.assertNotIn("cool-bible-tutor", render_validation_workflow())
    self.assertNotIn("vibe-coding-designer", render_validation_workflow())
```

Test catalog identity/version disagreement, missing registry entries, duplicate entries, verify-existing byte drift, disabled ClawHub `NOT APPLICABLE`, and enabled ClawHub without a native manifest `FAIL`.
Read the verifier template through `importlib.resources.files("obvious_one_plugin_framework")` in a test so an installed-wheel layout, rather than the repository root, is the required runtime path.

- [ ] **Step 2: Run CI-generation tests and confirm missing symbols**

Run: `python -B -m unittest tests.framework.test_marketplace_ci tests.test_templates -v`

Expected: `FAIL` because the generator and verifier template do not exist.

- [ ] **Step 3: Implement the validation registry and self-contained verifier**

The registry schema is:

```json
{
  "schema_version": 1,
  "marketplace_id": "obvious-one",
  "plugins": [
    {
      "plugin_id": "cool-bible-tutor",
      "version": "2.4.6",
      "mode": "verify_existing",
      "codex_path": "plugins/cool-bible-tutor",
      "openclaw_path": "openclaw/cool-bible-tutor",
      "commands": [
        {
          "id": "runtime-status-openclaw",
          "artifact": "openclaw",
          "argv": ["{python}", "-B", "{artifact_root}/scripts/cool_bible_tutor.py", "status", "--json"]
        }
      ]
    }
  ]
}
```

The generated verifier uses only Python's standard library. It accepts `--registry`, `--plugin`, and `--json`; validates both artifact trees and manifests; expands only `{python}` and `{artifact_root}` in opted-in commands; runs only the selected plugin's direct argv commands with `shell=False`; emits the result envelope; and performs no network or publication operation. Registry generation converts `{application_root}` to `{artifact_root}` separately for each declared marketplace target and rejects every other development-only placeholder.

Load the verifier source with `importlib.resources.files` and extend package
data explicitly:

```toml
[tool.setuptools.package-data]
obvious_one_plugin_framework = [
  "templates/runtime/obvious_one_runtime/*.py",
  "templates/marketplace/*.template"
]
```

- [ ] **Step 4: Replace named-plugin workflow logic with a dynamic matrix**

Render a bootstrap job that reads `.obvious-one-validation.json` and writes `matrix={"plugin":[...]}` to `$GITHUB_OUTPUT`. Render a validation job with `matrix.plugin` and `matrix.os: [windows-latest, ubuntu-latest, macos-latest]` that invokes:

```text
python -B tools/verify_marketplace.py --registry .obvious-one-validation.json --plugin <matrix.plugin> --json
```

Keep `fail-fast: false`; add an aggregate job that fails if any required matrix result failed. Do not install ClawHub in this workflow.

- [ ] **Step 5: Run generated verifier inside a temporary staged marketplace**

Run: `python -B -m unittest tests.framework.test_marketplace_ci tests.framework.test_marketplace tests.test_templates -v`

Expected: `PASS`; both a built v3 fixture and a preserved legacy fixture validate through the generated script.

- [ ] **Step 6: Commit generic marketplace CI generation**

```powershell
git add src/obvious_one_plugin_framework/marketplace_ci.py src/obvious_one_plugin_framework/marketplace.py src/obvious_one_plugin_framework/templates/marketplace/verify_marketplace.py.template pyproject.toml templates/github-workflows/validate.yml.template tests/framework/test_marketplace_ci.py tests/test_templates.py
git commit -m "feat: generate catalog-driven marketplace ci"
```

### Task 9: Marketplace CLI operations and consolidated reports

**Files:**
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Create: `src/obvious_one_plugin_framework/readiness_report.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`
- Modify: `tests/framework/test_cli.py`
- Create: `tests/framework/test_readiness_report.py`

**Interfaces:**
- Consumes: Tasks 6-8 marketplace APIs and Task 1 `load_result`/`result_payload`.
- Produces: CLI commands `prepare-marketplace`, `verify-marketplace`, and `report`; `combine_results(inputs: Sequence[Path]) -> OperationResult`.

- [ ] **Step 1: Write failing end-to-end CLI tests**

Invoke `prepare-marketplace` against a temporary catalog/baseline and assert `PASS`, a populated staged artifact list, no baseline mutation, and exact `mutations`. Invoke `verify-marketplace` for filesystem, index, commit, and fresh-checkout modes. Invoke `report` with one blocked input and assert the aggregate is `BLOCKED`; invoke it with a failed input and assert `FAIL` takes precedence.

- [ ] **Step 2: Run focused CLI/report tests and confirm absent commands**

Run: `python -B -m unittest tests.framework.test_cli tests.framework.test_readiness_report -v`

Expected: `FAIL` because the marketplace commands and report combiner do not exist.

- [ ] **Step 3: Implement dispatch and result aggregation**

Add mutually exclusive `--index`, `--commit REF`, and `--fresh-checkout` verification options. The aggregate precedence is `FAIL`, then `BLOCKED`, then `PASS`; gate evidence retains `PASS`, `FAIL`, `NOT VERIFIED`, and `NOT APPLICABLE`. `report --output` writes canonical JSON transactionally and includes no wall-clock timestamp or absolute private path.

```python
def combine_results(inputs: Sequence[Path]) -> OperationResult:
    payloads = tuple(load_result(path) for path in inputs)
    status = "FAIL" if any(item.status == "FAIL" for item in payloads) else (
        "BLOCKED" if any(item.status == "BLOCKED" for item in payloads) else "PASS"
    )
    return OperationResult(
        operation="report",
        status=status,
        code="combined_results",
        evidence={"inputs": [result_payload(item) for item in payloads]},
    )
```

- [ ] **Step 4: Run all CLI and marketplace framework tests**

Run: `python -B -m unittest tests.framework.test_cli tests.framework.test_readiness_report tests.framework.test_marketplace tests.framework.test_git_evidence tests.framework.test_marketplace_ci -v`

Expected: `PASS`.

- [ ] **Step 5: Commit marketplace CLI orchestration**

```powershell
git add src/obvious_one_plugin_framework/cli.py src/obvious_one_plugin_framework/readiness_report.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_cli.py tests/framework/test_readiness_report.py
git commit -m "feat: expose marketplace preparation and verification"
```

### Task 10: Vibe schema-v3 canary and legacy Cool verification catalog

**Files:**
- Create: `marketplaces/obvious-one.json`
- Modify: `applications/vibe-coding-designer/openclaw/distribution.json`
- Modify: `applications/vibe-coding-designer/conversion.json`
- Modify: `applications/cool-bible-tutor/conversion.json`
- Modify: `applications/vibe-coding-designer/tests/test_distribution.py`
- Modify: `applications/vibe-coding-designer/tests/test_marketplace_release.py`
- Modify: `tests/framework/test_verification_config.py`
- Modify: `tests/test_application_config.py`

**Interfaces:**
- Consumes: schema-v3 contract, preparation-catalog, package, and marketplace APIs.
- Produces: real `obvious-one` catalog entries with Vibe `mode: build` and Cool `mode: verify_existing`, plus application-owned marketplace command target declarations. Cool's distribution contract, product assets, behavior, and version remain unchanged.

- [ ] **Step 1: Write failing Vibe schema and catalog-boundary tests**

```python
def test_vibe_distribution_is_schema_v3_with_complete_rules(self) -> None:
    contract = load_contract(ROOT / "openclaw/distribution.json")
    self.assertEqual(contract.schema_version, 3)
    result = build_package(contract, self.output / "vibe")
    self.assertEqual(verify_package(contract, result.output), result)

def test_obvious_one_catalog_defers_cool_migration(self) -> None:
    catalog = load_preparation_catalog(REPOSITORY / "marketplaces/obvious-one.json", REPOSITORY)
    modes = {entry.plugin_id: entry.mode for entry in catalog.applications}
    self.assertEqual(modes, {"cool-bible-tutor": "verify_existing", "vibe-coding-designer": "build"})
```

Assert every final Vibe source path matches one content rule, source decisions are the rights provenance, GitHub marketplace is enabled, ClawHub is disabled with null native fields, and no Vibe behavior/content changes.

- [ ] **Step 2: Run Vibe and application-config tests and observe schema failures**

Run: `python -B -m unittest discover -s applications/vibe-coding-designer/tests -v`

Run: `python -B -m unittest tests.test_application_config tests.framework.test_verification_config -v`

Expected: `FAIL` until Vibe and the preparation catalog use the new contract.

- [ ] **Step 3: Migrate only Vibe to schema v3**

Add text rules for `.codex-plugin`, root documentation, `docs`, `scripts`, and `skills`; no Vibe binary package files exist. Point each rule's redistribution provenance to `docs/source-decisions.md`. Enable GitHub marketplace and disable ClawHub explicitly. Do not change Vibe's version or packaged content.

```json
"content_rules": [
  {
    "id": "redistributable-text",
    "paths": [".codex-plugin/plugin.json", "README.md", "DISTRIBUTION.md", "LICENSE", "PRIVACY.md", "SECURITY.md", "THIRD_PARTY_CONTENT.md", "THIRD_PARTY_NOTICES.md"],
    "prefixes": ["docs", "scripts", "skills"],
    "classification": "text",
    "redistribution": {"status": "approved", "provenance": "docs/source-decisions.md"}
  }
],
"publication": {
  "github_marketplace": {"enabled": true},
  "clawhub": {"enabled": false, "family": null, "native_manifest": null}
}
```

- [ ] **Step 4: Add the preparation catalog, mappings, and marketplace command targets**

Create `marketplaces/obvious-one.json` with the two approved modes and safe repository-relative paths. Add Vibe's existing public destinations and approved-delta path to `conversion.json` using the established `verification.marketplace` fields. Mark Vibe's runtime-status command for both targets and leave its development-fixture validators unmarked. In Cool's `conversion.json` only, mark distribution audit and runtime status for both targets and exact passage for OpenClaw. Do not modify Cool's distribution contract, assets, tests, version, runtime behavior, or packaged bytes.

```json
{"id": "runtime-status", "argv": ["{python}", "-B", "{application_root}/scripts/vibe_designer.py", "status", "--json"], "marketplace_targets": ["codex", "openclaw"]}
```

For Cool, retain each current argv unchanged and add only the approved target array to its command object.

- [ ] **Step 5: Prove the Codex and OpenClaw Vibe artifacts remain behaviorally equivalent**

Run: `python -B -m unittest discover -s applications/vibe-coding-designer/tests -v`

Run: `python -B .\scripts\verify_extraction.py --application vibe-coding-designer`

Expected: product tests and declared runtime commands `PASS`; marketplace evidence may remain `NOT VERIFIED` without a supplied checkout.

- [ ] **Step 6: Commit the Vibe canary migration**

```powershell
git add marketplaces/obvious-one.json applications/vibe-coding-designer/openclaw/distribution.json applications/vibe-coding-designer/conversion.json applications/cool-bible-tutor/conversion.json applications/vibe-coding-designer/tests/test_distribution.py applications/vibe-coding-designer/tests/test_marketplace_release.py tests/framework/test_verification_config.py tests/test_application_config.py
git commit -m "feat: migrate Vibe distribution to schema v3"
```

### Task 11: Documentation, local marketplace delta, and complete verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`
- Modify: `tests/test_documentation_contract.py`
- Modify: `tests/test_agents_contract.py`
- Modify: `scripts/verify_extraction.py` only if the full verifier needs to consume result-schema-v1 output without product-specific branching.
- Generated, ignored: `dist/marketplace-delta/obvious-one/`
- Generated, ignored: `.tmp/verification/`

**Interfaces:**
- Consumes: all preceding public APIs and commands.
- Produces: documented schema-v3 workflow, machine-readable final evidence, and a locally prepared marketplace delta only.

- [ ] **Step 1: Write failing documentation-contract tests**

Require documentation to contain `schema_version": 3`, `validate-contract`, `migrate-contract`, `prepare-marketplace`, `verify-marketplace`, `verify_existing`, `legacy_contract_read_only`, the caller/decision-owner distinction, and the statement that preparation does not apply or publish a delta. Remove tests that describe schema v2 as the current build schema while retaining text that v1/v2 are readable legacy formats.

- [ ] **Step 2: Run documentation tests and observe missing references**

Run: `python -B -m unittest tests.test_documentation_contract tests.test_agents_contract -v`

Expected: `FAIL` until the guides describe the new contracts.

- [ ] **Step 3: Update framework and user documentation**

Document exact PowerShell examples for all new commands, exit codes, result statuses, v3 content/publication rules, migration proposals, `build`/`verify_existing`, exact-byte Git attributes, and local-only marketplace staging. State that Cool remains legacy and that ClawHub disabled is `NOT APPLICABLE`, not a package failure.

- [ ] **Step 4: Run the generic and affected repository suites**

Run: `python -B -m unittest discover -s .\tests\framework -v`

Run: `python -B -m unittest discover -s .\tests -v`

Run: `python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v`

Expected: all tests `PASS`.

- [ ] **Step 5: Build Vibe twice in isolated roots and compare exact bytes**

Run the schema-v3 `build-package` command into `.tmp/verification/vibe-one` and `.tmp/verification/vibe-two`. Compare sorted relative paths and SHA-256 values with a PowerShell script that reads bytes without rewriting them. Expected: identical trees and aggregate identities.

- [ ] **Step 6: Build the framework wheel without network access and inspect resources**

Run: `python -B -m pip wheel . --no-deps --no-build-isolation --wheel-dir .\.tmp\wheels`

Open the resulting wheel with Python's standard-library `zipfile` module and assert it contains `obvious_one_plugin_framework/templates/marketplace/verify_marketplace.py.template` plus every existing runtime template. Expected: one wheel builds without dependency download and contains all declared package resources.

- [ ] **Step 7: Prepare and verify the marketplace delta locally**

Run:

```powershell
python -B -m obvious_one_plugin_framework.cli prepare-marketplace `
  --catalog .\marketplaces\obvious-one.json `
  --marketplace D:\GitHub\obvious-one-plugins `
  --output .\dist\marketplace-delta\obvious-one
```

Then initialize a temporary Git repository from the staged output, stage and commit it with test-only identity, and run `verify-marketplace` in filesystem, index, commit, and fresh-checkout modes. Expected: Vibe is rebuilt under v3, Cool is byte-identical to the baseline, both appear in every generated OS matrix, and all exact-byte gates `PASS`.

- [ ] **Step 8: Run application-aware verification against the read-only marketplace baseline**

Run: `python -B .\scripts\verify_extraction.py --all --marketplace D:\GitHub\obvious-one-plugins`

Expected: framework and Vibe gates `PASS`; any remaining Cool legacy mismatch is reported against Cool only and does not invalidate the generic implementation or change Cool files. Record the exact evidence state rather than reporting `READY` if a required remote OS gate has not run.

- [ ] **Step 9: Confirm repository cleanliness boundaries**

Run: `git diff --check`

Run: `git status --short`

Run: `git -C D:\GitHub\obvious-one-plugins status --short`

Expected: no generated `dist` or `.tmp` file is tracked; the marketplace checkout remains unchanged; only intended implementation and documentation changes are present before the final commit.

- [ ] **Step 10: Commit documentation and verifier integration**

```powershell
git add README.md docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md docs/GPT_TO_PLUGIN_USER_GUIDE.md tests/test_documentation_contract.py tests/test_agents_contract.py scripts/verify_extraction.py
git commit -m "docs: document schema v3 marketplace workflow"
```

- [ ] **Step 11: Request final code review and report publication boundary**

Use `superpowers:requesting-code-review`, resolve actionable findings, rerun the affected tests, then use `superpowers:verification-before-completion`. Report the final commit range, test totals, local delta path, exact unverified gates, and that no marketplace, tag, release, push, or ClawHub mutation occurred.
