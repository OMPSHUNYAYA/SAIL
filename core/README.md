# **SAIL v5.9.0 Core Runtime**

## **Evidence Integrity Runtime**

**Structural AI Layer**

**One Structural Foundation. Infinite Manifestations.**

---

## **Purpose**

This directory contains the executable **SAIL v5.9.0 Evidence Integrity Runtime** and its core validation artifacts.

For the complete project introduction, architecture, structural philosophy, reference applications, documentation, license, and roadmap, see the repository-level README.

---

## **Core Files**

* `SAIL_v5_9_0_Evidence_Integrity_Runtime.html`
* `README.md`
* `SAIL_v5_9_0_console_tests.txt`
* `SAIL_v5_9_0_behavioral_oracles.json`
* `sail_v5_9_0_runtime_behavior_test.py`
* `sail_v5_9_0_source_integrity_test.py`
* `SHA256SUMS.txt`

`SHA256SUMS.txt` records hashes for the execution-critical core files.

A matching checksum confirms file identity against the supplied manifest.

It does not prove behavioral validity.

`matching checksum != behavioral validity`

---

## **Validated Core Status**

* Runtime version: **5.9.0**
* Certified structural layers: **37**
* Synthetic structural conformance executions: **347,400**
* Independent behavioral specifications: **96**
* Behavioral failures: **0**
* Controlled source-mutation operators: **5**
* Controlled source mutations detected: **5**
* Supplemental environment-isolation checks: **7**
* Environment-isolation failures: **0**
* Realization-audit cases: **48,600**
* Legacy structural-federation audit cases: **450**
* Federation-network audit checks: **43,200**
* Evidence validation: **PASS**
* Runtime behavioral validation: **PASS**
* Source and release-package integrity: **PASS**

---

## **Structural Chain**

`Input -> Structure -> Invariant -> Reasoning -> Evidence -> Certificate -> Execution -> Measurement -> Outcome -> Realization Certificate`

Realization chain:

`Requirement -> Workflow -> Execution -> Measurement -> Outcome -> Realization Certificate`

Primary invariant:

`same structure -> same evidence -> same certificate -> same replayable outcome`

---

# **Evidence Model**

## **Synthetic Structural Conformance**

Classification:

`SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS`

Execution count:

`347400`

The synthetic conformance audit validates:

* deterministic canonicalization
* structural hashing
* cloning and round-trip consistency
* certificate stability
* replay consistency
* component integration
* structural self-consistency
* expected execution-count integrity

The **347,400** figure represents total synthetic execution volume over bounded structural case-template sets.

It does not represent **347,400 distinct input structures, unique scenarios, or independent behavioral specifications**.

Some audit families repeatedly cycle through their available structural templates until their configured execution totals are reached. This tests deterministic stability and replay consistency under repetition.

`synthetic execution count != unique template count`

`synthetic execution count != independent behavioral specification count`

---

## **Independent Behavioral Validation**

Audit mode:

`independent_behavioral_specification_audit`

Oracle origin:

`EXTERNALLY_SPECIFIED_LITERAL_EXPECTATIONS`

Specification count:

`96`

Execution count:

`96`

The behavioral specifications cover:

* arithmetic and formula evaluation
* constraint resolution
* bounded proof checking
* contradiction detection
* malformed-input abstention
* identity and permission behavior
* persistence and tamper rejection
* federation quorum boundaries
* realization thresholds
* missing realization evidence
* exact-boundary behavior
* metamorphic invariants

Expected results are defined independently from the runtime parser and resolver.

The external runtime test additionally executes **7 supplemental environment-isolation checks**.

These checks are separate from, and are not included in, the **96 independently specified behavioral specifications**.

`behavioral specification count = 96`

`environment-isolation check count = 7`

---

## **Controlled Mutation Sensitivity**

Controlled source-mutation operators:

`5`

The executable test applies mutations affecting:

* arithmetic results
* date-contradiction handling
* inventory boundaries
* federation quorum boundaries
* realization thresholds

Required result:

`source_mutations_detected = source_mutation_operators`

Expected:

`5 = 5`

Detection of these five supplied operators demonstrates sensitivity to those mutations.

It does not establish exhaustive defect detection.

---

# **Core Validation**

Open:

`SAIL_v5_9_0_Evidence_Integrity_Runtime.html`

Run in the browser developer console:

```javascript
[
  SAIL.version(),
  SAIL.certify().certified,
  SAIL.certify().layers,
  SAIL.conformanceAudit().allPass,
  SAIL.conformanceAudit().conformance_execution_count,
  SAIL.behaviorAudit().allPass,
  SAIL.behaviorAudit().specification_count,
  SAIL.behaviorAudit().failed_count,
  SAIL.evidenceValidation().allPass,
  SAIL.realizationAudit().allPass,
  SAIL.realizationAudit().case_count,
  SAIL.federationAudit().allPass,
  SAIL.federationAudit().case_count,
  SAIL.federationNetworkAudit().allPass,
  SAIL.federationNetworkAudit().case_count
]
```

Expected:

```javascript
[
  "5.9.0",
  true,
  37,
  true,
  347400,
  true,
  96,
  0,
  true,
  true,
  48600,
  true,
  450,
  true,
  43200
]
```

**Federation API distinction**

`SAIL.federationAudit().case_count = 450`

`SAIL.federationNetworkAudit().case_count = 43200`

`SAIL.federationAudit()` is the legacy structural-federation audit.

`SAIL.federationNetworkAudit()` validates the federation-network runtime.

The two APIs and counts must not be conflated.

---

## **Evidence Profile**

Run:

```javascript
SAIL.evidenceProfile()
```

Expected core fields:

```javascript
{
  version: "5.9.0",
  conformance_classification:
    "SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS",
  synthetic_conformance_execution_count: 347400,
  behavioral_specification_count: 96,
  behavioral_execution_count: 96,
  independent_oracle: true,
  external_mutation_operator_count: 5,
  third_party_certification: false
}
```

The profile must preserve the distinction between synthetic conformance volume and independent behavioral evidence.

---

# **Executable Validation**

The executable behavioral test:

* launches the HTML runtime in Chromium
* invokes the public SAIL APIs
* executes all **96 independent behavioral specifications**
* compares observed and expected results
* applies the **5 controlled source mutations**
* verifies that all controlled mutations are detected
* executes **7 supplemental environment-isolation checks**
* verifies that environment-dependent expressions produce `ABSTAIN`
* verifies certificate stability after browser-environment changes
* verifies evidence and conformance counts

Install the dependency once:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Run:

```bash
python sail_v5_9_0_runtime_behavior_test.py
```

Expected core results:

```text
version: 5.9.0
external_behavioral_oracles: 96
behavioral_failures: 0
synthetic_conformance_executions: 347400
source_mutation_operators: 5
source_mutations_detected: 5
environment_isolation_checks: 7
environment_isolation_failures: 0
status: PASS
```

Environment-isolation boundary:

`environment-dependent expression -> ABSTAIN`

`undeclared identifier -> ABSTAIN`

`property or constructor access -> ABSTAIN`

`same rejected expression + changed browser environment -> same rejection state + same certificate`

---

## **Source and Release-Package Integrity**

Run:

```bash
python sail_v5_9_0_source_integrity_test.py
```

Expected:

```text
SAIL v5.9.0 source and release-package integrity checks passed
```

The source-integrity test verifies:

* release identity
* required runtime files
* required public API bindings
* expected evidence classifications
* expected evidence-validation counts
* behavioral-oracle consistency
* required runtime markers
* bounded environment-isolated expression-evaluator markers
* integration of supplemental environment-isolation validation
* absence of unrestricted `Function(...)` expression evaluation
* prohibited fail-open release patterns
* synchronization of core validation artifacts

It complements executable runtime validation but does not replace it.

---

# **Structural Realization**

The realization runtime connects certified workflow structure to measurable outcomes.

Core rule:

`realization_certified iff required_structure_complete AND outcome_criteria_satisfied`

The runtime distinguishes:

`workflow_executed != outcome_realized`

`result_exists != result_certified`

`transition_requested != transition_admitted`

`structural_identity != operational_record_identity`

Primary realization APIs:

* `SAIL.realizationRuntime(input, options)`
* `SAIL.realize(input, options)`
* `SAIL.measureOutcome(input, options)`
* `SAIL.verifyOutcome(input, options)`
* `SAIL.realizationCertificate(input, options)`
* `SAIL.outcomeLedger(input, options)`
* `SAIL.realizationReplay(input, options)`
* `SAIL.realizationAudit()`

---

# **Evidence and Release APIs**

Evidence APIs:

* `SAIL.conformanceAudit()`
* `SAIL.behaviorAudit()`
* `SAIL.behaviorSpecifications()`
* `SAIL.evidenceValidation()`
* `SAIL.evidenceProfile()`

Release APIs:

* `SAIL.version()`
* `SAIL.certify()`
* `SAIL.verify()`
* `SAIL.benchmark()`
* `SAIL.releaseManifest()`
* `SAIL.layerRegistry()`

The backward-compatible `SAIL.benchmark()` interface reports the synthetic conformance execution count.

`SAIL.benchmark().benchmark_case_count = 347400`

This value represents repeated synthetic conformance execution volume, not independent behavioral coverage.

Federation audit APIs:

* `SAIL.federationAudit()`
* `SAIL.federationNetworkAudit()`

The legacy structural-federation audit reports **450 cases**.

The federation-network audit reports **43,200 checks**.

`SAIL.federationAudit().case_count = 450`

`SAIL.federationNetworkAudit().case_count = 43200`

The APIs and counts must not be conflated.

---

# **Certification Explorer**

The Certification Explorer displays:

`VALIDATING_EVIDENCE`

during first-run evidence initialization.

After validation completes, it exposes the current certificate, evidence profile, dependencies, replay state, and release manifest.

Subsequent openings may use cached validation results.

Explorer controls:

* **Open Certification Explorer**
* **Return to Workspace**

---

# **Certification Boundary**

SAIL certification denotes internal structural conformance and independently specified behavioral validation within the supplied reference implementation.

It is not:

* third-party certification
* regulatory certification
* safety certification
* security certification
* compliance certification
* standards-body certification
* proof of exhaustive behavioral coverage
* proof that no implementation defects remain

A SAIL certificate is a deterministic runtime object binding visible structural input, evidence, resolution state, and replay identity within the documented runtime boundary.

`documented claim scope <= validated evidence scope`

---

# **Core Principles**

`same structural payload -> same structural identity`

`same structure -> same evidence -> same certificate`

`same certified structure -> same replay result`

`separate runtime record -> separate operational identity`

`operational metadata excluded -> structural certificate remains stable`

`changed structural input -> dependent certificates reset`

`downstream certification allowed iff required upstream structures are certified`

`repeat accepted transition -> same certificate + unchanged transition timestamp`

---

## **SAIL v5.9.0**

**Deterministic Structure**

**Independent Behavioral Evidence**

**Replayable Certification**

**Measurable Realization**

**One Structural Foundation. Infinite Manifestations.**
