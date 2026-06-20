from pathlib import Path
import json
import math
import re
import sys
import shutil

try:
    from playwright.sync_api import sync_playwright
except Exception:
    raise SystemExit("Playwright is required: python -m pip install playwright && playwright install chromium")

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_v5_9_0_Evidence_Integrity_Runtime.html"
ORACLES = ROOT / "SAIL_v5_9_0_behavioral_oracles.json"

html = HTML.read_text(encoding="utf-8")
oracle_pack = json.loads(ORACLES.read_text(encoding="utf-8"))
specifications = oracle_pack["specifications"]


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    return value


def equal(left, right):
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    return canonical(left) == canonical(right)


def execute_case(page, spec):
    return page.evaluate("""
    spec => {
      const pathValue=(value,path)=>!path?value:String(path).split('.').reduce((current,key)=>current===null||current===undefined?undefined:current[key],value);
      const canonical=value=>{
        if(value===undefined)return 'undefined';
        if(value===null||typeof value!=='object')return JSON.stringify(value);
        if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
        return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+canonical(value[key])).join(',')+'}';
      };
      const same=(a,b)=>canonical(a)===canonical(b);
      if(spec.op==='extract_path')return pathValue(SAIL.extract(spec.input),spec.path);
      if(spec.op==='api_path')return pathValue(SAIL[spec.api](...(spec.args||[])),spec.path);
      if(spec.op==='persistence_valid')return SAIL.restore(SAIL.exportPack(spec.input)).restore_state;
      if(spec.op==='persistence_context_tamper'){const pack=SAIL.exportPack(spec.input);pack.visible_context+=' tampered';return SAIL.restore(pack).restore_state;}
      if(spec.op==='persistence_replay_tamper'){const pack=SAIL.exportPack(spec.input);pack.replay_hash='00000000';return SAIL.restore(pack).restore_state;}
      if(spec.op==='compare_export'){const a=pathValue(SAIL.exportPack(spec.left),spec.path),b=pathValue(SAIL.exportPack(spec.right),spec.path);return same(a,b)?'equal':'different';}
      if(spec.op==='compare_extract'){const a=pathValue(SAIL.extract(spec.left),spec.path),b=pathValue(SAIL.extract(spec.right),spec.path);return same(a,b)?'equal':'different';}
      if(spec.op==='compare_api'){const a=pathValue(SAIL[spec.api](...(spec.left_args||[])),spec.path),b=pathValue(SAIL[spec.api](...(spec.right_args||[])),spec.path);return same(a,b)?'equal':'different';}
      throw new Error('UNKNOWN_SPEC_OPERATION');
    }
    """, spec)


def run_suite(browser, source, include_validation=True):
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(source, wait_until="load", timeout=120000)
    failures = []
    for spec in specifications:
        try:
            actual = execute_case(page, spec)
            if not equal(actual, spec["expected"]):
                failures.append({"id": spec["id"], "expected": spec["expected"], "actual": actual})
        except Exception as error:
            failures.append({"id": spec["id"], "expected": spec["expected"], "error": str(error)})
    report = page.evaluate("SAIL.behaviorAudit(true)")
    version = page.evaluate("SAIL.version()")
    validation = page.evaluate("SAIL.evidenceValidation(true)") if include_validation else None
    page.close()
    return failures, errors, report, version, validation


mutations = [
    {"name": "arithmetic_result_shift", "replacements": [("result:safeEval(s.expression,{})", "result:safeEval(s.expression,{})+1")]},
    {"name": "date_contradiction_disabled", "replacements": [
        ("if(/\\byesterday\\b/.test(low)&&/\\bnext\\s+friday\\b/.test(low))addContradiction(out,\"date\",[\"yesterday\",\"next_friday\"],\"conflicting_date_phrases\")", "if(false&&/\\byesterday\\b/.test(low)&&/\\bnext\\s+friday\\b/.test(low))addContradiction(out,\"date\",[\"yesterday\",\"next_friday\"],\"conflicting_date_phrases\")"),
        ("if(scenario===\"travel_booking\"&&/yesterday/i.test(text)&&/next\\s+friday/i.test(text))", "if(false&&scenario===\"travel_booking\"&&/yesterday/i.test(text)&&/next\\s+friday/i.test(text))")
    ]},
    {"name": "inventory_boundary_inclusive", "replacements": [("condition_true:s.stock<s.reorder_level,action:s.stock<s.reorder_level?", "condition_true:s.stock<=s.reorder_level,action:s.stock<=s.reorder_level?")]},
    {"name": "quorum_boundary_strict", "replacements": [("var quorum_met=certifiedNodes.length>=n.quorum;", "var quorum_met=certifiedNodes.length>n.quorum;")]},
    {"name": "realization_threshold_strict", "replacements": [("r.score>=r.threshold", "r.score>r.threshold")]},
]

