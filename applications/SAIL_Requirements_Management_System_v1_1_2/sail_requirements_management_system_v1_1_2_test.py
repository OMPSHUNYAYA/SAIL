from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_Requirements_Management_System_v1_1_2.html"

if not HTML.exists():
    raise FileNotFoundError(f"Missing application file: {HTML}")

html = HTML.read_text(encoding="utf-8")

source_checks = {
    "release title": "SAIL Requirements Management System v1.1.2" in html,
    "html title": "<title>SAIL Requirements Management System v1.1.2</title>" in html,
    "application version": 'const VERSION="1.1.2";' in html,
    "sail version": 'const SAIL_VERSION="5.9.0";' in html,
    "layer count": "const LAYERS=37;" in html,
    "conformance count": "const CONFORMANCE_EXECUTIONS=347400;" in html,
    "behavioral count": "const BEHAVIORAL_SPECIFICATIONS=96;" in html,
    "mutation operators": "const SOURCE_MUTATION_OPERATORS=5;" in html,
    "mutations detected": "const SOURCE_MUTATIONS_DETECTED=5;" in html,
    "realization audit count": "const REALIZATION_AUDIT=48600;" in html,
    "application audit count": "const EXPECTED_AUDIT_CASES=12000;" in html,
    "audit scenarios": "const AUDIT_SCENARIOS=8;" in html,
    "audit iterations": "const ITERATIONS_PER_SCENARIO=1500;" in html,
    "priority admission": 'const PRIORITIES=["LOW","MEDIUM","HIGH","CRITICAL"];' in html,
    "policy admission": 'const POLICIES=["standard_review","security_review","audit_review","release_gate"];' in html,
    "deep freeze": "function deepFreeze(value)" in html,
    "snapshot clone": "function clone(value)" in html,
    "monotonic record function": "function newRecordId()" in html,
    "monotonic record format": 'return "REQREC-"+String(recordSequence).padStart(12,"0");' in html,
    "record format validation": '/^REQREC-\\d{12}$/' in html,
    "requirement identity": "function requirementId(input)" in html,
    "requirement certificate": "function requirementCertificateValue(input)" in html,
    "policy certificate": "function policyCertificateValue(requirementCertificate,policy)" in html,
    "trace certificate": "function traceCertificateValue(requirementCertificate,policyCertificate,measurement)" in html,
    "approval certificate": "function approvalCertificateValue(item)" in html,
    "realization certificate": "function realizationCertificateValue(item)" in html,
    "invalid fields": "invalid_fields:invalidFields" in html,
    "invalid priority rejection": 'invalidFields.push("priority")' in html,
    "invalid policy rejection": 'invalidFields.push("policy")' in html,
    "null incomplete certificate": "const requirementCertificate=certified?requirementCertificateValue(normalized):null;" in html,
    "certification integrity": "function certificationIntegrity(item)" in html,
    "approval integrity": "function approvalIntegrity(item)" in html,
    "realization integrity": "function realizationIntegrity(item)" in html,
    "public integrity api": "integrity:integrity" in html,
    "approval integrity block": "APPROVAL_BLOCKED_INTEGRITY_REQUIRED" in html,
    "realization integrity block": "REALIZATION_BLOCKED_INTEGRITY_REQUIRED" in html,
    "trace invalid state": "REQUIREMENT_TRACE_CHAIN_INVALID" in html,
    "trace certified state": "REQUIREMENT_TRACE_CHAIN_CERTIFIED" in html,
    "trace progress state": "REQUIREMENT_TRACE_CHAIN_IN_PROGRESS" in html,
    "chain certified field": "chain_certified:chainCertified" in html,
    "chain integrity reason": "integrity_reason:chainCertified?null:lifecycle.reason" in html,
    "null incomplete chain": ":null\n    });\n  }\n\n  function escapeHtml" in html,
    "pack classifier": "function classifyPack(items)" in html,
    "pack certified state": "REQUIREMENTS_PACK_CERTIFIED" in html,
    "pack unresolved state": "REQUIREMENTS_PACK_UNRESOLVED" in html,
    "pack incomplete state": "REQUIREMENTS_PACK_INCOMPLETE" in html,
    "pack empty state": "REQUIREMENTS_PACK_EMPTY" in html,
    "pack certified field": "pack_certified:classification.certified" in html,
    "pack integrity reason": "integrity_reason:classification.reason" in html,
    "structural payload": "structural_payload:" in html,
    "operational metadata": "operational_metadata:" in html,
    "record exclusion": "record_id_fields_excluded_from_certificates:true" in html,
    "timestamp exclusion": "timestamp_fields_excluded_from_certificates:true" in html,
    "audit snapshot": "return clone(AUDIT_RESULT);" in html,
    "current snapshot": "current:function(){return clone(selectedInternal());}" in html,
    "certify snapshot": "certify:function(input){return clone(deriveRequirement(input));}" in html,
    "export snapshot": "return clone(pack);" in html,
    "new requirement button": 'onclick="SAIL_REQ.newRequirement()"' in html,
    "new requirement function": "function newRequirement()" in html,
    "public new requirement api": "newRequirement:newRequirement" in html,
    "explicit selection only": "return requirements.find(item=>item.record_id===selectedRecordId)||null;" in html,
    "examples create new records": "function loadExample(kind){\n    newRequirement();" in html,
    "local classification": 'classification:"LOCAL_APPLICATION_CONFORMANCE_EXECUTIONS"' in html,
    "local execution": 'application_audit_execution:"LOCAL_RUNTIME"' in html,
    "referenced conformance": 'conformance_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced behavior": 'behavioral_validation:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced evidence": 'evidence_validation:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced realization": 'realization_audit_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "no random identity": "Math.random" not in html and "crypto.randomUUID" not in html,
    "no time identity": "performance.now" not in html and "time:Date.now()" not in html,
    "no old sail version": "5.8.1" not in html,
    "no old app version": "1.1.1" not in html and "v1.1.1" not in html,
    "no todo": "TODO" not in html,
    "no fixme": "FIXME" not in html,
    "no html comments": "<!--" not in html,
    "no block comments": "/*" not in html,
    "no line comments": not bool(re.search(r"(^|\s)//", html)),
}

