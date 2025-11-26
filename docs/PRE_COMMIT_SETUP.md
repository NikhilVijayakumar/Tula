# Pre-commit Setup Guide

This guide explains how to use the automated code quality enforcement system for Amsha.

---

## Overview

We use **two-tier code quality enforcement**:

1. **Automated Checks** (mypy, black, flake8) - Always run
2. **AI-Powered Review** (LLM against AGENTS.md) - Optional but recommended

---

## Quick Start

### 1. Install Pre-commit

```bash
pip install pre-commit
```

### 2. Install the Git Hooks

```bash
cd /path/to/Amsha
pre-commit install
```

This installs hooks that run automatically on `git commit`.

### 3. (Optional) Set up AI Review

For AI-powered architectural review, set your OpenAI API key:

```bash
# Linux/Mac
export OPENAI_API_KEY='your-key-here'

# Windows PowerShell
$env:OPENAI_API_KEY='your-key-here'

# Add to your shell profile for persistence
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.bashrc  # Linux/Mac
```

Also install the OpenAI library:

```bash
pip install openai
```

---

## What Gets Checked

### Automated Checks (Always Run)

1. **Trailing Whitespace** - Removes trailing spaces
2. **YAML/JSON Validation** - Ensures config files are valid
3. **Large Files** - Prevents committing files >1MB
4. **Type Checking (mypy)** 🔴 **CRITICAL**
   - Validates all type hints
   - Ensures `Protocol` and `ABC` are used correctly
   - Enforces strict typing per AGENTS.md
5. **Code Formatting (black)** - Auto-formats Python code
6. **Import Sorting (isort)** - Organizes imports
7. **Linting (flake8)** - Catches code smells

### AI-Powered Review (Optional)

8. **Architecture Audit** 🤖
   - Reviews diff against AGENTS.md guidelines
   - Checks for Clean Architecture violations
   - Validates ABC vs Protocol usage
   - Ensures dependency injection patterns
   - Detects framework coupling issues

---

## Usage

### Normal Commit (All Checks)

```bash
git add .
git commit -m "Your commit message"
```

Pre-commit runs automatically. If any check fails:
- **Auto-fixable issues** (black, isort): Automatically fixed, re-stage and commit
- **Type errors** (mypy): Fix manually, then re-commit
- **AI review failures**: Fix violations or skip (see below)

### Skip AI Review (When Needed)

If you need to commit without AI review:

```bash
SKIP_AI_AUDIT=1 git commit -m "Emergency fix"
```

**When to skip:**
- Emergency hotfixes
- AI is down/slow
- You've manually verified compliance with AGENTS.md

### Run Checks Manually

Test all hooks without committing:

```bash
pre-commit run --all-files
```

Run specific hook:

```bash
pre-commit run mypy --all-files
pre-commit run ai-architecture-audit --all-files
```

### Update Hook Versions

Update to latest hook versions:

```bash
pre-commit autoupdate
```

---

## Configuration Files

### `.pre-commit-config.yaml`
Defines which hooks run and their configuration.

### `mypy.ini`
Mypy type checking configuration. Key settings:
- `strict = True` - Enforces strict type checking
- `disallow_untyped_defs = True` - All functions must have type hints
- Per-module settings for external libraries

### `scripts/ai_audit.py`
AI-powered architectural review script. Can run standalone:

```bash
python scripts/ai_audit.py
```

---

## Troubleshooting

### "mypy: command not found"

Install mypy:
```bash
pip install mypy
```

### "OpenAI API key not set"

Either:
1. Set the API key: `export OPENAI_API_KEY='your-key'`
2. Skip AI audit: `SKIP_AI_AUDIT=1 git commit -m '...'`

### "Hook failed" - How to fix

1. **Read the error message** - It tells you what's wrong
2. **Fix the issue** in your code
3. **Re-stage** the fixed files: `git add .`
4. **Try committing again**: `git commit -m '...'`

### Type errors in external libraries

