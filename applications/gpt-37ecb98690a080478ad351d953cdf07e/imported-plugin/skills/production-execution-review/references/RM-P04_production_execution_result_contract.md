# RM-P04 — Production Execution & Result Contract
## Provider-Neutral Professional Reference for L3 Direct Production Execution, Job Lifecycle, Result Association, and Recovery

**Reference ID:** RM-P04  
**Version:** 1.0-DRAFT  
**Status:** Professional Knowledge Reference — awaiting owner approval  
**Primary behavioral users:** WF-05/L3, WF-06; IM-13, IM-14; supporting IM-10, IM-11, IM-12, IM-15  
**Depends on:** RM-P01 Canonical Production Specification Standard; RM-P02 Portable Production Package Standard; RM-P03 Target Capability & Adaptation Standard  
**Authority scope:** L3 execution eligibility, preflight, approval, submission, job state, partial completion, result association, retry/recovery, execution evidence, and fallback  
**Out of scope:** Specific provider APIs, MCP schemas, SDK implementations, credentials, authentication storage, provider pricing tables, provider-specific polling endpoints

---

# 1. Purpose

RM-P04 defines the professional contract for moving from a **target-ready production export** into actual external video-production execution.

It governs the transition:

> **Approved canonical project**  
> → **Target-aware derived export**  
> → **Preflight**  
> → **Human authorization**  
> → **External production action**  
> → **Job/result lifecycle**  
> → **Result association and review**

RM-P04 exists to prevent a common failure mode:

> treating “we prepared a prompt” or “we submitted something” as equivalent to “the requested production result exists and is valid.”

The standard distinguishes clearly among:

- preparation;
- eligibility;
- authorization;
- submission;
- provider acceptance;
- pending/running state;
- partial completion;
- success;
- failure;
- cancellation;
- result retrieval;
- production acceptance.

---

# 2. Core Principle

Direct production execution is an **optional capability**, never a prerequisite for preserving the project.

If L3 execution cannot proceed, the application must preserve the L1/L2 outputs and fall back cleanly.

Canonical rule:

> **L3 unavailable or blocked → preserve canonical project and target export → offer L2/manual continuation.**

The application must never claim direct execution merely because:

- a provider exists;
- an adapter exists;
- a target export exists;
- a request payload was created;
- a local helper script exists;
- a tool binding is documented.

Execution claims require runtime evidence.

---

# 3. Execution Preconditions

Before an external production action may be initiated, the application must establish that all required preconditions are satisfied.

Preconditions fall into five categories:

1. **Project state**
2. **Target compatibility**
3. **Asset readiness**
4. **Runtime/external capability**
5. **Human authorization**

---

# 4. Project-State Preconditions

The source scene or project must be in an approved production state.

Typical requirements:

- Director Project approved for production;
- canonical Production Specification current;
- target export derived from current canonical revision;
- no blocking stale/superseded relationship;
- no unresolved REQUIRED production dependency.

A stale target export must not be submitted as though it were current.

---

# 5. Target-Compatibility Preconditions

The target-aware export must have a compatibility state from RM-P03.

Execution should normally require:

- `FULLY_SUPPORTED`, or
- `PARTIALLY_SUPPORTED` with accepted degradations.

Execution must not silently proceed when:

- a REQUIRED canonical requirement is `UNSUPPORTED`;
- capability is `TARGET_CAPABILITY_UNVERIFIED` and the uncertainty is material;
- target profile is stale and materially affects execution validity.

A user may explicitly accept some degradations, but accepted degradation must be recorded.

---

# 6. Asset Preconditions

All required production assets must be ready and resolvable.

Examples:

- Start Frame;
- End Frame;
- character reference;
- source video;
- voice reference;
- audio;
- target-specific uploaded asset;
- required prior-scene result.

Asset state should support at least:

- `READY`
- `MISSING`
- `PENDING`
- `STALE`
- `INVALID`
- `UNRESOLVABLE`

A REQUIRED asset that is not READY normally blocks direct execution.

---

# 7. Runtime Capability Preconditions

The application must verify that an executable capability actually exists in the current environment.

Possible realizations include:

- connected external tool;
- MCP-exposed action;
- registered runtime-native capability;
- approved API bridge;
- supported local runtime tool;
- another valid execution mechanism.

