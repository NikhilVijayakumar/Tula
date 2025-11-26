"""
Prompt loader utility for Tula code audit

Loads and renders prompt templates from configuration files.
Supports custom prompt paths and variable substitution.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class PromptLoader:
    """Loads and manages prompt templates from YAML files"""
    
    def __init__(self, custom_prompts_dir: Optional[Path] = None):
        """
        Initialize prompt loader
        
        Args:
            custom_prompts_dir: Optional custom directory for prompt files.
                              If not provided, will search standard locations.
        """
        self.custom_prompts_dir = custom_prompts_dir
        self._system_prompt_data: Optional[Dict[str, Any]] = None
        self._user_prompts_data: Optional[Dict[str, str]] = None
    
    def _find_prompt_file(self, filename: str) -> Optional[Path]:
        """
        Find prompt file in order of priority:
        1. Custom prompts directory (if provided)
        2. Current directory config/prompts/
        3. Parent directories config/prompts/ (up to 3 levels)
        4. Package default (relative to this file)
        """
        # 1. Custom directory
        if self.custom_prompts_dir:
            custom_path = self.custom_prompts_dir / filename
            if custom_path.exists():
                return custom_path
        
        # 2. Current directory
        cwd_path = Path.cwd() / "config" / "prompts" / filename
        if cwd_path.exists():
            return cwd_path
        
        # 3. Parent directories (up to 3 levels)
        current = Path.cwd()
        for _ in range(3):
            current = current.parent
            parent_path = current / "config" / "prompts" / filename
            if parent_path.exists():
                return parent_path
        
        # 4. Package default (relative to this file)
        package_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "prompts" / filename
        if package_path.exists():
            return package_path
        
        return None
    
    def _load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Load YAML file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _get_system_prompt_data(self) -> Dict[str, Any]:
        """Load system prompt data (cached)"""
        if self._system_prompt_data is None:
            prompt_file = self._find_prompt_file("system_prompt.yaml")
            if prompt_file:
                self._system_prompt_data = self._load_yaml(prompt_file)
            else:
                # Fallback to default embedded prompt
                self._system_prompt_data = self._get_default_system_prompt()
        return self._system_prompt_data
    
    def _get_user_prompts_data(self) -> Dict[str, str]:
        """Load user prompts data (cached)"""
        if self._user_prompts_data is None:
            prompt_file = self._find_prompt_file("user_prompts.yaml")
            if prompt_file:
                self._user_prompts_data = self._load_yaml(prompt_file)
            else:
                # Fallback to default embedded prompts
                self._user_prompts_data = self._get_default_user_prompts()
        return self._user_prompts_data
    
    def _get_default_system_prompt(self) -> Dict[str, Any]:
        """Default system prompt if config file not found"""
        return {
            "role": "Senior Architect",
            "context": "You are a Senior Architect reviewing code changes.",
            "focus_areas": [
                "Architecture: Dependencies, layer separation",
                "Interfaces: ABC vs Protocol usage",
                "Dependency Injection: Injected vs instantiated",
                "Exceptions: Custom vs generic",
                "Type Hints: Complete coverage",
                "Framework Isolation: Adapters vs direct usage",
                "Dependency Management: pyproject.toml vs requirements.txt"
            ],
            "response_format": {
                "type": "json",
                "description": "Respond in JSON format"
            }
        }
    
    def _get_default_user_prompts(self) -> Dict[str, str]:
        """Default user prompts if config file not found"""
        return {
            "single_review": "Review this git diff:\n\n```diff\n{diff}\n```\n\nProvide JSON review.",
            "chunked_review": "Review chunk {chunk_num} ({file_count} files):\nFiles: {filenames}\n\n```diff\n{diff}\n```\n\nJSON review:",
            "file_review": "Review file `{filepath}`:\n\n```python\n{content}\n```\n\nJSON format."
        }
    
    def build_system_prompt(self, rules: str, dependencies: Optional[str] = None) -> str:
        """
        Build complete system prompt with role-playing
        
        Args:
            rules: Architectural rules content
            dependencies: Optional dependencies guidelines content
        
        Returns:
            Formatted system prompt string
        """
        data = self._get_system_prompt_data()
        
        # Build prompt with role-playing
        prompt_parts = []
        
        # Add role and goal (CrewAI-style)
        role = data.get('role', 'Senior Architect')
        goal = data.get('goal', 'Review code changes for architectural compliance')
        prompt_parts.append(f"# Role: {role}")
        prompt_parts.append(f"# Goal: {goal}\n")
        
        # Add backstory if present
        if 'backstory' in data:
            prompt_parts.append("# Backstory:")
            prompt_parts.append(data['backstory'])
            prompt_parts.append("")
        
        # Add instructions with rules
        instructions = data.get('instructions', 'Review the git diff against these coding standards:\n\n{rules}')
        prompt_parts.append(instructions.format(rules=rules))
        
        # Add dependencies if provided
        if dependencies and 'dependency_guidelines_intro' in data:
            dep_intro = data['dependency_guidelines_intro'].format(dependencies=dependencies)
            prompt_parts.append(dep_intro)
        
        # Add focus areas
        if 'focus_areas' in data:
            prompt_parts.append("\nFocus on:")
            for i, area in enumerate(data['focus_areas'], 1):
                prompt_parts.append(f"{i}. {area}")
        
        # Add response format
        if 'response_format' in data:
            fmt = data['response_format']
            prompt_parts.append(f"\n{fmt.get('description', 'Respond in JSON format:')}")
            if 'example' in fmt:
                prompt_parts.append(fmt['example'])
        
        return '\n'.join(prompt_parts)
    
    def get_user_prompt(self, template_name: str, **kwargs) -> str:
        """
        Get and render user prompt template
        
        Args:
            template_name: Name of the template (e.g., 'single_review', 'chunked_review')
            **kwargs: Variables to substitute in the template
        
        Returns:
            Rendered prompt string
        """
        prompts = self._get_user_prompts_data()
        template = prompts.get(template_name, "")
        
        if not template:
            raise ValueError(f"Prompt template '{template_name}' not found")
        
        return template.format(**kwargs)
