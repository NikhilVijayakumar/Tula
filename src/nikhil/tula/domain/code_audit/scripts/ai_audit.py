#!/usr/bin/env python3
"""
AI-Powered Architectural Audit Script - Using llm_factory

This script reviews git diff against AGENTS.md architectural guidelines.
Uses Amsha's existing llm_factory infrastructure and llm_config.yaml.

Usage:
    python scripts/ai_audit.py                    # Check staged changes
    python scripts/ai_audit.py --all              # Check all uncommitted changes
    SKIP_AI_AUDIT=1 git commit -m "..."          # Skip AI audit for this commit

Configuration:
    Uses llm_config.yaml (same as your crew_forge examples)
    Default path: config/llm_config.yaml
    Or set: LLM_CONFIG_PATH environment variable
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add src to path to import Amsha modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from nikhil.tula.utils.yaml_utils import YamlUtils
    from nikhil.tula.domain.llm_factory.settings.llm_settings import LLMSettings
    from nikhil.tula.domain.llm_factory.service.llm_builder import LLMBuilder
    from nikhil.tula.domain.llm_factory.domain.llm_type import LLMType
    HAS_TULA = True
except ImportError:
    HAS_TULA = False


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  🤖 AI Architecture Audit{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(msg: str):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")


def print_error(msg: str):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")


def print_info(msg: str):
    print(f"{Colors.OKCYAN}ℹ️  {msg}{Colors.ENDC}")


def should_skip_audit() -> bool:
    """Check if audit should be skipped via environment variable"""
    return os.environ.get('SKIP_AI_AUDIT', '0') == '1'


def get_git_diff() -> Optional[str]:
    """Get git diff of staged changes"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--diff-filter=ACMR'],
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicitly use UTF-8
            errors='replace',  # Replace invalid characters instead of failing
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to get git diff: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error getting diff: {e}")
        return None


def load_agents_md() -> Optional[str]:
    """Load AGENTS.md content as system prompt"""
    agents_path = Path(__file__).parent.parent / "AGENTS.md"
    
    if not agents_path.exists():
        print_warning("AGENTS.md not found. Skipping AI audit.")
        return None
    
    try:
        return agents_path.read_text(encoding='utf-8')
    except Exception as e:
        print_error(f"Failed to read AGENTS.md: {e}")
        return None


def load_dependencies_md() -> Optional[str]:
    """Load DEPENDENCIES.md for framework coupling context"""
    deps_path = Path(__file__).parent.parent / "DEPENDENCIES.md"
    
    if deps_path.exists():
        try:
            return deps_path.read_text(encoding='utf-8')
        except Exception as e:
            print_warning(f"Could not read DEPENDENCIES.md: {e}")
    
    return None


def find_llm_config() -> Optional[Path]:
    """Find llm_config.yaml - check multiple locations"""
    base_path = Path(__file__).parent.parent
    
    # Check in order of preference
    possible_paths = [
        # Environment variable override
        Path(os.environ['LLM_CONFIG_PATH']) if 'LLM_CONFIG_PATH' in os.environ else None,
        # Root config/ directory
        base_path / "config" / "llm_config.yaml",
        # Example config (template)
        base_path / "src" / "nikhil" / "amsha" / "toolkit" / "crew_forge" / "example" / "config" / "llm_config.yaml",
    ]
    
    for path in possible_paths:
        if path and path.exists() and path.is_file():
            return path
    
    return None


def load_llm_via_factory(llm_config_path: Path) -> Optional[Any]:
    """Load LLM using Tula's llm_factory"""
    if not HAS_TULA:
        print_error("Tula modules not importable. Make sure you're in the project root.")
        return None
    
    try:
        # Load YAML config
        config_data = YamlUtils.yaml_safe_load(str(llm_config_path))
        
        # Parse into LLMSettings
        settings = LLMSettings(**config_data)
        
        # Build LLM for evaluation (stricter, lower temperature)
        builder = LLMBuilder(settings)
        llm_result = builder.build_evaluation()
        
        print_success(f"Loaded LLM: {llm_result.model_name}")
        return llm_result.llm
        
    except Exception as e:
        print_error(f"Failed to load LLM via factory: {e}")
        return None


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4


