from pathlib import Path
import json
import re
import shutil
import sys

try:
    from playwright.sync_api import sync_playwright
except Exception:
    raise SystemExit("Playwright is required: python -m pip install playwright && playwright install chromium")

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_Compliance_Audit_Console_v1_1_2.html"

if not HTML.is_file():
    raise SystemExit(f"Missing required release file: {HTML.name}")

html = HTML.read_text(encoding="utf-8")

source_checks = {
    "application title": '<title>SAIL Compliance and Audit Console v1.1.2</title>' in html,
    "application version": 'const VERSION="1.1.2";' in html,
    "core version": 'const SAIL_VERSION="5.9.0";' in html,
    "certified layers": "const LAYERS=37;" in html,
    "conformance count": "const CONFORMANCE_EXECUTIONS=347400;" in html,
    "behavioral count": "const BEHAVIORAL_SPECIFICATIONS=96;" in html,
    "mutation count": "const SOURCE_MUTATION_OPERATORS=5;" in html,
    "mutation detection": "const SOURCE_MUTATIONS_DETECTED=5;" in html,
    "conformance classification": 'const CONFORMANCE_CLASSIFICATION="SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS";' in html,
    "application audit count": "const EXPECTED_AUDIT_CASES=12000;" in html,
    "result admission": 'const RESULTS=Object.freeze(["PASS","FAIL","EXCEPTION"]);' in html,
    "new control operation": "function newControl()" in html,
    "guarded receipt derivation": "function receiptFor(s){return canIssueReceipt(s)?receiptDigest(s):null}" in html,
    "incomplete pack state": "COMPLIANCE_PACK_INCOMPLETE" in html,
    "partial pack state": "COMPLIANCE_PACK_PARTIALLY_CERTIFIED" in html,
    "certified pack state": "COMPLIANCE_PACK_CERTIFIED" in html,
    "pack certification flag": "pack_certified" in html,
    "evaluation counts": "incomplete_control_count" in html,
    "local application audit": 'application_audit_execution:"LOCAL_RUNTIME"' in html,
    "referenced core validation": 'conformance_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "no random identity": "Math.random" not in html,
    "no html comments": "<!--" not in html,
    "no block comments": "/*" not in html,
    "no line comments": re.search(r"(^|\s)//", html) is None,
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
                    return playwright.chromium.launch(headless=True, executable_path=candidate)
                except Exception:
                    pass
        raise SystemExit(str(first_error))


def run_case(page, case_id, expression, expected):
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
    page_errors = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(html, wait_until="load", timeout=120000)

    results.append(run_case(
        page,
        "release identity",
        "() => [SAIL_AUD.version(), SAIL_AUD.stackVersion(), SAIL.certify().layers, SAIL.benchmark().benchmark_case_count]",
        ["1.1.2", "5.9.0", 37, 347400],
    ))

    results.append(run_case(
        page,
        "local application audit",
        "() => { const a=SAIL_AUD.audit(true); return [a.allPass,a.case_count,a.expected_case_count,a.count_match,a.failed_case_count,a.classification,a.execution]; }",
        [True, 12000, 12000, True, 0, "LOCAL_APPLICATION_CONFORMANCE_EXECUTIONS", "LOCAL_RUNTIME"],
    ))

    results.append(run_case(
        page,
        "referenced core evidence",
        "() => { const m=SAIL_AUD.stackManifest(); return [m.conformance_classification,m.conformance_execution_count,m.conformance_execution,m.behavioral_specification_count,m.behavioral_validation,m.source_mutation_operator_count,m.source_mutations_detected]; }",
        ["SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS", 347400, "REFERENCE_RELEASE_VALIDATION", 96, "REFERENCE_RELEASE_VALIDATION", 5, 5],
    ))

    results.append(run_case(
        page,
        "pass evaluation",
        "() => { const r=SAIL_AUD.certify({title:'Pass',statement:'Control passes.',policy:'audit_receipt_required',evidence:'Visible evidence',owner:'audit_team',result:'PASS',exceptionReason:''}); return [r.evaluation_certified,r.control_state,r.compliance_state,r.exception_state,r.compliant,r.exception]; }",
        [True, "CONTROL_PASSED", "COMPLIANT", "NO_EXCEPTION", True, False],
    ))

    results.append(run_case(
        page,
        "fail evaluation",
        "() => { const r=SAIL_AUD.certify({title:'Fail',statement:'Control fails.',policy:'access_review_required',evidence:'Visible evidence',owner:'security_team',result:'FAIL',exceptionReason:''}); return [r.evaluation_certified,r.control_state,r.compliance_state,r.exception_state,r.compliant,r.exception,r.exception_certificate]; }",
        [True, "CONTROL_FAILED", "NON_COMPLIANT", "NO_EXCEPTION", False, False, None],
    ))

    results.append(run_case(
        page,
        "exception evaluation",
        "() => { const r=SAIL_AUD.certify({title:'Exception',statement:'Approved deviation.',policy:'release_approval_required',evidence:'Visible evidence',owner:'release_team',result:'EXCEPTION',exceptionReason:'Approved deviation pending review'}); return [r.evaluation_certified,r.control_state,r.compliance_state,r.exception_state,r.compliant,r.exception,typeof r.exception_certificate==='string'&&r.exception_certificate.startsWith('EXCEPT-')]; }",
        [True, "CONTROL_EXCEPTION", "EXCEPTION", "EXCEPTION_RECORDED", False, True, True],
    ))

    results.append(run_case(
        page,
        "missing exception reason",
        "() => { const r=SAIL_AUD.certify({title:'Exception',statement:'Approved deviation.',policy:'release_approval_required',evidence:'Visible evidence',owner:'release_team',result:'EXCEPTION',exceptionReason:''}); return [r.evaluation_certified,r.control_state,r.compliance_state,r.incomplete_fields]; }",
        [False, "CONTROL_INCOMPLETE", "UNRESOLVED", ["exceptionReason"]],
    ))

    results.append(run_case(
        page,
        "invalid result rejection",
        "() => { const r=SAIL_AUD.certify({title:'Invalid',statement:'Result must be admitted.',policy:'audit_receipt_required',evidence:'Visible evidence',owner:'audit_team',result:'BOGUS',exceptionReason:''}); return [r.evaluation_certified,r.certified,r.control_state,r.compliance_state,r.incomplete_fields,r.invariant.result_admitted]; }",
        [False, False, "CONTROL_INCOMPLETE", "UNRESOLVED", ["result"], False],
    ))

    results.append(run_case(
        page,
        "deterministic structural identity",
        "() => { const i={title:'Identity',statement:'Same structure.',policy:'audit_receipt_required',evidence:'Visible evidence',owner:'audit_team',result:'PASS',exceptionReason:''}; const a=SAIL_AUD.certify(i); const b=SAIL_AUD.certify(i); return [a.control_id===b.control_id,a.control_certificate===b.control_certificate,a.policy_certificate===b.policy_certificate,a.evidence_certificate===b.evidence_certificate,a.record_id!==b.record_id,SAIL_AUD.deterministicId(i)===a.control_id]; }",
        [True, True, True, True, True, True],
    ))

    results.append(run_case(
        page,
        "public receipt guard",
        "() => { const r=SAIL_AUD.certify({title:'Receipt',statement:'Receipt guard.',policy:'audit_receipt_required',evidence:'Visible evidence',owner:'audit_team',result:'PASS',exceptionReason:''}); const before=SAIL_AUD.receiptFor(r); r.accepted=true; const after=SAIL_AUD.receiptFor(r); return [before,typeof after==='string'&&after.startsWith('AUDIT-')]; }",
        [None, True],
    ))

    results.append(run_case(
        page,
        "selected receipt lifecycle",
        "() => { SAIL_AUD.reset(); const before=SAIL_AUD.issueReceipt(); const accepted=SAIL_AUD.acceptSelected(); const after=SAIL_AUD.issueReceipt(); const p=SAIL_AUD.exportPack(); const c=p.structural_payload.controls[0]; return [before,accepted,after,c.receipt_state,typeof c.audit_receipt==='string'&&c.audit_receipt.startsWith('AUDIT-')]; }",
        [False, True, True, "AUDIT_RECEIPT_ISSUED", True],
    ))

    results.append(run_case(
        page,
        "multi-control register",
        "() => { SAIL_AUD.reset(); const before=SAIL_AUD.exportPack(); SAIL_AUD.newControl(); document.getElementById('title').value='Second Control'; document.getElementById('statement').value='Second control statement.'; document.getElementById('evidence').value='Second evidence'; document.getElementById('owner').value='second_team'; const second=SAIL_AUD.createOrUpdate(); const after=SAIL_AUD.exportPack(); const ids=after.operational_metadata.records.map(x=>x.record_id); return [before.evaluation_counts.total_control_count,after.evaluation_counts.total_control_count,new Set(ids).size,second.evaluation_certified]; }",
        [1, 2, 2, True],
    ))

    results.append(run_case(
        page,
        "certified pack",
        "() => { SAIL_AUD.reset(); const p=SAIL_AUD.exportPack(); return [p.pack_state,p.pack_certified,p.evaluation_counts.total_control_count,p.evaluation_counts.certified_control_count,p.evaluation_counts.incomplete_control_count]; }",
        ["COMPLIANCE_PACK_CERTIFIED", True, 1, 1, 0],
    ))

    results.append(run_case(
        page,
        "incomplete pack",
        "() => { SAIL_AUD.reset(); document.getElementById('statement').value=''; document.getElementById('evidence').value=''; document.getElementById('owner').value=''; SAIL_AUD.createOrUpdate(); const p=SAIL_AUD.exportPack(); return [p.pack_state,p.pack_certified,p.evaluation_counts.total_control_count,p.evaluation_counts.certified_control_count,p.evaluation_counts.incomplete_control_count]; }",
        ["COMPLIANCE_PACK_INCOMPLETE", False, 1, 0, 1],
    ))

    results.append(run_case(
        page,
        "partially certified pack",
        "() => { SAIL_AUD.reset(); SAIL_AUD.newControl(); document.getElementById('title').value='Incomplete'; document.getElementById('statement').value=''; document.getElementById('evidence').value=''; document.getElementById('owner').value=''; SAIL_AUD.createOrUpdate(); const p=SAIL_AUD.exportPack(); return [p.pack_state,p.pack_certified,p.evaluation_counts.total_control_count,p.evaluation_counts.certified_control_count,p.evaluation_counts.incomplete_control_count]; }",
        ["COMPLIANCE_PACK_PARTIALLY_CERTIFIED", False, 2, 1, 1],
    ))

    results.append(run_case(
        page,
        "structural operational separation",
        "() => { SAIL_AUD.reset(); const p=SAIL_AUD.exportPack(); const s=p.structural_payload.controls[0]; const o=p.operational_metadata.records[0]; return [Object.prototype.hasOwnProperty.call(s,'record_id'),Object.prototype.hasOwnProperty.call(s,'created_at'),Object.prototype.hasOwnProperty.call(o,'record_id'),Object.prototype.hasOwnProperty.call(o,'created_at'),p.operational_metadata.timestamp_fields_excluded_from_certificates]; }",
        [False, False, True, True, True],
    ))

    browser.close()

if page_errors:
    raise AssertionError("Browser page errors: " + " | ".join(page_errors))

print("SAIL Compliance and Audit Console v1.1.2 validation passed")
print(f"Source integrity checks: {len(source_checks)}")
print(f"Runtime behavioral checks: {len(results)}")
print("Application audit executions: 12000")
print("Failed checks: 0")
