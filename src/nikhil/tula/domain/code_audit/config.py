"""
Unified configuration management for Tula

Handles tula_config.yaml which can contain:
- LLM configuration (inline or reference to external file)
- Prompt configuration (inline or reference to external files)
- Output directory settings
- Audit settings
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml


@dataclass
class OutputConfig:
    """Output directory configuration"""
    base_dir: Path = Path(".tula/output")
    intermediate_dir: Optional[str] = "intermediate"
    final_dir: str = "final"
    
    def get_intermediate_path(self) -> Optional[Path]:
        """Get intermediate output path if enabled"""
        if self.intermediate_dir:
            return self.base_dir / self.intermediate_dir
        return None
    
    def get_final_path(self) -> Path:
        """Get final output path"""
        return self.base_dir / self.final_dir
    
    def ensure_directories(self):
        """Create output directories if they don't exist"""
        self.get_final_path().mkdir(parents=True, exist_ok=True)
        intermediate = self.get_intermediate_path()
        if intermediate:
            intermediate.mkdir(parents=True, exist_ok=True)


@dataclass
class AuditConfig:
    """Configuration for AI code audit"""
    rules_file: Optional[Path] = None
    llm_config_path: Optional[Path] = None
    dependencies_file: Optional[Path] = None
    skip_audit: bool = False
    max_tokens_per_chunk: int = 14000
    
    # Prompt configuration
    system_prompt_path: Optional[Path] = None
    user_prompts_path: Optional[Path] = None
    
    # Output configuration
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Advanced options
    save_llm_responses: bool = True
    save_chunk_info: bool = True
    verbose: bool = False
    
    @classmethod
    def from_cli_args(cls, args) -> "AuditConfig":
        """Create config from command-line arguments"""
        return cls(
            rules_file=Path(args.rules) if hasattr(args, 'rules') and args.rules else None,
            llm_config_path=Path(args.config) if hasattr(args, 'config') and args.config else None,
            dependencies_file=Path(args.dependencies) if hasattr(args, 'dependencies') and args.dependencies else None,
            skip_audit=getattr(args, 'skip', False),
            max_tokens_per_chunk=getattr(args, 'max_tokens', 14000),
            verbose=getattr(args, 'verbose', False),
        )
    
    @classmethod
    def from_environment(cls) -> "AuditConfig":
        """Create config from environment variables"""
        return cls(
            rules_file=Path(os.environ['TULA_RULES_FILE']) if 'TULA_RULES_FILE' in os.environ else None,
            llm_config_path=Path(os.environ['TULA_LLM_CONFIG']) if 'TULA_LLM_CONFIG' in os.environ else None,
            dependencies_file=Path(os.environ['TULA_DEPENDENCIES_FILE']) if 'TULA_DEPENDENCIES_FILE' in os.environ else None,
            skip_audit=os.environ.get('SKIP_AI_AUDIT', '0') == '1',
        )
    
    @classmethod
    def from_tula_config(cls, config_path: Path) -> "AuditConfig":
        """
        Load configuration from tula_config.yaml
        
        This is the main configuration file that can contain:
        - LLM config (inline or path to external file)
        - Prompt config (inline or paths to external files)
        - Output directories
        - Audit settings
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Parse output configuration
        output_config = OutputConfig()
        if 'output' in data:
            output_data = data['output']
            output_config.base_dir = Path(output_data.get('base_dir', '.tula/output'))
            output_config.intermediate_dir = output_data.get('intermediate_dir', 'intermediate')
            output_config.final_dir = output_data.get('final_dir', 'final')
        
        # Parse audit configuration
        audit_data = data.get('audit', {})
        
        # Parse prompt configuration
        prompts_data = data.get('prompts', {})
        system_prompt_path = prompts_data.get('system_prompt_path')
        user_prompts_path = prompts_data.get('user_prompts_path')
        
        # LLM config can be inline or external
        llm_config_path = None
        if 'llm_config_path' in data:
            llm_config_path = Path(data['llm_config_path'])
        elif 'llm' in data:
            # Inline LLM config - save to temp file for  AIAuditor to use
            import json
            temp_dir = Path(output_config.base_dir) / ".temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            llm_config_path = temp_dir / "inline_llm_config.yaml"
            
            # Save inline config to temp file
            with open(llm_config_path, 'w', encoding='utf-8') as f:
                yaml.dump({'llm': data['llm'], 'llm_parameters': data.get('llm_parameters', {})}, f)
        
        # Parse advanced options
        advanced_data = data.get('advanced', {})
        
        # Parse logging
        logging_data = data.get('logging', {})
        
        return cls(
            rules_file=Path(audit_data['rules_file']) if 'rules_file' in audit_data else None,
            llm_config_path=llm_config_path,
            dependencies_file=Path(audit_data['dependencies_file']) if 'dependencies_file' in audit_data else None,
            skip_audit=audit_data.get('skip_audit', False),
            max_tokens_per_chunk=audit_data.get('max_tokens_per_chunk', 14000),
            system_prompt_path=Path(system_prompt_path) if system_prompt_path else None,
            user_prompts_path=Path(user_prompts_path) if user_prompts_path else None,
            output=output_config,
            save_llm_responses=advanced_data.get('save_llm_responses', True),
            save_chunk_info=advanced_data.get('save_chunk_info', True),
            verbose=logging_data.get('verbose', False),
        )


def find_config_file(filename: str, start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Search for configuration file in priority order:
    1. Current directory
    2. config/ subdirectory
    3. Parent directories (up to 3 levels)
    4. Home directory ~/.tula/
    5. Package default
    """
    start_dir = start_dir or Path.cwd()
    
    # 1. Current directory
    if (start_dir / filename).exists():
        return start_dir / filename
    
    # 2. config/ subdirectory
    if (start_dir / "config" / filename).exists():
        return start_dir / "config" / filename
    
    # 3. Parent directories (up to 3 levels)
    current = start_dir
    for _ in range(3):
        current = current.parent
        if (current / filename).exists():
            return current / filename
        if (current / "config" / filename).exists():
            return current / "config" / filename
    
    # 4. Home directory
    home_config = Path.home() / ".tula" / filename
    if home_config.exists():
        return home_config
    
    # 5. Package default (if it's a template)
    if filename.endswith('.md') or filename.endswith('.yaml'):
        package_default = Path(__file__).parent / "templates" / filename
        if package_default.exists():
            return package_default
    
    return None