def split_diff_by_file(diff: str) -> list[tuple[str, str]]:
    """
    Split git diff into individual file diffs
    Returns list of (filename, file_diff) tuples
    """
    file_diffs = []
    current_file = None
    current_diff = []
    
    for line in diff.split('\n'):
        if line.startswith('diff --git'):
            # Save previous file
            if current_file:
                file_diffs.append((current_file, '\n'.join(current_diff)))
            
            # Start new file
            # Extract filename from: diff --git a/path/to/file b/path/to/file
            parts = line.split(' ')
            if len(parts) >= 3:
                current_file = parts[2].replace('a/', '', 1)
            else:
                current_file = "unknown"
            current_diff = [line]
        else:
            current_diff.append(line)
    
    # Save last file
    if current_file:
        file_diffs.append((current_file, '\n'.join(current_diff)))
    
    return file_diffs


def chunk_files_by_tokens(file_diffs: list[tuple[str, str]], system_prompt: str, max_tokens: int = 14000) -> list[list[tuple[str, str]]]:
    """
    Group files into chunks that fit within token limit
    Leaves 2k tokens buffer for safety (14k usable from 16k total)
    """
    system_tokens = estimate_tokens(system_prompt)
    available_tokens = max_tokens - system_tokens - 500  # 500 token buffer for response
    
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0
    
    for filename, file_diff in file_diffs:
        file_tokens = estimate_tokens(file_diff)
        
        # If single file exceeds limit, include it alone (will be truncated if needed)
        if file_tokens > available_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            chunks.append([(filename, file_diff)])
            current_chunk = []
            current_chunk_tokens = 0
            continue
        
        # If adding this file would exceed limit, start new chunk
        if current_chunk_tokens + file_tokens > available_tokens:
            chunks.append(current_chunk)
            current_chunk = [(filename, file_diff)]
            current_chunk_tokens = file_tokens
        else:
            current_chunk.append((filename, file_diff))
            current_chunk_tokens += file_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def review_with_llm_factory(llm, diff: str, agents_md: str, deps_md: Optional[str] = None) -> Dict[str, Any]:
    """
    Send diff to LLM loaded via llm_factory for review
    Supports chunked review for large diffs
    """
    try:
        system_prompt = construct_system_prompt(agents_md, deps_md)
        
        # Check if diff is too large for single call
        total_tokens = estimate_tokens(system_prompt + diff)
        
        if total_tokens > 14000:  # Use chunking
            print_info(f"Large diff detected (~{total_tokens} tokens). Using chunked review...")
            return review_with_chunks(llm, diff, system_prompt)
        else:
            # Single call for small diffs
            return review_single_call(llm, diff, system_prompt)
        
    except Exception as e:
        print_error(f"LLM review failed: {e}")
        print_warning("Falling back to basic checks...")
        return {"approved": True, "issues": [], "suggestions": [], "error": str(e)}


def review_single_call(llm, diff: str, system_prompt: str) -> Dict[str, Any]:
    """Single LLM call for small diffs"""
    user_prompt = construct_user_prompt(diff)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    print_info(f"Sending code to LLM via llm_factory...")
    
    # Call the LLM (CrewAI format)
    response = llm.call([{"role": "user", "content": full_prompt}])
    
    return parse_llm_response(response)


