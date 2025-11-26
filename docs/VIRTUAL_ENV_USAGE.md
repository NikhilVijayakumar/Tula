# Virtual Environment Usage for Amsha Development

## Issue
Installation was happening to user-level packages instead of virtual environment.

## Solution

### Always Activate Virtual Environment First

**PowerShell:**
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Verify activation (should show venv path)
$env:VIRTUAL_ENV

# Now install/run commands
pip install -e .
amsha-audit --help
```

**Bash/Linux:**
```bash
# Activate venv
source venv/bin/activate

# Verify
echo $VIRTUAL_ENV

# Install/run
pip install -e .
amsha-audit --help
```

### How to Tell If Virtual Environment is Active

**PowerShell:**
```powershell
if (Test-Path env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual env active: $env:VIRTUAL_ENV"
} else {
    Write-Host "❌ No virtual environment active"
}
```

**Prompt Indicator:**
```
(venv) PS E:\Python\Amsha>  # ✅ Active (note the (venv) prefix)
PS E:\Python\Amsha>         # ❌ Not active
```

### Installation Path Check

**User-level (Wrong for dev):**
```
c:\users\nikhi\appdata\roaming\python\python312\site-packages
```

**Virtual environment (Correct):**
```
e:\python\amsha\venv\lib\site-packages
```

## Workflow for Development

### 1. One-Time Setup
```powershell
# Create venv (if not exists)
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .
```

### 2. Daily Workflow
```powershell
# Always activate first
.\venv\Scripts\Activate.ps1

# Then work normally
python scripts/something.py
amsha-audit
pytest
git commit
```

### 3. Deactivate When Done
```powershell
deactivate
```

## VS Code Integration

### Auto-Activate in VS Code

1. **Select Python Interpreter:**
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose `.\venv\Scripts\python.exe`

2. **VS Code will auto-activate venv in terminals**

3. **Verify in new terminal:**
   ```powershell
   # Should see (venv) prefix
   (venv) PS E:\Python\Amsha>
   ```

## Pre-commit Hooks

Pre-commit hooks use the active environment:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ai-audit
        name: AI Audit
        entry: amsha-audit  # Uses venv's amsha-audit
        language: system
```

**Important:** Run `pre-commit install` from activated venv:
```powershell
.\venv\Scripts\Activate.ps1
pre-commit install
```

## Common Issues

### Issue: "amsha-audit not found"
**Cause:** Not in venv or not installed
**Solution:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -e .
amsha-audit --version
```

### Issue: "Installing to user packages"
**Cause:** Venv not activated
**Solution:**
```powershell
# Check
$env:VIRTUAL_ENV

# If empty, activate
.\venv\Scripts\Activate.ps1
```

### Issue: "Module not found"
**Cause:** Installed in user packages, running in venv
**Solution:**
```powershell
# Reinstall in venv
.\venv\Scripts\Activate.ps1
pip uninstall amsha
pip install -e .
```

## Best Practices

✅ **Always activate venv before:**
- Installing packages
- Running scripts
- Running commands
- Installing pre-commit

✅ **Add to .gitignore:**
```
venv/
.venv/
*.pyc
__pycache__/
```

✅ **Document in README:**
```markdown
## Development Setup

1. Create virtual environment:
   ```
   python -m venv venv
   ```

2. Activate:
   ```
   .\venv\Scripts\Activate.ps1  # Windows
   source venv/bin/activate     # Linux/Mac
   ```

3. Install:
   ```
   pip install -e .
   ```
```

## PowerShell Profile (Optional)

Add to PowerShell profile for quick activation:

```powershell
# Edit profile
notepad $PROFILE

# Add function
function venv {
    if (Test-Path .\venv\Scripts\Activate.ps1) {
        .\venv\Scripts\Activate.ps1
        Write-Host "✅ Virtual environment activated"
    } else {
        Write-Host "❌ No venv found in current directory"
    }
}

# Save and reload
. $PROFILE

# Now just type 'venv' to activate
```

## Summary

**Problem:** Installed to user packages instead of venv  
**Solution:** Always activate venv first: `.\venv\Scripts\Activate.ps1`  
**Verification Path:** `e:\python\amsha\venv\lib\site-packages` ✅  
**Command now works:** `amsha-audit --version` ✅
