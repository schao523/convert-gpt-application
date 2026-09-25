# Hosted OpenAI Plugin Deployment Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic, deterministic, non-interactive workflow that creates or updates a complete OpenAI-hosted plugin archive from one canonical converted application, with optional one-time identity import and explicit capability evidence.

**Architecture:** Five focused framework modules own strict deployment contracts, hostile archive identity import, planning, transactional artifact construction, and complete-archive verification. Existing schema-v3 content policy, application verification commands, and `result-schema-v1` remain authoritative integration boundaries; application-specific adapter content and canary assertions remain under Vibe Coding Designer.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `hashlib`, `json`, `pathlib`, `subprocess`, `tempfile`, and `zipfile`; `unittest`; existing `obvious_one_plugin_framework` contract, content-policy, results, and verification APIs.

**Spec:** `docs/superpowers/specs/2026-09-25-hosted-openai-deployment-workflow-design.md`

## Global Constraints

- One canonical converted plugin remains authoritative across OpenAI hosted deployment, Obvious-One, and future public submission.
- Support exactly `OPENAI_HOSTED_CREATE` and `OPENAI_HOSTED_UPDATE` in schema v1.
- Create requires no previous archive, identity record, or marketplace state.
- Update requires an approved identity record, exact package-name preservation, and a target version newer than `last_confirmed_version`.
- An exported hosted ZIP is an optional one-time identity-import input, never a recurring build dependency or canonical source.
- New package bytes require schema-v3 content classification and approved redistribution evidence.
- Target adapters may contain manifests, presentation assets, and approved compatibility routing, but no duplicate portable implementation.
- Build a complete ZIP; do not merge a prior ZIP or claim undocumented hosted retention/deletion behavior.
- Canonicalize approved text to UTF-8 LF, preserve binary bytes exactly, sort archive members, and fix ZIP timestamps and permissions.
- Keep package-static, local-execution, hosted-execution, upload, installation, marketplace, and publication evidence separate.
- A required capability always blocks when unavailable; only an optional capability may use its exact approved fallback.
- Emit exactly one ASCII-safe `result-schema-v1` document per CLI invocation.
- Keep credentials, workspace IDs, private absolute paths, exported archives, diagnostics, and generated artifacts out of tracked source.
- Stop at locally verified artifacts; do not upload, install, publish, submit, push, tag, or mutate any marketplace.
- Preserve the two pre-existing untracked experiment files and never stage them without separate cleanup approval.

## Review Focus

- A crafted identity ZIP with traversal, aliases, links, encryption, collisions, or expansion abuse must fail before proposal mutation; Task 2 owns these tests.
- A create contract must not accidentally inherit update-only identity requirements, while update must never accept a proposal or unconfirmed identity; Task 1 owns these tests.
- Target-adapter files must not bypass schema-v3 rights or duplicate canonical skill/tool implementations; Tasks 3 and 7 own these tests.
- Failed builds and verification must preserve a previous versioned artifact directory byte-for-byte, including on Windows; Tasks 4 and 5 own these tests.
- Local capability success and a local ZIP build must never mark hosted execution, installation, marketplace, or publication current; Tasks 3, 5, and 6 own these tests.

---

### Task 1: Strict deployment and identity contracts

**Files:**
- Create: `src/obvious_one_plugin_framework/hosted_deployment_contract.py`
- Create: `tests/framework/test_hosted_deployment_contract.py`
- Create: `tests/framework/fixtures/hosted-deployment/application/docs/source-inventory.json`
- Create: `tests/framework/fixtures/hosted-deployment/application/docs/source-decisions.md`
- Create: `tests/framework/fixtures/hosted-deployment/application/openclaw/distribution.json`
- Create: `tests/framework/fixtures/hosted-deployment/application/hosted-openai/lineage-decision.json`
- Create: `tests/framework/fixtures/hosted-deployment/application/hosted-openai/deployment.json`
- Create: `tests/framework/fixtures/hosted-deployment/application/hosted-openai/hosted-identity.json`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Consumes: `load_contract(path: Path) -> DistributionContract` and schema-v3 `ContentRule` records.
- Produces: `HostedDeploymentError`, `HostedIdentityRecord`, `DeploymentMapping`, `CapabilityContract`, `ChannelRecord`, `HostedDeploymentContract`, `load_hosted_identity(path: Path) -> HostedIdentityRecord`, and `load_hosted_deployment_contract(path: Path) -> HostedDeploymentContract`.

- [ ] **Step 1: Write failing create/update and strict-schema tests**

```python
class HostedDeploymentContractTests(unittest.TestCase):
    def test_create_requires_no_identity_record(self) -> None:
        contract = load_hosted_deployment_contract(self.contract_path)
        self.assertEqual(contract.operation, "OPENAI_HOSTED_CREATE")
        self.assertIsNone(contract.identity_record)

    def test_update_requires_confirmed_identity_and_newer_version(self) -> None:
        path = self.update_contract(target_version="1.0.0")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_version_not_advanced"):
            load_hosted_deployment_contract(path)

    def test_identity_proposal_cannot_be_used_as_identity_record(self) -> None:
        path = self.update_contract(identity_file="hosted-identity-proposal.json")
        with self.assertRaisesRegex(HostedDeploymentError, "hosted_identity_unapproved"):
            load_hosted_deployment_contract(path)

    def test_required_capability_cannot_use_fallback(self) -> None:
        path = self.contract_with_required_fallback()
        with self.assertRaisesRegex(HostedDeploymentError, "invalid_required_capability_policy"):
            load_hosted_deployment_contract(path)
```