def review_with_chunks(llm, diff: str, system_prompt: str) -> Dict[str, Any]:
    """Multiple LLM calls for large diffs, chunked by file"""
    
    # Split diff by file
    file_diffs = split_diff_by_file(diff)
    print_info(f"Split diff into {len(file_diffs)} files")
    
    # Group files into token-limited chunks
    chunks = chunk_files_by_tokens(file_diffs, system_prompt)
    print_info(f"Grouped into {len(chunks)} chunks for review")
    
    # Review each chunk
    all_issues = []
    all_suggestions = []
    chunk_summaries = []
    
    for i, chunk in enumerate(chunks):
        print_info(f"Reviewing chunk {i+1}/{len(chunks)} ({len(chunk)} files)...")
        
        # Combine chunk files into single diff
        chunk_diff = '\n\n'.join([file_diff for _, file_diff in chunk])
        chunk_filenames = [filename for filename, _ in chunk]
        
        # Create user prompt for this chunk
        user_prompt = f"""Review this chunk of changes ({len(chunk)} files):
Files in this chunk: {', '.join(chunk_filenames)}

```diff
{chunk_diff}
```

Provide your review in JSON format."""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            # Call LLM for this chunk
            response = llm.call([{"role": "user", "content": full_prompt}])
            result = parse_llm_response(response)
            
            # Aggregate results
            if result.get('issues'):
                all_issues.extend(result['issues'])
            if result.get('suggestions'):
                all_suggestions.extend(result['suggestions'])
            if result.get('summary'):
                chunk_summaries.append(f"Chunk {i+1}: {result['summary']}")
            
            print_success(f"Chunk {i+1} reviewed")
            
        except Exception as e:
            print_warning(f"Chunk {i+1} failed: {e}")
            chunk_summaries.append(f"Chunk {i+1}: Review failed - {str(e)}")
    
    # Deduplicate issues and suggestions
    all_issues = list(set(all_issues))
    all_suggestions = list(set(all_suggestions))
    
    # Determine overall approval
    approved = len(all_issues) == 0
    
    return {
        "approved": approved,
        "issues": all_issues,
        "suggestions": all_suggestions,
        "summary": f"Chunked review of {len(file_diffs)} files in {len(chunks)} batches. " + "; ".join(chunk_summaries)
    }



def construct_system_prompt(agents_md: str, deps_md: Optional[str] = None) -> str:
    """Construct system prompt with architectural guidelines"""
    prompt = f"""You are a Senior Architect reviewing code changes for the Tula library.

Your job is to review the git diff against our coding standards in AGENTS.md.

{agents_md}

"""
    
    if deps_md:
        prompt += f"\n\nAlso consider our framework dependency guidelines:\n\n{deps_md}\n"
    
    prompt += """
Focus on:
1. Clean Architecture: Are dependencies pointing the right way?
2. ABC vs Protocol: Are interfaces using the correct pattern?
3. Dependency Injection: Are dependencies injected, not instantiated?
4. Exception Handling: Are custom exceptions used?
5. Type Hints: Are all parameters and returns typed?
6. Framework Isolation: Is framework code isolated in adapters?
7. Dependency Management: Are dependencies added to correct files (pyproject.toml vs requirements.txt)?

Respond in JSON format:
{
    "approved": true/false,
    "issues": ["list of critical violations that must be fixed"],
    "suggestions": ["list of recommendations for improvement"],
    "summary": "brief summary of the review"
}
"""
    return prompt


def construct_user_prompt(diff: str) -> str:
    """Construct user prompt with git diff"""
    return f"""Review this git diff for architectural compliance:

```diff
{diff}
```

Provide your review in JSON format."""


def parse_llm_response(content: str) -> Dict[str, Any]:
    """Parse LLM response, handling both JSON and plain text"""
    try:
        # Try parsing as JSON first
        return json.loads(content)
    except json.JSONDecodeError:
        # If not JSON, try to extract JSON from markdown code blocks
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            json_str = content[start:end].strip()
            try:
                return json.loads(json_str)
            except:
                pass
        
        # Fall back to simple parsing
        issues = []
        suggestions = []
        approved = True
        
        if any(word in content.lower() for word in ['violation', 'error', 'must fix', 'critical']):
            approved = False
            issues.append("LLM detected architectural issues (see full output)")
        
        return {
            "approved": approved,
            "issues": issues,
            "suggestions": ["Review full LLM output for details"],
            "summary": content[:200] + "..." if len(content) > 200 else content
        }


