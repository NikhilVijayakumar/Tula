# Report File Structure

Tula generates multiple report files for different purposes.

## File Structure

```
.tula/output/final/
├── latest.json              ← Always overwritten (current run)
├── latest.md                ← Always overwritten (human-readable)
├── comparison.md            ← Historical comparison report
└── history/                 ← Timestamped archive
    ├── audit_20250126_123045.json
    ├── audit_20250126_123045.md
    ├── audit_20250126_143022.json
    ├── audit_20250126_143022.md
    └── ...
```

## Report Files Explained

### 1. `latest.json` (Always Overwritten) ✅

**Purpose:** Quick access to the most recent audit result

**When to use:**
- CI/CD pipelines checking current status
- Editor/IDE integrations
- Quick status checks

**Format:**
```json
{
  "timestamp": "2025-01-26T12:30:45",
  "git_commit": "abc123",
  "model_used": "gemini-1.5-flash",
  "approved": false,
  "total_issues": 3,
  "total_suggestions": 5,
  "issues": ["..."],
  "suggestions": ["..."],
  "summary": "Found 3 architectural violations"
}
```

### 2. `latest.md` (Always Overwritten) ✅

**Purpose:** Human-readable version of latest.json

**When to use:**
- Quick review in GitHub PR comments
- Terminal output
- Documentation

**Example:**
```markdown
# Code Audit Report

**Date:** 2025-01-26T12:30:45
**Model:** gemini-1.5-flash
**Status:** ❌ NOT APPROVED

## Issues (3)
1. Missing type hints in auth.py
2. Using generic Exception instead of custom
3. Direct framework coupling in service layer
```

### 3. `history/audit_YYYYMMDD_HHMMSS.json` (Timestamped Archive) 📚

**Purpose:** Historical record of all audit runs

**When to use:**
- Tracking changes over time
- Comparing before/after refactoring
- Analyzing trends
- Compliance auditing

**Naming Convention:**
- `audit_20250126_123045.json` - January 26, 2025 at 12:30:45
- Format: `audit_YYYYMMDD_HHMMSS.json`

**Benefits:**
- Never lost - each run is preserved
- Git-friendly timestamped names
- Easy to find specific runs
- Can track improvement over time

### 4. `comparison.md` (Historical Trends) 📊

**Purpose:** Shows trends and comparisons across multiple runs

**Generated:** Automatically after each audit (if history exists)

**Contains:**
- Summary table of recent runs
- Trend analysis (improving/regressing)
- Most common issues
- Recent changes comparison

**Example:**
```markdown
# Historical Code Audit Comparison

## Summary Statistics
| Date       | Model          | Approved | Issues | Suggestions |
|------------|----------------|----------|--------|-------------|
| 2025-01-26 | gemini-1.5-flash | ❌      | 3      | 5           |
| 2025-01-25 | gemini-1.5-flash | ❌      | 5      | 7           |
| 2025-01-24 | gemini-1.5-flash | ✅      | 0      | 3           |

## Trend Analysis
**Issues Trend:** 📉 Decreased (-2)
**Latest Status:** ❌ Not Approved

## Most Common Issues
- **3x** Missing type hints
- **2x** Generic exception usage
- **1x** Framework coupling
```

## Usage Patterns

### For Developers

**After each commit:**
```bash
tula-audit
cat .tula/output/final/latest.md
```

**Check improvement:**
```bash
cat .tula/output/final/comparison.md
```

### For CI/CD

**GitHub Actions:**
```yaml
- name: Run Tula Audit
  run: tula-audit

- name: Check Status
  run: |
    approved=$(jq -r '.approved' .tula/output/final/latest.json)
    if [ "$approved" != "true" ]; then
      exit 1
    fi

- name: Post PR Comment
  run: gh pr comment ${{ github.event.pull_request.number }} --body-file .tula/output/final/latest.md
```

### For Tracking Progress

**Compare over time:**
```bash
# See all historical runs
ls -lh .tula/output/final/history/

# View specific run
cat .tula/output/final/history/audit_20250125_143022.json

# Generate comparison
tula-audit --compare-history
```

## Configuration

Control report generation in `tula_config.yaml`:

```yaml
output:
  base_dir: ".tula/output"
  final_dir: "final"

reporting:
  # Always save timestamped history
  save_history: true
  
  # Generate comparison report
  generate_comparison: true
  
  # Number of reports to keep in history
  max_history: 50
  
  # Automatically clean up old reports
  auto_cleanup: true
  keep_recent: 20
```

## Cleanup

### Manual Cleanup

```bash
# Remove old history (keep latest 10)
ls -t .tula/output/final/history/audit_*.json | tail -n +11 | xargs rm

# Remove all history
rm -rf .tula/output/final/history/

# Fresh start
rm -rf .tula/output/final/*
```

### Automatic Cleanup

Set in config:
```yaml
reporting:
  auto_cleanup: true
  keep_recent: 20  # Keep only 20 most recent reports
```

## Best Practices

### ✅ DO

1. **Commit `latest.md` to version control** - Shows current audit status
2. **Git-ignore `history/`** - Prevents bloating repository
3. **Review `comparison.md` regularly** - Track improvement trends
4. **Archive important milestones** - Copy key reports to `docs/audits/`
5. **Clean up periodically** - Don't let history grow unbounded

### ❌ DON'T

1. **Don't commit all history** - Too many files, grows quickly
2. **Don't rely only on `latest.json`** - Gets overwritten; use history for tracking
3. **Don't ignore `comparison.md`** - It shows valuable trends
4. **Don't delete history before major refactors** - Good baseline for comparison

## Git Integration

### Recommended `.gitignore`

```gitignore
# Tula outputs
.tula/
!.tula/output/final/latest.json
!.tula/output/final/latest.md
!.tula/output/final/comparison.md
```

This keeps:
- ✅ Latest report status (for PR reviews)
- ✅ Comparison report (for tracking)
- ❌ History files (too many, bloats repo)
- ❌ Intermediate files (debugging only)

### GitHub PR Integration

**Automatic comment on PR:**
```yaml
- name: Audit & Comment
  run: |
    tula-audit
    gh pr comment ${{ github.event.pull_request.number }} \
      --body-file .tula/output/final/latest.md
```

## File Size Management

**Typical sizes:**
- `latest.json`: 2-10 KB
- `latest.md`: 1-5 KB
- `comparison.md`: 5-20 KB
- Each history file: 2-10 KB

**For 50 historical runs:**
- Total: ~0.5-1 MB (very manageable)

**Cleanup threshold:**
- Keep 20-50 recent reports
- Archive important milestones separately
- Auto-cleanup in CI/CD environments

---

For configuration details, see `tula_config.example.yaml`