Add table-driven tests for unknown keys at every object level, absolute and
escaping paths, invalid operation, invalid semver, package-name mismatch,
duplicate mapping/capability IDs, case-fold target collision, unsupported
provider/status values, missing packaged-executable artifacts, optional fallback
without a fallback object, missing local-test ID, credentials/workspace IDs in
identity data, and channel states without evidence.

- [ ] **Step 2: Run tests and verify the missing-module failure**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_contract -v
```

Expected: import error for `hosted_deployment_contract`.

- [ ] **Step 3: Implement immutable models and strict parsers**

```python
DeploymentOperation = Literal["OPENAI_HOSTED_CREATE", "OPENAI_HOSTED_UPDATE"]
ChannelStatus = Literal[
    "UNPUBLISHED", "PENDING_ACTION", "CURRENT_BY_DECLARATION", "STALE", "UNKNOWN"
]


class HostedDeploymentError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class HostedIdentityRecord:
    application_id: str
    package_name: str
    last_confirmed_version: str
    last_confirmed_archive_sha256: str
    origin: Literal["imported_hosted_archive", "prior_verified_deployment"]
    recorded_at: str
    evidence_reference: str


@dataclass(frozen=True)
class HostedDeploymentContract:
    schema_version: int
    application_id: str
    operation: DeploymentOperation
    contract_path: Path
    application_root: Path
    source_inventory: Path
    distribution_contract: Path
    lineage_decision: Path
    package_name: str
    identity_record: HostedIdentityRecord | None
    target_version: str
    archive_name: str
    portable_manifest: str
    legacy_manifest: str
    max_archive_bytes: int
    canonical_mappings: tuple[DeploymentMapping, ...]
    adapter_mappings: tuple[DeploymentMapping, ...]
    expected_skills: tuple[str, ...]
    explicit_only_skills: tuple[str, ...]
    required_application_tests: tuple[str, ...]
    capabilities: tuple[CapabilityContract, ...]
    channels: Mapping[str, ChannelRecord]
```

Use exact allowed-key sets, POSIX-relative path confinement, a strict semantic
version comparator, SHA-256 validation, ISO-8601 UTC timestamp validation,
unique IDs/targets, schema-v3 enforcement, provider/fallback validation, and
operation-specific identity rules.

- [ ] **Step 4: Export the public contract API and rerun tests**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_contract tests.framework.test_contract -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit the contract slice**

```powershell
git add src/obvious_one_plugin_framework/hosted_deployment_contract.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_hosted_deployment_contract.py tests/framework/fixtures/hosted-deployment
git commit -m "feat: define hosted deployment contracts"
```

### Task 2: Safe one-time hosted identity import

**Files:**
- Create: `src/obvious_one_plugin_framework/hosted_identity.py`
- Create: `tests/framework/test_hosted_identity.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Consumes: `HostedDeploymentError`, application identity, and a caller-supplied exported ZIP.
- Produces: `ArchiveLimits`, `HostedIdentityCandidate`, `HostedIdentityInventory`, `inventory_hosted_identity_archive(path: Path, limits: ArchiveLimits = ArchiveLimits()) -> HostedIdentityInventory`, and `propose_hosted_identity(application_path: Path, archive: Path, output: Path) -> OperationResult`.

- [ ] **Step 1: Write failing hostile-archive and proposal tests**

```python
class HostedIdentityTests(unittest.TestCase):
    def test_proposal_contains_hashes_but_no_private_path_or_member_bytes(self) -> None:
        result = propose_hosted_identity(self.application, self.archive, self.proposal)
        payload = json.loads(self.proposal.read_text(encoding="utf-8"))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.code, "hosted_identity_approval_required")
        self.assertEqual(payload["proposal_schema"], "hosted-identity-proposal-v1")
        self.assertNotIn(str(self.archive), json.dumps(payload))
        self.assertNotIn("secret member body", json.dumps(payload))

    def test_existing_destination_is_preserved(self) -> None:
        self.proposal.write_text("keep", encoding="utf-8")
        result = propose_hosted_identity(self.application, self.archive, self.proposal)
        self.assertEqual(result.code, "hosted_identity_proposal_exists")
        self.assertEqual(self.proposal.read_text(encoding="utf-8"), "keep")

    def test_casefold_collision_fails_before_proposal_mutation(self) -> None:
        archive = self.write_zip({"Plugin.json": b"{}", "plugin.json": b"{}"})
        with self.assertRaisesRegex(HostedDeploymentError, "archive_casefold_collision"):
            inventory_hosted_identity_archive(archive)
        self.assertFalse(self.proposal.exists())
```

