from __future__ import annotations

import json
import shutil
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:
    raise SystemExit(
        "Playwright is required: python -m pip install playwright && playwright install chromium"
    ) from exc

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_Incident_Management_System_v1_1_2.html"

if not HTML.is_file():
    raise SystemExit(f"Missing required release file: {HTML.name}")

html = HTML.read_text(encoding="utf-8")

source_checks = {
    "application title": '<title>SAIL Incident Management System v1.1.2</title>' in html,
    "application version": 'const VERSION="1.1.2";' in html,
    "stack version": 'const SAIL_VERSION="5.9.0";' in html,
    "certified layers": "const LAYERS=37;" in html,
    "conformance count": "const CONFORMANCE_EXECUTIONS=347400;" in html,
    "behavioral count": "const BEHAVIORAL_SPECIFICATIONS=96;" in html,
    "mutation count": "const SOURCE_MUTATIONS_DETECTED=5;" in html,
    "realization audit count": "const REALIZATION_AUDIT=48600;" in html,
    "application audit count": "const EXPECTED_AUDIT_CASES=12000;" in html,
    "audit scenarios": "const AUDIT_SCENARIOS=8;" in html,
    "audit iterations": "const AUDIT_ITERATIONS=1500;" in html,
    "admitted conditions": 'const CONDITIONS=Object.freeze(["NORMAL","TIMEOUT","DEGRADED","CRITICAL_FAILURE"]);' in html,
    "admitted severities": 'const SEVERITIES=Object.freeze(["LOW","MEDIUM","HIGH","CRITICAL"]);' in html,
    "snapshot clone": "function clone(x)" in html,
    "deep freeze": "function deepFreeze(x)" in html,
    "incident blueprint": "function incidentBlueprint(input)" in html,
    "incident integrity": "function incidentIntegrity(incident)" in html,
    "escalation integrity": "function escalationIntegrity(incident)" in html,
    "recovery integrity": "function recoveryIntegrity(incident)" in html,
    "verification integrity": "function verificationIntegrity(incident)" in html,
    "lifecycle consistency": "function lifecycleConsistent(incident)" in html,
    "escalation certificate reproduction": "function expectedEscalationCertificate(incident)" in html,
    "recovery certificate reproduction": "function expectedRecoveryCertificate(incident)" in html,
    "verification certificate reproduction": "function expectedVerificationCertificate(incident)" in html,
    "realization certificate reproduction": "function expectedRealizationCertificate(incident,verificationCertificate)" in html,
    "invalid chain state": "INCIDENT_CERTIFICATE_CHAIN_INVALID" in html,
    "certified chain state": "INCIDENT_CERTIFICATE_CHAIN_CERTIFIED" in html,
    "truthful pack flag": 'pack_certified:state==="INCIDENT_PACK_CERTIFIED"' in html,
    "audit snapshot": "return clone(AUDIT_RESULT);" in html,
    "current snapshot": "current:function(){return clone(selected())}" in html,
    "chain snapshot": "certificateChain:function(input){return clone(certificateChain(input))}" in html,
    "local runtime classification": 'application_audit_execution:"LOCAL_RUNTIME"' in html,
    "referenced conformance classification": 'conformance_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced realization classification": 'realization_audit_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "no prior application version": "v1.1.1" not in html,
    "no prior stack version": "5.8.1" not in html,
    "session-local record identity": 'return"REC-"+String(recordCounter).padStart(12,"0");' in html,
    "no random identity": "Math.random" not in html and "crypto.randomUUID" not in html,
    "no html comments": "<!--" not in html,
}

failed_source_checks = [name for name, passed in source_checks.items() if not passed]
if failed_source_checks:
    raise AssertionError("Source integrity failures: " + ", ".join(failed_source_checks))


def launch_browser(playwright):
    try:
        return playwright.chromium.launch(headless=True)
    except Exception as first_error:
        candidates = [
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("msedge"),
        ]
        for candidate in candidates:
            if candidate:
                try:
                    return playwright.chromium.launch(
                        headless=True,
                        executable_path=candidate,
                    )
                except Exception:
                    pass
        raise SystemExit(str(first_error))


