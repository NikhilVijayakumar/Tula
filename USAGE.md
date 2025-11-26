# Running Tula Code Audit

This guide shows how to run Tula code audits in different scenarios.

## 🎯 Quick Start

### Scenario 1: Running in Tula Repository (Development)

```bash
# 1. Install dependencies
pip install -e .

# 2. Create/configure tula_config.yaml (see Configuration section)

# 3. Run audit
python run_audit.py
```

### Scenario 2: Using Tula as Dependency (Client Project)

```bash
# 1. Install Tula
pip install tula

# 2. Create tula_config.yaml in your project root

# 3. Run via CLI
tula-audit

# OR via Python
python -c "from nikhil.tula.domain.code_audit.scripts.ai_audit import main; main()"

# OR create your own script (see examples below)
```

## 📋 Configuration

### Required: tula_config.yaml

Create `tula_config.yaml` in your project root:

```yaml
# Output directories
output:
  base_dir: ".tula/output"
  intermediate_dir: "intermediate"  # For debugging
  final_dir: "final"

# LLM Configuration (works with local or cloud LLMs via LiteLLM)
llm:
  evaluation:
    default: local  # or gemini, openai, claude
    models:
      # Local LLM (LM Studio, Ollama)
      local:
        model: "openai/local-model"
        base_url: "http://localhost:1234/v1"  # LM Studio default
        api_key: "not-needed"
      
      # Or cloud LLM
      gemini:
        model: "gemini/gemini-1.5-flash"
        api_key: ${GEMINI_API_KEY}
  
  # Optional: Different model for markdown formatting
  creative:
    default: local
    models:
      local:
        model: "openai/local-model"
        base_url: "http://localhost:1234/v1"
        api_key: "not-needed"
  
  llm_parameters:
    evaluation:
      temperature: 0.0
      max_completion_tokens: 4096
    creative:
      temperature: 0.3
      max_completion_tokens: 4096

# Prompts (optional, uses defaults if not specified)
prompts:
  system_prompt_path: "config/prompts/system_prompt.yaml"
  user_prompts_path: "config/prompts/user_prompts.yaml"

# Audit settings
audit:
  rules_file: "AGENTS.md"  # Your architectural rules
  dependencies_file: "DEPENDENCIES.md"  # Optional
  max_tokens_per_chunk: 14000
  skip_audit: false

# Advanced
advanced:
  save_llm_responses: true  # Save intermediate results
  save_chunk_info: true
```

### Required: AGENTS.md

Create `AGENTS.md` with your coding standards:

```markdown
# Coding Standards

## Architecture
- Follow clean architecture principles
- Use dependency injection
- Domain layer should not depend on infrastructure

## Python Best Practices
- Use type hints for all functions
- Use custom exceptions, not generic Exception
- Follow PEP 8 style guide

## Testing
- Write unit tests for business logic
- Mock external dependencies
```

### Optional: DEPENDENCIES.md

```markdown
# Dependency Guidelines

## Allowed
- FastAPI for web framework
- Pydantic for validation

## Forbidden
- Direct database imports in service layer
```

## 🚀 Usage Examples

### Example 1: Basic Audit (Tula Repo)

```bash
# Run with default config
python run_audit.py

# Run with specific config
python run_audit.py --config path/to/tula_config.yaml
```

### Example 2: Python Script (Client Project)

```python
#!/usr/bin/env python
"""Audit example for client project"""

from pathlib import Path
from nikhil.tula.domain.code_audit.config import AuditConfig, resolve_config
from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor

# Load config
config = AuditConfig.from_tula_config(Path("tula_config.yaml"))
config = resolve_config(config)

# Run audit
auditor = AIAuditor(config)
result = auditor.audit()

# Check results
if result.approved:
    print("✅ Code approved!")
    exit(0)
else:
    print(f"❌ {len(result.issues)} issues found")
    for issue in result.issues:
        print(f"  - {issue}")
    exit(1)
```

### Example 3: Pre-commit Hook

```python
#!/usr/bin/env python
"""Use as Git pre-commit hook"""

import sys
from pathlib import Path
from nikhil.tula.domain.code_audit.config import AuditConfig, resolve_config
from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor

# Quick config
config = AuditConfig(
    rules_file=Path("AGENTS.md"),
    llm_config_path=Path("tula_config.yaml"),
    skip_audit=False
)
config = resolve_config(config)

# Run audit
auditor = AIAuditor(config)
result = auditor.audit()

# Block commit if not approved
if not result.approved and not result.skipped:
    print(f"\n❌ Pre-commit audit failed: {len(result.issues)} issues")
    for issue in result.issues[:3]:
        print(f"  • {issue}")
    sys.exit(1)

print("✅ Pre-commit audit passed")
```