Add explicit cases for traversal, absolute POSIX/Windows names, backslash
aliases, duplicate members, encrypted flags, Unix/Windows links, unsupported
compression, member count, per-member bytes, total expanded bytes, missing or
malformed manifests, missing identity fields, and archive paths containing
non-ASCII text.

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
python -B -m unittest tests.framework.test_hosted_identity -v
```

Expected: import error for `hosted_identity`.

- [ ] **Step 3: Implement streaming archive inspection and proposal writing**

```python
@dataclass(frozen=True)
class ArchiveLimits:
    max_members: int = 4096
    max_member_bytes: int = 64 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024


@dataclass(frozen=True)
class HostedIdentityInventory:
    archive_sha256: str
    package_name: str
    version: str
    identity_members: tuple[tuple[str, str, int], ...]
    presentation_asset_hashes: Mapping[str, str]
```

Inspect all `ZipInfo` records before reading identity-bearing members. Stream
hashes, parse only known manifests, serialize safe relative member names and
hashes, mark approval fields unresolved, write through a sibling temporary file,
and refuse replacement of an existing destination.

- [ ] **Step 4: Export the identity API and run focused tests**

```powershell
python -B -m unittest tests.framework.test_hosted_identity tests.framework.test_results -v
```

Expected: all tests pass and no result contains an absolute archive path.

- [ ] **Step 5: Commit the identity-import slice**

```powershell
git add src/obvious_one_plugin_framework/hosted_identity.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_hosted_identity.py
git commit -m "feat: import hosted identity safely"
```

### Task 3: Deployment planning, validation, and capability closure

**Files:**
- Create: `src/obvious_one_plugin_framework/hosted_deployment_planner.py`
- Create: `tests/framework/test_hosted_deployment_planner.py`
- Create: `tests/framework/test_hosted_deployment_validation.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Consumes: `ApplicationConfig`, `DistributionContract`, `HostedDeploymentContract`, `resolve_content_policies`, and application verification command IDs.
- Produces: `HostedDeploymentPlan`, `HostedDeploymentValidation`, `plan_hosted_deployment(application_path: Path, operation: str, output: Path) -> OperationResult`, and `validate_hosted_deployment(contract: HostedDeploymentContract) -> HostedDeploymentValidation`.

- [ ] **Step 1: Write failing create/update planning tests**

```python
class HostedDeploymentPlannerTests(unittest.TestCase):
    def test_create_plan_requires_no_identity_or_marketplace(self) -> None:
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_CREATE", self.output)
        proposal = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(result.code, "hosted_deployment_decisions_required")
        self.assertNotIn("hosted_identity", proposal["required_inputs"])
        self.assertNotIn("marketplace", proposal["required_inputs"])

    def test_update_plan_reports_missing_identity_decision(self) -> None:
        result = plan_hosted_deployment(self.application, "OPENAI_HOSTED_UPDATE", self.output)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("hosted_identity_required", [item.code for item in result.diagnostics])
```

Add deterministic proposal ordering, no approved-contract mutation, destination
collision, unclassified canonical file, ambiguous content rule, unresolved
adapter rights, and candidate adapter duplication cases.

- [ ] **Step 2: Write failing validation and capability tests**

```python
class HostedDeploymentValidationTests(unittest.TestCase):
    def test_valid_complete_mapping_has_exact_member_set(self) -> None:
        contract = load_hosted_deployment_contract(self.contract_path)
        validation = validate_hosted_deployment(contract)
        self.assertEqual(validation.archive_paths, tuple(sorted(validation.archive_paths)))
        self.assertEqual(validation.hosted_capabilities["exact-retrieval"], "NOT VERIFIED")

    def test_adapter_cannot_duplicate_canonical_skill(self) -> None:
        self.map_adapter_to("skills/example/SKILL.md")
        with self.assertRaisesRegex(HostedDeploymentError, "adapter_duplicates_canonical_content"):
            validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))

    def test_local_build_cannot_mark_external_channel_current(self) -> None:
        validation = validate_hosted_deployment(load_hosted_deployment_contract(self.contract_path))
        self.assertEqual(validation.generated_channels["openai_hosted"], "PENDING_ACTION")
        self.assertEqual(validation.generated_channels["obvious_one"], validation.declared_channels["obvious_one"])
```

Add tests for exact identity preservation, version progression, manifest target
presence, expected skill closure, explicit-only skills, unknown test IDs,
required capability artifacts, optional fallback paths, secrets/forbidden names,
max archive size, and channel evidence independence.

- [ ] **Step 3: Run both modules and confirm failure**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_planner tests.framework.test_hosted_deployment_validation -v
```

Expected: missing planner and validation APIs.

- [ ] **Step 4: Implement deterministic planning and transactional proposals**

```python
@dataclass(frozen=True)
class HostedDeploymentPlan:
    proposal: Mapping[str, object]
    unresolved_codes: tuple[str, ...]


def plan_hosted_deployment(
    application_path: Path,
    operation: str,
    output: Path,
) -> OperationResult:
    application = load_application_config_path(application_path, _repository_root(application_path))
    plan = _build_plan(application, operation)
    _write_new_json_transactionally(output, plan.proposal)
    return _plan_result(plan, output)