def run_basic_checks(diff: str) -> Dict[str, Any]:
    """Run basic pattern-matching checks without LLM"""
    issues = []
    suggestions = []
    
    # Check for common anti-patterns
    if "from crewai import" in diff and "/service/" in diff:
        issues.append("CrewAI imported in service layer - should be in adapters only")
    
    if "import dvc" in diff and "/service/" in diff:
        issues.append("DVC imported in service layer - should use IDataVersioner interface")
    
    if "raise Exception(" in diff or "raise ValueError(" in diff:
        suggestions.append("Consider using custom exceptions instead of generic Exception/ValueError")
    
    if "def " in diff and "->" not in diff:
        suggestions.append("Some functions may be missing return type hints")
    
    # Check dependency management
    if "pyproject.toml" in diff and "requirements.txt" not in diff:
        suggestions.append("Added dependency to pyproject.toml - did you also add to requirements.txt?")
    
    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "summary": "Basic pattern matching checks completed"
    }


def main():
    print_header("AI Architecture Audit")
    
    # Check if should skip
    if should_skip_audit():
        print_info("AI audit skipped (SKIP_AI_AUDIT=1)")
        return 0
    
    # Get git diff
    print_info("Getting staged changes...")
    diff = get_git_diff()
    
    if not diff:
        print_info("No staged changes to review")
        return 0
    
    if len(diff) < 10:
        print_info("Diff too small to review")
        return 0
    
    print_success(f"Found {len(diff.splitlines())} lines of changes")
    
    # Load architectural guidelines
    print_info("Loading AGENTS.md...")
    agents_md = load_agents_md()
    
    if not agents_md:
        print_warning("Proceeding with basic checks only")
        result = run_basic_checks(diff)
    else:
        deps_md = load_dependencies_md()
        
        # Find llm_config.yaml
        llm_config_path = find_llm_config()
        
        if not llm_config_path:
            print_warning("llm_config.yaml not found. Falling back to basic checks.")
            print_info("Create config/llm_config.yaml or set LLM_CONFIG_PATH environment variable")
            result = run_basic_checks(diff)
        else:
            print_info(f"Using LLM config: {llm_config_path}")
            
            # Load LLM via llm_factory
            llm = load_llm_via_factory(llm_config_path)
            
            if llm:
                result = review_with_llm_factory(llm, diff, agents_md, deps_md)
            else:
                print_warning("LLM loading failed. Using basic checks.")
                result = run_basic_checks(diff)
    
    # Display results
    print(f"\n{Colors.BOLD}Review Results:{Colors.ENDC}\n")
    
    if result.get('summary'):
        print(f"📝 {result['summary']}\n")
    
    if result.get('issues'):
        print(f"{Colors.FAIL}{Colors.BOLD}Critical Issues:{Colors.ENDC}")
        for issue in result['issues']:
            print(f"  ❌ {issue}")
        print()
    
    if result.get('suggestions'):
        print(f"{Colors.WARNING}{Colors.BOLD}Suggestions:{Colors.ENDC}")
        for suggestion in result['suggestions']:
            print(f"  💡 {suggestion}")
        print()
    
    # Final verdict
    if result.get('approved', True):
        print_success("✨ Architectural review PASSED")
        print_info("Changes comply with AGENTS.md standards")
        return 0
    else:
        print_error("🚫 Architectural review FAILED")
        print_error("Please fix the issues above before committing")
        print_info("\nTo bypass this check: SKIP_AI_AUDIT=1 git commit -m '...'")
        print_warning("(Only bypass if you've manually verified compliance)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