RM-P04 does not prescribe which mechanism is used.

The critical rule is:

> **Declared capability is not sufficient; installed/runtime availability must be established.**

Recommended execution-capability states:

- `AVAILABLE`
- `AVAILABLE_WITH_LIMITATIONS`
- `UNAVAILABLE`
- `AUTH_REQUIRED`
- `MISCONFIGURED`
- `UNKNOWN`

---

# 8. Authentication and Authorization Boundary

Authentication and user authorization are distinct.

## 8.1 Authentication

Authentication answers:

> Can the runtime identify itself to the external service?

Examples:

- API key;
- OAuth;
- provider account connection;
- session token.

Authentication details must not be embedded into portable project artifacts or professional references.

## 8.2 User authorization

User authorization answers:

> Has the user approved this specific consequential action?

The application must not treat successful provider authentication as permission to spend credits, upload assets, or start jobs.

---

# 9. Human Approval Gate

Before consequential L3 execution, the user must receive enough information to make a meaningful decision.

The approval summary should include, as applicable:

- target provider/service/model or capability;
- affected scene(s);
- source project revision;
- target export revision;
- key production settings;
- material degradations;
- assets to be uploaded;
- expected external action;
- known cost/credit implications when available;
- privacy or data-transfer consequence when material.

Then the application must wait for explicit approval.

Silence is not approval.

---

# 10. Approval State

Recommended semantic states:

- `NOT_REQUESTED`
- `AWAITING_APPROVAL`
- `APPROVED`
- `REJECTED`
- `EXPIRED`
- `INVALIDATED_BY_CHANGE`

Approval should become invalid if a material input changes after approval, such as:

- target changed;
- scene revision changed;
- material degradation changed;
- assets changed;
- cost-relevant setting changed.

---

# 11. Execution Request

A direct-execution request should be created from:

1. canonical Production Specification;
2. target-aware derived export;
3. accepted degradation decisions;
4. runtime capability context;
5. user authorization state.

The execution request is a derived artifact.

It is not canonical project data.

---

# 12. Execution Request Identity

Every production action should have a stable local execution-request identity before submission.

Conceptual fields:

- `execution_request_id`
- source project revision
- source scene revision
- target export ID/revision
- target identity
- requested action
- requested settings
- approval record
- asset list
- creation time

This identity allows retries and results to be tracked even if the provider does not immediately return a job ID.

---

# 13. Submission States

Recommended submission lifecycle:

## 13.1 PREPARED

Execution request exists but has not been submitted.

## 13.2 APPROVED_FOR_SUBMISSION

Required user approval exists and remains valid.

## 13.3 SUBMITTING

The runtime is attempting to initiate the external action.

## 13.4 SUBMITTED

The external service has accepted the request sufficiently to return confirmation or a job/result identifier.

## 13.5 SUBMISSION_FAILED

The request could not be accepted by the external service.

Submission success is distinct from generation success.

---

# 14. External Job States

When the provider exposes asynchronous job state, normalize it into provider-neutral semantics.

Recommended states:

- `QUEUED`
- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `PARTIALLY_SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `EXPIRED`
- `UNKNOWN`

Provider-specific states may be mapped into these normalized states.

---

# 15. Synchronous Execution

Some targets may return a result directly without exposing an asynchronous job.

In that case, the application may transition:

`SUBMITTING → SUCCEEDED`

provided actual result evidence is returned.

A successful HTTP/tool response without a production result is not enough to classify the production result as SUCCEEDED.

---

# 16. Result Identity

Every returned production artifact should receive a stable result identity.

Conceptual semantics:

- `result_id`
- execution request ID
- provider job ID if any
- source project revision
- source scene revision
- target export revision
- produced asset(s)
- result state
- retrieval time
- provider metadata
- provenance

Generated assets may include:

- video clip;
- image;
- audio;
- subtitles;
- metadata;
- composite result.

---

# 17. Result States

Recommended result states:

- `NOT_AVAILABLE`
- `AVAILABLE`
- `PARTIAL`
- `CORRUPT`
- `UNRETRIEVABLE`
- `SUPERSEDED`
- `REJECTED_AFTER_REVIEW`
- `ACCEPTED_FOR_PRODUCTION`

Important distinction:

> `SUCCEEDED` execution does not imply `ACCEPTED_FOR_PRODUCTION`.

A provider may generate a technically valid clip that fails the director's creative requirements.

---

# 18. Partial Completion

Partial completion must be represented explicitly.

Examples:

- 4 of 6 scenes completed;
- video generated but audio failed;
- clip generated but result retrieval failed;
- scene generated but one required output variant missing.

The application must not summarize a partially completed production run as fully complete.

A partial run should identify:

- completed items;
- failed items;
- pending items;
- retryable items;
- non-retryable items.

---

# 19. Batch Execution

When multiple scenes are executed together, each scene should retain independent state.

Do not use only one global state such as:

`PROJECT_JOB = FAILED`

when:

- S01 succeeded;
- S02 succeeded;
- S03 failed;
- S04 pending.

The project-level state should summarize scene-level states without erasing them.

---

# 20. Idempotency and Duplicate Submission

Where possible, the execution layer should avoid accidental duplicate external jobs.

Potential mechanisms include:

- stable execution request ID;
- provider idempotency key;
- local duplicate detection;
- confirmation before retry when job state is uncertain.

RM-P04 does not mandate one mechanism.

The professional rule is:

> uncertain submission state should not trigger blind duplicate re-submission.

---

# 21. Retry Classification

Failures should be classified before retry.

Recommended retry classes:

## 21.1 TRANSIENT_RETRYABLE

Examples:

- temporary provider outage;
- rate limit;
- network timeout;
- provider queue overload.

## 21.2 INPUT_CORRECTION_REQUIRED

Examples:

- invalid file format;
- missing required asset;
- unsupported parameter.

## 21.3 AUTHENTICATION_REQUIRED

Examples:

- expired credentials;
- unconnected account.

## 21.4 APPROVAL_REQUIRED

Examples:

- material parameter changed;
- cost consequence changed;
- degradation changed.

## 21.5 NON_RETRYABLE

Examples:

- provider policy rejection;
- unsupported required capability;
- invalid project state.

## 21.6 UNKNOWN_FAILURE

Cause is not sufficiently established.

---

# 22. Retry Rules

A retry should preserve provenance.

A retry must identify:

- original execution request;
- retry sequence;
- changed inputs if any;
- reason for retry;
- whether new user approval is required.

If retry changes a material target input, it may require a new target export or renewed approval.

---

# 23. Recovery from Ambiguous Submission

A particularly dangerous state is:

> the local runtime timed out, but the provider may actually have accepted the job.

The application should avoid immediately submitting again.

Recommended recovery:

1. check for returned job ID;
2. query provider state if possible;
3. inspect provider-side history if available;
4. mark state `UNKNOWN` if unresolved;
5. ask user before potentially duplicating a costly job.

---

# 24. Cancellation

When the target supports cancellation, the application may offer it.

Cancellation state should distinguish:

- cancellation requested;
- cancellation confirmed;
- provider cannot cancel;
- cancellation failed;
- job completed before cancellation.

A local cancellation request does not prove provider cancellation.

---

# 25. Result Retrieval

When a job succeeds, the application should retrieve or record enough result information to preserve production continuity.

Possible result information:

- downloadable asset reference;
- provider-hosted asset ID;
- media metadata;
- duration;
- dimensions;
- audio presence;
- generation metadata;
- result checksum when appropriate.

The result may be embedded into an updated portable package or referenced externally.

---

# 26. External Result References

If a result remains provider-hosted, record:

- provider result ID;
- retrieval URL/reference where allowed;
- access requirements;
- expiration information when known;
- whether the reference is portable.

Do not represent temporary provider-hosted URLs as permanently portable assets.

---

# 27. Result Provenance Chain

The minimum provenance chain should be:

> Canonical Project  
> → Canonical Scene  
> → Target Export  
> → Execution Request  
> → External Job  
> → Generated Result

Each link should preserve identifiers or equivalent traceability.

---

# 28. Production Result Review

After a result is available, use RM-P01 canonical intent and relevant creative references to evaluate fidelity.

Review dimensions may include:

- scene purpose;
- visual fidelity;
- camera fidelity;
- motion fidelity;
- performance fidelity;
- dialogue/audio fidelity;
- style fidelity;
- continuity fidelity.

The review may result in:

- `ACCEPT`
- `REGENERATE`
- `ADJUST_TARGET_ADAPTATION`
- `REVISE_CANONICAL_PRODUCTION_SPEC`
- `RETURN_TO_CREATIVE_DIRECTION`

---

# 29. Acceptance vs Technical Success

Technical generation success answers:

> Did the provider produce a result?

Production acceptance answers:

> Is this result acceptable for the intended project?

These must remain separate.

Recommended semantics:

```yaml
execution:
  state: SUCCEEDED