```

Enumerate distribution-selected canonical files and `hosted-openai/adapter`
candidates, resolve schema-v3 policies, reject adapter overlap with canonical
implementations, sort all records, and leave suggested decisions unresolved.

- [ ] **Step 5: Implement validation and resolved archive closure**

```python
@dataclass(frozen=True)
class HostedDeploymentValidation:
    contract: HostedDeploymentContract
    archive_paths: tuple[str, ...]
    content_policies: Mapping[str, ResolvedContentPolicy]
    source_paths: Mapping[str, Path]
    local_capabilities: Mapping[str, str]
    hosted_capabilities: Mapping[str, str]
    declared_channels: Mapping[str, str]
    generated_channels: Mapping[str, str]
```

Validate operation-specific identity, complete unique mappings, rights,
manifests, exact skill inventory, explicit-only metadata, tests, capabilities,
fallbacks, secrets, limits, and independent channel evidence. Initialize hosted
capabilities to `NOT VERIFIED` and change only generated OpenAI status to
`PENDING_ACTION`.

- [ ] **Step 6: Export and run planner/validation/content-policy tests**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_planner tests.framework.test_hosted_deployment_validation tests.framework.test_content_policy -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the planning and validation slice**

```powershell
git add src/obvious_one_plugin_framework/hosted_deployment_planner.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_hosted_deployment_planner.py tests/framework/test_hosted_deployment_validation.py
git commit -m "feat: plan and validate hosted deployments"
```

### Task 4: Deterministic complete artifact builder

**Files:**
- Create: `src/obvious_one_plugin_framework/hosted_deployment_builder.py`
- Create: `tests/framework/test_hosted_deployment_builder.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Consumes: `HostedDeploymentValidation` and canonical content policies.
- Produces: `HostedDeploymentBuild` and `build_hosted_deployment(contract: HostedDeploymentContract, output: Path) -> HostedDeploymentBuild`.

- [ ] **Step 1: Write failing deterministic and transactional build tests**

```python
class HostedDeploymentBuilderTests(unittest.TestCase):
    def test_create_builds_complete_artifact_set_without_previous_archive(self) -> None:
        result = build_hosted_deployment(self.create_contract, self.output)
        self.assertEqual(set(path.name for path in self.output.iterdir()), {
            result.archive_path.name,
            "deployment-manifest.json",
            "validation-report.json",
            "deployment-report.json",
        })

    def test_two_builds_are_byte_identical(self) -> None:
        first = build_hosted_deployment(self.contract, self.root / "a")
        second = build_hosted_deployment(self.contract, self.root / "b")
        self.assertEqual(first.artifact_sha256, second.artifact_sha256)
        self.assertEqual(self.tree_bytes(self.root / "a"), self.tree_bytes(self.root / "b"))

    def test_failure_preserves_previous_artifact_directory(self) -> None:
        before = self.tree_bytes(self.output)
        self.break_source_mapping()
        with self.assertRaises(HostedDeploymentError):
            build_hosted_deployment(self.contract, self.output)
        self.assertEqual(self.tree_bytes(self.output), before)
```

Add cases for exact member allowlist, no prior ZIP merge, sorted members, fixed
timestamp `(1980, 1, 1, 0, 0, 0)`, mode `0o100644`, UTF-8 LF text, exact binary
bytes, case-fold collision, maximum bytes, deterministic JSON key ordering, and
no source mutation.

- [ ] **Step 2: Run builder tests and confirm failure**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_builder -v
```

Expected: missing builder API.

- [ ] **Step 3: Implement staged complete ZIP and reports**

```python
@dataclass(frozen=True)
class HostedDeploymentBuild:
    output: Path
    archive_path: Path
    archive_sha256: str
    artifact_sha256: str
    member_count: int
    total_bytes: int


def build_hosted_deployment(
    contract: HostedDeploymentContract,
    output: Path,
) -> HostedDeploymentBuild:
    validation = validate_hosted_deployment(contract)
    stage = _new_sibling_stage(output)
    _write_complete_zip(stage, validation)
    _write_reports(stage, validation)
    built = _audit_stage(stage, validation)
    _replace_directory_transactionally(stage, output)
    return replace(built, output=output, archive_path=output / built.archive_path.name)
```

Use `canonical_content_bytes`, fixed ZIP metadata, sorted members, canonical
newline-terminated JSON, a content-addressed artifact-tree hash, sibling staging,
and recoverable destination swap behavior appropriate to Windows.

- [ ] **Step 4: Export and run builder tests twice**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_builder -v
python -B -m unittest tests.framework.test_hosted_deployment_builder -v
```

Expected: both runs pass with identical hashes.

- [ ] **Step 5: Commit the builder slice**

```powershell
git add src/obvious_one_plugin_framework/hosted_deployment_builder.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_hosted_deployment_builder.py
git commit -m "feat: build complete hosted artifacts"
```

### Task 5: Complete-archive and capability verifier

**Files:**
- Create: `src/obvious_one_plugin_framework/hosted_deployment_verifier.py`
- Create: `tests/framework/test_hosted_deployment_verifier.py`
- Modify: `src/obvious_one_plugin_framework/__init__.py`

