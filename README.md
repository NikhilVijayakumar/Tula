# Tula - AI-Powered Code Audit Tool

An AI-powered architectural review system that integrates seamlessly into your development workflow via pre-commit hooks. Tula helps enforce coding standards and architectural guidelines automatically.

## ✨ Features

- **AI-Powered Reviews**: Leverages LLM technology to understand and evaluate code against architectural guidelines
- **Pre-commit Integration**: Automatically reviews code before commits 
- **Chunked Processing**: Efficiently handles large diffs by splitting them into manageable chunks
- **Customizable Rules**: Define your own architectural guidelines in markdown files
- **Multiple Review Modes**: Support for git diff review or full repository audits
- **Flexible Configuration**: Multiple configuration discovery strategies
- **Graceful Fallback**: Falls back to pattern matching when LLM is unavailable

## 📋 Requirements

- Python 3.8+
- Git
- Optional: Amsha toolkit (for LLM-powered features)

## 🚀 Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd Tula

# Install in development mode
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### Quick Start

1. **Create a rules file** (e.g., `AGENTS.md`) in your project root:

```markdown
# Architectural Guidelines

## Clean Architecture
- Dependencies should point inward
- Service layer must not import framework code directly

## Type Hints
- All function parameters must have type hints
- All functions must have return type annotations

## Exception Handling
- Use custom exceptions, not generic Exception or ValueError
```

2. **Optional: Create LLM config** (`config/llm_config.yaml`):

```yaml
llm:
  evaluation:
    default: gemini
    models:
      gemini:
        model: gemini-1.5-flash
        api_key: ${GEMINI_API_KEY}
```

3. **Run the audit**:

```bash
# Stage your changes
git add .

# Run audit
tula-audit
```

### Configuration Discovery

Tula searches for configuration files in the following order:

1. Current directory
2. `config/` subdirectory
3. Parent directories (up to 3 levels)
4. `~/.tula/` directory
5. Package defaults

### Environment Variables

- `TULA_RULES_FILE` - Path to rules file (e.g., AGENTS.md)
- `TULA_LLM_CONFIG` - Path to LLM config YAML
- `TULA_DEPENDENCIES_FILE` - Path to dependencies file
- `SKIP_AI_AUDIT` - Set to '1' to skip audit

## 📖 Usage

### Basic Usage

```bash
# Review staged changes
tula-audit

# Review with custom rules file
tula-audit --rules MY_RULES.md

# Review entire repository
tula-audit --full-repo --output report.json

# Skip audit for a single commit
SKIP_AI_AUDIT=1 git commit -m "message"
```

### CLI Options

```
Options:
  --rules PATH              Path to rules file
  --config PATH             Path to LLM configuration file
  --dependencies PATH       Path to dependencies file
  --skip                    Skip the audit
  --full-repo               Audit entire repository
  --output, -o PATH         Output file for full repo audit (JSON)
  --max-tokens INT          Maximum tokens per chunk (default: 14000)
  --verbose, -v             Verbose output
  --version                 Show version
  --help                    Show help message
```

### Pre-commit Hook Integration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: tula-audit
        name: Tula AI Architecture Audit
        entry: tula-audit
        language: system
        stages: [commit]
        pass_filenames: false
```

Then install the hooks:

```bash
pre-commit install
```

## 🏗️ Architecture

### Project Structure

```
Tula/
├── src/
│   └── nikhil/
│       └── tula/
│           ├── domain/
│           │   └── code_audit/
│           │       ├── __init__.py
│           │       ├── ai_auditor.py      # Main audit logic
│           │       ├── cli.py             # CLI interface
│           │       ├── config.py          # Configuration management
│           │       └── scripts/
│           │           └── ai_audit.py    # Standalone script
│           └── utils/
│               ├── json_utils.py
│               ├── yaml_utils.py
│               └── utf8_utils.py
├── docs/                                   # Documentation
├── pyproject.toml                          # Package configuration
├── requirements.txt                        # Dependencies
└── README.md
```

### Key Components

- **AIAuditor**: Main class that orchestrates the audit process
- **AuditConfig**: Configuration management with multiple discovery strategies
- **CLI**: Command-line interface with argparse

## 🔌 LLM Integration

Tula integrates with the Amsha toolkit for LLM-powered features. If you want to use AI-powered reviews:

1. Install the Amsha toolkit separately
2. Configure your LLM in `llm_config.yaml`
3. Set your API keys as environment variables

Without the Amsha toolkit, Tula will fall back to pattern-matching based reviews.

## 🛠️ Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .
pip install -r requirements.txt
```

### Running Tests

```bash
pytest
```

### Code Quality Tools

```bash
# Type checking
mypy src/

# Linting
flake8 src/

# Formatting
black src/
isort src/
```

## 📚 Examples

### Example 1: Basic Git Diff Review

```bash
# Make some changes
git add .

# Run audit
tula-audit
```

Output:
```
============================================================
  🤖 Tula AI Architecture Audit
============================================================

✅ Found 45 lines of changes
ℹ️  Using rules: AGENTS.md
ℹ️  Using LLM config: config/llm_config.yaml
ℹ️  Reviewing with gemini-1.5-flash...

Review Results:

📝 Code changes comply with architectural standards

✅ Architectural review PASSED
ℹ️  Changes comply with architectural standards
```

### Example 2: Full Repository Audit

```bash
tula-audit --full-repo --output audit_report.json
```

This generates:
- `audit_report.json` - Detailed JSON report
- `audit_report.md` - Human-readable markdown summary

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All tests pass
3. Type hints are provided for all functions
4. Documentation is updated

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- Built on top of the Amsha toolkit architecture
- Uses LLM technology for intelligent code review

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder

---

**Version**: 1.5.3
