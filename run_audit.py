#!/usr/bin/env python
"""
Tula Code Audit - Real Example Script

This script demonstrates how to run a complete code audit with:
1. Pattern matching (fast, local)
2. LLM analysis (uses your configured LLM - local or cloud)
3. Combined results with deduplication
4. Intermediate analysis results saved
5. Final reports (JSON + Markdown)

Usage:
    python run_audit.py [--config path/to/tula_config.yaml]

This works with:
- Local LLMs (LM Studio, Ollama via LiteLLM)
- Cloud LLMs (OpenAI, Gemini, Claude via LiteLLM)
- No LLM (pattern matching only)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path (for running in Tula repo)
repo_src = Path(__file__).parent / "src"
if repo_src.exists():
    sys.path.insert(0, str(repo_src))

try:
    from nikhil.tula.domain.code_audit.config import AuditConfig, resolve_config, find_tula_config
    from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor
    from nikhil.tula.domain.code_audit.report_manager import ReportManager, AuditReport
    from nikhil.tula.domain.code_audit.markdown_formatter import MarkdownFormatter
    from nikhil.tula.domain.llm_factory.service.llm_builder import LLMBuilder
    from nikhil.tula.domain.llm_factory.settings.llm_settings import LLMSettings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you've installed Tula:")
    print("  pip install -e .")
    print("\nOr if using as dependency:")
    print("  pip install tula")
    sys.exit(1)


def run_audit(config_path: Path = None):
    """
    Run complete audit with pattern matching + LLM
    
    Args:
        config_path: Optional path to tula_config.yaml
    """
    print("=" * 70)
    print("Tula Code Audit - Combined Approach")
    print("=" * 70)
    print()
    
    # Step 1: Load configuration
    print("📋 Step 1: Loading configuration...")
    
    if config_path and config_path.exists():
        print(f"  Using config: {config_path}")
        config = AuditConfig.from_tula_config(config_path)
    else:
        # Try to find tula_config.yaml
        found_config = find_tula_config()
        if found_config:
            print(f"  Found config: {found_config}")
            config = AuditConfig.from_tula_config(found_config)
        else:
            print("  No config found, using defaults")
            config = AuditConfig()
    
    # Resolve config (find files)
    config = resolve_config(config)
    
    print(f"  Rules: {config.rules_file or 'Not found'}")
    print(f"  LLM Config: {config.llm_config_path or 'Not found'}")
    print(f"  Output: {config.output.base_dir}")
    print(f"  Intermediate: {config.output.get_intermediate_path() or 'Disabled'}")
    print()
    
    # Step 2: Initialize auditor
    print("🔧 Step 2: Initializing auditor...")
    auditor = AIAuditor(config)
    print("  ✅ Auditor ready")
    print()
    
    # Step 3: Run audit (pattern matching + LLM)
    print("🚀 Step 3: Running audit...")
    print()
    
    try:
        result = auditor.audit()
        
        print()
        print("=" * 70)
        print("AUDIT RESULTS")
        print("=" * 70)
        print()
        print(f"Status: {'✅ APPROVED' if result.approved else '❌ NOT APPROVED'}")
        print(f"Issues: {len(result.issues)}")
        print(f"Suggestions: {len(result.suggestions)}")
        print(f"Summary: {result.summary}")
        
        if result.skipped:
            print("\n⚠️  Audit was skipped")
            if result.error:
                print(f"Reason: {result.error}")
            return
        
        if result.error:
            print(f"\n⚠️  Error: {result.error}")
        
        print()
        
        # Show issues
        if result.issues:
            print("Issues:")
            for i, issue in enumerate(result.issues, 1):
                print(f"  {i}. {issue}")
            print()
        
        # Show suggestions
        if result.suggestions:
            print("Suggestions:")
            for i, sug in enumerate(result.suggestions[:5], 1):
                print(f"  {i}. {sug}")
            if len(result.suggestions) > 5:
                print(f"  ... and {len(result.suggestions) - 5} more")
            print()
        
        # Step 4: Save reports
        print("💾 Step 4: Saving reports...")
        
        # Ensure output directories exist
        config.output.ensure_directories()
        
        # Create audit report
        audit_report = AuditReport(
            timestamp=datetime.now().isoformat(),
            git_commit=None,  # Could get from git
            model_used=auditor.model_name if auditor.model_name else "pattern-matching",
            rules_file=str(config.rules_file) if config.rules_file else "none",
            approved=result.approved,
            total_issues=len(result.issues),
            total_suggestions=len(result.suggestions),
            issues=result.issues,
            suggestions=result.suggestions,
            summary=result.summary,
            metadata={
                "skipped": result.skipped,
                "error": result.error,
            }
        )
        
        # Save with report manager
        report_manager = ReportManager(config.output.get_final_path())
        saved_files = report_manager.save_report(audit_report, save_history=True)
        
        print(f"  ✅ {saved_files['latest_json']}")
        print(f"  ✅ {saved_files['latest_md']}")
        print(f"  ✅ {saved_files['history_json']}")
        print()
        
        # Step 5: Generate markdown with LLM (optional)
        if auditor.llm and config.llm_config_path:
            print("🎨 Step 5: Generating LLM-powered markdown...")
            
            try:
                # Try to load creative LLM for formatting
                llm_settings = LLMSettings.from_yaml_file(config.llm_config_path)
                builder = LLMBuilder(llm_settings)
                
                # Try creative LLM first, fallback to evaluation
                try:
                    creative_llm = builder.build_creative()
                    formatter = MarkdownFormatter(creative_llm.llm)
                    print("  Using creative LLM for formatting")
                except:
                    formatter = MarkdownFormatter(auditor.llm)
                    print("  Using evaluation LLM for formatting")
                
                # Format with LLM
                markdown = formatter.format_json_to_markdown(audit_report.to_dict(), use_llm=True)
                
                # Save LLM-formatted version
                llm_md_path = config.output.get_final_path() / "report_llm_formatted.md"
                with open(llm_md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                print(f"  ✅ {llm_md_path}")
                print()
            except Exception as e:
                print(f"  ⚠️  LLM formatting failed: {e}")
                print("  Using template-based markdown instead")
                print()
        
        # Step 6: Show file structure
        print("📁 Generated files:")
        print()
        
        final_dir = config.output.get_final_path()
        for file in sorted(final_dir.rglob("*")):
            if file.is_file():
                rel_path = file.relative_to(final_dir.parent)
                size = file.stat().st_size
                print(f"  {rel_path} ({size:,} bytes)")
        
        intermediate_dir = config.output.get_intermediate_path()
        if intermediate_dir and intermediate_dir.exists():
            print()
            for file in sorted(intermediate_dir.rglob("*")):
                if file.is_file():
                    rel_path = file.relative_to(intermediate_dir.parent)
                    size = file.stat().st_size
                    print(f"  {rel_path} ({size:,} bytes)")
        
        print()
        print("=" * 70)
        print("✅ AUDIT COMPLETE")
        print("=" * 70)
        print()
        print("Next steps:")
        print(f"  • Review: {config.output.get_final_path()}/latest.md")
        if intermediate_dir and intermediate_dir.exists():
            print(f"  • Debug: {intermediate_dir}/analysis/")
        print(f"  • History: {config.output.get_final_path()}/history/")
        
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Tula code audit with combined pattern matching + LLM approach"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to tula_config.yaml (auto-detected if not specified)"
    )
    
    args = parser.parse_args()
    
    run_audit(args.config)


if __name__ == "__main__":
    main()
