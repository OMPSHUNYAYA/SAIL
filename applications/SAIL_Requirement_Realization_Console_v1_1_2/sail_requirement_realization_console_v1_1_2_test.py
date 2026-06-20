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
HTML = ROOT / "SAIL_Requirement_Realization_Console_v1_1_2.html"

if not HTML.is_file():
    raise SystemExit(f"Missing required release file: {HTML.name}")

html = HTML.read_text(encoding="utf-8")

source_checks = {
    "application title": '<title>SAIL Requirement Realization Console v1.1.2</title>' in html,
    "application version": 'const VERSION="1.1.2";' in html,
    "stack version": 'const SAIL_VERSION="5.9.0";' in html,
    "certified layers": "const LAYERS=37;" in html,
    "conformance count": "const CONFORMANCE_EXECUTIONS=347400;" in html,
    "behavioral count": "const BEHAVIORAL_SPECIFICATIONS=96;" in html,
    "mutation operators": "const SOURCE_MUTATION_OPERATORS=5;" in html,
    "mutation detection": "const SOURCE_MUTATIONS_DETECTED=5;" in html,
    "realization audit count": "const REALIZATION_AUDIT=48600;" in html,
    "application audit count": "const EXPECTED_AUDIT_CASES=10000;" in html,
    "snapshot clone": "function clone(x)" in html,
    "deep freeze": "function deepFreeze(x)" in html,
    "strict boolean admission": "function admittedBoolean(value)" in html,
    "expected validity": "expected_valid:expected.valid" in html,
    "actual validity": "actual_valid:actual.valid" in html,
    "invalid field reporting": 'invalid_fields.push("expected")' in html,
    "requirement certification": "function certifyRequirement(input)" in html,
    "workflow certification": "function certifyWorkflow(input,requirement)" in html,
    "execution certification": "function certifyExecution(input,workflow)" in html,
    "measurement certification": "function certifyMeasurement(input,execution)" in html,
    "outcome certification": "function certifyOutcome(input,measurement)" in html,
    "realization builder": "function buildRealization(input)" in html,
    "realization integrity": "function realizationIntegrity(result)" in html,
    "ledger integrity": "function ledgerInternal(result)" in html,
    "truthful blocked ledger": 'ledger_state:certified?"OUTCOME_LEDGER_CERTIFIED":"OUTCOME_LEDGER_BLOCKED"' in html,
    "truthful blocked pack": 'pack_state:certified?"REALIZATION_PACK_CERTIFIED":"REALIZATION_PACK_BLOCKED"' in html,
    "pack certified flag": "pack_certified:certified" in html,
    "blocked realization certificate": 'realization_certificate:realized?"REAL-"+hash(invariant):null' in html,
    "blocked ledger certificate": 'ledger_certificate:certified?"LEDGER-"+hash(invariant):null' in html,
    "threshold zero admission": "threshold.value>=0" in html,
    "score comparison": "input.score>=input.threshold" in html,
    "invalid boolean state": "OUTCOME_BLOCKED_INVALID_BOOLEAN" in html,
    "audit snapshot": "audit:function(force){return clone(auditInternal(force))}" in html,
    "current snapshot": "current:function(){return clone(LAST)}" in html,
    "stack manifest snapshot": "stackManifest:function(){return clone(stackManifest())}" in html,
    "export snapshot": "return clone(pack);" in html,
    "local runtime classification": 'application_audit_execution:"LOCAL_RUNTIME"' in html,
    "referenced conformance classification": 'conformance_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced behavior classification": 'behavioral_validation:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced realization classification": 'realization_audit_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "no random identity": "Math.random" not in html and "randomUUID" not in html,
    "no prior application version": "v1.1.1" not in html and "1.1.1" not in html,
    "no prior stack version": "5.8.1" not in html,
    "no internal markers": "TODO" not in html and "FIXME" not in html,
    "no html comments": "<!--" not in html,
    "no block comments": "/*" not in html,
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


pass_input = "{requirement:'Requirement: user can export report.',workflow:'Export Report Workflow',execution:'Export completed',measurement:'Report file generated',expected:true,actual:true,score:1,threshold:1}"

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
            "() => [SAIL_APP.version(),SAIL_APP.stackVersion(),SAIL.certify().layers,SAIL.benchmark().benchmark_case_count]",
            ["1.1.2", "5.9.0", 37, 347400],
        )
    )

    results.append(
        run_case(
            page,
            "local application audit",
            "() => { const a=SAIL_APP.audit(true); return [a.allPass,a.case_count,a.expected_case_count,a.count_match,a.failed_case_count,a.scenario_count,a.iterations_per_scenario,a.classification,a.execution]; }",
            [True, 10000, 10000, True, 0, 5, 2000, "LOCAL_APPLICATION_CONFORMANCE_EXECUTIONS", "LOCAL_RUNTIME"],
        )
    )

    results.append(
        run_case(
            page,
            "referenced release metadata",
            "() => { const m=SAIL_APP.stackManifest(); return [m.conformance_execution_count,m.conformance_execution,m.behavioral_specification_count,m.behavioral_validation,m.source_mutations_detected,m.realization_audit_case_count,m.realization_audit_execution]; }",
            [347400, "REFERENCE_RELEASE_VALIDATION", 96, "REFERENCE_RELEASE_VALIDATION", 5, 48600, "REFERENCE_RELEASE_VALIDATION"],
        )
    )

    results.append(
        run_case(
            page,
            "requirement independence",
            "() => { const r=SAIL_APP.requirement({requirement:'Requirement: user can export report.',workflow:''}); return [r.state,r.certified,!('workflow' in r.invariant),r.certificate.startsWith('REQ-')]; }",
            ["REQUIREMENT_CERTIFIED", True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "workflow separation",
            f"() => {{ const a=SAIL_APP.realize({pass_input}); const b=SAIL_APP.realize({{...{pass_input},workflow:'Alternative Export Workflow'}}); return [a.requirement.certificate===b.requirement.certificate,a.workflow.certificate!==b.workflow.certificate]; }}",
            [True, True],
        )
    )

    results.append(
        run_case(
            page,
            "complete realization integrity",
            f"() => {{ const r=SAIL_APP.realize({pass_input}); const i=SAIL_APP.integrity(r); return [r.realized,r.realization_state,r.realization_certificate.startsWith('REAL-'),i.valid,i.certified,i.reason]; }}",
            [True, "REALIZATION_CERTIFIED", True, True, True, None],
        )
    )

    results.append(
        run_case(
            page,
            "invalid expected admission",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:'yes',actual:true,score:1,threshold:1}); return [r.realized,r.invalid_fields,r.outcome.state,r.outcome.expected_valid,r.outcome.certificate,r.realization_certificate]; }",
            [False, ["expected"], "OUTCOME_BLOCKED_INVALID_BOOLEAN", False, None, None],
        )
    )

    results.append(
        run_case(
            page,
            "invalid actual admission",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:false,actual:'no',score:1,threshold:1}); return [r.realized,r.invalid_fields,r.outcome.state,r.outcome.actual_valid,r.outcome.certificate]; }",
            [False, ["actual"], "OUTCOME_BLOCKED_INVALID_BOOLEAN", False, None],
        )
    )

    results.append(
        run_case(
            page,
            "invalid numeric admission",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:true,actual:true,score:'bad',threshold:1}); return [r.realized,r.invalid_fields,r.measurement.state,r.measurement.certificate,r.outcome.score_match]; }",
            [False, ["score"], "MEASUREMENT_BLOCKED", None, False],
        )
    )

    results.append(
        run_case(
            page,
            "negative threshold rejection",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:true,actual:true,score:1,threshold:-1}); return [r.realized,r.invalid_fields,r.measurement.state,r.measurement.invariant.threshold,r.measurement.invariant.threshold_valid]; }",
            [False, ["threshold"], "MEASUREMENT_BLOCKED", None, False],
        )
    )

    results.append(
        run_case(
            page,
            "zero threshold admission",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:true,actual:true,score:0,threshold:0}); return [r.realized,r.measurement.certified,r.outcome.boolean_match,r.outcome.score_match]; }",
            [True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "boolean mismatch blocking",
            "() => { const r=SAIL_APP.realize({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:true,actual:false,score:1,threshold:1}); return [r.realized,r.outcome.state,r.outcome.boolean_match,r.outcome.score_match,r.outcome.certificate,r.realization_certificate]; }",
            [False, "OUTCOME_NOT_VERIFIED", False, True, None, None],
        )
    )

    results.append(
        run_case(
            page,
            "deterministic realization replay",
            f"() => {{ const a=SAIL_APP.realize({pass_input}); const b=SAIL_APP.realize({pass_input}); return [a.requirement.certificate===b.requirement.certificate,a.workflow.certificate===b.workflow.certificate,a.execution.certificate===b.execution.certificate,a.measurement.certificate===b.measurement.certificate,a.outcome.certificate===b.outcome.certificate,a.realization_certificate===b.realization_certificate]; }}",
            [True, True, True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "certified ledger",
            f"() => {{ const l=SAIL_APP.ledger({pass_input}); return [l.ledger_state,l.ledger_certified,l.integrity_reason,l.ledger_certificate.startsWith('LEDGER-'),l.chain.realization_certificate.startsWith('REAL-')]; }}",
            ["OUTCOME_LEDGER_CERTIFIED", True, None, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "blocked ledger",
            "() => { const l=SAIL_APP.ledger({requirement:'R',workflow:'W',execution:'E',measurement:'M',expected:true,actual:false,score:1,threshold:1}); return [l.ledger_state,l.ledger_certified,l.integrity_reason,l.chain.outcome_certificate,l.chain.realization_certificate,l.ledger_certificate]; }",
            ["OUTCOME_LEDGER_BLOCKED", False, "REALIZATION_NOT_CERTIFIED", None, None, None],
        )
    )

    results.append(
        run_case(
            page,
            "certified pack",
            "() => { SAIL_APP.reset(); const p=SAIL_APP.exportPack(); return [p.pack_state,p.pack_certified,p.integrity_reason,p.delivery_mode,p.result.realized,p.ledger.ledger_certified,p.ledger.chain.realization_certificate===p.result.realization_certificate]; }",
            ["REALIZATION_PACK_CERTIFIED", True, None, "view", True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "blocked pack",
            "() => { SAIL_APP.loadExample('blocked'); const p=SAIL_APP.exportPack(); return [p.pack_state,p.pack_certified,p.integrity_reason,p.result.realized,p.result.realization_certificate,p.ledger.ledger_state,p.ledger.ledger_certificate]; }",
            ["REALIZATION_PACK_BLOCKED", False, "REALIZATION_NOT_CERTIFIED", False, None, "OUTCOME_LEDGER_BLOCKED", None],
        )
    )

    results.append(
        run_case(
            page,
            "returned run snapshot isolation",
            "() => { const x=SAIL_APP.reset(); x.realized=false; x.realization_certificate='REAL-FORGED'; x.outcome.certified=false; const c=SAIL_APP.current(); const p=SAIL_APP.exportPack(); return [c.realized,c.realization_certificate!=='REAL-FORGED',c.outcome.certified,p.pack_certified]; }",
            [True, True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "audit snapshot isolation",
            "() => { const a=SAIL_APP.audit(true); a.allPass=false; a.case_count=1; a.failed_case_count=999; const b=SAIL_APP.audit(); return [a===b,b.allPass,b.case_count,b.failed_case_count,b.cached]; }",
            [False, True, 10000, 0, True],
        )
    )

    results.append(
        run_case(
            page,
            "pack snapshot isolation",
            "() => { SAIL_APP.reset(); const a=SAIL_APP.exportPack(); a.pack_certified=false; a.result.realized=false; a.ledger.ledger_certified=false; const b=SAIL_APP.exportPack(); return [b.pack_certified,b.result.realized,b.ledger.ledger_certified]; }",
            [True, True, True],
        )
    )

    results.append(
        run_case(
            page,
            "forged realization rejection",
            f"() => {{ const r=SAIL_APP.realize({pass_input}); r.outcome.certificate='OUT-FORGED'; const i=SAIL_APP.integrity(r); return [i.valid,i.certified,i.reason]; }}",
            [False, False, "OUTCOME_INTEGRITY_INVALID"],
        )
    )

    results.append(
        run_case(
            page,
            "status bar alignment",
            "() => { SAIL_APP.reset(); return [document.getElementById('reqState').textContent,document.getElementById('workflowState').textContent,document.getElementById('execState').textContent,document.getElementById('measureState').textContent,document.getElementById('outcomeState').textContent,document.getElementById('certState').textContent,document.getElementById('appStatus').textContent]; }",
            ["CERTIFIED", "CERTIFIED", "CERTIFIED", "CERTIFIED", "VERIFIED", "ISSUED", "CERTIFIED"],
        )
    )

    results.append(
        run_case(
            page,
            "blocked interface alignment",
            "() => { SAIL_APP.loadExample('blocked'); return [document.getElementById('reqState').textContent,document.getElementById('workflowState').textContent,document.getElementById('execState').textContent,document.getElementById('measureState').textContent,document.getElementById('outcomeState').textContent,document.getElementById('certState').textContent,document.getElementById('appStatus').textContent]; }",
            ["CERTIFIED", "CERTIFIED", "CERTIFIED", "CERTIFIED", "BLOCKED", "BLOCKED", "ATTENTION"],
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

print("SAIL Requirement Realization Console v1.1.2 validation passed")
print(f"Source integrity checks: {len(source_checks)}")
print(f"Runtime behavioral checks: {len(results)}")
print("Application audit executions: 10000")
print("Failed checks: 0")