result:
  state: AVAILABLE

production_review:
  decision: REGENERATE
```

This is a valid state.

---

# 30. L3 Fallback to L2

If any of the following prevents direct execution:

- executable runtime unavailable;
- authentication unavailable;
- provider action blocked;
- approval denied;
- required asset unavailable;
- direct API/tool unavailable;
- execution capability unverifiable;

the application should preserve:

- canonical Production Specification;
- target compatibility assessment;
- target export;
- manual instructions.

Then offer L2/manual continuation.

---

# 31. Execution Evidence Standard

Execution evidence should be classified carefully.

Recommended evidence levels:

## 31.1 PREPARED_ONLY

A target request or payload exists.

No external action has been proven.

## 31.2 SUBMISSION_EVIDENCED

The external service acknowledged request acceptance.

## 31.3 JOB_STATE_EVIDENCED

A provider/runtime job state has been observed.

## 31.4 RESULT_EVIDENCED

A production result has been retrieved or directly observed.

## 31.5 RESULT_REVIEWED

The result has been compared against canonical production intent.

Do not collapse these evidence states into a generic “done.”

---

# 32. Verification Language

Use explicit language.

Good:

- “Target export prepared.”
- “Submission accepted; job pending.”
- “Generation succeeded; result retrieved.”
- “Result retrieved but not yet reviewed.”
- “Direct execution unavailable; L2 export preserved.”

Avoid:

- “Video generated” when only request preparation occurred.
- “Done” when result retrieval is pending.
- “Verified” when only static bindings exist.

---

# 33. Execution-State Example

Illustrative:

```yaml
execution_request:
  id: EX-S03-004
  source_project_revision: 1.4
  source_scene_revision: 2
  target_export: EXP-S03-X02
  approval_state: APPROVED
  state: SUBMITTED

external_job:
  provider_job_id: JOB-88217
  state: RUNNING

result:
  state: NOT_AVAILABLE

evidence:
  level: JOB_STATE_EVIDENCED
```

Later:

```yaml
execution_request:
  id: EX-S03-004
  state: SUBMITTED

external_job:
  provider_job_id: JOB-88217
  state: SUCCEEDED

result:
  id: RES-S03-009
  state: AVAILABLE
  asset_ref: VIDEO-S03-009

evidence:
  level: RESULT_EVIDENCED

production_review:
  decision: REGENERATE
  reason: "Camera motion is too fast and facial recognition beat is weak."
```

---

# 34. Batch Execution Example

```yaml
batch:
  id: BATCH-02
  scenes:
    S01:
      job_state: SUCCEEDED
      result_state: ACCEPTED_FOR_PRODUCTION
    S02:
      job_state: SUCCEEDED
      result_state: AVAILABLE
    S03:
      job_state: FAILED
      retry_class: TRANSIENT_RETRYABLE
    S04:
      job_state: RUNNING

summary:
  total: 4
  accepted: 1
  available_unreviewed: 1
  failed: 1
  running: 1
  overall: PARTIAL