**Interfaces:**
- Consumes: built artifact directory, `HostedDeploymentValidation`, `ApplicationConfig`, `VerificationCommand`, and `expand_argv`.
- Produces: `CapabilityEvidence`, `HostedDeploymentVerification`, and `verify_hosted_deployment(contract: HostedDeploymentContract, artifact: Path) -> HostedDeploymentVerification`.

- [ ] **Step 1: Write failing archive, report, and local-execution tests**

```python
class HostedDeploymentVerifierTests(unittest.TestCase):
    def test_verifies_complete_archive_and_reports(self) -> None:
        result = verify_hosted_deployment(self.contract, self.artifact)
        self.assertEqual(result.gates["complete_archive"], "PASS")
        self.assertEqual(result.archive_paths, self.contract_validation.archive_paths)

    def test_local_capability_pass_never_upgrades_hosted_execution(self) -> None:
        result = verify_hosted_deployment(self.contract, self.artifact)
        evidence = result.capabilities["exact-retrieval"]
        self.assertEqual(evidence.local_execution, "STATICALLY VERIFIED")
        self.assertEqual(evidence.hosted_execution, "NOT VERIFIED")

    def test_reports_do_not_claim_external_mutation(self) -> None:
        result = verify_hosted_deployment(self.contract, self.artifact)
        self.assertEqual(result.upload_status, "NOT_PERFORMED")
        self.assertEqual(result.marketplace_status, "NOT_PERFORMED")
        self.assertEqual(result.publication_status, "NOT_PERFORMED")
```

Add tests for extra/missing ZIP members, malformed ZIP, manifest disagreement,
identity/version mismatch, expected skills, explicit-only policy, broken
references/indexes/assets, report hash disagreement, changed artifact after
build, command timeout, clean environment prefixes, failing local test,
`NOT APPLICABLE` local test, optional fallback, and no deletion/retention claim.

- [ ] **Step 2: Run verifier tests and confirm failure**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_verifier -v
```

Expected: missing verifier API.

- [ ] **Step 3: Implement complete-archive and report verification**

```python
@dataclass(frozen=True)
class CapabilityEvidence:
    package_static: str
    local_execution: str
    hosted_execution: str


@dataclass(frozen=True)
class HostedDeploymentVerification:
    artifact_sha256: str
    archive_sha256: str
    archive_paths: tuple[str, ...]
    capabilities: Mapping[str, CapabilityEvidence]
    gates: Mapping[str, str]
    upload_status: str
    installation_status: str
    marketplace_status: str
    publication_status: str
```

Revalidate ZIP safety and exact membership without extracting over existing
paths. Parse manifests and skill metadata, check references and generated JSON
hashes, and compare all values with the approved contract and fresh validation.
Explicitly report hosted installation as `NOT VERIFIED` and external mutations
as `NOT_PERFORMED`.

- [ ] **Step 4: Implement isolated declared product-command execution**

Resolve command IDs only from `ApplicationConfig.verification.commands`. Expand
with `ExpansionContext`, use the application root as working directory, write
captured logs only below an isolated diagnostics root, remove declared clean
environment prefixes, apply a fixed timeout, and reject unsafe log paths. Map a
pass to local `STATICALLY VERIFIED`, no local command to `NOT APPLICABLE`, and a
failure to `capability_local_verification_failed`; never alter hosted state.

- [ ] **Step 5: Export and run verifier/runtime/result tests**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_verifier tests.framework.test_verification_runtime tests.framework.test_results -v
```

Expected: all tests pass and verification leaves the artifact directory
byte-identical.

- [ ] **Step 6: Commit the verifier slice**

```powershell
git add src/obvious_one_plugin_framework/hosted_deployment_verifier.py src/obvious_one_plugin_framework/__init__.py tests/framework/test_hosted_deployment_verifier.py
git commit -m "feat: verify hosted deployment artifacts"
```

### Task 6: CLI commands and stable result mapping

**Files:**
- Modify: `src/obvious_one_plugin_framework/cli.py`
- Modify: `tests/framework/test_cli.py`

**Interfaces:**
- Consumes: all hosted deployment public APIs from Tasks 1 through 5.
- Produces: `plan-hosted-deployment`, `import-hosted-identity`, `validate-hosted-deployment`, `build-hosted-deployment`, and `verify-hosted-deployment` commands.

- [ ] **Step 1: Write failing CLI and exit-code tests**

```python
def test_hosted_create_build_emits_one_ascii_safe_result(self) -> None:
    code, payload = self.invoke(
        "build-hosted-deployment",
        "--contract", str(self.hosted_contract),
        "--output", str(self.output / "hosted"),
        "--json",
    )
    self.assertEqual((code, payload["status"], payload["code"]), (0, "PASS", "hosted_deployment_built"))
    json.dumps(payload, ensure_ascii=True).encode("cp1252")

def test_identity_proposal_is_blocked_but_written(self) -> None:
    code, payload = self.invoke(*self.identity_import_arguments())
    self.assertEqual((code, payload["status"]), (2, "BLOCKED"))
    self.assertEqual(payload["code"], "hosted_identity_approval_required")
    self.assertTrue(self.identity_proposal.is_file())
```

