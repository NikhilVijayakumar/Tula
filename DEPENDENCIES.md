# Tula Project Dependencies

This document defines the allowed dependencies and their usage guidelines for the Tula project.

## Core Dependencies

### 1. Vak (`nikhil.vak`)
- **Purpose**: LLM Factory and abstraction layer.
- **Usage**:
  - MUST be used for all LLM instantiation.
  - Import path: `nikhil.vak.domain.llm_factory...`
  - Do NOT bypass Vak to use `litellm` directly.

### 2. PyYAML (`yaml`)
- **Purpose**: Configuration file parsing.
- **Usage**:
  - Used for `tula_config.yaml`, `llm_config.yaml`, and prompt files.
  - Always use `safe_load`.

### 3. Pydantic (`pydantic`)
- **Purpose**: Data validation and settings management.
- **Usage**:
  - Use `BaseModel` for configuration objects and data structures.
  - Use for validating LLM responses if structured output is needed.

## Standard Library

- **pathlib**: MUST be used for all file path operations. Do NOT use `os.path`.
- **argparse**: Used for CLI argument parsing.
- **logging**: Used for application logging.
- **typing**: Used for type hints.

## Forbidden Dependencies

- **litellm**: Do NOT import directly. Use `Vak` instead.
- **openai/anthropic/google**: Do NOT import SDKs directly. Use `Vak` abstraction.
- **langchain**: Not used in this project. Keep architecture lightweight.

## Development Dependencies

- **pytest**: For testing.
- **black/isort/flake8**: For code formatting and linting.
- **pre-commit**: For git hooks.
