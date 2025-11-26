#!/usr/bin/env python
"""
Example: Use Tula in client project

This shows how a client project would use Tula as a dependency.
"""

# Install: pip install tula
from nikhil.tula import TulaAuditor

# Simple usage - auto-detects tula_config.yaml in project root
def quick_audit():
    """Quick pre-commit audit"""
    auditor = TulaAuditor()
    result = auditor.audit_git_diff()
    
    if not result.approved:
        print("❌ Audit failed!")
        for issue in result.issues:
            print(f"  • {issue}")
        return False
    
    print("✅ Audit passed!")
    return True


# Custom configuration
def custom_audit():
    """Audit with custom settings"""
    auditor = TulaAuditor(
        config_path="config/tula_config.yaml",  # Custom location
        rules_file="docs/ARCHITECTURE.md",      # Custom rules
        output_dir=".tula/audits",              # Custom output
        save_intermediate=True                   # Enable debugging
    )
    
    # Audit git diff
    result = auditor.audit_git_diff()
    
    # Save with LLM-formatted markdown
    files = auditor.save_audit_result(
        result,
        save_history=True,
        use_llm_markdown=True  # Use LLM for beautiful markdown
    )
    
    print(f"Report: {files['latest_md']}")
    
    return result.approved


# Full repository audit
def full_audit():
    """Comprehensive repository audit"""
    auditor = TulaAuditor()
    
    # Audit entire repo
    report = auditor.audit_repository()
    
    # Check results
    if report['total_violations'] > 0:
        print(f"Found {report['total_violations']} violations")
        return False
    
    print("Repository is clean!")
    return True


# Historical analysis
def check_trends():
    """Analyze audit trends over time"""
    auditor = TulaAuditor()
    
    # Get comparison report
    comparison = auditor.generate_comparison_report(limit=10)
    print(comparison)
    
    # Get history
    history = auditor.get_history(limit=5)
    print(f"\nLast {len(history)} audits:")
    for report in history:
        status = "✅" if report.approved else "❌"
        print(f"  {status} {report.timestamp}: {report.total_issues} issues")


if __name__ == "__main__":
    import sys
    
    # Run quick audit
    if not quick_audit():
        sys.exit(1)
    
    # Optionally check trends
    # check_trends()