Add cases for parser errors, no interactive input, missing update identity,
blocking decisions, archive safety failure, build/verify failure, environment
I/O failure, output collision, safe diagnostics, relative artifact records, and
separate hosted/local/channel evidence.

- [ ] **Step 2: Run CLI tests and verify unknown-command failure**

```powershell
python -B -m unittest tests.framework.test_cli -v
```

Expected: hosted commands return `invalid_cli_arguments`.

- [ ] **Step 3: Add command parsers and dispatch branches**

Implement these exact argument sets:

```text
plan-hosted-deployment     --application --operation --output --json
import-hosted-identity     --application --archive --output --json
validate-hosted-deployment --contract --json
build-hosted-deployment    --contract --output --json
verify-hosted-deployment   --contract --artifact --json
```

Return relative artifact/mutation records, exact archive/artifact hashes,
operation, identity, member inventory, capability gates, channel declarations,
`upload_status: NOT_PERFORMED`, and the update instruction only for
`OPENAI_HOSTED_UPDATE`.

- [ ] **Step 4: Add stable blocking/error mappings**

Add decision codes to `BLOCKING_CODES`:

```python
{
    "hosted_deployment_decisions_required",
    "hosted_identity_approval_required",
    "hosted_identity_required",
    "hosted_lineage_unresolved",
    "capability_decision_required",
    "required_capability_artifact_missing",
}
```

Handle `HostedDeploymentError` through `_typed_failure`. Keep unsafe archives,
invalid approved records, deterministic mismatches, and failed local tests as
`FAIL` unless their stable code represents an unresolved decision.

- [ ] **Step 5: Run CLI and result suites**

```powershell
python -B -m unittest tests.framework.test_cli tests.framework.test_results -v
```

Expected: all tests pass, every invocation emits one JSON document, and exit
codes remain compatible with the command reference.

- [ ] **Step 6: Commit the CLI slice**

```powershell
git add src/obvious_one_plugin_framework/cli.py tests/framework/test_cli.py
git commit -m "feat: expose hosted deployment commands"
```

### Task 7: Vibe Coding Designer create and update canary

**Files:**
- Create: `applications/vibe-coding-designer/hosted-openai/deployment.json`
- Create: `applications/vibe-coding-designer/hosted-openai/lineage-decision.json`
- Create: `applications/vibe-coding-designer/hosted-openai/adapter/plugin.json`
- Create: `applications/vibe-coding-designer/hosted-openai/adapter/.codex-plugin/plugin.json`
- Create: `applications/vibe-coding-designer/hosted-openai/adapter/skills/instructions/SKILL.md`
- Create: `applications/vibe-coding-designer/hosted-openai/adapter/skills/instructions/agents/openai.yaml`
- Create: `applications/vibe-coding-designer/hosted-openai/adapter/skills/instructions/lookup/knowledge-index.json`
- Create: `applications/vibe-coding-designer/tests/fixtures/hosted-create.json`
- Create: `applications/vibe-coding-designer/tests/fixtures/hosted-update.json`
- Create: `applications/vibe-coding-designer/tests/fixtures/hosted-identity.json`
- Create: `applications/vibe-coding-designer/tests/test_hosted_deployment.py`
- Modify: `applications/vibe-coding-designer/docs/source-decisions.md`
- Modify: `applications/vibe-coding-designer/tests/coverage-matrix.md`

**Interfaces:**
- Consumes: the generic hosted deployment API and Vibe schema-v3 distribution evidence.
- Produces: HOD-A27 through HOD-A29 canary coverage without application logic in generic modules.

- [ ] **Step 1: Write failing Vibe create/update tests**

```python
class VibeHostedDeploymentTests(unittest.TestCase):
    def test_create_builds_seven_native_skills_and_explicit_router(self) -> None:
        contract = load_hosted_deployment_contract(ROOT / "tests/fixtures/hosted-create.json")
        result = build_hosted_deployment(contract, self.output)
        with zipfile.ZipFile(result.archive_path) as archive:
            skills = self.skill_roots(archive.namelist())
            router = archive.read("skills/instructions/agents/openai.yaml").decode("utf-8")
        self.assertEqual(skills, NATIVE_SKILLS | {"instructions"})
        self.assertIn("allow_implicit_invocation: false", router)

    def test_update_preserves_identity_and_general_software_scope(self) -> None:
        contract = load_hosted_deployment_contract(ROOT / "tests/fixtures/hosted-update.json")
        result = build_hosted_deployment(contract, self.output)
        with zipfile.ZipFile(result.archive_path) as archive:
            manifest = json.loads(archive.read("plugin.json"))
            router = archive.read("skills/instructions/SKILL.md").decode("utf-8")
        self.assertEqual(manifest["name"], contract.identity_record.package_name)
        self.assertIn("never assume a Web GUI is required", router)
```

Add tests that adapter paths are limited to two manifests, icon/presentation
assets, and compatibility router; all seven focused skills must be byte-derived
from canonical `skills/`; no scripts, tests, `conversion.json`, or marketplace
metadata enter the hosted archive; complete builds are deterministic.

