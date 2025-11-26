"""
Markdown formatter using LLM

Converts JSON audit results to well-formatted, human-readable Markdown.
Supports chunking for large reports and flexible model selection.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class MarkdownFormatter:
    """Format audit reports as Markdown using LLM"""
    
    def __init__(self, llm_client=None):
        """
        Initialize formatter
        
        Args:
            llm_client: Optional LLM client for formatting (uses 'creative' model)
                       If None, uses template-based formatting
        """
        self.llm = llm_client
    
    def format_json_to_markdown(self, json_data: Dict[str, Any], 
                               use_llm: bool = True) -> str:
        """
        Convert JSON audit report to Markdown
        
        Args:
            json_data: Audit report data
            use_llm: Whether to use LLM for formatting (vs template)
        
        Returns:
            Formatted Markdown string
        """
        if use_llm and self.llm:
            return self._llm_format(json_data)
        else:
            return self._template_format(json_data)
    
    def _llm_format(self, json_data: Dict[str, Any]) -> str:
        """Use LLM to format JSON as beautiful Markdown"""
        # Create prompt for LLM
        prompt = f"""Convert this code audit report from JSON to beautiful, well-formatted Markdown.

JSON Report:
```json
{json.dumps(json_data, indent=2)}
```

Requirements:
1. Use proper Markdown headers (# ## ###)
2. Use tables for statistics
3. Use emojis for status (✅ ❌ ⚠️ 💡)
4. Use code blocks for code references
5. Make it easy to read and scan
6. Include all information from the JSON
7. Use bullet points and numbered lists appropriately

Generate the Markdown report:"""

        # Call LLM
        try:
            markdown = self.llm.call([{"role": "user", "content": prompt}])
            
            # Clean up if LLM wrapped in code blocks
            if markdown.startswith("```markdown"):
                markdown = markdown[11:]
            if markdown.startswith("```"):
                markdown = markdown[3:]
            if markdown.endswith("```"):
                markdown = markdown[:-3]
            
            return markdown.strip()
        except Exception as e:
            print(f"⚠️  LLM formatting failed: {e}. Using template.")
            return self._template_format(json_data)
    
    def _template_format(self, json_data: Dict[str, Any]) -> str:
        """Template-based Markdown formatting (no LLM needed)"""
        lines = []
        
        # Header
        lines.append("# Code Audit Report\n")
        
        # Metadata
        if 'timestamp' in json_data:
            lines.append(f"**Date:** {json_data['timestamp']}")
        if 'model_used' in json_data:
            lines.append(f"**Model:** {json_data['model_used']}")
        if 'rules_file' in json_data:
            lines.append(f"**Rules:** {json_data['rules_file']}")
        if 'git_commit' in json_data:
            lines.append(f"**Git Commit:** `{json_data['git_commit']}`")
        lines.append("")
        
        # Status
        approved = json_data.get('approved', False)
        status_emoji = "✅ APPROVED" if approved else "❌ NOT APPROVED"
        lines.append(f"## Status: {status_emoji}\n")
        
        # Summary
        if 'summary' in json_data:
            lines.append(f"**{json_data['summary']}**\n")
        
        # Combined Results (if present)
        if 'pattern_matching' in json_data or 'llm_review' in json_data:
            lines.append("## Review Methods\n")
            
            if 'pattern_matching' in json_data:
                pm = json_data['pattern_matching']
                lines.append("### 🔍 Pattern Matching")
                lines.append(f"- Issues: {pm.get('total_issues', 0)}")
                lines.append(f"- Suggestions: {pm.get('total_suggestions', 0)}")
                lines.append("")
            
            if 'llm_review' in json_data:
                llm = json_data['llm_review']
                lines.append("### 🤖 LLM Analysis")
                lines.append(f"- Issues: {llm.get('total_issues', 0)}")
                lines.append(f"- Suggestions: {llm.get('total_suggestions', 0)}")
                lines.append("")
        
        # Issues
        issues = json_data.get('issues', [])
        lines.append(f"## Issues ({len(issues)})\n")
        if issues:
            for i, issue in enumerate(issues, 1):
                # Check if issue has source tag
                if isinstance(issue, dict):
                    source = issue.get('source', 'unknown')
                    text = issue.get('text', str(issue))
                    lines.append(f"{i}. [{source}] {text}")
                else:
                    lines.append(f"{i}. {issue}")
        else:
            lines.append("No issues found! 🎉")
        lines.append("")
        
        # Suggestions
        suggestions = json_data.get('suggestions', [])
        lines.append(f"## Suggestions ({len(suggestions)})\n")
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                if isinstance(suggestion, dict):
                    source = suggestion.get('source', 'unknown')
                    text = suggestion.get('text', str(suggestion))
                    lines.append(f"{i}. 💡 [{source}] {text}")
                else:
                    lines.append(f"{i}. 💡 {suggestion}")
        else:
            lines.append("No suggestions.")
        lines.append("")
        
        # Additional Information
        if 'metadata' in json_data:
            lines.append("## Additional Information\n")
            for key, value in json_data['metadata'].items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_large_report_chunked(self, json_data: Dict[str, Any], 
                                    chunk_size: int = 50) -> str:
        """
        Format large report by chunking issues/suggestions
        
        Args:
            json_data: Full audit report
            chunk_size: Number of issues/suggestions per chunk
        
        Returns:
            Combined Markdown report
        """
        # Split issues into chunks
        issues = json_data.get('issues', [])
        suggestions = json_data.get('suggestions', [])
        
        # If small enough, format normally
        if len(issues) + len(suggestions) <= chunk_size:
            return self.format_json_to_markdown(json_data)
        
        # Otherwise, chunk and combine
        markdown_parts = []
        
        # Header and metadata (once)
        header_data = {
            'timestamp': json_data.get('timestamp'),
            'model_used': json_data.get('model_used'),
            'rules_file': json_data.get('rules_file'),
            'git_commit': json_data.get('git_commit'),
            'approved': json_data.get('approved'),
            'summary': json_data.get('summary'),
        }
        markdown_parts.append(self._format_header(header_data))
        
        # Format issues in chunks
        for i in range(0, len(issues), chunk_size):
            chunk_issues = issues[i:i + chunk_size]
            chunk_data = {
                'issues': chunk_issues,
                'chunk_info': f"Issues {i+1}-{min(i+chunk_size, len(issues))} of {len(issues)}"
            }
            markdown_parts.append(self._format_issues_chunk(chunk_data))
        
        # Format suggestions in chunks
        for i in range(0, len(suggestions), chunk_size):
            chunk_suggestions = suggestions[i:i + chunk_size]
            chunk_data = {
                'suggestions': chunk_suggestions,
                'chunk_info': f"Suggestions {i+1}-{min(i+chunk_size, len(suggestions))} of {len(suggestions)}"
            }
            markdown_parts.append(self._format_suggestions_chunk(chunk_data))
        
        return '\n\n---\n\n'.join(markdown_parts)
    
    def _format_header(self, data: Dict[str, Any]) -> str:
        """Format report header"""
        lines = ["# Code Audit Report\n"]
        
        if data.get('timestamp'):
            lines.append(f"**Date:** {data['timestamp']}")
        if data.get('model_used'):
            lines.append(f"**Model:** {data['model_used']}")
        if data.get('rules_file'):
            lines.append(f"**Rules:** {data['rules_file']}")
        lines.append("")
        
        approved = data.get('approved', False)
        status = "✅ APPROVED" if approved else "❌ NOT APPROVED"
        lines.append(f"## Status: {status}\n")
        
        if data.get('summary'):
            lines.append(f"**{data['summary']}**\n")
        
        return '\n'.join(lines)
    
    def _format_issues_chunk(self, data: Dict[str, Any]) -> str:
        """Format a chunk of issues"""
        lines = [f"## {data.get('chunk_info', 'Issues')}\n"]
        
        for i, issue in enumerate(data.get('issues', []), 1):
            if isinstance(issue, dict):
                source = issue.get('source', '')
                text = issue.get('text', str(issue))
                lines.append(f"{i}. [{source}] {text}")
            else:
                lines.append(f"{i}. {issue}")
        
        return '\n'.join(lines)
    
    def _format_suggestions_chunk(self, data: Dict[str, Any]) -> str:
        """Format a chunk of suggestions"""
        lines = [f"## {data.get('chunk_info', 'Suggestions')}\n"]
        
        for i, suggestion in enumerate(data.get('suggestions', []), 1):
            if isinstance(suggestion, dict):
                source = suggestion.get('source', '')
                text = suggestion.get('text', str(suggestion))
                lines.append(f"{i}. 💡 [{source}] {text}")
            else:
                lines.append(f"{i}. 💡 {suggestion}")
        
        return '\n'.join(lines)
