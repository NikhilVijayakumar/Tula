# AI Audit Setup and Usage Guide

## Overview

The AI audit script now supports **three LLM providers**:
1. **LM Studio** (OpenAI-compatible local API)
2. **Google Gemini** (Free API)
3. **OpenAI** (Paid API)

## Quick Setup

### 1. Configure Your Provider

Copy the template and edit:

```bash
cp .ai_audit.env.template .ai_audit.env
```

Edit `.ai_audit.env` and set your provider:

```env
# For LM Studio (local)
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model

# For Gemini (free)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# For OpenAI (paid)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 2. Install Dependencies

```bash
# For LM Studio or OpenAI
pip install openai

# For Gemini
pip install google-generativeai

# Or install all
pip install openai google-generativeai
```

### 3. Usage

The script runs automatically on `git commit`, or manually:

```bash
# Manual run
python scripts/ai_audit.py

# Skip AI audit for one commit
SKIP_AI_AUDIT=1 git commit -m "Emergency fix"
```

## Provider Details

### LM Studio (Recommended for Local Development)

**Pros:**
- Free (runs locally)
- Privacy (no data sent to external APIs)
- No rate limits
- Works offline

**Setup:**
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a model (recommend: Mistral 7B or Llama 2 7B)
3. Start local server (Tools → Start Server)
4. Default runs on `http://localhost:1234`

**Configuration:**
```env
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model  # Model name doesn't matter for local
LM_STUDIO_API_KEY=not-needed
```

### Google Gemini (Recommended for Free Cloud Option)

**Pros:**
- Free tier available
- Fast inference
- Good code analysis
- No local resources needed

**Setup:**
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Free tier: 60 requests per minute

**Configuration:**
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-1.5-flash  # Or gemini-pro
```

### OpenAI (Best Quality, Paid)

**Pros:**
- Highest quality reviews
- Best architectural understanding
- JSON mode support

**Cons:**
- Costs money (GPT-4 ~$0.03/request)
- Requires internet
- Rate limits

**Configuration:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini  # Or gpt-4 for better quality
```

## What the AI Checks

The AI reviews your code against **AGENTS.md** and **DEPENDENCIES.md**:

1. **Clean Architecture**
   - ✅ Dependencies flow inward
   - ❌ Framework imports in service layer

2. **Interface Patterns**
   - ✅ `ABC` for repository interfaces
   - ✅ `Protocol` for client APIs

3. **Dependency Injection**
   - ✅ Dependencies injected via constructor
   - ❌ Manual instantiation of repositories

4. **Exception Handling**
   - ✅ Custom exceptions
   - ❌ Generic `Exception` or `ValueError`

5. **Type Hints**
   - ✅ All parameters and returns typed

6. **Framework Isolation**
   - ✅ Framework code in adapters
   - ❌ Direct framework usage in services

7. **Dependency Management**
   - ✅ Production deps in `pyproject.toml` AND `requirements.txt`
   - ✅ Dev deps only in `requirements.txt`

## Example Review Output

```
🤖 AI Architecture Audit
═══════════════════════════════════════

ℹ️  Getting staged changes...
✅ Found 47 lines of changes
ℹ️  Loading AGENTS.md...
ℹ️  Using LLM provider: lmstudio
ℹ️  Sending code to LM Studio (http://localhost:1234/v1)...

Review Results:

📝 Changes follow clean architecture principles. Minor suggestions provided.

Suggestions:
  💡 Consider adding type hints to helper function on line 23
  💡 New dependency added - ensure it's in both pyproject.toml and requirements.txt

✨ Architectural review PASSED
ℹ️  Changes comply with AGENTS.md standards
```

## Troubleshooting

### LM Studio Issues

**Error: "Connection refused"**
- Solution: Start LM Studio server (Tools → Start Server)
- Check it's running on port 1234

**Error: "Slow responses"**
- Solution: Use smaller model (7B instead of 13B/70B)
- Reduce `MAX_TOKENS` in `.ai_audit.env`

### Gemini Issues

**Error: "GEMINI_API_KEY not set"**
- Solution: Set your API key in `.ai_audit.env`
- Get key from: https://makersuite.google.com/app/apikey

**Error: "Rate limit exceeded"**
- Solution: Free tier has limits (60/min)
- Wait a minute and try again

### OpenAI Issues

**Error: "OPENAI_API_KEY not set"**
- Solution: Set your API key in `.ai_audit.env`

**Error: "Insufficient credits"**
- Solution: Add credits to your OpenAI account

## Advanced Configuration

### Adjusting Review Strictness

Edit `.ai_audit.env`:

```env
# More lenient (faster, less detailed)
TEMPERATURE=0.5
MAX_TOKENS=500

# More strict (slower, more detailed)
TEMPERATURE=0.1
MAX_TOKENS=2000
```

### Using Different Models

```env
# LM Studio: Any model you've loaded
LM_STUDIO_MODEL=mistral-7b-instruct

# Gemini: Pro for better quality
GEMINI_MODEL=gemini-pro

# OpenAI: GPT-4 for best results
OPENAI_MODEL=gpt-4
```

## Security Notes

- ⚠️ `.ai_audit.env` contains API keys - **NEVER commit it!**
- ✅ `.ai_audit.env` is in `.gitignore`
- ✅ Use `.ai_audit.env.template` for sharing configuration format

## Fallback Behavior

If LLM review fails, the script falls back to **basic pattern matching**:
- Checks for common anti-patterns
- Validates import locations
- Ensures type hints presence
- Less sophisticated than LLM review but still useful

## Recommendation

**For Development:**
Use **LM Studio** for fast, free, local reviews

**For CI/CD:**
Use **Gemini** (free tier) or skip AI audit in CI

**For Important Reviews:**
Use **OpenAI GPT-4** for highest quality architectural feedback