If mypy complains about external libraries (crewai, pymongo, etc.):
- Add to `mypy.ini` under `[mypy-library_name.*]`
- Set `ignore_missing_imports = True`

---

## AI Review Details

### What the AI Checks

The AI reviews your code against **AGENTS.md** guidelines:

1. **Clean Architecture**
   - Dependencies flow inward (domain → service → infrastructure)
   - No framework imports in service layer

2. **Interface Patterns**
   - `ABC` used for repository interfaces
   - `Protocol` used for client APIs

3. **Dependency Injection**
   - Dependencies injected, not instantiated
   - Services don't create their own repositories

4. **Exception Handling**
   - Custom exceptions instead of generic `Exception`
   - Proper exception hierarchy

5. **Type Hints**
   - All parameters have types
   - All returns have types

6. **Framework Isolation**
   - Framework code in adapters only
   - No tight coupling to CrewAI, DVC, etc.

### Sample AI Review Output

```
🤖 AI Architecture Audit
═══════════════════════════════════════════════════

ℹ️  Getting staged changes...
✅ Found 47 lines of changes
ℹ️  Loading AGENTS.md...
ℹ️  Performing LLM-powered review...

Review Results:

📝 Changes follow clean architecture principles. Minor suggestions provided.

Suggestions:
  💡 Consider adding type hints to helper function on line 23
  💡 Exception handling could use custom exception instead of ValueError

✨ Architectural review PASSED
ℹ️  Changes comply with AGENTS.md standards
```

---

## Best Practices

### 1. Commit Often, Review Often
Small commits are easier to review and fix.

### 2. Fix Type Errors Immediately
Don't accumulate type errors. Fix them as you code.

### 3. Read AI Feedback
The AI suggestions often catch subtle violations.

### 4. Use AI Review for Learning
Read why the AI flagged something - it helps internalize the patterns.

### 5. Don't Bypass Checks Habitually
Bypassing checks defeats their purpose. Only skip when truly necessary.

---

## Integration with Development Workflow

### Recommended Workflow

```bash
# 1. Make changes
vim src/nikhil/amsha/toolkit/crew_forge/service/my_service.py

# 2. Test manually (optional but recommended before committing)
pytest tests/unit/test_my_service.py

# 3. Stage changes
git add src/nikhil/amsha/toolkit/crew_forge/service/my_service.py

# 4. Commit (pre-commit runs automatically)
git commit -m "Add new service method"

# 5. If checks fail, fix and re-commit
# Pre-commit will tell you what to fix

# 6. Push when all checks pass
git push
```

### CI/CD Integration

Add to your CI pipeline (`.github/workflows/ci.yml` or similar):

```yaml
- name: Run pre-commit checks
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

This ensures all PRs pass the same checks.

---

## Advanced: Manual AI Review with Antigravity

You can also ask Antigravity to review your code:

```
# Before committing:
git diff > changes.diff

# In Antigravity chat:
"Review this diff against AGENTS.md: <paste diff>"

# Or more directly:
"Review my staged changes against our architectural standards"
```

This gives you conversational feedback before even attempting to commit.

---

## Disabling Specific Hooks

To temporarily disable a hook, edit `.pre-commit-config.yaml`:

```yaml
# Comment out the hook you want to disable
#  - repo: https://github.com/pre-commit/mirrors-mypy
#    rev: v1.8.0
#    hooks:
#      - id: mypy
```

Or use `SKIP` environment variable:

```bash
SKIP=mypy git commit -m "Bypass mypy for this commit"
SKIP=ai-architecture-audit,mypy git commit -m "Bypass multiple hooks"
```

---

## Summary

✅ **Automated enforcement** catches mistakes early  
✅ **AI review** ensures architectural compliance  
✅ **Easy to use** - just commit normally  
✅ **Easy to bypass** when needed - use `SKIP_AI_AUDIT=1`  
✅ **Aligned with AGENTS.md** - same standards, automated

**Questions?** Check the [pre-commit documentation](https://pre-commit.com/) or ask in team chat.
