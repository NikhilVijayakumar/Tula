"""
Tula Code Auditor - Main Orchestrator

Simple interface for running code audits in 2 scenarios:
1. Git diff audit (before commit)
2. Full repository audit

Usage:
    from nikhil.tula import TulaAuditor
    
    auditor = TulaAuditor("tula_config.yaml")
    result = auditor.audit_git_diff()  # Scenario 1
    # OR
    result = auditor.audit_repository()  # Scenario 2
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from nikhil.tula.domain.code_audit.config import AuditConfig, resolve_config
from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor, AuditResult
from nikhil.tula.domain.code_audit.report_manager import ReportManager, AuditReport
from nikhil.tula.domain.code_audit.markdown_formatter import MarkdownFormatter
from nikhil.vak.domain.llm_factory.service.llm_builder import LLMBuilder
from nikhil.vak.domain.llm_factory.settings.llm_settings import LLMSettings


class TulaAuditor:
    """
    Main orchestrator for Tula code audits
    
    Provides simple interface for both audit scenarios:
    - Git diff audit (pre-commit checks)
    - Full repository audit
    
    Example:
        # Basic usage
        auditor = TulaAuditor("tula_config.yaml")
        result = auditor.audit_git_diff()
        
        # Custom config
        auditor = TulaAuditor(
            config_path="my_config.yaml",
            rules_file="ARCHITECTURE.md",
            save_intermediate=True
        )
        result = auditor.audit_repository()
        
        # Check results
        if result.approved:
            print(f"✅ Audit passed - ready to commit!")
        else:
            for issue in result.issues:
                print(f"❌ {issue}")
    """
    
    @classmethod
    def from_cli_args(cls, args):
        """
        Create TulaAuditor from CLI arguments
        
        Convenience factory method for CLI adapter.
        Maps --config argument to TulaAuditor(config_path).
        
        Args:
            args: argparse.Namespace with CLI arguments
            
        Returns:
            TulaAuditor instance configured from config file
        
        Example:
            parser = argparse.ArgumentParser()
            parser.add_argument('--config', type=str)
            args = parser.parse_args()
            
            auditor = TulaAuditor.from_cli_args(args)
        """
        config_path = getattr(args, 'config', None)
        return cls(config_path)
    
    def __init__(self, config_path: Optional[str | Path] = None):
        """
        Initialize Tula Auditor
        
        **Simplified Config-Driven Approach:**
        - If config_path provided: Load from that file
        - If not provided: Auto-discover tula_config.yaml
        - If no config found: Use sensible defaults
        
        All configuration (rules, LLM, output, etc.) comes from the config file.
        No need for individual parameter overrides - keep it in config.
        
        Args:
            config_path: Optional path to tula_config.yaml
                        If None, auto-discovers in current/parent/config directories
        
        Examples:
            # Auto-discover config
            auditor = TulaAuditor()
            
            # Explicit config
            auditor = TulaAuditor("path/to/tula_config.yaml")
        """
        # Load configuration from file (or use defaults)
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                self.config = AuditConfig.from_tula_config(config_file)
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")
        else:
            # Auto-discover tula_config.yaml
            from nikhil.tula.domain.code_audit.config import find_tula_config
            tula_config_path = find_tula_config()
            
            if tula_config_path:
                self.config = AuditConfig.from_tula_config(tula_config_path)
            else:
                # No config found - use defaults with auto-discovery
                self.config = AuditConfig()
        
        # Resolve configuration (auto-discover rules, llm_config if not in tula_config)
        self.config = resolve_config(self.config)
        
        # Ensure output directories exist
        self.config.output.ensure_directories()
        
        # Initialize internal components
        self._ai_auditor = AIAuditor(self.config)
        self._report_manager = ReportManager(self.config.output.get_final_path())
        self._markdown_formatter = None
    
    def audit_git_diff(self) -> AuditResult:
        """
        Scenario 1: Audit git diff (pre-commit)
        
        Audits only the staged changes (git diff --cached).
        Fast, suitable for pre-commit hooks.
        
        Returns:
            AuditResult with issues, suggestions, and approval status
        
        Example:
            auditor = TulaAuditor()
            result = auditor.audit_git_diff()
            
            if not result.approved:
                print(f"Found {len(result.issues)} issues")
                exit(1)
        """
        return self._ai_auditor.audit()
    
    def audit_repository(self, 
                        output_file: Optional[Path] = None,
                        module_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Scenario 2: Audit entire repository
        
        Performs comprehensive audit of all Python files in the repository.
        Slower, suitable for CI/CD or periodic checks.
        
        Args:
            output_file: Where to save detailed report (optional)
            module_filter: Only audit specific module (e.g., "nikhil.tula.domain")
        
        Returns:
            Dict with detailed audit results
        
        Example:
            auditor = TulaAuditor()
            report = auditor.audit_repository()
            
            print(f"Total files: {report['total_files']}")
            print(f"Violations: {report['total_violations']}")
        """
        return self._ai_auditor.audit_repository(output_file)
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent audit report (JSON)
        
        Returns:
            Latest audit report as dict, or None if no reports
        """
        import json
        
        latest_json = self.config.output.get_final_path() / "latest.json"
        if latest_json.exists():
            with open(latest_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_latest_report_markdown(self) -> Optional[str]:
        """
        Get the most recent audit report (Markdown)
        
        Returns:
            Latest audit report as markdown string, or None if no reports
        """
        latest_md = self.config.output.get_final_path() / "latest.md"
        if latest_md.exists():
            with open(latest_md, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def get_history(self, limit: int = 10) -> list:
        """
        Get historical audit reports
        
        Args:
            limit: Maximum number of reports to return
        
        Returns:
            List of AuditReport objects (most recent first)
        """
        return self._report_manager.get_history(limit=limit)
    
    def generate_comparison_report(self, limit: int = 10) -> str:
        """
        Generate historical comparison report
        
        Args:
            limit: Number of recent reports to compare
        
        Returns:
            Markdown report showing trends and comparisons
        """
        return self._report_manager.generate_comparison_report(limit=limit)
    
    def save_audit_result(self, 
                         result: AuditResult,
                         save_history: bool = True,
                         use_llm_markdown: bool = False) -> Dict[str, Path]:
        """
        Save audit result to reports
        
        Args:
            result: AuditResult from audit_git_diff()
            save_history: Save timestamped copy
            use_llm_markdown: Use LLM to format markdown (vs template)
        
        Returns:
            Dict of saved file paths
        
        Example:
            result = auditor.audit_git_diff()
            files = auditor.save_audit_result(result)
            print(f"Saved to: {files['latest_json']}")
        """
        # Create audit report
        audit_report = AuditReport(
            timestamp=datetime.now().isoformat(),
            git_commit=self._get_git_commit(),
            model_used=self._ai_auditor.model_name or "pattern-matching",
            rules_file=str(self.config.rules_file) if self.config.rules_file else "none",
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
        saved_files = self._report_manager.save_report(audit_report, save_history=save_history)
        
        # Optionally generate LLM-formatted markdown
        if use_llm_markdown and self._ai_auditor.llm:
            try:
                self._ensure_markdown_formatter()
                markdown = self._markdown_formatter.format_json_to_markdown(
                    audit_report.to_dict(),
                    use_llm=True
                )
                
                llm_md_path = self.config.output.get_final_path() / "report_llm_formatted.md"
                with open(llm_md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                saved_files['llm_formatted_md'] = llm_md_path
            except Exception as e:
                print(f"⚠️  LLM markdown formatting failed: {e}")
        
        return saved_files
    
    def _ensure_markdown_formatter(self):
        """Initialize markdown formatter if needed"""
        if self._markdown_formatter is None:
            # Try to load creative LLM for formatting
            if self.config.llm_config_path:
                try:
                    llm_settings = LLMSettings.from_yaml_file(self.config.llm_config_path)
                    builder = LLMBuilder(llm_settings)
                    creative_llm = builder.build_creative()
                    self._markdown_formatter = MarkdownFormatter(creative_llm.llm)
                except:
                    # Fallback to evaluation LLM or template
                    self._markdown_formatter = MarkdownFormatter(self._ai_auditor.llm)
            else:
                self._markdown_formatter = MarkdownFormatter(None)
    
    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
        except:
            pass
        return None
    
    @property
    def model_name(self) -> Optional[str]:
        """Get the LLM model name being used"""
        return self._ai_auditor.model_name
    
    @property
    def has_llm(self) -> bool:
        """Check if LLM is configured and available"""
        return self._ai_auditor.llm is not None
    
    @property
    def output_directory(self) -> Path:
        """Get the output directory path"""
        return self.config.output.base_dir
