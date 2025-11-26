# Tula Code Auditor - Quick Reference

## 🎯 Two Scenarios

### Scenario 1: Git Diff Audit (Pre-Commit)
Audits only staged changes. Fast, runs in ~1-5 seconds.

```python
from nikhil.tula import TulaAuditor

auditor = TulaAuditor("tula_config.yaml")
result = auditor.audit_git_diff()

if result.approved:
    print("✅ Ready to commit")
else:
    print(f"❌ {len(result.issues)} issues found")
```

### Scenario 2: Full Repository Audit
Audits all Python files. Comprehensive, takes longer.

```python
from nikhil.tula import TulaAuditor

auditor = TulaAuditor("tula_config.yaml")
report = auditor.audit_repository()

print(f"Files: {report['total_files']}")
print(f"Violations: {report['total_violations']}")
```

## 📦 Installation

### In Tula Repo (Development)
```bash
pip install -e .
python examples/audit_git_diff.py
```

### As Dependency (Client Project)
```bash
pip install tula
```

```python
# your_project/audit.py
from nikhil.tula import TulaAuditor

auditor = TulaAuditor()  # Auto-detects tula_config.yaml
result = auditor.audit_git_diff()
```

## ⚙️ Quick Configuration

Create `tula_config.yaml`:

```yaml
output:
  base_dir: ".tula/output"
  intermediate_dir: "intermediate"
  final_dir: "final"

llm:
  evaluation:
    default: local  # or gemini, openai, claude
    models:
      local:
        model: "openai/local-model"
        base_url: "http://localhost:1234/v1"  # LM Studio
        api_key: "not-needed"

audit:
  rules_file: "AGENTS.md"
```

## 📝 Examples

See `examples/` directory:
- `audit_git_diff.py` - Pre-commit check
- `audit_repository.py` - Full repo audit
- `client_usage.py` - Client integration patterns

## 📊 What You Get

### Pattern Matching (Always Runs)
- Fast local checks (~5ms)
- No LLM required
- Catches common violations

### LLM Analysis (If Configured)
- Deep architectural review
- Works with local (LM Studio) or cloud LLMs
- Automatic chunking for large diffs

### Combined Results
- Merges pattern + LLM findings
- Deduplicates issues
- Tagged with source: `[pattern]` or `[llm]`

### Reports Generated
```
.tula/output/
├── intermediate/analysis/    # Debugging
│   ├── pattern_matching.json
│   ├── llm_analysis.json
│   └── combined_results.json
└── final/
    ├── latest.json           # Current (JSON)
    ├── latest.md             # Current (Markdown)
    ├── comparison.md         # Trends
    └── history/              # Archive
```

## 🚀 Common Use Cases

### Pre-commit Hook
```python
#!/usr/bin/env python
from nikhil.tula import TulaAuditor
import sys

auditor = TulaAuditor()
result = auditor.audit_git_diff()

if not result.approved:
    sys.exit(1)  # Block commit
```

### CI/CD Pipeline
```yaml
- name: Audit Code
  run: python examples/audit_git_diff.py
```

### Periodic Check
```bash
# Weekly full audit
python examples/audit_repository.py
```

---

**Full Documentation:** See `USAGE.md` for comprehensive guide