```

---

# 35. Cost and Credit Awareness

When external action may consume credits or incur cost, the application should:

- disclose known cost-relevant settings where practical;
- avoid pretending to know pricing when it cannot verify it;
- include cost impact in approval when material;
- avoid blind retries that may duplicate paid jobs.

RM-P04 does not define provider pricing.

---

# 36. Privacy and Data Transfer

Before external execution, the application should recognize whether production assets may leave the current environment.

Potentially sensitive assets include:

- user-uploaded images;
- voice recordings;
- private story materials;
- proprietary characters;
- unpublished scripts.

When external transfer is consequential, approval should cover that action.

---

# 37. Provider Policy Rejection

A provider may reject a request because of policy.

The application should:

1. preserve the canonical project;
2. record the rejection at execution layer;
3. avoid rewriting canonical creative intent automatically;
4. explain available alternatives;
5. allow target change or project revision.

Provider rejection is not automatically a canonical project defect.

---

# 38. Execution Invariants

The following are normative.

## EI-01 — No execution without valid source

Direct execution must derive from a current canonical source and target export.

## EI-02 — No consequential execution without approval

Required human approval must be valid at submission time.

## EI-03 — No false execution claim

Prepared payload ≠ submitted job.

Submitted job ≠ successful result.

Successful result ≠ accepted production result.

## EI-04 — Preserve provenance

Every job/result must remain traceable to canonical source.

## EI-05 — Preserve partial state

Partial completion must not be summarized as complete.

## EI-06 — Preserve fallback

L3 failure/unavailability must not destroy L1/L2 usability.

## EI-07 — No blind duplicate retry

Ambiguous submission should be resolved before retry where possible.

## EI-08 — External credentials remain external

Portable packages and professional references must not embed secrets.

---

# 39. Anti-Patterns

## 39.1 Payload-equals-execution

Bad:

“Request JSON is ready, therefore video generation is complete.”

Correct:

Prepared request only proves PREPARED_ONLY.

---

## 39.2 Provider acceptance equals success

Bad:

Provider returned job ID, therefore clip is done.

Correct:

Job ID proves SUBMISSION_EVIDENCED.

---

## 39.3 Success equals acceptance

Bad:

Provider produced a clip, therefore scene is approved.

Correct:

Production result must still be reviewed.

---

## 39.4 Blind retry

Bad:

Timeout occurred → immediately submit same paid job again.

Correct:

Resolve ambiguous state where possible.

---

## 39.5 Global-state collapse

Bad:

“Batch failed” when only one of ten scenes failed.

Correct:

Preserve scene-level result states.

---

## 39.6 Credential leakage

Bad:

Store API key in production package or target export.

Correct:

Keep authentication external.

---

## 39.7 Silent fallback

Bad:

Direct execution fails, application quietly downgrades to manual without telling user.

Correct:

Explain L3 failure/unavailability and offer L2 fallback explicitly.

---

# 40. Relationship to RM-P01

RM-P01 defines canonical production meaning.

RM-P04 must never change canonical meaning merely because external execution failed.

---

# 41. Relationship to RM-P02

RM-P02 defines the portable package.

Execution metadata/results may later be associated with or added to an updated package, but L1 portability must remain intact without L3.

---

# 42. Relationship to RM-P03

RM-P03 defines target compatibility and target-ready derived export.

RM-P04 should normally execute only from a target export that has passed compatibility assessment.

---

# 43. Relationship to RM-P05

RM-P05 defines long-lived identity, provenance, stale/superseded state, and asset lineage.

RM-P04 provides the execution/job/result state events that RM-P05 records across revisions.

---

# 44. Consultation Guidance for the Application

Consult RM-P04 whenever the application:

- prepares to initiate direct production;
- checks L3 execution eligibility;
- asks for user approval before external action;
- creates an execution request;
- submits an external job;
- tracks job state;
- handles partial completion;
- handles retry/recovery;
- handles cancellation;
- retrieves a result;
- records result provenance;
- distinguishes technical success from production acceptance;
- falls back from L3 to L2.

Do not use RM-P04 as authority for:

- target capability facts;
- canonical production semantics;
- package structure.

Those belong to RM-P01, RM-P02, and RM-P03.

---

# 45. Professional Standard Summary

A professional direct-production execution layer must be:

- **approval-gated**
- **runtime-evidenced**
- **stateful**
- **traceable**
- **retry-aware**
- **duplicate-safe**
- **partial-result aware**
- **cost-aware when possible**
- **privacy-aware**
- **provider-neutral at the contract level**
- **honest about uncertainty**
- **separate from production acceptance**
- **safe to fall back to L2**

The canonical question is not:

> “Did we call the API?”

It is:

> **“Was the correct approved production request submitted through a real executable capability, what happened to that job, what result was actually returned, how is it traced back to the canonical project, and has that result been accepted for production?”**