def run_case(page, case_id: str, expression: str, expected):
    actual = page.evaluate(expression)
    if actual != expected:
        raise AssertionError(
            json.dumps(
                {"case": case_id, "expected": expected, "actual": actual},
                indent=2,
                sort_keys=True,
            )
        )
    return {"case": case_id, "passed": True}


results = []
with sync_playwright() as playwright:
    browser = launch_browser(playwright)
    page = browser.new_page()
    page_errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.set_content(html, wait_until="load", timeout=120000)

    results.append(
        run_case(
            page,
            "release identity",
            "() => [SAIL_INC.version(), SAIL_INC.stackVersion(), SAIL.certify().layers, SAIL.benchmark().benchmark_case_count]",
            ["1.1.2", "5.9.0", 37, 347400],
        )
    )

    results.append(
        run_case(
            page,
            "local application audit",
            "() => { const a=SAIL_INC.audit(true); return [a.allPass,a.case_count,a.expected_case_count,a.count_match,a.failed_case_count,a.scenario_count,a.iterations_per_scenario,a.classification,a.execution]; }",
            [True, 12000, 12000, True, 0, 8, 1500, "LOCAL_APPLICATION_CONFORMANCE_EXECUTIONS", "LOCAL_RUNTIME"],
        )
    )

    results.append(
        run_case(
            page,
            "referenced release metadata",
            "() => { const m=SAIL_INC.stackManifest(); return [m.conformance_execution_count,m.conformance_execution,m.behavioral_specification_count,m.behavioral_validation,m.source_mutations_detected,m.realization_audit_case_count,m.realization_audit_execution]; }",
            [347400, "REFERENCE_RELEASE_VALIDATION", 96, "REFERENCE_RELEASE_VALIDATION", 5, 48600, "REFERENCE_RELEASE_VALIDATION"],
        )
    )

    results.append(
        run_case(
            page,
            "deterministic structural identity",
            "() => { const input={title:'Export Service Timeout',description:'Incident: export service response timeout detected.',service:'Report Export Service',condition:'TIMEOUT',severity:'MEDIUM',owner:'operations_team',measurement:'Service restored and export verified'}; const a=SAIL_INC.certify(input); const b=SAIL_INC.certify(input); const aNumber=Number(a.record_id.slice(4)); const bNumber=Number(b.record_id.slice(4)); return [a.incident_id===b.incident_id,a.incident_certificate===b.incident_certificate,a.triage_certificate===b.triage_certificate,a.record_id!==b.record_id,/^REC-[0-9]{12}$/.test(a.record_id),/^REC-[0-9]{12}$/.test(b.record_id),bNumber===aNumber+1,!('record_id' in a.invariant),!('created_at' in a.invariant)]; }",
            [True, True, True, True, True, True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "invalid incident admission",
            "() => { const x=SAIL_INC.certify({title:'Invalid',description:'Invalid incident.',service:'Service',condition:'UNKNOWN',severity:'EXTREME',owner:'owner',measurement:'measurement'}); return [x.certified,x.invalid_fields,x.incomplete_fields,x.risk_score,x.triage,x.detection_state,x.triage_state]; }",
            [False, ["condition", "severity"], [], None, "UNRESOLVED", "INCIDENT_INCOMPLETE", "TRIAGE_WAITING"],
        )
    )

    results.append(
        run_case(
            page,
            "current snapshot isolation",
            "() => { SAIL_INC.reset(); const x=SAIL_INC.current(); x.recovered=true; x.recovery_state='RECOVERY_CERTIFIED'; x.recovery_certificate='REC-FORGED'; const accepted=SAIL_INC.verifySelected(); const y=SAIL_INC.current(); return [accepted,y.recovered,y.verified,y.recovery_certificate,y.verification_state]; }",
            [False, False, False, None, "VERIFICATION_BLOCKED_RECOVERY_REQUIRED"],
        )
    )

    results.append(
        run_case(
            page,
            "returned create snapshot isolation",
            "() => { const x=SAIL_INC.reset(); x.certified=false; x.incident_certificate='INCCERT-FORGED'; const y=SAIL_INC.current(); return [y.certified,y.incident_certificate!=='INCCERT-FORGED',y.detection_state]; }",
            [True, True, "INCIDENT_CERTIFIED"],
        )
    )

    results.append(
        run_case(
            page,
            "incomplete incident guards",
            "() => { SAIL_INC.clear(); document.getElementById('title').value='Incomplete'; document.getElementById('description').value='Incomplete incident.'; document.getElementById('service').value='Service'; document.getElementById('condition').value='TIMEOUT'; document.getElementById('severity').value='MEDIUM'; document.getElementById('owner').value='owner'; document.getElementById('measurement').value=''; const x=SAIL_INC.createOrUpdate(); const e=SAIL_INC.escalateSelected(); const r=SAIL_INC.recoverSelected(); const v=SAIL_INC.verifySelected(); const y=SAIL_INC.current(); return [x.certified,x.incomplete_fields,e,r,v,y.incident_resolved,y.verification_state]; }",
            [False, ["measurement"], False, False, False, False, "VERIFICATION_BLOCKED_INCIDENT_REQUIRED"],
        )
    )

    results.append(
        run_case(
            page,
            "critical recovery guard",
            "() => { const x=SAIL_INC.loadExample('critical'); const accepted=SAIL_INC.recoverSelected(); const y=SAIL_INC.current(); return [x.escalation_needed,accepted,y.recovered,y.recovery_state]; }",
            [True, False, False, "RECOVERY_BLOCKED_ESCALATION_REQUIRED"],
        )
    )

    results.append(
        run_case(
            page,
            "optional complete lifecycle",
            "() => { SAIL_INC.reset(); const r=SAIL_INC.recoverSelected(); const v=SAIL_INC.verifySelected(); const x=SAIL_INC.current(); const c=SAIL_INC.certificateChain(x); return [r,v,x.recovered,x.verified,x.incident_resolved,x.resolution_state,c.chain_state,c.chain_certified,c.chain_certificate.startsWith('CHAIN-')]; }",
            [True, True, True, True, True, "INCIDENT_RESOLVED", "INCIDENT_CERTIFICATE_CHAIN_CERTIFIED", True, True],
        )
    )

    results.append(
        run_case(
            page,
            "critical complete lifecycle",
            "() => { SAIL_INC.loadExample('critical'); const e=SAIL_INC.escalateSelected(); const r=SAIL_INC.recoverSelected(); const v=SAIL_INC.verifySelected(); const x=SAIL_INC.current(); return [e,r,v,x.escalation_certificate.startsWith('ESC-'),x.recovery_certificate.startsWith('REC-'),x.verification_certificate.startsWith('VER-'),x.realization_certificate.startsWith('INC-REAL-'),x.incident_resolved]; }",
            [True, True, True, True, True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "idempotent lifecycle",
            "() => { SAIL_INC.loadExample('critical'); SAIL_INC.escalateSelected(); const e1=SAIL_INC.current(); const e2a=SAIL_INC.escalateSelected(); const e2=SAIL_INC.current(); SAIL_INC.recoverSelected(); const r1=SAIL_INC.current(); const r2a=SAIL_INC.recoverSelected(); const r2=SAIL_INC.current(); SAIL_INC.verifySelected(); const v1=SAIL_INC.current(); const v2a=SAIL_INC.verifySelected(); const v2=SAIL_INC.current(); return [e2a,e1.escalation_certificate===e2.escalation_certificate,e1.updated_at===e2.updated_at,r2a,r1.recovery_certificate===r2.recovery_certificate,r1.updated_at===r2.updated_at,v2a,v1.verification_certificate===v2.verification_certificate,v1.realization_certificate===v2.realization_certificate,v1.updated_at===v2.updated_at]; }",
            [True, True, True, True, True, True, True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "structural change reset",
            "() => { SAIL_INC.loadExample('critical'); SAIL_INC.escalateSelected(); SAIL_INC.recoverSelected(); SAIL_INC.verifySelected(); const before=SAIL_INC.current(); document.getElementById('severity').value='HIGH'; const after=SAIL_INC.createOrUpdate(); return [before.record_id===after.record_id,before.incident_id!==after.incident_id,after.escalated,after.recovered,after.verified,after.incident_resolved,after.escalation_certificate,after.recovery_certificate,after.verification_certificate,after.realization_certificate]; }",
            [True, True, False, False, False, False, None, None, None, None],
        )
    )

    results.append(
        run_case(
            page,
            "forged certificate chain rejection",
            "() => { SAIL_INC.reset(); const x=SAIL_INC.current(); x.recovered=true; x.verified=true; x.incident_resolved=true; x.recovery_state='RECOVERY_CERTIFIED'; x.verification_state='OUTCOME_VERIFIED'; x.resolution_state='INCIDENT_RESOLVED'; x.recovery_certificate='REC-FORGED'; x.verification_certificate='VER-FORGED'; x.realization_certificate='INC-REAL-FORGED'; const c=SAIL_INC.certificateChain(x); return [c.chain_state,c.chain_certified,c.chain_certificate,c.integrity_reason]; }",
            ["INCIDENT_CERTIFICATE_CHAIN_INCOMPLETE", False, None, "RECOVERY_INTEGRITY_INVALID"],
        )
    )

    results.append(
        run_case(
            page,
            "audit snapshot isolation",
            "() => { const a=SAIL_INC.audit(true); a.allPass=false; a.case_count=1; a.failed_case_count=999; const b=SAIL_INC.audit(); return [a===b,b.allPass,b.case_count,b.failed_case_count,b.cached]; }",
            [False, True, 12000, 0, True],
        )
    )

    results.append(
        run_case(
            page,
            "truthful pack lifecycle",
            "() => { SAIL_INC.reset(); const a=SAIL_INC.exportPack(); SAIL_INC.recoverSelected(); const b=SAIL_INC.exportPack(); SAIL_INC.verifySelected(); const c=SAIL_INC.exportPack(); return [[a.pack_state,a.pack_certified],[b.pack_state,b.pack_certified],[c.pack_state,c.pack_certified,c.structural_payload.certificate_chains[0].chain_certified]]; }",
            [["INCIDENT_PACK_UNRESOLVED", False], ["INCIDENT_PACK_UNRESOLVED", False], ["INCIDENT_PACK_CERTIFIED", True, True]],
        )
    )

    results.append(
        run_case(
            page,
            "pack snapshot isolation",
            "() => { SAIL_INC.reset(); SAIL_INC.recoverSelected(); SAIL_INC.verifySelected(); const a=SAIL_INC.exportPack(); a.pack_certified=false; a.structural_payload.incidents[0].verified=false; const b=SAIL_INC.exportPack(); return [b.pack_certified,b.structural_payload.incidents[0].verified,b.structural_payload.certificate_chains[0].chain_certified]; }",
            [True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "empty and incomplete pack states",
            "() => { SAIL_INC.clear(); const empty=SAIL_INC.exportPack(); document.getElementById('title').value='Incomplete'; document.getElementById('description').value='Incomplete incident.'; document.getElementById('service').value='Service'; document.getElementById('condition').value='TIMEOUT'; document.getElementById('severity').value='MEDIUM'; document.getElementById('owner').value='owner'; document.getElementById('measurement').value=''; SAIL_INC.createOrUpdate(); const incomplete=SAIL_INC.exportPack(); return [[empty.pack_state,empty.pack_certified],[incomplete.pack_state,incomplete.pack_certified]]; }",
            [["INCIDENT_PACK_EMPTY", False], ["INCIDENT_PACK_INCOMPLETE", False]],
        )
    )

    results.append(
        run_case(
            page,
            "verified status counter",
            "() => { SAIL_INC.reset(); const before=document.getElementById('verifiedCount').textContent; SAIL_INC.recoverSelected(); SAIL_INC.verifySelected(); return [before,document.getElementById('verifiedCount').textContent,document.getElementById('systemStatus').textContent]; }",
            ["0", "1", "RESOLVED"],
        )
    )

    results.append(
        run_case(
            page,
            "empty selection guards",
            "() => { SAIL_INC.clear(); const e=SAIL_INC.escalateSelected(); const r=SAIL_INC.recoverSelected(); const v=SAIL_INC.verifySelected(); return [e,r,v,SAIL_INC.current(),document.getElementById('systemStatus').textContent]; }",
            [False, False, False, None, "NO INCIDENT SELECTED"],
        )
    )

    if page_errors or console_errors:
        raise AssertionError(
            json.dumps(
                {"page_errors": page_errors, "console_errors": console_errors},
                indent=2,
            )
        )

    browser.close()

print("SAIL Incident Management System v1.1.2 validation passed")
print(f"Source integrity checks: {len(source_checks)}")
print(f"Runtime behavioral checks: {len(results)}")
print("Application audit executions: 12000")
print("Failed checks: 0")
