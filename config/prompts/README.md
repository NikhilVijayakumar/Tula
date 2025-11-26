# Prompt Configuration Guide

This directory contains customizable prompt templates for the Tula code audit tool.

## 📁 Files

- **`system_prompt.yaml`** - System-level prompt configuration (role, focus areas, response format)
- **`user_prompts.yaml`** - User prompt templates for different review scenarios

## 🎯 Purpose

Externalizing prompts allows you to:
- **Customize** code review criteria without modifying code
- **Experiment** with different prompting strategies
- **Override** default prompts for your specific needs
- **Version control** your prompt configurations

## 📝 File Format

### system_prompt.yaml

```yaml
# Role and context
role: "Senior Architect"
context: "You are a Senior Architect reviewing code changes."

# Instructions template
instructions: |
  Review the git diff against these coding standards:
  
  {rules}

# Focus areas
focus_areas:
  - "Architecture: Dependencies, layer separation"
  - "Interfaces: ABC vs Protocol usage"
  # ... more areas

# Response format
response_format:
  type: "json"
  description: "Respond in JSON format:"
  schema:
    approved: "boolean"
    issues: "array of strings"
    suggestions: "array of strings"
    summary: "string"
```

### user_prompts.yaml

```yaml
# Each key is a template name, value is the template string
single_review: |
  Review this git diff:
  
  ```diff
  {diff}
  ```
  
  Provide your review in JSON format.

chunked_review: |
  Review chunk {chunk_num} of {total_chunks}...
```

## 🔧 Template Variables

User prompts support variable substitution using `{variable_name}` syntax:

### single_review
- `{diff}` - The git diff content

### chunked_review
- `{chunk_num}` - Current chunk number
- `{total_chunks}` - Total number of chunks
- `{file_count}` - Number of files in chunk
- `{filenames}` - Comma-separated list of files

### chunk_with_files
- `{chunk_index}` - Current chunk index
- `{file_count}` - Number of files
- `{file_list}` - Comma-separated file list
- `{chunk_diff}` - The diff content for this chunk

### file_review
- `{filepath}` - Path to the file being reviewed
- `{content}` - File content

## 🎨 Customization

### Option 1: Modify Default Prompts

Edit the files in this directory directly:

```bash
cd config/prompts/
vim system_prompt.yaml
```

### Option 2: Create Project-Specific Prompts

Create a `config/prompts/` directory in your project root:

```bash
mkdir -p config/prompts
cp /path/to/tula/config/prompts/system_prompt.yaml config/prompts/
# Customize your copy
vim config/prompts/system_prompt.yaml
```

Tula will automatically find and use your project-specific prompts.

### Option 3: Use Custom Prompt Directory

Specify a custom directory via CLI (future feature):

```bash
tula-audit --prompts-dir /path/to/custom/prompts
```

## 🔍 Discovery Order

Tula searches for prompt files in this order:

1. **Custom prompts directory** (if specified via `--prompts-dir`)
2. **Current directory**: `./config/prompts/`
3. **Parent directories**: `../config/prompts/`, `../../config/prompts/`, etc. (up to 3 levels)
4. **Package defaults**: Built-in prompts from the Tula package

## 💡 Examples

### Example: Adding a New Focus Area

Edit `system_prompt.yaml`:

```yaml
focus_areas:
  - "Architecture: Dependencies, layer separation"
  - "Interfaces: ABC vs Protocol usage"
  - "Security: Input validation and sanitization"  # NEW
  - "Performance: Algorithm complexity"  # NEW
```

### Example: Changing Review Tone

Edit `system_prompt.yaml`:

```yaml
context: "You are a friendly Senior Architect reviewing code changes. Be constructive and encouraging while maintaining high standards."
```

### Example: Custom Review Template

Edit `user_prompts.yaml`:

```yaml
single_review: |
  🔍 **Code Review Request**
  
  Please review the following changes:
  
  ```diff
  {diff}
  ```
  
  **Focus on:**
  - Code quality
  - Best practices
  - Potential issues
  
  **Response format:** JSON with approved, issues, suggestions, and summary fields.
```

## ⚠️ Important Notes

1. **Variable names are case-sensitive**: Use `{diff}` not `{Diff}`
2. **YAML syntax matters**: Indentation, quotes, and special characters must be correct
3. **Fallback prompts**: If your custom prompts have errors, Tula will fall back to built-in defaults
4. **JSON format required**: The system prompt should always request JSON output format for parsing

## 🧪 Testing Your Prompts

After modifying prompts, test them:

```bash
# Run a simple audit to see if prompts load correctly
tula-audit --verbose

# Check what prompt files are being used (in verbose output)
```

## 📚 Best Practices

1. **Keep it focused**: Don't make prompts too long or complex
2. **Be specific**: Clearly define what you're looking for
3. **Use examples**: The response_format section should include example output
4. **Version control**: Commit your prompt configurations with your code
5. **Document changes**: Comment why you changed prompts for future reference
6. **Test thoroughly**: Verify changes work with different code samples

## 🆘 Troubleshooting

**Prompts not being used?**
- Check file names are exactly `system_prompt.yaml` and `user_prompts.yaml`
- Verify YAML syntax is valid
- Check file permissions
- Try `--verbose` flag to see discovery process

**Getting errors?**
- Verify all required variables are in your templates
- Check YAML indentation
- Make sure response_format expects JSON

**Unexpected results?**
- Review your focus_areas and instructions
- Compare with default prompts
- Simplify and iterate

---

For more information, see the main [README.md](../../README.md) or [documentation](../../docs/).
