# Using Amsha AI Audit in Your Client Project

This guide explains how client projects can use Amsha's AI-powered code audit system.

---

## Overview

Amsha provides a packageable AI audit tool (`amsha-audit`) that:
- Reviews code against architectural rules
- Works with your own rules files (AGENTS.md, ARCHITECTURE.md, etc.)
- Uses your LLM configuration
- Integrates with pre-commit hooks
- Requires **zero code maintenance** from clients

---

## Quick Start

### 1. Install Amsha

```bash
# Basic installation
pip install amsha

# With AI audit support (includes Gemini)
pip install amsha[audit]

# With all dev tools
pip install amsha[dev]
```

### 2. Create Your Rules File

```bash
# Option A: Use Amsha's template as starting point
python -c "from pathlib import Path; import nikhil.amsha.toolkit.code_audit as ca; print((Path(ca.__file__).parent / 'templates' / 'AGENTS.md.template').read_text())" > MY_RULES.md

# Option B: Create from scratch
cat > MY_RULES.md << 'EOF'
# My Project - Architectural Rules

## Critical Rules
- Use dependency injection
- All functions must have type hints
- Custom exceptions only (no generic Exception)

## Code Style
- Use black for formatting
- Maximum line length: 120
EOF
```

### 3. Set Up LLM Configuration

