from pathlib import Path
import json
import re
import shutil

try:
    from playwright.sync_api import sync_playwright
except Exception:
    raise SystemExit("Playwright is required: python -m pip install playwright && playwright install chromium")

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_Federation_Operations_Console_v1_1_2.html"

if not HTML.is_file():
    raise SystemExit(f"Missing required release file: {HTML.name}")

html = HTML.read_text(encoding="utf-8")

source_checks = {
    "application title": '<title>SAIL Federation Operations Console v1.1.2</title>' in html,
    "application version": 'const VERSION="1.1.2";' in html,
    "core version": 'const SAIL_VERSION="5.9.0";' in html,
    "certified layers": "const LAYERS=37;" in html,
    "conformance count": "const CONFORMANCE_EXECUTIONS=347400;" in html,
    "behavioral count": "const BEHAVIORAL_SPECIFICATIONS=96;" in html,
    "mutation operator count": "const SOURCE_MUTATION_OPERATORS=5;" in html,
    "mutation detection count": "const SOURCE_MUTATIONS_DETECTED=5;" in html,
    "federation audit count": "const FEDERATION_AUDIT_CASES=43200;" in html,
    "application audit count": "const EXPECTED_AUDIT_CASES=9000;" in html,
    "role admission": 'const ROLES=Object.freeze(["coordinator","peer","auditor","observer"]);' in html,
    "state admission": 'const NODE_STATES=Object.freeze(["CERTIFIED","PENDING","BLOCKED"]);' in html,
    "configuration validation": "function validateNetworkConfiguration(input)" in html,
    "configured flag": 'configured:true' in html,
    "node invariant": "function nodeInvariant(input)" in html,
    "node integrity": "function nodeIntegrity(node)" in html,
    "snapshot isolation": "function snapshot(x)" in html,
    "deep freeze": "function deepFreeze(x)" in html,
    "fail closed clear": 'state:"NETWORK_CONFIGURATION_INVALID"' in html,
    "truthful pack certification": 'pack_certified:state==="FEDERATION_PACK_CERTIFIED"' in html,
    "certified pack state": "FEDERATION_PACK_CERTIFIED" in html,
    "unresolved pack state": "FEDERATION_PACK_UNRESOLVED" in html,
    "local application audit": 'application_audit_execution:"LOCAL_RUNTIME"' in html,
    "referenced core conformance": 'conformance_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced behavior": 'behavioral_validation:"REFERENCE_RELEASE_VALIDATION"' in html,
    "referenced federation audit": 'federation_audit_execution:"REFERENCE_RELEASE_VALIDATION"' in html,
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
        "() => [SAIL_FED.version(), SAIL_FED.stackVersion(), SAIL.certify().layers, SAIL.benchmark().benchmark_case_count]",
        ["1.1.2", "5.9.0", 37, 347400],
    ))

    results.append(run_case(
        page,
        "local application audit",
        "() => { const a=SAIL_FED.audit(true); return [a.allPass,a.case_count,a.expected_case_count,a.count_match,a.failed_case_count,a.scenario_count,a.iterations_per_scenario,a.classification,a.execution]; }",
        [True, 9000, 9000, True, 0, 6, 1500, "LOCAL_APPLICATION_CONFORMANCE_EXECUTIONS", "LOCAL_RUNTIME"],
    ))

    results.append(run_case(
        page,
        "referenced core evidence",
        "() => { const m=SAIL_FED.stackManifest(); return [m.conformance_classification,m.conformance_execution_count,m.conformance_execution,m.behavioral_specification_count,m.behavioral_validation,m.source_mutation_operator_count,m.source_mutations_detected,m.federation_audit_case_count,m.federation_audit_execution]; }",
        ["SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS", 347400, "REFERENCE_RELEASE_VALIDATION", 96, "REFERENCE_RELEASE_VALIDATION", 5, 5, 43200, "REFERENCE_RELEASE_VALIDATION"],
    ))

    results.append(run_case(
        page,
        "network configuration",
        "() => { const r=SAIL_FED.configureNetwork({network_id:'NETWORK_A',quorum:3}); const c=SAIL_FED.networkConfiguration(); return [r.configured,r.configuration_state,c.configured,c.network_id,c.quorum,typeof c.configuration_certificate==='string'&&c.configuration_certificate.startsWith('NETCFG-')]; }",
        [True, "NETWORK_CONFIGURATION_CERTIFIED", True, "NETWORK_A", 3, True],
    ))

    results.append(run_case(
        page,
        "invalid configuration does not mutate",
        "() => { SAIL_FED.configureNetwork({network_id:'NETWORK_A',quorum:3}); const before=SAIL_FED.networkConfiguration(); const invalid=SAIL_FED.configureNetwork({network_id:'',quorum:0}); const after=SAIL_FED.networkConfiguration(); return [invalid.configured,invalid.state,invalid.invalid_fields,before.network_id===after.network_id,before.quorum===after.quorum]; }",
        [False, "NETWORK_CONFIGURATION_INVALID", ["network_id", "quorum"], True, True],
    ))

    results.append(run_case(
        page,
        "node certificate independent from quorum",
        "() => { const input={network_id:'NETWORK_A',node_id:'Node A',role:'peer',scope:'scope',state:'CERTIFIED'}; SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); const a=SAIL_FED.certifyNode(input); SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:5}); const b=SAIL_FED.certifyNode(input); return [a.node_certificate===b.node_certificate,!('quorum' in a),!('quorum' in a.invariant),a.certified,b.certified]; }",
        [True, True, True, True, True],
    ))

    results.append(run_case(
        page,
        "invalid node admission",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); const role=SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'Role',role:'root',scope:'scope',state:'CERTIFIED'}); const state=SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'State',role:'peer',scope:'scope',state:'TRUSTED'}); const blank=SAIL_FED.certifyNode({network_id:'',node_id:'Blank',role:'peer',scope:'scope',state:'CERTIFIED'}); const n=SAIL_FED.networkState(); return [role.certified,role.identity_state,role.invalid_fields,state.certified,state.identity_state,state.invalid_fields,blank.certified,blank.network_id,blank.incomplete_fields,n.certified_node_count]; }",
        [False, "NODE_IDENTITY_INVALID", ["role"], False, "NODE_IDENTITY_INVALID", ["state"], False, "", ["network_id"], 0],
    ))

    results.append(run_case(
        page,
        "pending blocked and invalid exclusion",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'Good',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'Pending',role:'peer',scope:'scope',state:'PENDING'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'Blocked',role:'peer',scope:'scope',state:'BLOCKED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'Bad',role:'root',scope:'scope',state:'CERTIFIED'}); const n=SAIL_FED.resolveNetwork(); return [n.node_count,n.certified_node_count,n.quorum_met,n.consensus_met,n.federation_certified]; }",
        [4, 1, False, False, False],
    ))

    results.append(run_case(
        page,
        "returned node mutation isolation",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); const a=SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'PENDING'}); a.state='CERTIFIED'; a.certified=true; SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'peer',scope:'scope',state:'CERTIFIED'}); const n=SAIL_FED.resolveNetwork(); return [n.certified_node_count,n.quorum_met,n.federation_certified,n.nodes.find(x=>x.node_id==='A').state,n.nodes.find(x=>x.node_id==='A').certified]; }",
        [1, False, False, "PENDING", False],
    ))

    results.append(run_case(
        page,
        "network snapshot mutation isolation",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'peer',scope:'scope',state:'CERTIFIED'}); const first=SAIL_FED.networkState(); first.nodes[0].certified=false; first.nodes[0].state='BLOCKED'; const second=SAIL_FED.resolveNetwork(); return [second.certified_node_count,second.quorum_met,second.consensus_met,second.federation_certified,second.nodes[0].certified]; }",
        [2, True, True, True, True],
    ))

    results.append(run_case(
        page,
        "network identity consensus",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_B',node_id:'B',role:'peer',scope:'scope',state:'CERTIFIED'}); const n=SAIL_FED.resolveNetwork(); return [n.quorum_met,n.network_identity_aligned,n.scope_aligned,n.consensus_met,n.federation_certified]; }",
        [True, False, True, False, False],
    ))

    results.append(run_case(
        page,
        "scope consensus",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope_a',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'peer',scope:'scope_b',state:'CERTIFIED'}); const n=SAIL_FED.resolveNetwork(); return [n.quorum_met,n.network_identity_aligned,n.scope_aligned,n.consensus_met,n.federation_certified]; }",
        [True, True, False, False, False],
    ))

    results.append(run_case(
        page,
        "replay guard",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'CERTIFIED'}); return [SAIL_FED.replayNetwork(),SAIL_FED.networkState().replayed,SAIL_FED.networkState().replay_certificate]; }",
        [False, False, None],
    ))

    results.append(run_case(
        page,
        "audit guard and full lifecycle",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'coordinator',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'observer',scope:'scope',state:'CERTIFIED'}); const resolved=SAIL_FED.resolveNetwork(); const before=SAIL_FED.issueAudit(); const replay=SAIL_FED.replayNetwork(); const after=SAIL_FED.issueAudit(); const n=SAIL_FED.networkState(); return [resolved.federation_certified,before,replay,after,n.replayed,n.audited,typeof n.replay_certificate==='string'&&n.replay_certificate.startsWith('REPLAY-'),typeof n.audit_certificate==='string'&&n.audit_certificate.startsWith('AUDIT-')]; }",
        [True, False, True, True, True, True, True, True],
    ))

    results.append(run_case(
        page,
        "truthful pack lifecycle",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.resolveNetwork(); const resolved=SAIL_FED.exportPack(); SAIL_FED.replayNetwork(); const replayed=SAIL_FED.exportPack(); SAIL_FED.issueAudit(); const audited=SAIL_FED.exportPack(); return [resolved.pack_state,resolved.pack_certified,replayed.pack_state,replayed.pack_certified,audited.pack_state,audited.pack_certified]; }",
        ["FEDERATION_PACK_UNRESOLVED", False, "FEDERATION_PACK_UNRESOLVED", False, "FEDERATION_PACK_CERTIFIED", True],
    ))

    results.append(run_case(
        page,
        "invalid clear network is fail closed",
        "() => { SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'peer',scope:'scope',state:'CERTIFIED'}); const before=SAIL_FED.networkState(); const result=SAIL_FED.clearNetwork({network_id:'',quorum:0}); const after=SAIL_FED.networkState(); return [result.cleared,result.configured,result.state,result.invalid_fields,before.node_count===after.node_count,before.network_id===after.network_id,before.quorum===after.quorum]; }",
        [False, False, "NETWORK_CONFIGURATION_INVALID", ["network_id", "quorum"], True, True, True],
    ))

    results.append(run_case(
        page,
        "audit snapshot mutation isolation",
        "() => { const first=SAIL_FED.audit(true); first.allPass=false; first.case_count=1; const second=SAIL_FED.audit(); return [second.allPass,second.case_count,second.failed_case_count,second.cached]; }",
        [True, 9000, 0, True],
    ))

    results.append(run_case(
        page,
        "deterministic federation replay",
        "() => { const build=()=>{ SAIL_FED.clearNetwork({network_id:'NETWORK_A',quorum:2}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'A',role:'coordinator',scope:'scope',state:'CERTIFIED'}); SAIL_FED.certifyNode({network_id:'NETWORK_A',node_id:'B',role:'peer',scope:'scope',state:'CERTIFIED'}); SAIL_FED.resolveNetwork(); SAIL_FED.replayNetwork(); SAIL_FED.issueAudit(); return SAIL_FED.networkState(); }; const a=build(); const b=build(); return [a.network_configuration_certificate===b.network_configuration_certificate,a.nodes.map(x=>x.node_certificate).sort().join('|')===b.nodes.map(x=>x.node_certificate).sort().join('|'),a.network_certificate===b.network_certificate,a.replay_certificate===b.replay_certificate,a.audit_certificate===b.audit_certificate]; }",
        [True, True, True, True, True],
    ))

    if page_errors:
        raise AssertionError("Browser runtime errors: " + " | ".join(page_errors))

    browser.close()

print("SAIL Federation Operations Console v1.1.2 validation passed")
print(f"Source integrity checks: {len(source_checks)}")
print(f"Runtime behavioral checks: {len(results)}")
print("Application audit executions: 9000")
print("Failed checks: 0")