### Example 4: CI/CD Pipeline

```yaml
# .github/workflows/audit.yml
name: Code Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Tula
        run: pip install tula
      
      - name: Run Audit
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          tula-audit
          
          # Check results
          approved=$(jq -r '.approved' .tula/output/final/latest.json)
          if [ "$approved" != "true" ]; then
            echo "❌ Audit failed"
            cat .tula/output/final/latest.md
            exit 1
          fi
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        run: |
          gh pr comment ${{ github.event.pull_request.number }} \
            --body-file .tula/output/final/latest.md
```

## 🔍 How It Works

### Combined Audit Approach

Tula runs a 3-stage audit:

**Stage 1: Pattern Matching** (Always runs, ~5ms)
- Fast, local checks
- No LLM required
- Catches common violations

**Stage 2: LLM Analysis** (If configured)
- Deep architectural review
- Uses your configured LLM (local or cloud)
- Automatic chunking for large diffs
- Understands context and architecture

**Stage 3: Combine Results**
- Merges pattern + LLM results
- Deduplicates issues
- Tags each issue with source: `[pattern]` or `[llm]`
- Saves intermediate results for debugging

### Output Structure

```
.tula/output/
├── intermediate/          # Debugging (if enabled)
│   └── analysis/
│       ├── pattern_matching.json
│       ├── llm_analysis.json
│       └── combined_results.json
└── final/                 # Final reports
    ├── latest.json        # Current run (JSON)
    ├── latest.md          # Current run (Markdown)
    ├── comparison.md      # Historical trends
    └── history/           # Timestamped archive
        ├── audit_20250126_123045.json
        └── audit_20250126_123045.md
```

## 🎨 LLM Configuration

### Local LLMs (No API costs!)

**LM Studio:**
```yaml
llm:
  evaluation:
    default: lmstudio
    models:
      lmstudio:
        model: "openai/local-model"
        base_url: "http://localhost:1234/v1"
        api_key: "not-needed"
```

**Ollama:**
```yaml
llm:
  evaluation:
    default: ollama
    models:
      ollama:
        model: "ollama/llama2"  # or codellama, mistral
        # Ollama auto-detected on localhost:11434
```

### Cloud LLMs

**Google Gemini:**
```yaml
llm:
  evaluation:
    default: gemini
    models:
      gemini:
        model: "gemini/gemini-1.5-flash"
        api_key: ${GEMINI_API_KEY}
```

**OpenAI:**
```yaml
llm:
  evaluation:
    default: openai
    models:
      openai:
        model: "gpt-4"
        api_key: ${OPENAI_API_KEY}
```

**Anthropic Claude:**
```yaml
llm:
  evaluation:
    default: claude
    models:
      claude:
        model: "claude-3-opus-20240229"
        api_key: ${ANTHROPIC_API_KEY}
```

## 🐛 Troubleshooting

### No LLM configured
```
⚠️  LLM not available, using pattern matching only
```
→ Pattern matching still runs! LLM is optional.

### LLM connection failed
```
❌ LLM API call failed: Connection refused
```
→ Check LM Studio/Ollama is running, or API key is correct

### No changes to review
```
✅ No changes to review
```
→ Make sure you have staged changes: `git add .`

### No rules file
```
⚠️  No rules file found, using basic checks
```
→ Create `AGENTS.md` with your coding standards

## 📚 Advanced: Custom Integration

```python
from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor
from nikhil.tula.domain.code_audit.config import AuditConfig, OutputConfig
from pathlib import Path

# Custom configuration
config = AuditConfig(
    rules_file=Path("my_rules.md"),
    llm_config_path=Path("my_llm_config.yaml"),
    system_prompt_path=Path("custom_prompts/system.yaml"),
    output=OutputConfig(
        base_dir=Path("custom_output"),
        intermediate_dir="debug",
        final_dir="reports"
    ),
    save_llm_responses=True,
    max_tokens_per_chunk=10000
)

# Run audit
auditor = AIAuditor(config)
result = auditor.audit()

# Process results
if result.approved:
    # Deploy to production
    deploy()
else:
    # Block deployment
    notify_team(result.issues)
```

---

For more details, see:
- [Report Files Documentation](docs/REPORT_FILES.md)
- [Output Structure](docs/OUTPUT_STRUCTURE.md)
- [Prompt Configuration](config/prompts/README.md)
