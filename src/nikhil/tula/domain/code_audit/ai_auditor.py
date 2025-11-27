"""
AI-powered code auditor - refactored from scripts/ai_audit.py
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import json
import sys

# Add src to path for imports
if str(Path(__file__).parent.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from nikhil.tula.utils.yaml_utils import YamlUtils
from nikhil.vak.domain.llm_factory.settings.llm_settings import LLMSettings
from nikhil.vak.domain.llm_factory.service.llm_builder import LLMBuilder
from nikhil.tula.domain.code_audit.config import AuditConfig
from nikhil.tula.domain.code_audit.prompt_loader import PromptLoader


@dataclass
class AuditResult:
    """Result of an AI audit"""
    approved: bool
    issues: List[str]
    suggestions: List[str]
    summary: str
    error: Optional[str] = None
    skipped: bool = False


class AIAuditor:
    """AI-powered code auditor using Vak's llm_factory"""
    
    def __init__(self, config: AuditConfig):
        self.config = config
        self.llm = None
        self.model_name = None
        self.prompt_loader = PromptLoader()  # Initialize prompt loader
    
    def _get_git_diff(self) -> Optional[str]:
        """Get git diff of staged changes"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get git diff: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting diff: {e}")
            return None
    
    def _get_all_python_files(self, base_dir: Optional[Path] = None) -> List[Path]:
        """Get all Python files in repository"""
        if not base_dir:
            base_dir = Path.cwd()
        
        python_files = []
        
        # Common directories to scan
        scan_dirs = ['src', 'lib', 'app']
        
        # Try to find source directory
        for dir_name in scan_dirs:
            scan_path = base_dir / dir_name
            if scan_path.exists() and scan_path.is_dir():
                python_files.extend(scan_path.rglob('*.py'))
        
        # If no standard directories, scan current directory
        if not python_files:
            python_files = list(base_dir.rglob('*.py'))
        
        # Filter out common exclusions
        excluded_patterns = [
            'venv', '.venv', 'env', '.env',
            '__pycache__', '.git', '.tox',
            'build', 'dist', '.egg-info',
            'node_modules', 'migrations'
        ]
        
        filtered_files = []
        for file in python_files:
            # Check if any excluded pattern in path
            if not any(pattern in str(file) for pattern in excluded_patterns):
                filtered_files.append(file)
        
        return filtered_files
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content safely"""
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return None
    
    def _create_file_review_prompt(self, file_path: Path, content: str) -> str:
        """Create review prompt for a single file"""
        return self.prompt_loader.get_user_prompt(
            'file_review',
            filepath=file_path,
            content=content
        )
    
    def _group_files_by_module(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by module/package for organized review"""
        groups = {}
        
        for file in files:
            # Extract module name (first directory after src/)
            parts = file.parts
            
            # Find 'src' index
            try:
                src_idx = parts.index('src')
                if len(parts) > src_idx + 1:
                    module = parts[src_idx + 1]
                else:
                    module = 'root'
            except ValueError:
                module = 'root'
            
            if module not in groups:
                groups[module] = []
            groups[module].append(file)
        
        return groups
    
    def _load_llm(self) -> bool:
        """Load LLM using Vak's llm_factory"""
        if not self.config.llm_config_path or not self.config.llm_config_path.exists():
            return False
        
        try:
            config_data = YamlUtils.yaml_safe_load(str(self.config.llm_config_path))
            settings = LLMSettings(**config_data)
            builder = LLMBuilder(settings)
            llm_result = builder.build_evaluation()
            
            self.llm = llm_result.llm
            self.model_name = llm_result.model_name
            
            # Read max_tokens from model config if available
            eval_config = settings.llm.get('evaluation')
            if eval_config:
                default_model_key = eval_config.default
                model_config = eval_config.models.get(default_model_key)
                
                # Check if model has custom max_tokens setting
                if hasattr(model_config, 'max_tokens'):
                    self.config.max_tokens_per_chunk = model_config.max_tokens
                    print(f"ℹ️  Using model-specific chunk size: {model_config.max_tokens} tokens")
                # Otherwise check llm_parameters
                elif 'llm_parameters' in config_data and 'evaluation' in config_data['llm_parameters']:
                    params = config_data['llm_parameters']['evaluation']
                    if 'max_completion_tokens' in params:
                        # Use 80% of max_completion_tokens for input
                        self.config.max_tokens_per_chunk = int(params['max_completion_tokens'] * 3)
                        print(f"ℹ️  Using parameter-based chunk size: {self.config.max_tokens_per_chunk} tokens")
            
            return True
        except Exception as e:
            print(f"❌ Failed to load LLM: {e}")
            return False
    
    def _load_file(self, path: Optional[Path]) -> Optional[str]:
        """Load file content"""
        if not path or not path.exists():
            return None
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Could not read {path}: {e}")
            return None
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def _split_diff_by_file(self, diff: str) -> List[Tuple[str, str]]:
        """Split git diff into individual file diffs"""
        file_diffs = []
        current_file = None
        current_diff = []
        
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    file_diffs.append((current_file, '\n'.join(current_diff)))
                
                parts = line.split(' ')
                if len(parts) >= 3:
                    current_file = parts[2].replace('a/', '', 1)
                else:
                    current_file = "unknown"
                current_diff = [line]
            else:
                current_diff.append(line)
        
        if current_file:
            file_diffs.append((current_file, '\n'.join(current_diff)))
        
        return file_diffs
    
    def _chunk_files_by_tokens(self, file_diffs: List[Tuple[str, str]], 
                               system_prompt: str) -> List[List[Tuple[str, str]]]:
        """Group files into chunks within token limit"""
        system_tokens = self._estimate_tokens(system_prompt)
        available_tokens = self.config.max_tokens_per_chunk - system_tokens - 500
        
        chunks = []
        current_chunk = []
        current_chunk_tokens = 0
        
        for filename, file_diff in file_diffs:
            file_tokens = self._estimate_tokens(file_diff)
            
            if file_tokens > available_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                chunks.append([(filename, file_diff)])
                current_chunk = []
                current_chunk_tokens = 0
                continue
            
            if current_chunk_tokens + file_tokens > available_tokens:
                chunks.append(current_chunk)
                current_chunk = [(filename, file_diff)]
                current_chunk_tokens = file_tokens
            else:
                current_chunk.append((filename, file_diff))
                current_chunk_tokens += file_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _construct_system_prompt(self, rules: str, dependencies: Optional[str] = None) -> str:
        """Construct system prompt using prompt loader"""
        return self.prompt_loader.build_system_prompt(rules, dependencies)
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                try:
                    return json.loads(content[start:end].strip())
                except:
                    pass
            
            return {
                "approved": not any(w in content.lower() for w in ['violation', 'error', 'critical']),
                "issues": [],
                "suggestions": ["Review full output"],
                "summary": content[:200]
            }
    
    def _review_chunk(self, llm, chunk_diff: str, system_prompt: str) -> Dict[str, Any]:
        """Review a single chunk"""
        user_prompt = self.prompt_loader.get_user_prompt(
            'single_review',
            diff=chunk_diff
        )
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = llm.call([{"role": "user", "content": full_prompt}])
        return self._parse_llm_response(response)
    
    def _review_with_llm(self, diff: str, rules: str, dependencies: Optional[str]) -> AuditResult:
        """Review diff with LLM"""
        system_prompt = self._construct_system_prompt(rules, dependencies)
        total_tokens = self._estimate_tokens(system_prompt + diff)
        
        try:
            if total_tokens > self.config.max_tokens_per_chunk:
                print(f"ℹ️  Large diff (~{total_tokens} tokens). Using chunked review...")
                return self._review_chunked(diff, system_prompt)
            else:
                print(f"ℹ️  Reviewing with {self.model_name}...")
                result = self._review_chunk(self.llm, diff, system_prompt)
                return AuditResult(**result)
        except Exception as e:
            return AuditResult(
                approved=True,
                issues=[],
                suggestions=[],
                summary="LLM review failed",
                error=str(e)
            )
    
    def _review_chunked(self, diff: str, system_prompt: str) -> AuditResult:
        """Review with chunking"""
        file_diffs = self._split_diff_by_file(diff)
        chunks = self._chunk_files_by_tokens(file_diffs, system_prompt)
        
        print(f"ℹ️  Split into {len(file_diffs)} files, {len(chunks)} chunks")
        
        all_issues = []
        all_suggestions = []
        summaries = []
        
        for i, chunk in enumerate(chunks):
            print(f"ℹ️  Chunk {i+1}/{len(chunks)} ({len(chunk)} files)...")
            
            chunk_diff = '\n\n'.join([fd for _, fd in chunk])
            filenames = [fn for fn, _ in chunk]
            
            user_prompt = self.prompt_loader.get_user_prompt(
                'chunk_with_files',
                chunk_index=i+1,
                file_count=len(chunk),
                file_list=', '.join(filenames),
                chunk_diff=chunk_diff
            )
            
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.llm.call([{"role": "user", "content": full_prompt}])
                result = self._parse_llm_response(response)
                
                if result.get('issues'):
                    all_issues.extend(result['issues'])
                if result.get('suggestions'):
                    all_suggestions.extend(result['suggestions'])
                if result.get('summary'):
                    summaries.append(f"Chunk {i+1}: {result['summary']}")
                
                print(f"✅ Chunk {i+1} reviewed")
            except Exception as e:
                print(f"⚠️  Chunk {i+1} failed: {e}")
                summaries.append(f"Chunk {i+1}: Failed")
        
        return AuditResult(
            approved=len(all_issues) == 0,
            issues=list(set(all_issues)),
            suggestions=list(set(all_suggestions)),
            summary=f"Chunked review: {len(file_diffs)} files, {len(chunks)} batches. " + "; ".join(summaries)
        )
    
    def _basic_checks(self, diff: str) -> AuditResult:
        """Basic pattern matching checks"""
        issues = []
        suggestions = []
        
        if "from crewai import" in diff and "/service/" in diff:
            issues.append("CrewAI imported in service layer")
        
        if "import dvc" in diff and "/service/" in diff:
            issues.append("DVC imported in service layer")
        
        if "raise Exception(" in diff or "raise ValueError(" in diff:
            suggestions.append("Use custom exceptions")
        
        if "pyproject.toml" in diff and "requirements.txt" not in diff:
            suggestions.append("Dependency added to pyproject.toml - also add to requirements.txt?")
        
        return AuditResult(
            approved=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            summary="Basic pattern matching"
        )
    
    def audit(self) -> AuditResult:
        """Run the audit with combined approach"""
        # Check skip flag
        if self.config.skip_audit:
            return AuditResult(
                approved=True,
                issues=[],
                suggestions=[],
                summary="Audit skipped",
                skipped=True
            )
        
        # Get diff
        diff = self._get_git_diff()
        if not diff or len(diff) < 10:
            return AuditResult(
                approved=True,
                issues=[],
                suggestions=[],
                summary="No changes to review",
                skipped=True
            )
        
        print(f"✅ Found {len(diff.splitlines())} lines of changes")
        
        # STAGE 1: Always run basic pattern matching (fast, free)
        print("🔍 Running pattern matching checks...")
        basic_result = self._basic_checks(diff)
        
        # Save intermediate result if configured
        if self.config.save_llm_responses and self.config.output.get_intermediate_path():
            intermediate_dir = self.config.output.get_intermediate_path() / "analysis"
            intermediate_dir.mkdir(parents=True, exist_ok=True)
            self._save_intermediate_result(
                basic_result,
                intermediate_dir / "pattern_matching.json",
                "Pattern Matching"
            )
        
        # Load rules
        rules = self._load_file(self.config.rules_file)
        
        # STAGE 2: Try LLM review if available
        llm_result = None
        if rules and self._load_llm():
            print(f"🤖 Running LLM analysis with {self.model_name}...")
            print(f"ℹ️  Using rules: {self.config.rules_file}")
            print(f"ℹ️  Using LLM config: {self.config.llm_config_path}")
            
            dependencies = self._load_file(self.config.dependencies_file)
            llm_result = self._review_with_llm(diff, rules, dependencies)
            
            # Save intermediate result
            if self.config.save_llm_responses and self.config.output.get_intermediate_path():
                intermediate_dir = self.config.output.get_intermediate_path() / "analysis"
                self._save_intermediate_result(
                    llm_result,
                    intermediate_dir / "llm_analysis.json",
                    "LLM Analysis"
                )
        elif not rules:
            print("⚠️  No rules file found, using pattern matching only")
        else:
            print("⚠️  LLM not available, using pattern matching only")
        
        # STAGE 3: Combine results
        if llm_result:
            print("🔄 Combining pattern matching + LLM results...")
            combined_result = self._combine_results(basic_result, llm_result)
            
            # Save combined result
            if self.config.save_llm_responses and self.config.output.get_intermediate_path():
                intermediate_dir = self.config.output.get_intermediate_path() / "analysis"
                self._save_intermediate_result(
                    combined_result,
                    intermediate_dir / "combined_results.json",
                    "Combined Analysis"
                )
            
            return combined_result
        else:
            # Only pattern matching available
            return basic_result
    
    def _combine_results(self, basic: AuditResult, llm: AuditResult) -> AuditResult:
        """
        Combine pattern matching and LLM results
        
        - Merges issues and suggestions
        - Tags each item with source (pattern/llm)
        - Deduplicates similar items
        - Uses most restrictive approval status
        """
        # Tag issues with source
        tagged_issues = []
        
        for issue in basic.issues:
            tagged_issues.append({
                'source': 'pattern',
                'text': issue
            })
        
        for issue in llm.issues:
            tagged_issues.append({
                'source': 'llm',
                'text': issue
            })
        
        # Tag suggestions with source
        tagged_suggestions = []
        
        for sug in basic.suggestions:
            tagged_suggestions.append({
                'source': 'pattern',
                'text': sug
            })
        
        for sug in llm.suggestions:
            tagged_suggestions.append({
                'source': 'llm',
                'text': sug
            })
        
        # Deduplicate (simple text matching for now)
        unique_issues = self._deduplicate_tagged(tagged_issues)
        unique_suggestions = self._deduplicate_tagged(tagged_suggestions)
        
        # Most restrictive approval (both must approve)
        combined_approved = basic.approved and llm.approved
        
        # Combined summary
        summary_parts = []
        if basic.issues:
            summary_parts.append(f"Pattern: {len(basic.issues)} issues")
        if llm.issues:
            summary_parts.append(f"LLM: {len(llm.issues)} issues")
        
        summary = f"Combined analysis: {', '.join(summary_parts) if summary_parts else 'No issues found'}"
        
        return AuditResult(
            approved=combined_approved,
            issues=[item['text'] if isinstance(item, dict) else item for item in unique_issues],
            suggestions=[item['text'] if isinstance(item, dict) else item for item in unique_suggestions],
            summary=summary,
            error=llm.error if llm.error else basic.error
        )
    
    def _deduplicate_tagged(self, tagged_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Deduplicate tagged items while preserving source information"""
        seen = set()
        unique = []
        
        for item in tagged_items:
            # Normalize text for comparison (lowercase, strip)
            normalized = item['text'].lower().strip()
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(item)
            else:
                # If duplicate, prefer LLM source
                if item['source'] == 'llm':
                    # Replace existing with LLM version
                    for i, existing in enumerate(unique):
                        if existing['text'].lower().strip() == normalized:
                            unique[i] = item
                            break
        
        return unique
    
    def _save_intermediate_result(self, result: AuditResult, filepath: Path, stage_name: str):
        """Save intermediate audit result"""
        import json
        from datetime import datetime
        
        data = {
            'stage': stage_name,
            'timestamp': datetime.now().isoformat(),
            'approved': result.approved,
            'total_issues': len(result.issues),
            'total_suggestions': len(result.suggestions),
            'issues': result.issues,
            'suggestions': result.suggestions,
            'summary': result.summary,
            'error': result.error,
            'skipped': result.skipped
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"📝 Saved intermediate result: {filepath.name}")
    
    def audit_repository(self, output_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Audit entire repository for architectural compliance
        Returns summary report
        """
        print("🔍 Starting full repository audit...")
        
        # Load rules
        rules = self._load_file(self.config.rules_file)
        if not rules:
            print("❌ No rules file found. Cannot perform audit.")
            return {"error": "No rules file"}
        
        print(f"ℹ️  Using rules: {self.config.rules_file}")
        
        # Get all Python files
        python_files = self._get_all_python_files()
        if not python_files:
            print("❌ No Python files found")
            return {"error": "No files found"}
        
        print(f"✅ Found {len(python_files)} Python files")
        
        # Group by module
        file_groups = self._group_files_by_module(python_files)
        print(f"ℹ️  Organized into {len(file_groups)} modules")
        
        # Load LLM if available
        has_llm = self._load_llm()
        if has_llm:
            print(f"✅ Using LLM: {self.model_name}")
        else:
            print("⚠️  LLM not available, using pattern matching")
        
        # Audit each module
        report = {
            "total_files": len(python_files),
            "modules": {},
            "summary": {
                "total_issues": 0,
                "total_suggestions": 0,
                "files_with_issues": 0,
                "clean_files": 0
            },
            "issues_by_category": {},
            "files_with_violations": []
        }
        
        dependencies = self._load_file(self.config.dependencies_file)
        system_prompt = self._construct_system_prompt(rules, dependencies) if has_llm else None
        
        for module_name, files in file_groups.items():
            print(f"\n📦 Auditing module: {module_name} ({len(files)} files)")
            
            module_report = {
                "files": len(files),
                "issues": [],
                "suggestions": [],
                "file_reports": []
            }
            
            for file_path in files:
                content = self._read_file_content(file_path)
                if not content:
                    continue
                
                # Skip very small files (< 10 lines)
                if len(content.splitlines()) < 10:
                    continue
                
                print(f"  ℹ️  Reviewing {file_path.name}...")
                
                if has_llm and system_prompt:
                    # LLM review for this file
                    file_prompt = self._create_file_review_prompt(file_path, content)
                    full_prompt = f"{system_prompt}\n\n{file_prompt}"
                    
                    # Token check
                    if self._estimate_tokens(full_prompt) > self.config.max_tokens_per_chunk:
                        # File too large, use basic checks
                        file_result = self._basic_checks(content)
                    else:
                        try:
                            response = self.llm.call([{"role": "user", "content": full_prompt}])
                            file_result = self._parse_llm_response(response)
                        except Exception as e:
                            print(f"    ⚠️  LLM failed: {e}")
                            file_result = self._basic_checks(content)
                else:
                    # Pattern matching
                    file_result = self._basic_checks(content)
                
                # Add to module report
                if file_result.get('issues'):
                    module_report['issues'].extend([
                        f"{file_path.name}: {issue}" 
                        for issue in file_result['issues']
                    ])
                    report['summary']['files_with_issues'] += 1
                    report['files_with_violations'].append(str(file_path))
                else:
                    report['summary']['clean_files'] += 1
                
                if file_result.get('suggestions'):
                    module_report['suggestions'].extend([
                        f"{file_path.name}: {sug}"
                        for sug in file_result['suggestions']
                    ])
                
                module_report['file_reports'].append({
                    "file": str(file_path),
                    "approved": file_result.get('approved', True),
                    "issues": file_result.get('issues', []),
                    "suggestions": file_result.get('suggestions', [])
                })
            
            report['modules'][module_name] = module_report
            report['summary']['total_issues'] += len(module_report['issues'])
            report['summary']['total_suggestions'] += len(module_report['suggestions'])
            
            print(f"  ✅ {module_name}: {len(module_report['issues'])} issues, {len(module_report['suggestions'])} suggestions")
        
        # Generate summary report
        print("\n" + "="*60)
        print("📊 Repository Audit Summary")
        print("="*60)
        print(f"Total files reviewed: {report['total_files']}")
        print(f"Modules: {len(report['modules'])}")
        print(f"Files with issues: {report['summary']['files_with_issues']}")
        print(f"Clean files: {report['summary']['clean_files']}")
        print(f"Total issues: {report['summary']['total_issues']}")
        print(f"Total suggestions: {report['summary']['total_suggestions']}")
        
        # Save report if output file specified
        if output_file:
            self._save_report(report, output_file)
            print(f"\n💾 Detailed report saved to: {output_file}")
        
        return report
    
    def _save_report(self, report: Dict[str, Any], output_file: Path):
        """Save detailed report to file"""
        import json
        from datetime import datetime
        
        # Add metadata
        report['metadata'] = {
            "audit_date": datetime.now().isoformat(),
            "rules_file": str(self.config.rules_file),
            "llm_config": str(self.config.llm_config_path) if self.config.llm_config_path else None,
            "model_used": self.model_name if self.llm else "pattern-matching"
        }
        
        # Save as JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Also create markdown summary
        md_file = output_file.with_suffix('.md')
        self._save_report_markdown(report, md_file)
    
    def _save_report_markdown(self, report: Dict[str, Any], md_file: Path):
        """Save report as markdown for easy reading"""
        lines = [
            "# Repository Audit Report",
            "",
            f"**Date:** {report['metadata']['audit_date']}",
            f"**Rules:** {report['metadata']['rules_file']}",
            f"**Model:** {report['metadata']['model_used']}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Total Files:** {report['total_files']}",
            f"- **Modules:** {len(report['modules'])}",
            f"- **Files with Issues:** {report['summary']['files_with_issues']}",
            f"- **Clean Files:** {report['summary']['clean_files']}",
            f"- **Total Issues:** {report['summary']['total_issues']}",
            f"- **Total Suggestions:** {report['summary']['total_suggestions']}",
            "",
            "---",
            ""
        ]
        
        # Add module details
        lines.append("## Module Reports\n")
        
        for module_name, module_data in report['modules'].items():
            lines.append(f"### {module_name}\n")
            lines.append(f"- Files: {module_data['files']}")
            lines.append(f"- Issues: {len(module_data['issues'])}")
            lines.append(f"- Suggestions: {len(module_data['suggestions'])}")
            lines.append("")
            
            if module_data['issues']:
                lines.append("**Issues:**")
                for issue in module_data['issues']:
                    lines.append(f"- ❌ {issue}")
                lines.append("")
            
            if module_data['suggestions']:
                lines.append("**Suggestions:**")
                for sug in module_data['suggestions']:
                    lines.append(f"- 💡 {sug}")
                lines.append("")
            
            lines.append("---\n")
        
        # Add files with violations
        if report['files_with_violations']:
            lines.append("## Files with Violations\n")
            for file in report['files_with_violations']:
                lines.append(f"- `{file}`")
            lines.append("")
        
        md_file.write_text('\n'.join(lines), encoding='utf-8')