failed_source = [name for name, passed in source_checks.items() if not passed]
if failed_source:
    raise AssertionError(
        "Source integrity checks failed:\n"
        + "\n".join(f"- {name}" for name in failed_source)
    )

scripts = re.findall(
    r"<script>(.*?)</script>",
    html,
    flags=re.DOTALL | re.IGNORECASE,
)

if not scripts:
    raise AssertionError("No inline JavaScript block found")

node = shutil.which("node")

if node:
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "requirements_management_runtime.js"
        script_path.write_text("\n".join(scripts), encoding="utf-8")

        syntax = subprocess.run(
            [node, "--check", str(script_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if syntax.returncode != 0:
            raise AssertionError(
                "JavaScript syntax validation failed:\n"
                + syntax.stdout
                + syntax.stderr
            )


def launch_chromium(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except PlaywrightError as first_error:
        candidates = [
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("msedge"),
        ]

        executable = next(
            (candidate for candidate in candidates if candidate),
            None,
        )

        if not executable:
            raise RuntimeError(
                "Chromium is unavailable. Install it with: "
                "playwright install chromium"
            ) from first_error

        return playwright.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox"],
        )


runtime_checks: dict[str, bool] = {}
console_errors: list[str] = []
page_errors: list[str] = []

with sync_playwright() as playwright:
    browser = launch_chromium(playwright)
    page = browser.new_page(accept_downloads=True)

    page.on(
        "console",
        lambda message: (
            console_errors.append(message.text)
            if message.type == "error"
            else None
        ),
    )

    page.on(
        "pageerror",
        lambda error: page_errors.append(str(error)),
    )

    page.set_content(html, wait_until="load")

    page.wait_for_function(
        "window.SAIL_REQ && SAIL_REQ.audit().allPass === true",
        timeout=120000,
    )

    identity = page.evaluate(
        """() => ({
          app:SAIL_REQ.version(),
          stack:SAIL_REQ.stackVersion(),
          audit:SAIL_REQ.audit(),
          layers:SAIL.certify().layers,
          benchmark:SAIL.benchmark().benchmark_case_count
        })"""
    )

    runtime_checks["release identity"] = (
        identity["app"] == "1.1.2"
        and identity["stack"] == "5.9.0"
        and identity["layers"] == 37
        and identity["benchmark"] == 347400
    )

    runtime_checks["application audit"] = (
        identity["audit"]["allPass"] is True
        and identity["audit"]["case_count"] == 12000
        and identity["audit"]["expected_case_count"] == 12000
        and identity["audit"]["failed_case_count"] == 0
        and identity["audit"]["scenario_count"] == 8
        and identity["audit"]["iterations_per_scenario"] == 1500
    )

    reference = page.evaluate(
        """() => {
          const m=SAIL_REQ.stackManifest();
          return {
            conformance:m.conformance_execution_count,
            behavior:m.behavioral_specification_count,
            mutations:[
              m.source_mutation_operator_count,
              m.source_mutations_detected
            ],
            realization:m.realization_audit_case_count,
            local:m.application_audit_execution,
            reference:m.conformance_execution
          };
        }"""
    )

    runtime_checks["referenced validation boundary"] = (
        reference["conformance"] == 347400
        and reference["behavior"] == 96
        and reference["mutations"] == [5, 5]
        and reference["realization"] == 48600
        and reference["local"] == "LOCAL_RUNTIME"
        and reference["reference"] == "REFERENCE_RELEASE_VALIDATION"
    )

    deterministic = page.evaluate(
        """() => {
          const input={
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          };

          const a=SAIL_REQ.certify(input);
          const b=SAIL_REQ.certify(input);

          return {
            same_id:
              a.requirement_id===b.requirement_id,
            same_requirement:
              a.requirement_certificate===
              b.requirement_certificate,
            same_policy:
              a.policy_certificate===
              b.policy_certificate,
            same_trace:
              a.trace_certificate===
              b.trace_certificate,
            a_record:a.record_id,
            b_record:b.record_id
          };
        }"""
    )

    a_number = int(deterministic["a_record"].split("-")[-1])
    b_number = int(deterministic["b_record"].split("-")[-1])

    runtime_checks["deterministic structural identity"] = all(
        deterministic[key]
        for key in (
            "same_id",
            "same_requirement",
            "same_policy",
            "same_trace",
        )
    )

    runtime_checks["session-local monotonic record identity"] = (
        bool(
            re.fullmatch(
                r"REQREC-\d{12}",
                deterministic["a_record"],
            )
        )
        and bool(
            re.fullmatch(
                r"REQREC-\d{12}",
                deterministic["b_record"],
            )
        )
        and b_number == a_number + 1
    )

    incomplete = page.evaluate(
        """() => SAIL_REQ.certify({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"",
          priority:"MEDIUM",
          policy:"standard_review",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["incomplete requirement fails closed"] = (
        incomplete["certified"] is False
        and incomplete["certification_state"]
        == "REQUIREMENT_INCOMPLETE"
        and incomplete["incomplete_fields"] == ["object"]
        and incomplete["requirement_certificate"] is None
        and incomplete["policy_certificate"] is None
        and incomplete["trace_certificate"] is None
    )

    invalid_priority = page.evaluate(
        """() => SAIL_REQ.certify({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"URGENT",
          policy:"standard_review",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["invalid priority rejection"] = (
        invalid_priority["certified"] is False
        and invalid_priority["invalid_fields"] == ["priority"]
        and invalid_priority["requirement_certificate"] is None
    )

    invalid_policy = page.evaluate(
        """() => SAIL_REQ.certify({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"MEDIUM",
          policy:"made_up_policy",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["invalid policy rejection"] = (
        invalid_policy["certified"] is True
        and invalid_policy["policy_bound"] is False
        and invalid_policy["invalid_fields"] == ["policy"]
        and invalid_policy["policy_state"] == "POLICY_INVALID"
        and invalid_policy["policy_certificate"] is None
    )

    missing_policy = page.evaluate(
        """() => SAIL_REQ.certify({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"MEDIUM",
          policy:"",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["missing policy guard"] = (
        missing_policy["certified"] is True
        and missing_policy["policy_bound"] is False
        and missing_policy["policy_missing_fields"] == ["policy"]
        and missing_policy["policy_state"]
        == "POLICY_WAITING_POLICY_REQUIRED"
        and missing_policy["trace_state"]
        == "TRACE_BLOCKED_POLICY_REQUIRED"
    )

    missing_measurement = page.evaluate(
        """() => SAIL_REQ.certify({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"MEDIUM",
          policy:"standard_review",
          measurement:""
        })"""
    )

    runtime_checks["missing measurement guard"] = (
        missing_measurement["trace_certified"] is False
        and missing_measurement["trace_missing_fields"]
        == ["measurement"]
        and missing_measurement["trace_state"]
        == "TRACE_WAITING_MEASUREMENT_REQUIRED"
        and missing_measurement["trace_certificate"] is None
    )

    approval = page.evaluate(
        """() => SAIL_REQ.approve({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"MEDIUM",
          policy:"standard_review",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["approval certification"] = (
        approval["approved"] is True
        and approval["approval_state"] == "APPROVED"
        and approval["approval_certificate"].startswith("APPROVAL-")
        and approval["realization_state"] == "WAITING"
    )

    precondition = page.evaluate(
        """() => SAIL_REQ.realize({
          title:"Export Report",
          statement:"Requirement: user can export report.",
          actor:"user",
          action:"export",
          object:"report",
          priority:"MEDIUM",
          policy:"standard_review",
          measurement:"Report file generated"
        })"""
    )

    runtime_checks["realization approval precondition"] = (
        precondition["realized"] is False
        and precondition["realization_state"]
        == "REALIZATION_BLOCKED_APPROVAL_REQUIRED"
        and precondition["realization_certificate"] is None
    )

    realized = page.evaluate(
        """() => {
          const approved=SAIL_REQ.approve({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          return SAIL_REQ.realize(approved);
        }"""
    )

    runtime_checks["realization certification"] = (
        realized["approved"] is True
        and realized["realized"] is True
        and realized["realization_state"] == "REALIZED"
        and realized["realization_certificate"].startswith("REAL-")
    )

    forged_requirement = page.evaluate(
        """() => {
          const item=SAIL_REQ.certify({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          item.requirement_certificate="REQCERT-FORGED";

          return SAIL_REQ.approve(item);
        }"""
    )

    runtime_checks["forged requirement rejection"] = (
        forged_requirement["approved"] is False
        and forged_requirement["approval_state"]
        == "APPROVAL_BLOCKED_INTEGRITY_REQUIRED"
        and forged_requirement["approval_certificate"] is None
        and forged_requirement["integrity_reason"]
        == "REQUIREMENT_CERTIFICATE_INTEGRITY_INVALID"
    )

    forged_approval = page.evaluate(
        """() => {
          const item=SAIL_REQ.approve({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          item.approval_certificate="APPROVAL-FORGED";

          return SAIL_REQ.realize(item);
        }"""
    )

    runtime_checks["forged approval rejection"] = (
        forged_approval["realized"] is False
        and forged_approval["realization_state"]
        == "REALIZATION_BLOCKED_INTEGRITY_REQUIRED"
        and forged_approval["realization_certificate"] is None
        and forged_approval["integrity_reason"]
        == "APPROVAL_INTEGRITY_INVALID"
    )

    forged_realization = page.evaluate(
        """() => {
          const approved=SAIL_REQ.approve({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          const item=SAIL_REQ.realize(approved);
          item.realization_certificate="REAL-FORGED";

          return {
            integrity:SAIL_REQ.integrity(item),
            trace:SAIL_REQ.trace(item)
          };
        }"""
    )

    runtime_checks["forged realization rejection"] = (
        forged_realization["integrity"]["valid"] is False
        and forged_realization["integrity"]["certified"] is False
        and forged_realization["integrity"]["reason"]
        == "REALIZATION_INTEGRITY_INVALID"
        and forged_realization["trace"]["trace_chain_state"]
        == "REQUIREMENT_TRACE_CHAIN_INVALID"
        and forged_realization["trace"]["chain_certificate"] is None
    )

    progress_trace = page.evaluate(
        """() => {
          const item=SAIL_REQ.certify({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          return SAIL_REQ.trace(item);
        }"""
    )

    runtime_checks["trace chain in progress"] = (
        progress_trace["trace_chain_state"]
        == "REQUIREMENT_TRACE_CHAIN_IN_PROGRESS"
        and progress_trace["chain_certified"] is False
        and progress_trace["integrity_reason"]
        == "REALIZATION_NOT_CERTIFIED"
        and progress_trace["chain_certificate"] is None
    )

    certified_trace = page.evaluate(
        """() => {
          const approved=SAIL_REQ.approve({
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          });

          const item=SAIL_REQ.realize(approved);
          const first=SAIL_REQ.trace(item);
          const second=SAIL_REQ.trace(item);

          return {
            first,
            deterministic:
              first.chain_certificate===
              second.chain_certificate
          };
        }"""
    )

    runtime_checks["trace chain certification"] = (
        certified_trace["first"]["trace_chain_state"]
        == "REQUIREMENT_TRACE_CHAIN_CERTIFIED"
        and certified_trace["first"]["chain_certified"] is True
        and certified_trace["first"]["integrity_reason"] is None
        and certified_trace["first"]["chain_certificate"].startswith(
            "REQCHAIN-"
        )
        and certified_trace["deterministic"] is True
    )

    idempotent = page.evaluate(
        """() => {
          const input={
            title:"Export Report",
            statement:"Requirement: user can export report.",
            actor:"user",
            action:"export",
            object:"report",
            priority:"MEDIUM",
            policy:"standard_review",
            measurement:"Report file generated"
          };

          const firstApproval=SAIL_REQ.approve(input);
          const secondApproval=SAIL_REQ.approve(firstApproval);
          const firstRealization=SAIL_REQ.realize(firstApproval);
          const secondRealization=SAIL_REQ.realize(
            firstRealization
          );

          return {
            approval_certificate:
              firstApproval.approval_certificate===
              secondApproval.approval_certificate,
            approval_time:
              firstApproval.updated_at===
              secondApproval.updated_at,
            realization_certificate:
              firstRealization.realization_certificate===
              secondRealization.realization_certificate,
            realization_time:
              firstRealization.updated_at===
              secondRealization.updated_at
          };
        }"""
    )

    runtime_checks["idempotent lifecycle"] = all(
        idempotent.values()
    )

    resets = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          const before=SAIL_REQ.current();

          document.getElementById("policy").value=
            "security_review";

          const policy=SAIL_REQ.addOrUpdate();

          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          const beforeMeasurement=SAIL_REQ.current();

          document.getElementById("measurement").value=
            "Different measurement";

          const measurement=SAIL_REQ.addOrUpdate();

          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          const beforeStructure=SAIL_REQ.current();

          document.getElementById("object").value=
            "report archive";

          const structure=SAIL_REQ.addOrUpdate();

          return {
            before,
            policy,
            beforeMeasurement,
            measurement,
            beforeStructure,
            structure
          };
        }"""
    )

    runtime_checks["policy change reset"] = (
        resets["before"]["requirement_id"]
        == resets["policy"]["requirement_id"]
        and resets["before"]["policy_certificate"]
        != resets["policy"]["policy_certificate"]
        and resets["policy"]["approved"] is False
        and resets["policy"]["realized"] is False
    )

    runtime_checks["measurement change reset"] = (
        resets["beforeMeasurement"]["requirement_id"]
        == resets["measurement"]["requirement_id"]
        and resets["beforeMeasurement"]["trace_certificate"]
        != resets["measurement"]["trace_certificate"]
        and resets["measurement"]["approved"] is False
        and resets["measurement"]["realized"] is False
    )

    runtime_checks["structural change reset"] = (
        resets["beforeStructure"]["record_id"]
        == resets["structure"]["record_id"]
        and resets["beforeStructure"]["requirement_id"]
        != resets["structure"]["requirement_id"]
        and resets["beforeStructure"]["requirement_certificate"]
        != resets["structure"]["requirement_certificate"]
        and resets["structure"]["approved"] is False
        and resets["structure"]["realized"] is False
    )

    current_isolation = page.evaluate(
        """() => {
          SAIL_REQ.reset();

          const first=SAIL_REQ.current();

          first.certified=false;
          first.requirement_certificate="REQCERT-FORGED";
          first.actor_action_object.actor="forged";

          const second=SAIL_REQ.current();

          return {
            independent:first!==second,
            certified:second.certified,
            certificate:second.requirement_certificate,
            actor:second.actor_action_object.actor
          };
        }"""
    )

    runtime_checks["current snapshot isolation"] = (
        current_isolation["independent"] is True
        and current_isolation["certified"] is True
        and current_isolation["certificate"]
        != "REQCERT-FORGED"
        and current_isolation["actor"] == "user"
    )

    returned_isolation = page.evaluate(
        """() => {
          const returned=SAIL_REQ.reset();

          returned.certified=false;
          returned.requirement_certificate=
            "REQCERT-FORGED";
          returned.invalid_fields.push("forged");

          const current=SAIL_REQ.current();

          return {
            certified:current.certified,
            certificate:current.requirement_certificate,
            invalid:current.invalid_fields
          };
        }"""
    )

    runtime_checks["returned result snapshot isolation"] = (
        returned_isolation["certified"] is True
        and returned_isolation["certificate"]
        != "REQCERT-FORGED"
        and returned_isolation["invalid"] == []
    )

    audit_isolation = page.evaluate(
        """() => {
          const first=SAIL_REQ.audit(true);

          first.allPass=false;
          first.case_count=1;
          first.failed_case_count=999;

          const second=SAIL_REQ.audit();

          return {
            independent:first!==second,
            second
          };
        }"""
    )

    runtime_checks["audit snapshot isolation"] = (
        audit_isolation["independent"] is True
        and audit_isolation["second"]["allPass"] is True
        and audit_isolation["second"]["case_count"] == 12000
        and audit_isolation["second"]["failed_case_count"]
        == 0
    )

    examples = page.evaluate(
        """() => {
          SAIL_REQ.reset();

          const first=SAIL_REQ.current();
          const security=SAIL_REQ.loadExample("security");
          const incident=SAIL_REQ.loadExample("incident");
          const pack=SAIL_REQ.exportPack();

          return {
            count:Number(
              document.getElementById("reqCount").textContent
            ),
            titles:
              pack.structural_payload.requirements
                .map(item=>item.title)
                .sort(),
            records:
              pack.operational_metadata.records
                .map(item=>item.record_id),
            first:first.record_id,
            security:security.record_id,
            incident:incident.record_id
          };
        }"""
    )

    example_numbers = [
        int(record.split("-")[-1])
        for record in examples["records"]
    ]

    runtime_checks["examples accumulate requirements"] = (
        examples["count"] == 3
        and examples["titles"] == [
            "Escalate Incident",
            "Export Report",
            "Review Access",
        ]
        and len(set(examples["records"])) == 3
        and max(example_numbers) - min(example_numbers) == 2
        and sorted(example_numbers)
        == list(
            range(
                min(example_numbers),
                max(example_numbers) + 1,
            )
        )
    )

    new_insertion = page.evaluate(
        """() => {
          SAIL_REQ.reset();

          const first=SAIL_REQ.current();
          const state=SAIL_REQ.newRequirement();

          document.getElementById("title").value=
            "Archive Report";
          document.getElementById("statement").value=
            "Requirement: user can archive report.";
          document.getElementById("actor").value="user";
          document.getElementById("action").value="archive";
          document.getElementById("object").value="report";
          document.getElementById("priority").value="HIGH";
          document.getElementById("policy").value=
            "standard_review";
          document.getElementById("measurement").value=
            "Archive created";

          const second=SAIL_REQ.addOrUpdate();
          const pack=SAIL_REQ.exportPack();

          return {
            state,
            count:Number(
              document.getElementById("reqCount").textContent
            ),
            first:first.record_id,
            second:second.record_id,
            titles:
              pack.structural_payload.requirements
                .map(item=>item.title)
          };
        }"""
    )

    first_number = int(
        new_insertion["first"].split("-")[-1]
    )

    second_number = int(
        new_insertion["second"].split("-")[-1]
    )

    runtime_checks["new requirement insertion"] = (
        new_insertion["state"]["state"] == "NEW_REQUIREMENT"
        and new_insertion["state"]["requirement_count"] == 1
        and new_insertion["count"] == 2
        and set(new_insertion["titles"])
        == {"Export Report", "Archive Report"}
        and second_number == first_number + 1
    )

    selected_update = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.loadExample("security");

          const before=SAIL_REQ.current();

          const beforeCount=Number(
            document.getElementById("reqCount").textContent
          );

          document.getElementById("measurement").value=
            "Updated review receipt";

          const changed=SAIL_REQ.addOrUpdate();
          const pack=SAIL_REQ.exportPack();

          return {
            beforeCount,
            afterCount:Number(
              document.getElementById("reqCount").textContent
            ),
            sameRecord:
              before.record_id===changed.record_id,
            measurement:changed.measurement,
            titles:
              pack.structural_payload.requirements
                .map(item=>item.title)
                .sort()
          };
        }"""
    )

    runtime_checks["selected requirement updates in place"] = (
        selected_update["beforeCount"] == 2
        and selected_update["afterCount"] == 2
        and selected_update["sameRecord"] is True
        and selected_update["measurement"]
        == "Updated review receipt"
        and selected_update["titles"]
        == ["Export Report", "Review Access"]
    )

    mixed_packs = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          SAIL_REQ.loadExample("security");

          const unresolved=SAIL_REQ.exportPack();

          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          const certified=SAIL_REQ.exportPack();

          SAIL_REQ.newRequirement();

          document.getElementById("title").value=
            "Incomplete Requirement";
          document.getElementById("statement").value=
            "Requirement structure is incomplete.";
          document.getElementById("actor").value="user";
          document.getElementById("action").value="inspect";
          document.getElementById("object").value="";
          document.getElementById("priority").value="MEDIUM";
          document.getElementById("policy").value=
            "standard_review";
          document.getElementById("measurement").value=
            "Inspection complete";

          SAIL_REQ.addOrUpdate();

          const incomplete=SAIL_REQ.exportPack();

          return {
            unresolved,
            certified,
            incomplete
          };
        }"""
    )

    runtime_checks["mixed multi-record pack classification"] = (
        mixed_packs["unresolved"]["pack_state"]
        == "REQUIREMENTS_PACK_UNRESOLVED"
        and mixed_packs["unresolved"]["pack_certified"]
        is False
        and len(
            mixed_packs["unresolved"]
            ["structural_payload"]["requirements"]
        )
        == 2
        and mixed_packs["certified"]["pack_state"]
        == "REQUIREMENTS_PACK_CERTIFIED"
        and mixed_packs["certified"]["pack_certified"]
        is True
        and len(
            mixed_packs["certified"]
            ["structural_payload"]["requirements"]
        )
        == 2
        and mixed_packs["incomplete"]["pack_state"]
        == "REQUIREMENTS_PACK_INCOMPLETE"
        and mixed_packs["incomplete"]["pack_certified"]
        is False
        and len(
            mixed_packs["incomplete"]
            ["structural_payload"]["requirements"]
        )
        == 3
    )

    multi_pack_isolation = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.loadExample("security");

          const first=SAIL_REQ.exportPack();

          first.structural_payload.requirements[0].title=
            "FORGED";

          first.structural_payload.requirements[1]
            .actor_action_object.actor="forged";

          first.operational_metadata.records[0].record_id=
            "REQREC-FORGED";

          const second=SAIL_REQ.exportPack();

          return {
            count:
              second.structural_payload.requirements.length,
            titles:
              second.structural_payload.requirements
                .map(item=>item.title)
                .sort(),
            actors:
              second.structural_payload.requirements
                .map(item=>item.actor_action_object.actor)
                .sort(),
            records:
              second.operational_metadata.records
                .map(item=>item.record_id)
          };
        }"""
    )

    runtime_checks["multi-record pack snapshot isolation"] = (
        multi_pack_isolation["count"] == 2
        and multi_pack_isolation["titles"]
        == ["Export Report", "Review Access"]
        and multi_pack_isolation["actors"]
        == ["admin", "user"]
        and all(
            re.fullmatch(r"REQREC-\d{12}", record)
            for record in multi_pack_isolation["records"]
        )
    )

    certified_pack = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          return SAIL_REQ.exportPack();
        }"""
    )

    runtime_checks["certified pack state"] = (
        certified_pack["pack_state"]
        == "REQUIREMENTS_PACK_CERTIFIED"
        and certified_pack["pack_certified"] is True
        and certified_pack["integrity_reason"] is None
        and certified_pack["structural_payload"]
        ["trace_chains"][0]["chain_certified"] is True
    )

    unresolved_pack = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          return SAIL_REQ.exportPack();
        }"""
    )

    runtime_checks["unresolved pack state"] = (
        unresolved_pack["pack_state"]
        == "REQUIREMENTS_PACK_UNRESOLVED"
        and unresolved_pack["pack_certified"] is False
        and unresolved_pack["integrity_reason"]
        == "REQUIREMENT_LIFECYCLE_INCOMPLETE"
    )

    incomplete_pack = page.evaluate(
        """() => {
          SAIL_REQ.reset();

          document.getElementById("object").value="";

          SAIL_REQ.addOrUpdate();

          return SAIL_REQ.exportPack();
        }"""
    )

    runtime_checks["incomplete pack state"] = (
        incomplete_pack["pack_state"]
        == "REQUIREMENTS_PACK_INCOMPLETE"
        and incomplete_pack["pack_certified"] is False
        and incomplete_pack["structural_payload"]
        ["requirements"][0]["requirement_certificate"] is None
    )

    empty_pack = page.evaluate(
        """() => {
          SAIL_REQ.clear();
          return SAIL_REQ.exportPack();
        }"""
    )

    runtime_checks["empty pack state"] = (
        empty_pack["pack_state"]
        == "REQUIREMENTS_PACK_EMPTY"
        and empty_pack["pack_certified"] is False
        and empty_pack["integrity_reason"] == "NO_REQUIREMENTS"
    )

    pack_isolation = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          const first=SAIL_REQ.exportPack();

          first.pack_certified=false;
          first.structural_payload.requirements[0]
            .realized=false;
          first.structural_payload.requirements[0]
            .actor_action_object.actor="forged";
          first.operational_metadata.records[0]
            .record_id="REQREC-FORGED";

          const second=SAIL_REQ.exportPack();

          return second;
        }"""
    )

    runtime_checks["pack snapshot isolation"] = (
        pack_isolation["pack_certified"] is True
        and pack_isolation["structural_payload"]
        ["requirements"][0]["realized"] is True
        and pack_isolation["structural_payload"]
        ["requirements"][0]["actor_action_object"]["actor"]
        == "user"
        and bool(
            re.fullmatch(
                r"REQREC-\d{12}",
                pack_isolation["operational_metadata"]
                ["records"][0]["record_id"],
            )
        )
    )

    separation = page.evaluate(
        """() => {
          SAIL_REQ.reset();

          const pack=SAIL_REQ.exportPack();
          const structural=JSON.stringify(
            pack.structural_payload
          );

          return {
            structural_has_record:
              structural.includes("record_id"),
            structural_has_created:
              structural.includes("created_at"),
            structural_has_updated:
              structural.includes("updated_at"),
            operational_record:
              pack.operational_metadata.records[0]
                .record_id,
            record_excluded:
              pack.operational_metadata
                .record_id_fields_excluded_from_certificates,
            timestamp_excluded:
              pack.operational_metadata
                .timestamp_fields_excluded_from_certificates
          };
        }"""
    )

    runtime_checks["structural operational separation"] = (
        separation["structural_has_record"] is False
        and separation["structural_has_created"] is False
        and separation["structural_has_updated"] is False
        and bool(
            re.fullmatch(
                r"REQREC-\d{12}",
                separation["operational_record"],
            )
        )
        and separation["record_excluded"] is True
        and separation["timestamp_excluded"] is True
    )

    empty_guards = page.evaluate(
        """() => {
          const cleared=SAIL_REQ.clear();
          const approval=SAIL_REQ.approveSelected();
          const realization=SAIL_REQ.realizeSelected();

          return {
            cleared,
            approval,
            realization,
            current:SAIL_REQ.current(),
            status:
              document.getElementById("systemStatus")
                .textContent
          };
        }"""
    )

    runtime_checks["empty selection guards"] = (
        empty_guards["cleared"]["requirement_count"] == 0
        and empty_guards["approval"] is False
        and empty_guards["realization"] is False
        and empty_guards["current"] is None
        and empty_guards["status"] == "NO REQUIREMENT SELECTED"
    )

    interface = page.evaluate(
        """() => {
          SAIL_REQ.reset();
          SAIL_REQ.approveSelected();
          SAIL_REQ.realizeSelected();

          return {
            count:
              document.getElementById("reqCount").textContent,
            certified:
              document.getElementById("certCount").textContent,
            approved:
              document.getElementById("approvedCount").textContent,
            realized:
              document.getElementById("realizedCount").textContent,
            status:
              document.getElementById("systemStatus").textContent,
            audit:
              document.getElementById("auditState").textContent
          };
        }"""
    )

    runtime_checks["interface status alignment"] = (
        interface
        == {
            "count": "1",
            "certified": "1",
            "approved": "1",
            "realized": "1",
            "status": "REALIZED",
            "audit": "PASS",
        }
    )

    with page.expect_download(timeout=30000) as download_info:
        downloaded_pack = page.evaluate(
            "SAIL_REQ.downloadPack()"
        )

    download = download_info.value

    runtime_checks["download pack state"] = (
        downloaded_pack["pack_state"]
        == "REQUIREMENTS_PACK_CERTIFIED"
        and downloaded_pack["pack_certified"] is True
        and downloaded_pack["delivery_mode"] == "download"
        and download.suggested_filename
        == "sail_requirements_pack.json"
    )

    runtime_checks["browser console clean"] = not console_errors
    runtime_checks["browser page errors clean"] = not page_errors

    browser.close()

failed_runtime = [
    name
    for name, passed in runtime_checks.items()
    if not passed
]

if failed_runtime:
    details = "\n".join(
        f"- {name}"
        for name in failed_runtime
    )

    if console_errors:
        details += (
            "\nConsole errors:\n"
            + "\n".join(console_errors)
        )

    if page_errors:
        details += (
            "\nPage errors:\n"
            + "\n".join(page_errors)
        )

    raise AssertionError(
        "Runtime behavioral checks failed:\n"
        + details
    )

print(
    "SAIL Requirements Management System "
    "v1.1.2 validation passed"
)
print(f"Source integrity checks: {len(source_checks)}")
print(f"Runtime behavioral checks: {len(runtime_checks)}")
print("Application audit executions: 12000")
print("Failed checks: 0")