def find_tula_config() -> Optional[Path]:
    """Find tula_config.yaml file"""
    return find_config_file("tula_config.yaml")


def resolve_config(config: AuditConfig) -> AuditConfig:
    """
    Resolve configuration by finding files if not explicitly set
    
    Priority order:
    1. Files explicitly set in config
    2. tula_config.yaml if exists
    3. Individual config files (llm_config.yaml, prompts, rules)
    4. Defaults
    """
    # Try to load tula_config.yaml if main config not fully specified
    tula_config_path = find_tula_config()
    if tula_config_path and not config.llm_config_path:
        # Merge with tula_config
        tula_config = AuditConfig.from_tula_config(tula_config_path)
        
        # Use tula_config values if not set in current config
        if not config.rules_file and tula_config.rules_file:
            config.rules_file = tula_config.rules_file
        if not config.llm_config_path and tula_config.llm_config_path:
            config.llm_config_path = tula_config.llm_config_path
        if not config.system_prompt_path and tula_config.system_prompt_path:
            config.system_prompt_path = tula_config.system_prompt_path
        if not config.user_prompts_path and tula_config.user_prompts_path:
            config.user_prompts_path = tula_config.user_prompts_path
        
        # Use output config from tula_config
        config.output = tula_config.output
    
    # Find rules file if not set
    if not config.rules_file:
        rules = find_config_file("AGENTS.md")
        if not rules:
            # Try alternative names
            rules = find_config_file("ARCHITECTURE.md") or find_config_file("RULES.md")
        config.rules_file = rules
    
    # Find LLM config if not set
    if not config.llm_config_path:
        config.llm_config_path = find_config_file("llm_config.yaml")
    
    # Find dependencies file if not set
    if not config.dependencies_file:
        config.dependencies_file = find_config_file("DEPENDENCIES.md")
    
    # Ensure output directories exist
    config.output.ensure_directories()
    
    return config