Create `llm_config.yaml` (same format as Amsha's):

```yaml
llm:
  evaluation:
    default: gpt  # or gemini
    models:
      gpt:
        base_url: "http://localhost:1234/v1"
        model: "lm_studio/your-model"
        api_key: "lm_studio"
      gemini:
        model: "gemini/gemini-1.5-flash"
        api_key: "your-gemini-key"

llm_parameters:
  evaluation:
    temperature: 0.3
    max_completion_tokens: 1000
```

### 4. Configure Pre-commit

Create `.pre-commit-config.yaml`:

```yaml
repos:
  # Basic checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  # Amsha AI Audit
  - repo: local
    hooks:
      - id: ai-audit
        name: 🤖 AI Architecture Review  
        entry: amsha-audit --rules MY_RULES.md
        language: system
        pass_filenames: false
```

Install hooks:

```bash
pre-commit install
```

### 5. Test

```bash
# Test the command
amsha-audit --help

# Run audit manually
amsha-audit --rules MY_RULES.md

# Make a commit (triggers automatically)
git add .
git commit -m "Test commit"
```

---

## Configuration Options

### Command-Line Arguments

```bash
# Use default config discovery
amsha-audit

# Specify custom rules
amsha-audit --rules docs/ARCHITECTURE.md

# Specify LLM config
amsha-audit --config config/my_llm_config.yaml

# Specify dependencies tracking file
amsha-audit --dependencies docs/DEPS.md

# Skip audit (for emergencies)
amsha-audit --skip

# Adjust max tokens per chunk
amsha-audit --max-tokens 12000

# Verbose output
amsha-audit --verbose
```

### Environment Variables

```bash
# Set rules file location
export AMSHA_RULES_FILE="docs/architecture/RULES.md"

# Set LLM config location
export AMSHA_LLM_CONFIG="config/llm.yaml"

# Set dependencies file
export AMSHA_DEPENDENCIES_FILE="docs/DEPENDENCIES.md"

# Skip audit
export SKIP_AI_AUDIT=1

# Then just run
amsha-audit
```

### Config File Discovery

`amsha-audit` automatically searches for config files:

**Priority order:**
1. Command-line arguments (`--rules`, `--config`)
2. Environment variables (`AMSHA_RULES_FILE`, etc.)
3. Current directory (`./ AGENTS.md`, `./llm_config.yaml`)
4. `config/` subdirectory
5. Parent directories (up to 3 levels)
6. Home directory (`~/.amsha/`)
7. Package defaults (Amsha's templates)

**File names searched:**
- Rules: `AGENTS.md`, `ARCHITECTURE.md`, `RULES.md`
- LLM: `llm_config.yaml`
- Dependencies: `DEPENDENCIES.md`

---

## Client Project Structure

Typical client project layout:

```
my-project/
├── .pre-commit-config.yaml     # Pre-commit hooks
├── ARCHITECTURE.md             # Your architectural rules
├── config/
│   └── llm_config.yaml         # LLM configuration
├── .gitignore                  # Ignore llm_config.yaml
├── pyproject.toml              # Includes: amsha[audit]
└── src/
    └── ...
```

---

## Examples

### Example 1: Minimal Setup

```bash
# Install
pip install amsha[audit]

# Create simple rules
echo "# Rules\n- Use type hints\n- Custom exceptions" > RULES.md

# Run
amsha-audit --rules RULES.md
```

### Example 2: Full Setup with LM Studio

```bash
# Install
pip install amsha[audit]

# Create rules
cp /path/to/amsha/templates/AGENTS.md.template ARCHITECTURE.md
vim ARCHITECTURE.md  # Customize

# Create LLM config
cat > llm_config.yaml << 'EOF'
llm:
  evaluation:
    default: local
    models:
      local:
        base_url: "http://localhost:1234/v1"
        model: "lm_studio/my-model"
        api_key: "not-needed"
llm_parameters:
  evaluation:
    temperature: 0.3
    max_completion_tokens: 1000
EOF

# Test
amsha-audit --verbose

# Configure pre-commit
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: local
    hooks:
      - id: ai-audit
        name: AI Audit
        entry: amsha-audit
        language: system
EOF

pre-commit install
```

### Example 3: Team Setup with Shared Config

```bash
# Create ~/.amsha/ for shared config
mkdir -p ~/.amsha

# Shared rules for all projects
cp company_standards.md ~/.amsha/AGENTS.md

# Shared LLM config
cp company_llm_config.yaml ~/.amsha/llm_config.yaml

# Now all projects use these by default
cd any-project
amsha-audit  # Uses ~/.amsha/ configs
```

---

## Integration Patterns

### Pattern 1: Per-Project Rules

Each project has its own rules:

```
project-a/AGENTS.md  # Project A's rules
project-b/AGENTS.md  # Project B's rules
```

### Pattern 2: Shared Organization Rules

Organization-wide rules in home directory:

```
~/.amsha/AGENTS.md         # Shared rules
~/.amsha/llm_config.yaml   # Shared LLM config
```

Projects can override:

```
my-project/AGENTS.md  # Overrides ~/.amsha/AGENTS.md
```

### Pattern 3: Hybrid

```
~/.amsha/AGENTS.md         # Base rules
my-project/AGENTS.md       # Extends base with project-specific
```

In `my-project/AGENTS.md`:

```markdown
# My Project Rules

See ~/.amsha/AGENTS.md for organization standards.

## Additional Project-Specific Rules
- ...
```

---

## Troubleshooting

### "No rules file found"

```bash
# Check what's being searched
amsha-audit --verbose

# Specify explicitly
amsha-audit --rules /path/to/RULES.md

# Or set environment
export AMSHA_RULES_FILE="/path/to/RULES.md"
```

### "LLM config not found"

```bash
# Check search path
amsha-audit --verbose

# Create in current directory
cp example_llm_config.yaml llm_config.yaml

# Or specify
amsha-audit --config /path/to/llm_config.yaml
```

### "LLM connection failed"

```bash
# For LM Studio: ensure it's running
# Check http://localhost:1234/v1

# For Gemini: check API key
# Test: export GEMINI_API_KEY="your-key"

# fallback to pattern matching works anyway
```

### Pre-commit hook fails

```bash
# Test manually first
amsha-audit

# Skip for urgent commit
SKIP_AI_AUDIT=1 git commit -m "Emergency fix"

# Or in pre-commit hook
entry: amsha-audit --skip
```

---

## Benefits for Clients

✅ **Zero Code Maintenance**
- No scripts to copy or maintain
- Updates come with `pip install --upgrade amsha`

✅ **Simple Configuration**
- Just provide `AGENTS.md` (rules)
- Optional `llm_config.yaml` (for LLM support)

✅ **Flexible**
- Works with or without LLM
- Multiple LLM providers supported
- Custom token limits

✅ **Team-Friendly**
- Shared configurations via `~/.amsha/`
- Project-specific overrides
- Clear documentation

✅ **Pre-commit Integration**
- One-line setup
- Automatic on every commit
- Easy to skip when needed

---

## Upgrading

```bash
# Upgrade Amsha
pip install --upgrade amsha[audit]

# Check version
amsha-audit --version

# Test
amsha-audit --help
```

Your rules files and configs remain unchanged!

---

## Support

For issues or questions:
1. Check `amsha-audit --help`
2. Run with `--verbose` for diagnostics
3. Review Amsha documentation
4. Check example configs in Amsha repository

---

## Summary

**To use Amsha AI Audit in your project:**

1. `pip install amsha[audit]`
2. Create `AGENTS.md` (your rules)
3. Optional: Create `llm_config.yaml`
4. Add to `.pre-commit-config.yaml`:
   ```yaml
   - id: ai-audit
     entry: amsha-audit
     language: system
   ```
5. `pre-commit install`

**That's it!** All implementation and dependencies are managed by Amsha.
