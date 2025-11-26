# Tula Output Directory Structure

The `.tula/` directory is the default location for all Tula-generated output files.

## Directory Structure

```
.tula/
└── output/
    ├── intermediate/          # Optional: Intermediate results for debugging
    │   ├── chunks/           # Chunk breakdowns for large diffs
    │   ├── llm_responses/    # Raw LLM responses
    │   └── analysis/         # Intermediate analysis results
    └── final/                # Final audit results
        ├── audit_report.json
        ├── audit_report.md
        └── audit_YYYYMMDD_HHMMSS.json  # Timestamped reports
```

## Configuration

Configure output directories in `tula_config.yaml`:

```yaml
output:
  base_dir: ".tula/output"
  intermediate_dir: "intermediate"  # Set to null to disable
  final_dir: "final"
```

## Intermediate Output

When enabled, intermediate output helps with:

### 1. **Chunk Breakdown** (`intermediate/chunks/`)
For large diffs that are split into chunks:
- `chunks_manifest.json` - List of all chunks
- `chunk_001.json` - Individual chunk details
- `chunk_002.json`
- ...

### 2. **LLM Responses** (`intermediate/llm_responses/`)
Raw responses from the LLM:
- `response_chunk_001.json` - Raw LLM response for chunk 1
- `response_chunk_002.json`
- ...

###3. **Analysis Steps** (`intermediate/analysis/`)
Step-by-step analysis results:
- `pattern_matching.json` - Basic pattern matching results
- `llm_analysis.json` - LLM-based analysis
- `combined_results.json` - Merged results

## Final Output

Final audit results are always saved:

### 1. **audit_report.json**
Complete audit report in JSON format:
```json
{
  "metadata": {
    "timestamp": "2025-01-26T12:30:45",
    "model_used": "gemini-1.5-flash",
    "rules_file": "AGENTS.md"
  },
  "summary": {
    "total_issues": 2,
    "total_suggestions": 5,
    "approved": false
  },
  "issues": ["..."],
  "suggestions": ["..."],
  "details": {...}
}
```

### 2. **audit_report.md**
Human-readable markdown report

### 3. **Timestamped Reports**
Each audit run creates a timestamped copy for history

## Benefits of Intermediate Output

✅ **Debugging** - See exactly what happened at each step
✅ **Tracking** - Monitor LLM responses and chunking strategy
✅ **Optimization** - Identify bottlenecks and improve prompts
✅ **Auditing** - Review what the LLM actually said
✅ **Cost Tracking** - See which chunks used most tokens

## Disabling Intermediate Output

To save disk space and simplify output:

```yaml
output:
  base_dir: ".tula/output"
  intermediate_dir: null  # or comment out
  final_dir: "final"
```

Or via CLI:
```bash
tula-audit --no-intermediate
```

## .gitignore

The `.tula/` directory is gitignored by default to avoid committing:
- API keys (if accidentally in configs)
- Large output files
- Intermediate debugging data

To version control final reports only:
```gitignore
.tula/
!.tula/output/final/*.md
```

## Cleanup

Remove old intermediate files:
```bash
# Remove intermediate output
rm -rf .tula/output/intermediate

# Remove all output
rm -rf .tula/output

# Keep only final reports
find .tula/output/intermediate -type f -delete
```

## Best Practices

1. **Enable intermediate for development** - Helps understand what's happening
2. **Disable for CI/CD** - Reduces artifacts and speeds up pipeline
3. **Archive important reports** - Move final reports to a `reports/` directory for version control
4. **Review intermediate periodically** - Optimize prompts based on LLM responses
5. **Clean up regularly** - Intermediate files can accumulate quickly

---

For configuration details, see `tula_config.example.yaml`
