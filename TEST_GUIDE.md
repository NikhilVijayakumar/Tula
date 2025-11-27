# Simple Test Guide

Follow these steps to test Tula after the Vak refactoring:

## Step 1: Install Packages

```bash
# First install Vak (required dependency)
cd /home/dell/PycharmProjects/Vak
pip install -e .

# Then install Tula
cd /home/dell/PycharmProjects/Tula
pip install -e .
```

## Step 2: Create Minimal Configuration

You already have `config/llm_config.yaml` ✅

Now create a simple rules file for testing:

```bash
cd /home/dell/PycharmProjects/Tula
cat > AGENTS.md << 'EOF'
# Coding Rules

## Type Hints
- All functions must have type hints
- Return types must be specified

## Exception Handling
- Use custom exceptions, not generic Exception or ValueError
EOF
```

## Step 3: Test the Audit

### Option A: Test with Pattern Matching Only (No LLM)

```bash
# Make a dummy change to test
echo "# test change" >> test_file.py
git add test_file.py

# Run audit (will use pattern matching)
python3 run_audit.py

# Clean up
git reset HEAD test_file.py
rm test_file.py
```

### Option B: Test with the CLI

```bash
# Stage some changes
git add .

# Run via CLI
tula-audit --verbose
```

### Option C: Test with Skip Mode (Fastest)

```bash
tula-audit --skip
```

## Step 4: Test with LLM (Optional)

Your `config/llm_config.yaml` already has Gemini configured. To use it:

```bash
# Make sure API key is valid in llm_config.yaml
# Then run:
python3 run_audit.py
```

It will automatically use Gemini for evaluation.

## What to Expect

✅ **Success Output:**
```
==================================================
Tula Code Audit - Combined Approach
==================================================

📋 Step 1: Loading configuration...
  Using config: <path>
  Rules: AGENTS.md
  LLM Config: config/llm_config.yaml
  ...

✅ AUDIT COMPLETE
```

❌ **If you see import errors:**
- Make sure Vak is installed: `cd /home/dell/PycharmProjects/Vak && pip install -e .`
- Make sure Tula is installed: `cd /home/dell/PycharmProjects/Tula && pip install -e .`

## Quick Test Commands

```bash
# 1. Verify imports work
python3 -c "from nikhil.vak.domain.llm_factory.settings.llm_settings import LLMSettings; print('✅ Vak OK')"
python3 -c "from nikhil.tula.domain.code_audit.ai_auditor import AIAuditor; print('✅ Tula OK')"

# 2. Test CLI help
python3 run_audit.py --help

# 3. Run actual test
echo "# test" > test.py
git add test.py
python3 run_audit.py
git reset HEAD test.py
rm test.py
```
