#!/usr/bin/env python
"""
Basic Usage Example for Tula

Demonstrates how to use TulaAuditor for code reviews.
This is the canonical example showing the library API.
"""

import sys
from pathlib import Path

# Add src to path for local development
repo_src = Path(__file__).parent.parent / "src"
if repo_src.exists():
    sys.path.insert(0, str(repo_src))

from nikhil.tula import TulaAuditor


def main():
    """Run a simple git diff audit using TulaAuditor"""
    
    print("=" * 70)
    print("Tula Code Audit - Local Testing Example")
    print("=" * 70)
    print()
    
    # Simple usage - auto-discovers tula_config.yaml
    # Looks for: tula_config.yaml in current/parent/config directories
    # If found: Uses config from file
    # If not found: Auto-discovers AGENTS.md, llm_config.yaml individually
    #auditor = TulaAuditor()
    
    # Alternative: Specify config file explicitly
    auditor = TulaAuditor("config/tula_config.yaml")
    
    print("Running git diff audit...")
    result = auditor.audit_git_diff()
    
    # Display results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    if result.skipped:
        print(f"ℹ️  {result.summary}")
        return 0
    
    print(f"Status: {'✅ APPROVED' if result.approved else '❌ FAILED'}")
    print(f"Summary: {result.summary}")
    print(f"Issues: {len(result.issues)}")
    print(f"Suggestions: {len(result.suggestions)}")
    
    if result.issues:
        print("\nCritical Issues:")
        for i, issue in enumerate(result.issues, 1):
            print(f"  {i}. {issue}")
    
    if result.suggestions:
        print("\nSuggestions:")
        for i, sug in enumerate(result.suggestions, 1):
            print(f"  {i}. {sug}")
    
    print()
    print("=" * 70)
    
    if result.approved:
        print("✅ Audit passed - ready to commit!")
    else:
        print("❌ Audit failed - please fix issues before committing")
    
    return 0 if result.approved else 1


if __name__ == "__main__":
    sys.exit(main())
