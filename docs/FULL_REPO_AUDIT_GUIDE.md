# Full Repository Audit - Usage Guide

## Overview

The `--full-repo` mode audits your **entire codebase** against architectural rules, not just staged changes.

---

## Basic Usage

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Audit entire repository
amsha-audit --full-repo

# Save detailed report
amsha-audit --full-repo --output audit_report.json
```

---

## Chunking Support

**Yes!** Full repo scan fully supports chunking, and it's **model-aware**.

### How Chunking Works

1. **Per-File Chunking:**
   - Each Python file is reviewed individually
   - Large files are automatically chunked if needed
   - Chunks respect model context limits

2. **Model-Specific Chunk Sizes:**
   - **LM Studio (16k context):** ~12k token chunks
   - **Gemini (1M context):** ~200k token chunks
   - **GPT-4 (128k context):** ~100k token chunks

3. **Smart Grouping:**
   - Files grouped by module
   - Related files reviewed together when possible
   - Progress shown per module

---

## Configuring Chunk Sizes

### Option 1: Per-Model Configuration (Recommended)

Add `max_tokens` to model in `llm_config.yaml`:

```yaml
llm:
  evaluation:
    default: gemini  # Use Gemini for large repos
    models:
      gemini:
        model: "gemini/gemini-1.5-flash"
        api_key: "your-key"
        max_tokens: 200000  # Gemini can handle 200k chunks!
      
      gpt:
        base_url: "http://localhost:1234/v1"
        model: "lm_studio/openai/gpt-oss-20b"
        api_key: "lm_studio"
        max_tokens: 12000  # LM Studio: smaller chunks
```

### Option 2: CLI Override

```bash
# Override chunk size for this run
amsha-audit --full-repo --max-tokens 50000
```

### Option 3: Auto-Detection (Default)

If not specified, chunk size is calculated from `max_completion_tokens`:

```yaml
llm_parameters:
  evaluation:
    max_completion_tokens: 1000  # Response size
    # Input chunks auto-calculated as 3x this value
```

---

## Model Recommendations

### For Small Repositories (<100 files)

**LM Studio (Local):**
```yaml
evaluation:
  default: gpt
  models:
    gpt:
      base_url: "http://localhost:1234/v1"
      model: "lm_studio/openai/gpt-oss-20b"
      max_tokens: 12000  # Safe for 16k context
```

**Pros:**
- Free (local)
- Privacy
- Fast for small files

**Cons:**
- Smaller chunks
- More LLM calls for large files

### For Medium Repositories (100-500 files)

**Gemini (Free Tier):**
```yaml
evaluation:
  default: gemini
  models:
    gemini:
      model: "gemini/gemini-1.5-flash"
      api_key: "your-key"
      max_tokens: 100000  # Conservative for free tier
```

**Pros:**
- 1M token context
- Handles full modules in one call
- Free tier available
- Fast

**Cons:**
- Rate limits (free tier)
- Requires internet

### For Large Repositories (>500 files)

**Gemini with Maximum Chunks:**
```yaml
evaluation:
  default: gemini
  models:
    gemini:
      model: "gemini/gemini-1.5-flash"
      api_key: "your-key"
      max_tokens: 200000  # Review entire modules at once!
```

**Pros:**
- Can review entire module in single call
- Faster than small chunks
- Better context understanding

**Performance Example:**
- 500 files × 200 lines = 100k lines
- With 200k chunks: ~5-10 LLM calls
- With 12k chunks: ~100+ LLM calls

---

## Example: Amsha Repository Audit

### Current Amsha Stats
- Files: ~150 Python files
- Modules: ~8 modules
- Total lines: ~15k lines

### With LM Studio (12k chunks)
```bash
amsha-audit --full-repo --output amsha_audit.json

# Output:
# 📦 Module: crew_forge (45 files)
# 📦 Module: llm_factory (12 files)
# 📦 Module: code_audit (5 files)
# ...
# ✅ Total: 150 files, ~150 LLM calls, ~10 minutes
```

### With Gemini (200k chunks)
```bash
amsha-audit --full-repo --output amsha_audit.json