- [ ] **Step 2: Run the Vibe test and verify missing-declaration failure**

```powershell
python -B -m unittest applications.vibe-coding-designer.tests.test_hosted_deployment -v
```

Expected: failure because the hosted declarations and adapter do not exist.

- [ ] **Step 3: Add approved Vibe adapter and create contract**

Transcribe the already reviewed compatibility decisions into tracked adapter
files without importing the experimental script. The router must contain this
scope rule and explicit-only policy:

```markdown
Routine requests should use one of the seven focused skills directly.
Select the simplest software form that satisfies the goal; never assume a Web
GUI is required. Produce design material rather than implementing the designed
application, and never claim execution or verification without evidence.
```

```yaml
interface:
  display_name: "Vibe Coding Designer Compatibility"
  short_description: "Choose a focused Vibe Coding Designer skill."
  default_prompt: "Use $instructions to choose the appropriate Vibe Coding Designer skill."
policy:
  allow_implicit_invocation: false
```

Build both manifests from the canonical Vibe description, author, license, and
interface. The portable manifest uses
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`; the legacy
manifest declares `skills: "./skills/"`; both use the create contract's package
name and target version. Map the seven native skills from canonical `skills/`,
declare no non-instruction capability, use the canonical Vibe package identity
for the create fixture, and ensure production `deployment.json` contains only
approved create-mode decisions.

- [ ] **Step 4: Add synthetic update fixture and identity evidence**

Use a test-owned identity record with the known hosted package shape and a
synthetic valid digest. The fixture proves update semantics without claiming a
live deployment or committing an exported ZIP. Do not create a production
`hosted-identity.json` until the real `import-hosted-identity` proposal has been
separately reviewed and approved by the decision owner.

- [ ] **Step 5: Record rights and traceability**

Record adapter provenance and redistribution in `docs/source-decisions.md`.
Add HOD-001 through HOD-016 and HOD-A27 through HOD-A29 to the coverage matrix,
including explicit links to create/update tests and general-software scope.

- [ ] **Step 6: Run the full Vibe suite**

```powershell
python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v
```

Expected: all Vibe tests pass, including create, synthetic update, deterministic
artifact bytes, seven canonical skills, explicit-only router, and no forced Web
GUI.

- [ ] **Step 7: Commit only production declarations and new canary tests**

```powershell
git add applications/vibe-coding-designer/hosted-openai applications/vibe-coding-designer/tests/fixtures/hosted-create.json applications/vibe-coding-designer/tests/fixtures/hosted-update.json applications/vibe-coding-designer/tests/fixtures/hosted-identity.json applications/vibe-coding-designer/tests/test_hosted_deployment.py applications/vibe-coding-designer/docs/source-decisions.md applications/vibe-coding-designer/tests/coverage-matrix.md
git commit -m "feat: add Vibe hosted deployment canary"
```

Confirm the two pre-existing experiment files remain unstaged.

### Task 8: Documentation and repository verification integration

**Files:**
- Modify: `docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md`
- Modify: `docs/GPT_TO_PLUGIN_USER_GUIDE.md`
- Modify: `tests/framework/README.md`
- Modify: `scripts/verify_extraction.py`
- Modify: `tests/test_verify_extraction.py`

**Interfaces:**
- Consumes: final hosted commands and Vibe canary.
- Produces: current operator documentation and application-isolated repository gates.

- [ ] **Step 1: Write failing registration and evidence-state tests**

Add a hosted contract to only `plugin-alpha` in `_fixture_repository`, then add
these exact assertions while mocking the hosted verifier at the application
boundary:

```python
def test_hosted_gate_runs_only_for_application_that_owns_contract(self) -> None:
    with tempfile.TemporaryDirectory() as temp:
        repository = _fixture_repository(Path(temp))
        self.add_hosted_create_contract(repository, "plugin-alpha")
        alpha, beta = verifier.discover_applications(repository)
        with patch(
            "scripts.verify_extraction._hosted_deployment_gate",
            return_value=GateResult("hosted-deployment", "PASS", "verified"),
        ) as hosted:
            alpha_result = verifier.run_application(alpha, self.context(repository))
            beta_result = verifier.run_application(beta, self.context(repository))
        self.assertEqual(hosted.call_count, 1)
        self.assertIn("hosted-deployment", [gate.gate_id for gate in alpha_result.gates])
        self.assertNotIn("hosted-deployment", [gate.gate_id for gate in beta_result.gates])

def test_local_hosted_gate_does_not_report_external_actions(self) -> None:
    gate = self.run_fixture_hosted_gate("plugin-alpha")
    self.assertEqual(gate.details["upload"], "NOT PERFORMED")
    self.assertEqual(gate.details["installation"], "NOT VERIFIED")
    self.assertEqual(gate.details["marketplace"], "NOT PERFORMED")
    self.assertEqual(gate.details["public_submission"], "NOT PERFORMED")
