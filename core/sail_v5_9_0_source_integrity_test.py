from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "SAIL_v5_9_0_Evidence_Integrity_Runtime.html"
ORACLES = ROOT / "SAIL_v5_9_0_behavioral_oracles.json"
RUNTIME_TEST = ROOT / "sail_v5_9_0_runtime_behavior_test.py"
CONSOLE_TESTS = ROOT / "SAIL_v5_9_0_console_tests.txt"

for required_file in (HTML, ORACLES, RUNTIME_TEST, CONSOLE_TESTS):
    assert required_file.is_file(), f"Missing required release file: {required_file.name}"

html = HTML.read_text(encoding="utf-8")
oracles_text = ORACLES.read_text(encoding="utf-8")
runtime_test = RUNTIME_TEST.read_text(encoding="utf-8")
console_tests = CONSOLE_TESTS.read_text(encoding="utf-8")
oracles = json.loads(oracles_text)

assert html.count('version:"5.9.0"') == 1
assert 'expected_conformance_execution_count:347400' in html
assert 'expected_behavioral_specification_count:96' in html
assert 'expected_external_mutation_operator_count:5' in html
assert 'id="sail-v5-9-0-authoritative-conformance-release"' in html
assert 'id="sail-v5-9-0-evidence-integrity-release"' in html

for binding in (
    'window.SAIL.version=function(){return RELEASE.version;};',
    'window.SAIL.conformanceAudit=conformanceAudit;',
    'window.SAIL.behaviorAudit=behaviorAudit;',
    'window.SAIL.evidenceValidation=releaseValidation;',
    'window.SAIL.evidenceProfile=evidenceProfile;',
    'window.SAIL.benchmark=releaseValidation;',
    'window.SAIL.certify=releaseCertify;',
    'window.SAIL.realizationRuntime=realizationRuntime;',
    'window.SAIL.measureOutcome=measureOutcome;',
    'window.SAIL.verifyOutcome=verifyOutcome;',
    'window.SAIL.realizationCertificate=realizationCertificate;',
):
    assert binding in html, f"Missing public runtime binding: {binding}"

for behavior_marker in (
    'SYNTHETIC_STRUCTURAL_CONFORMANCE_EXECUTIONS',
    'EXTERNALLY_SPECIFIED_LITERAL_EXPECTATIONS',
    'ENVIRONMENT_ISOLATED_BOUNDED_EXPRESSION_EVALUATOR',
    'function boundedSafeEvalV590',
    'function validateBoundedExpressionStructureV590',
    'NON_FINITE_RESULT',
    'INVALID_DOMAIN_STEP',
    'tie_detected',
    'INVALID_THRESHOLD',
    'INCOMPLETE_REALIZATION_STRUCTURE',
):
    assert behavior_marker in html, f"Missing behavior marker: {behavior_marker}"

assert isinstance(oracles, dict)
assert oracles.get("specification_count") == 96
assert len(oracles.get("specifications", [])) == 96
assert 'source_mutation_operators' in runtime_test
assert 'source_mutations_detected' in runtime_test
assert 'environment_isolation_inputs' in runtime_test
assert 'environment_isolation_checks' in runtime_test
for forbidden_expression in (
    'sqrt(document.title.length)',
    'sqrt(window.innerWidth)',
    'sqrt(location.href.length)',
    'sqrt.constructor(1)',
    'Math.random()',
):
    assert forbidden_expression in runtime_test, f"Missing environment-isolation case: {forbidden_expression}"

assert not re.search(r'\bFunction(?:\.apply)?\s*\(', html), "Unbounded Function evaluator remains in runtime"

for section in (
    'EVIDENCE-HARDENED VALIDATION',
    'BACKWARD-COMPATIBLE CORE VALIDATION',
    'RUNTIME AVAILABILITY',
    'REALIZATION RUNTIME',
    'REALIZATION BOUNDARY VALIDATION',
    'FINAL COMBINED VALIDATION',
):
    assert section in console_tests, f"Missing console validation section: {section}"

assert not re.search(
    r'window\.SAIL\.(?:certify|benchmark|version)=function\s*\([^)]*\)\s*\{[^}]*!==false',
    html,
    re.S,
)

print("SAIL v5.9.0 source and release-package integrity checks passed")
