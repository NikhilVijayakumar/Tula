#!/usr/bin/env python
"""
Example: Audit entire repository

For comprehensive code quality checks.
"""

from nikhil.tula import TulaAuditor
from pathlib import Path

# Create auditor
auditor = TulaAuditor(
    config_path="tula_config.yaml",
    save_intermediate=True  # Save debugging info
)

print("🔍 Running full repository audit...")
print(f"Using LLM: {auditor.model_name or 'Pattern matching only'}")
print()

# Run full repository audit
report = auditor.audit_repository(
    output_file=Path(".tula/full_audit_report.json")
)

print("\n" + "=" * 60)
print("REPOSITORY AUDIT RESULTS")
print("=" * 60)
print()
print(f"Total files: {report['total_files']}")
print(f"Modules: {len(report['modules'])}")
print(f"Total violations: {report['total_violations']}")
print()

# Show per-module results
if report['modules']:
    print("Per-module results:")
    for module_name, module_data in report['modules'].items():
        issues = len(module_data['issues'])
        suggestions = len(module_data['suggestions'])
        print(f"  {module_name}: {issues} issues, {suggestions} suggestions")
print()

# Show files with violations
if report['files_with_violations']:
    print(f"Files with violations ({len(report['files_with_violations'])}):")
    for file in report['files_with_violations'][:10]:
        print(f"  - {file}")
    
    if len(report['files_with_violations']) > 10:
        print(f"  ... and {len(report['files_with_violations']) - 10} more")
print()

print(f"✅ Full report saved: {report['output_file']}")
