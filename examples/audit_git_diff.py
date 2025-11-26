#!/usr/bin/env python
"""
Simple example: Audit git diff before commit

This is the most common use case for Tula.
"""

from nikhil.tula import TulaAuditor

# Create auditor (auto-detects tula_config.yaml)
auditor = TulaAuditor()

print(f"Using LLM: {auditor.model_name or 'Pattern matching only'}")
print()

# Run audit on staged changes
print("Running audit...")
result = auditor.audit_git_diff()

# Save results
files = auditor.save_audit_result(result, save_history=True)
print(f"\n✅ Report saved: {files['latest_md']}")

# Check if approved
if result.approved:
    print("\n✅ AUDIT PASSED - Ready to commit!")
    exit(0)
else:
    print(f"\n❌ AUDIT FAILED - {len(result.issues)} issues found:")
    for i, issue in enumerate(result.issues[:5], 1):
        print(f"  {i}. {issue}")
    
    if len(result.issues) > 5:
        print(f"  ... and {len(result.issues) - 5} more")
    
    exit(1)
