"""
Command-line interface for Tula AI Code Audit
"""

import argparse
import sys
from pathlib import Path

from nikhil.tula.domain.code_audit.config import AuditConfig, resolve_config
from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor


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
  # Use auto-discovered configs
  tula-audit

  # Specify custom rules file
  tula-audit --rules MY_RULES.md

  # Specify all configs
  tula-audit --rules AGENTS.md --config llm_config.yaml --dependencies DEPS.md

  # Skip audit
  tula-audit --skip

Environment Variables:
  TULA_RULES_FILE        - Path to rules file (e.g., AGENTS.md)
  TULA_LLM_CONFIG        - Path to LLM config YAML
  TULA_DEPENDENCIES_FILE - Path to dependencies file
  SKIP_AI_AUDIT          - Set to '1' to skip audit

Config File Discovery:
  Searches in order:
  1. Current directory
  2. config/ subdirectory
  3. Parent directories (up to 3 levels)
  4. ~/.tula/ directory
  5. Package defaults
        """
    )
    
    parser.add_argument(
        '--rules',
        type=str,
        help='Path to rules file (e.g., AGENTS.md, ARCHITECTURE.md)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to LLM configuration file (llm_config.yaml)'
    )
    
    parser.add_argument(
        '--dependencies',
        type=str,
        help='Path to dependencies file (DEPENDENCIES.md)'
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
        '--max-tokens',
        type=int,
        default=14000,
        help='Maximum tokens per chunk (default: 14000)'
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
    
    # Build configuration from CLI args
    config = AuditConfig.from_cli_args(args)
    
    # Merge with environment
    env_config = AuditConfig.from_environment()
    if env_config.rules_file and not config.rules_file:
        config.rules_file = env_config.rules_file
    if env_config.llm_config_path and not config.llm_config_path:
        config.llm_config_path = env_config.llm_config_path
    if env_config.skip_audit:
        config.skip_audit = True
    
    # Resolve configuration (find files)
    config = resolve_config(config)
    
    # Validate configuration
    if not config.skip_audit and not config.rules_file:
        print_warning("No rules file found!")
        print("Searched for: AGENTS.md, ARCHITECTURE.md, RULES.md")
        print("\nOptions:")
        print("  1. Create AGENTS.md in current directory")
        print("  2. Use --rules to specify file")
        print("  3. Set AMSHA_RULES_FILE environment variable")
        print("\nProceeding with basic pattern matching only...")
    
    if args.verbose:
        print(f"\nConfiguration:")
        print(f"  Rules file: {config.rules_file or 'Not found'}")
        print(f"  LLM config: {config.llm_config_path or 'Not found'}")
        print(f"  Dependencies: {config.dependencies_file or 'Not found'}")
        print(f"  Max tokens: {config.max_tokens_per_chunk}")
        print()
    
    # Run audit
    auditor = AIAuditor(config)
    
    # Check if full repository audit requested
    if args.full_repo:
        output_path = Path(args.output) if args.output else None
        report = auditor.audit_repository(output_path)
        
        if report.get('error'):
            print_error(f"Audit failed: {report['error']}")
            return 1
        
        # Exit based on issues found
        if report['summary']['total_issues'] > 0:
            print_error(f"\\n🚫 Found {report['summary']['total_issues']} architectural violations")
            return 1
        else:
            print_success(f"\\n✨ Repository is compliant! No issues found.")
            return 0
    
    # Regular git diff audit
    result = auditor.audit()
    
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