with sync_playwright() as playwright:
    executable = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    launch_options = {"headless": True}
    if executable:
        launch_options["executable_path"] = executable
    browser = playwright.chromium.launch(**launch_options)
    failures, page_errors, report, version, validation = run_suite(browser, html)
    assert version == "5.9.0", version
    assert not page_errors, page_errors
    assert len(specifications) == 96
    assert not failures, failures
    assert report["allPass"] is True, report
    assert report["specification_count"] == 96
    assert report["independent_oracle"] is True
    assert validation["allPass"] is True, validation
    assert validation["synthetic_conformance_execution_count"] == 347400
    assert validation["behavioral_specification_count"] == 96
    environment_isolation_inputs = [
        "sqrt(document.title.length)",
        "sqrt(window.innerWidth)",
        "sqrt(location.href.length)",
        "sqrt(document.body.children.length)",
        "sqrt.constructor(1)",
        "sqrt(unknown_identifier)",
        "Math.random()",
    ]
    environment_isolation_results = []
    isolation_page = browser.new_page(viewport={"width": 1280, "height": 720})
    isolation_errors = []
    isolation_page.on("pageerror", lambda error: isolation_errors.append(str(error)))
    isolation_page.set_content(html, wait_until="load", timeout=120000)
    for expression in environment_isolation_inputs:
        before = isolation_page.evaluate("expression => SAIL.extract(expression)", expression)
        isolation_page.evaluate("document.title = 'ENVIRONMENT_CHANGED'; document.body.setAttribute('data-environment-test', 'changed')")
        isolation_page.set_viewport_size({"width": 1440, "height": 900})
        after = isolation_page.evaluate("expression => SAIL.extract(expression)", expression)
        passed = (
            before.get("status") == "ABSTAIN"
            and after.get("status") == "ABSTAIN"
            and before.get("certificate") == after.get("certificate")
        )
        environment_isolation_results.append({
            "input": expression,
            "before_status": before.get("status"),
            "after_status": after.get("status"),
            "certificate_stable": before.get("certificate") == after.get("certificate"),
            "passed": passed,
        })
    isolation_page.close()
    assert not isolation_errors, isolation_errors
    assert all(item["passed"] for item in environment_isolation_results), environment_isolation_results
    detected = []
    for mutation in mutations:
        name = mutation["name"]
        mutated = html
        for old, new in mutation["replacements"]:
            if old not in mutated:
                raise AssertionError(f"Mutation target missing: {name}")
            mutated = mutated.replace(old, new, 1)
        mutation_failures, mutation_errors, mutation_report, _, _ = run_suite(browser, mutated, include_validation=False)
        if mutation_errors:
            detected.append({"name": name, "detected": True, "mode": "runtime_error", "failures": len(mutation_failures)})
        else:
            caught = bool(mutation_failures) and mutation_report["allPass"] is False
            detected.append({"name": name, "detected": caught, "mode": "behavioral_failure", "failures": len(mutation_failures)})
    browser.close()

assert all(item["detected"] for item in detected), detected
print(json.dumps({
    "version": version,
    "external_behavioral_oracles": len(specifications),
    "behavioral_failures": 0,
    "synthetic_conformance_executions": validation["synthetic_conformance_execution_count"],
    "source_mutation_operators": len(detected),
    "source_mutations_detected": sum(1 for item in detected if item["detected"]),
    "environment_isolation_checks": len(environment_isolation_results),
    "environment_isolation_failures": sum(1 for item in environment_isolation_results if not item["passed"]),
    "environment_isolation_results": environment_isolation_results,
    "mutation_results": detected,
    "status": "PASS"
}, indent=2))
