# Tula Architectural Guidelines

This document defines the architectural rules and coding standards for the Tula project.
The AI Auditor uses these rules to review code changes.

## 1. Domain-Driven Design (DDD) Structure

- **Layered Architecture**: Code must strictly follow the layered architecture:
  - `domain/`: Core business logic, entities, and interfaces. NO external dependencies (except pure utils).
  - `application/` (or root package): Orchestration logic (e.g., `tula_auditor.py`). Connects domain to infrastructure.
  - `infrastructure/`: External adapters, CLI, file I/O, API clients.
  
- **Dependency Rule**: Dependencies must point INWARD.
  - Domain layer must NOT depend on Application or Infrastructure layers.
  - Infrastructure layer depends on Domain and Application layers.

- **TulaAuditor**: `TulaAuditor` is the primary Application Service/Orchestrator.
  - It should coordinate between `AIAuditor` (Domain) and external inputs (CLI/Config).
  - It should NOT contain low-level business logic.

## 2. SOLID Principles

- **Single Responsibility Principle (SRP)**:
  - Classes and functions should have one reason to change.
  - Example: `AIAuditor` handles audit logic, `ReportManager` handles file output.

- **Open/Closed Principle (OCP)**:
  - Classes should be open for extension but closed for modification.
  - Use interfaces/abstract classes for components that might change (e.g., LLM providers).

- **Dependency Inversion Principle (DIP)**:
  - High-level modules should not depend on low-level modules. Both should depend on abstractions.
  - Use dependency injection where possible.

## 3. Coding Standards

- **Type Hinting**: All function signatures must have type hints.
  - Use `Optional`, `List`, `Dict`, `Any` from `typing` module.
  - Return types must be specified.

- **Error Handling**:
  - Use custom exceptions for domain errors (e.g., `AuditError`, `ConfigError`).
  - Do NOT catch generic `Exception` unless absolutely necessary (and log it).
  - Fail fast and provide helpful error messages.

- **Configuration**:
  - Configuration should be data-driven (YAML), not hardcoded.
  - Use `AuditConfig` object to pass configuration around.

## 4. LLM Integration

- **Vak Library**: MUST use `nikhil.vak` for all LLM interactions.
  - Do NOT import `litellm` or `openai` directly.
  - Use `LLMBuilder` from Vak to create LLM instances.
  
- **Prompts**:
  - Prompts should be externalized in YAML files or constants.
  - Do NOT hardcode long prompt strings in logic methods.

## 5. Testing

- **Unit Tests**: Business logic should be unit testable without external dependencies.
- **Integration Tests**: Test the full flow using `examples/local_testing.py`.
