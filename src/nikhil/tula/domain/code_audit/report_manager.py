"""
Report management for Tula code audit

Handles:
- Report generation (JSON and Markdown)
- Timestamped history
- Latest report (always overwritten)
- Historical comparison
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class AuditReport:
    """Audit report data structure"""
    timestamp: str
    git_commit: Optional[str]
    model_used: str
    rules_file: str
    approved: bool
    total_issues: int
    total_suggestions: int
    issues: List[str]
    suggestions: List[str]
    summary: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class ReportManager:
    """Manages audit report generation and history"""
    
    def __init__(self, output_dir: Path):
        """
        Initialize report manager
        
        Args:
            output_dir: Base output directory (e.g., .tula/output/final/)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # History directory for timestamped reports
        self.history_dir = self.output_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
    
    def save_report(self, report: AuditReport, save_history: bool = True) -> Dict[str, Path]:
        """
        Save audit report
        
        Creates:
        1. latest.json - Always overwritten (current run)
        2. latest.md - Always overwritten (human-readable)
        3. history/audit_YYYYMMDD_HHMMSS.json - Timestamped (if save_history=True)
        4. history/audit_YYYYMMDD_HHMMSS.md - Timestamped markdown
        
        Args:
            report: AuditReport to save
            save_history: Whether to save timestamped copy
        
        Returns:
            Dict of file paths created
        """
        created_files = {}
        
        # 1. Save latest.json (always overwritten)
        latest_json = self.output_dir / "latest.json"
        with open(latest_json, 'w', encoding='utf-8') as f:
            f.write(report.to_json())
        created_files['latest_json'] = latest_json
        
        # 2. Save latest.md (always overwritten)
        latest_md = self.output_dir / "latest.md"
        with open(latest_md, 'w', encoding='utf-8') as f:
            f.write(self._to_markdown(report))
        created_files['latest_md'] = latest_md
        
        # 3. Save timestamped history (optional)
        if save_history:
            # Extract timestamp from report or use current time
            timestamp = report.timestamp.replace(':', '').replace('-', '').replace(' ', '_')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + '_' + timestamp.split('T')[1].split('.')[0]
            
            history_json = self.history_dir / f"audit_{timestamp}.json"
            with open(history_json, 'w', encoding='utf-8') as f:
                f.write(report.to_json())
            created_files['history_json'] = history_json
            
            history_md = self.history_dir / f"audit_{timestamp}.md"
            with open(history_md, 'w', encoding='utf-8') as f:
                f.write(self._to_markdown(report))
            created_files['history_md'] = history_md
        
        return created_files
    
    def get_history(self, limit: Optional[int] = None) -> List[AuditReport]:
        """
        Get historical audit reports
        
        Args:
            limit: Maximum number of reports to return (most recent first)
        
        Returns:
            List of AuditReport objects sorted by timestamp (newest first)
        """
        history_files = sorted(self.history_dir.glob("audit_*.json"), reverse=True)
        
        if limit:
            history_files = history_files[:limit]
        
        reports = []
        for file_path in history_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports.append(AuditReport(**data))
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        
        return reports
    
    def generate_comparison_report(self, limit: int = 10) -> str:
        """
        Generate historical comparison report
        
        Shows trends over time:
        - Issues count over time
        - Approval rate
        - Common issues
        - Improvements/regressions
        
        Args:
            limit: Number of recent reports to compare
        
        Returns:
            Markdown report showing historical comparison
        """
        reports = self.get_history(limit=limit)
        
        if not reports:
            return "# Historical Comparison\n\nNo historical data available."
        
        md = ["# Historical Code Audit Comparison\n"]
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Reports Analyzed:** {len(reports)}\n")
        
        # Summary statistics
        md.append("## Summary Statistics\n")
        md.append("| Date | Model | Approved | Issues | Suggestions |")
        md.append("|------|-------|----------|--------|-------------|")
        
        for report in reports:
            date = report.timestamp.split('T')[0] if 'T' in report.timestamp else report.timestamp[:10]
            status = "✅" if report.approved else "❌"
            md.append(f"| {date} | {report.model_used} | {status} | {report.total_issues} | {report.total_suggestions} |")
        
        # Trend analysis
        md.append("\n## Trend Analysis\n")
        
        if len(reports) >= 2:
            latest = reports[0]
            previous = reports[1]
            
            issue_change = latest.total_issues - previous.total_issues
            issue_trend = "📈 Increased" if issue_change > 0 else "📉 Decreased" if issue_change < 0 else "➡️  Unchanged"
            
            md.append(f"**Issues Trend:** {issue_trend} ({issue_change:+d})")
            md.append(f"**Latest Status:** {'✅ Approved' if latest.approved else '❌ Not Approved'}")
        
        # Common issues
        md.append("\n## Most Common Issues (Last 5 Reports)\n")
        
        # Aggregate issues from recent reports
        all_issues = []
        for report in reports[:5]:
            all_issues.extend(report.issues)
        
        # Count frequency
        issue_counts = {}
        for issue in all_issues:
            # Simplified issue (first 100 chars for grouping)
            key = issue[:100] if len(issue) > 100 else issue
            issue_counts[key] = issue_counts.get(key, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_issues:
            for issue, count in sorted_issues[:10]:
                md.append(f"- **{count}x** {issue}{'...' if len(issue) == 100 else ''}")
        else:
            md.append("No issues found in recent reports! 🎉")
        
        # Improvements
        md.append("\n## Recent Changes\n")
        
        if len(reports) >= 2:
            latest = reports[0]
            previous = reports[1]
            
            md.append("### Compared to Previous Run\n")
            
            if latest.approved and not previous.approved:
                md.append("🎉 **Major Improvement:** Code is now approved!")
            elif not latest.approved and previous.approved:
                md.append("⚠️  **Regression:** Code is no longer approved")
            
            if latest.total_issues < previous.total_issues:
                md.append(f"✅ Fixed {previous.total_issues - latest.total_issues} issue(s)")
            elif latest.total_issues > previous.total_issues:
                md.append(f"❌ {latest.total_issues - previous.total_issues} new issue(s) introduced")
        
        # Save comparison report
        comparison_path = self.output_dir / "comparison.md"
        with open(comparison_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))
        
        return '\n'.join(md)
    
    def _to_markdown(self, report: AuditReport) -> str:
        """Convert report to markdown format"""
        md = ["# Code Audit Report\n"]
        
        # Metadata
        md.append(f"**Date:** {report.timestamp}")
        md.append(f"**Model:** {report.model_used}")
        md.append(f"**Rules:** {report.rules_file}")
        if report.git_commit:
            md.append(f"**Git Commit:** `{report.git_commit}`")
        md.append("")
        
        # Status
        status_emoji = "✅ APPROVED" if report.approved else "❌ NOT APPROVED"
        md.append(f"## Status: {status_emoji}\n")
        
        # Summary
        md.append(f"**{report.summary}**\n")
        
        # Issues
        md.append(f"## Issues ({report.total_issues})\n")
        if report.issues:
            for i, issue in enumerate(report.issues, 1):
                md.append(f"{i}. {issue}")
        else:
            md.append("No issues found! 🎉")
        
        md.append("")
        
        # Suggestions
        md.append(f"## Suggestions ({report.total_suggestions})\n")
        if report.suggestions:
            for i, suggestion in enumerate(report.suggestions, 1):
                md.append(f"{i}. {suggestion}")
        else:
            md.append("No suggestions.")
        
        md.append("")
        
        # Metadata
        if report.metadata:
            md.append("## Additional Information\n")
            for key, value in report.metadata.items():
                md.append(f"- **{key}:** {value}")
        
        return '\n'.join(md)
    
    def cleanup_old_reports(self, keep_recent: int = 20):
        """
        Clean up old historical reports
        
        Args:
            keep_recent: Number of recent reports to keep
        """
        history_files = sorted(self.history_dir.glob("audit_*.json"), reverse=True)
        
        if len(history_files) > keep_recent:
            for old_file in history_files[keep_recent:]:
                # Remove JSON and corresponding MD file
                old_file.unlink()
                md_file = old_file.with_suffix('.md')
                if md_file.exists():
                    md_file.unlink()
                
                print(f"Removed old report: {old_file.name}")