# Output:
# 📦 Module: crew_forge (45 files) - 1 chunk
# 📦 Module: llm_factory (12 files) - 1 chunk
# 📦 Module: code_audit (5 files) - 1 chunk
# ...
# ✅ Total: 150 files, ~8 LLM calls, ~2 minutes
```

---

## Generated Reports

### JSON Report (`audit_report.json`)

```json
{
  "metadata": {
    "audit_date": "2025-11-25T08:45:00",
    "rules_file": "AGENTS.md",
    "model_used": "gemini-1.5-flash"
  },
  "total_files": 150,
  "summary": {
    "total_issues": 23,
    "total_suggestions": 45,
    "files_with_issues": 18,
    "clean_files": 132
  },
  "modules": {
    "crew_forge": {
      "files": 45,
      "issues": ["file.py: Missing type hints", ...],
      "suggestions": [...]
    }
  },
  "files_with_violations": [
    "src/module/file.py",
    ...
  ]
}
```

### Markdown Report (`audit_report.md`)

```markdown
# Repository Audit Report

**Date:** 2025-11-25T08:45:00
**Rules:** AGENTS.md
**Model:** gemini-1.5-flash

## Summary

- **Total Files:** 150
- **Files with Issues:** 18
- **Clean Files:** 132
- **Total Issues:** 23
- **Total Suggestions:** 45

## Module Reports

### crew_forge

- Files: 45
- Issues: 5
- Suggestions: 12

**Issues:**
- ❌ service.py: CrewAI imported in service layer
- ❌ builder.py: Missing type hints

**Suggestions:**
- 💡 orchestrator.py: Use custom exceptions
...
```

---

## Scheduling Periodic Audits

### Weekly Audit (CI/CD)

```yaml
# .github/workflows/weekly-audit.yml
name: Weekly Architecture Audit

on:
  schedule:
    - cron: '0 0 * * 1'  # Every Monday

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install amsha[audit]
      - run: amsha-audit --full-repo --output weekly_audit.json
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      - uses: actions/upload-artifact@v3
        with:
          name: audit-report
          path: weekly_audit.*
```

### Monthly Deep Audit

```bash
#!/bin/bash
# monthly_audit.sh

source venv/bin/activate

echo "Running monthly architecture audit..."

amsha-audit --full-repo \
  --output "reports/audit_$(date +%Y%m).json" \
  --max-tokens 200000

echo "Report saved to reports/audit_$(date +%Y%m).json"
```

---

## Best Practices

### 1. Use Larger Chunks for Full Repo

```yaml
# For full repo audits, use Gemini with large chunks
evaluation:
  default: gemini
  models:
    gemini:
      max_tokens: 200000
```

### 2. Use Smaller Chunks for Pre-commit

```yaml
# For pre-commit (diff-based), smaller chunks are fine
# Use LM Studio for speed
```

### 3. Save Historical Reports

```bash
# Create reports directory
mkdir -p reports/audits

# Save with timestamp
amsha-audit --full-repo \
  --output "reports/audits/audit_$(date +%Y%m%d).json"
```

### 4. Compare Reports Over Time

```bash
# Track improvement
diff reports/audits/audit_20251101.md \
     reports/audits/audit_20251201.md
```

---

## Performance Comparison

| Model | Context | Chunk Size | Amsha (150 files) | Large Repo (500 files) |
|-------|---------|------------|-------------------|----------------------|
| LM Studio (GPT-OSS-20B) | 16k | 12k | ~10 mins | ~40 mins |
| Gemini 1.5 Flash | 1M | 100k | ~3 mins | ~8 mins |
| Gemini 1.5 Flash | 1M | 200k | ~2 mins | ~5 mins |
| GPT-4 (OpenAI) | 128k | 100k | ~5 mins | ~12 mins |

**Note:** Times include LLM calls + processing. Actual times vary by file size and complexity.

---

## Troubleshooting

### Issue: "Too many files, taking too long"

**Solution:** Use larger chunks with Gemini

```bash
amsha-audit --full-repo --max-tokens 200000
```

### Issue: "Context length exceeded"

**Solution:** Reduce chunk size

```bash
amsha-audit --full-repo --max-tokens 8000
```

### Issue: "LM Studio timeout"

**Solution:** 
1. Use smaller chunks for LM Studio
2. Or switch to Gemini for full repo audits

```yaml
# Use Gemini for full repo, LM Studio for diffs
evaluation:
  default: gemini  # Full repo
creative:
  default: gpt     # Daily work
```

---

## Summary

✅ **Full repo scan supports chunking**
✅ **Model-specific chunk sizes** (Gemini: 200k, LM Studio: 12k)
✅ **Configurable via llm_config.yaml and CLI**
✅ **Generates detailed JSON + Markdown reports**
✅ **Perfect for periodic compliance checks**

**Recommendation:**
- **Daily commits:** LM Studio with `amsha-audit` (diff-based)
- **Weekly/Monthly audits:** Gemini with `amsha-audit --full-repo --max-tokens 200000`
