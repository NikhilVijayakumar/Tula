"""
Command-line interface for Tula AI Code Audit

This is a thin adapter layer that maps CLI arguments to TulaAuditor API.
"""

import argparse
import sys
from pathlib import Path

from nikhil.tula import TulaAuditor, AuditResult


class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  🤖 Tula AI Architecture Audit{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(msg: str):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog='tula-audit',
        description='AI-powered code review for architectural compliance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover tula_config.yaml
  tula-audit

  # Specify config file explicitly
  tula-audit --config my_config.yaml

  # Full repository audit
  tula-audit --full-repo --output audit_report.json

  # Skip audit
  tula-audit --skip

Config File (tula_config.yaml):
  Put all configuration in this file:
  - rules_file: path to AGENTS.md
  - llm_config_path: path to llm_config.yaml
  - output directories  
  - audit settings
  
  See config/tula_config.example.yaml for template.

Environment Variables:
  SKIP_AI_AUDIT - Set to '1' to skip audit

Config File Discovery:
  Searches in order:
  1. Current directory (tula_config.yaml)
  2. config/ subdirectory
  3. Parent directories (up to 3 levels)
  4. ~/.tula/ directory
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to tula_config.yaml (auto-discovered if not specified)'
    )
    
    parser.add_argument(
        '--skip',
        action='store_true',
        help='Skip the audit (exit with success)'
    )
    
    parser.add_argument(
        '--full-repo',
        action='store_true',
        help='Audit entire repository instead of just git diff'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for full repository audit report (JSON)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.5.3 (Tula Code Audit)'
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    print_header()
    
    # Create TulaAuditor from CLI args using factory method
    auditor = TulaAuditor.from_cli_args(args)
    
    if args.verbose:
        print(f"\nConfiguration:")
        print(f"  Model: {auditor.model_name or 'Pattern matching only'}")
        print(f"  Output: {auditor.output_directory}")
        print()
    
    # Run appropriate audit
    if args.full_repo:
        # Full repository audit
        output_path = Path(args.output) if args.output else None
        report = auditor.audit_repository(output_file=output_path)
        
        if report.get('error'):
            print_error(f"Audit failed: {report['error']}")
            return 1
        
        # Display results
        total_issues = report['summary']['total_issues']
        if total_issues > 0:
            print_error(f"\n🚫 Found {total_issues} architectural violations")
            return 1
        else:
            print_success(f"\n✨ Repository is compliant! No issues found.")
            return 0
    
    # Git diff audit (default)
    result = auditor.audit_git_diff()
    
    # Display results
    if result.skipped:
        print(f"ℹ️  {result.summary}")
        return 0
    
    print(f"\n{Colors.BOLD}Review Results:{Colors.ENDC}\n")
    
    if result.summary:
        print(f"📝 {result.summary}\n")
    
    if result.issues:
        print(f"{Colors.FAIL}{Colors.BOLD}Critical Issues:{Colors.ENDC}")
        for issue in result.issues:
            print(f"  ❌ {issue}")
        print()
    
    if result.suggestions:
        print(f"{Colors.WARNING}{Colors.BOLD}Suggestions:{Colors.ENDC}")
        for suggestion in result.suggestions:
            print(f"  💡 {suggestion}")
        print()
    
    if result.error:
        print_warning(f"Error occurred: {result.error}")
        print("Falling back to basic checks...")
    
    # Final verdict
    if result.approved:
        print_success("✨ Architectural review PASSED")
        print("ℹ️  Changes comply with architectural standards")
        return 0
    else:
        print_error("🚫 Architectural review FAILED")
        print_error("Please fix the issues above before committing")
        print("\nℹ️  To bypass: SKIP_AI_AUDIT=1 git commit -m '...'")
        print("⚠️  (Only bypass if you've manually verified compliance)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