```

Add companion cases proving create requires no identity source, update requires
one, and the second application's result is unchanged when the first hosted
gate fails.

- [ ] **Step 2: Run the affected repository test and list current gates**

```powershell
python -B .\scripts\verify_extraction.py --list
```

Expected: hosted deployment gates are absent before registration.

- [ ] **Step 3: Document commands, contracts, and channel boundaries**

Document all five CLI commands, exit codes, create/update selection, optional
identity import, proposal approval, schema-v3 rights reuse, complete-archive
semantics, artifact directory contents, capability evidence, channel statuses,
manual upload instructions, and the difference between
`hosted_deployment_verified` and `READY`.

- [ ] **Step 4: Register application-isolated hosted gates**

Extend `verify_extraction.py` using existing selection/result conventions. Run
hosted verification only when the selected application owns a contract and its
required local inputs are configured. Otherwise report that exact gate as
`NOT VERIFIED`; never use Vibe evidence for Cool or Cool evidence for Vibe.

- [ ] **Step 5: Run repository-contract tests and full discovery**

```powershell
python -B .\scripts\verify_extraction.py --list
python -B -m unittest discover -s .\tests -v
```

Expected: registration and repository tests pass with isolated application
results.

- [ ] **Step 6: Commit documentation and verification integration**

```powershell
git add docs/PLUGIN_AND_FRAMEWORK_COMMAND_REFERENCE.md docs/GPT_TO_PLUGIN_USER_GUIDE.md tests/framework/README.md scripts/verify_extraction.py tests
git commit -m "docs: document hosted deployment workflow"
```

### Task 9: Full verification and completion evidence

**Files:**
- Modify only files needed to correct failures introduced by Tasks 1 through 8.
- Generate output only below ignored `.tmp` and `dist` roots.

**Interfaces:**
- Consumes: complete implementation and Vibe canary.
- Produces: fresh framework, product, deterministic-build, and repository evidence without external mutation.

- [ ] **Step 1: Run all focused hosted framework tests**

```powershell
python -B -m unittest tests.framework.test_hosted_deployment_contract tests.framework.test_hosted_identity tests.framework.test_hosted_deployment_planner tests.framework.test_hosted_deployment_validation tests.framework.test_hosted_deployment_builder tests.framework.test_hosted_deployment_verifier tests.framework.test_cli -v
```

Expected: zero failures and errors.

- [ ] **Step 2: Run the entire generic framework suite**

```powershell
python -B -m unittest discover -s .\tests\framework -v
```

Expected: zero failures and errors.

- [ ] **Step 3: Run the complete Vibe product suite**

```powershell
python -B -m unittest discover -s .\applications\vibe-coding-designer\tests -v
```

Expected: zero failures and errors.

- [ ] **Step 4: Build the Vibe create artifact twice and compare every byte**

```powershell
python -B -m obvious_one_plugin_framework.cli build-hosted-deployment --contract .\applications\vibe-coding-designer\tests\fixtures\hosted-create.json --output .\.tmp\hosted-create-a --json
python -B -m obvious_one_plugin_framework.cli build-hosted-deployment --contract .\applications\vibe-coding-designer\tests\fixtures\hosted-create.json --output .\.tmp\hosted-create-b --json
```

Compare a recursively sorted map of relative path, size, and SHA-256 for both
directories. Expected: exact equality for ZIP and all three JSON reports.

- [ ] **Step 5: Verify create and synthetic update artifacts**

```powershell
python -B -m obvious_one_plugin_framework.cli verify-hosted-deployment --contract .\applications\vibe-coding-designer\tests\fixtures\hosted-create.json --artifact .\.tmp\hosted-create-a --json
python -B -m obvious_one_plugin_framework.cli build-hosted-deployment --contract .\applications\vibe-coding-designer\tests\fixtures\hosted-update.json --output .\.tmp\hosted-update --json
python -B -m obvious_one_plugin_framework.cli verify-hosted-deployment --contract .\applications\vibe-coding-designer\tests\fixtures\hosted-update.json --artifact .\.tmp\hosted-update --json
```

Expected: `hosted_deployment_verified`; hosted execution and installation are
`NOT VERIFIED`; upload, marketplace synchronization, and public submission are
`NOT_PERFORMED`; update instructions target the existing plugin.

- [ ] **Step 6: Run application-aware repository verification and diff hygiene**

```powershell
python -B .\scripts\verify_extraction.py --application vibe-coding-designer
git diff --check
git status --short
```

Expected: applicable gates pass, tests leave tracked files unchanged, and the
two pre-existing untracked experiment files remain untouched.

- [ ] **Step 7: Commit verification-only corrections if required**

If Steps 1 through 6 required reviewed corrections, stage only those correction
files and run:

```powershell
git commit -m "test: verify hosted deployment workflow"
```

If no correction was required, do not create an empty commit.

- [ ] **Step 8: Produce the completion report**

Report HOD requirement coverage, public API and CLI commands, identity-import
behavior, framework/product test counts, exact deterministic hashes, create and
synthetic-update results, capability evidence, Git commits/status, and these
mandatory remaining states:

```text
hosted capability execution      NOT VERIFIED
hosted upload                    NOT VERIFIED
hosted installation              NOT VERIFIED
marketplace synchronization      NOT PERFORMED
public submission                NOT PERFORMED
```

Do not report `READY` or hosted behavioral equivalence.
