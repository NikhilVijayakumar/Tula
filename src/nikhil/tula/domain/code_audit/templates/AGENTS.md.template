# Amsha Library - Coding Constitution & Standards

**Role:** You are a Senior Architect working on `Amsha`, a common library for CrewAI orchestration.  
**Goal:** Maintain strict adherence to Clean Architecture, SOLID principles, and Dependency Injection while ensuring stability for multiple dependent projects.

---

## 1. Architectural Boundaries (The "Law")

This project follows **Clean Architecture**. You must strictly adhere to the Dependency Rule:

*   **Inner Layers (Domain)** must NEVER depend on **Outer Layers (Infrastructure/API)**.
*   **Domain (`src/nikhil/amsha/toolkit/*/domain`)**: Pure Python objects (Pydantic models). NO external framework dependencies.
*   **Repository Interfaces (`repo/interfaces`)**: Abstract contracts only. NO implementation details.
*   **Application/Service**: Business logic. Depends ONLY on domain models and repository interfaces.
*   **Infrastructure (`repo/adapters`, `api`, `mlops`)**: Concrete implementations (MongoDB, S3, FastAPI).

**Layer Dependencies (Inner → Outer):**
```
Domain (Models) ← Service/Application ← Orchestrator ← Infrastructure (Adapters/API)
```

---

## 2. Interface Design: ABC vs Protocol

**Critical Distinction:** The codebase uses BOTH `ABC` and `Protocol` for different purposes.

### When to Use `ABC` (Abstract Base Class)
**Purpose:** Nominal typing with runtime enforcement for **internal repository contracts**.

**Use for:**
- Repository interfaces (`IAgentRepository`, `ITaskRepository`, `ICrewConfigRepository`)
- Interfaces where you want to enforce implementation at runtime
- Internal library boundaries where strict contract validation is needed

**Example:**
```python
from abc import ABC, abstractmethod
from typing import Optional

class IAgentRepository(ABC):
    @abstractmethod
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentResponse]:
        """Must be implemented by concrete repository"""
        ...
```

### When to Use `Protocol`
**Purpose:** Structural typing (duck typing) for **external API boundaries**.

**Use for:**
- Client-facing interfaces (`BotManagerProtocol`, `TaskConfigProtocol`)
- Plugin/extension points where clients provide implementations
- Public API contracts where you want flexibility without inheritance

**Example:**
```python
from typing import Protocol, Any

class BotManagerProtocol(Protocol):
    def run(self, task_name: str) -> Any:
        """Client implements this without inheriting"""
        ...
```

**Rule of Thumb:**
- **Internal boundaries (repos)** → `ABC` with `@abstractmethod`
- **External boundaries (client contracts)** → `Protocol`

---

## 3. Dependency Injection (DI)

**Strict Rule:** Never instantiate complex classes manually inside services.

*   **BAD:** `self.repo = MongoAgentRepository()`
*   **GOOD:** `self.repo: IAgentRepository` (injected via `__init__`)
*   **CONTAINERS:** All wiring happens in `dependency/containers.py` using the `dependency-injector` library.
*   **FACTORIES:** Use Factory Providers for objects created at runtime (like LLM instances).

**Example:**
```python
class AtomicDbBuilderService:
    def __init__(self, agent_repo: IAgentRepository, task_repo: ITaskRepository):
        self.agent_repo = agent_repo  # Injected, not created
        self.task_repo = task_repo
```

---

## 4. SOLID Principles

*   **SRP (Single Responsibility):** If a service does both "Building Crews" and "Running Crews", split it.
    - `CrewBuilderService`: Builds crews
    - `DbCrewOrchestrator`: Executes crews
*   **OCP (Open/Closed):** New features (e.g., SQL Repository) must be added by creating a new class implementing the interface, NOT with `if type == 'SQL'` branching.
*   **LSP (Liskov Substitution):** Any `IAgentRepository` implementation must be swappable without breaking orchestrators.
*   **ISP (Interface Segregation):** Keep repository interfaces focused. Don't force implementations to have methods they don't need.
*   **DIP (Dependency Inversion):** High-level modules (Orchestrators) depend on `IRepository` interfaces, never on `MongoAgentRepository`.

---

## 5. Exception Handling Strategy

**Problem:** Current codebase has scattered exceptions (generic `ValueError`, component-specific exceptions).

**Standard:**

1.  **Create Custom Exceptions in Component Directories:**
    ```
    toolkit/crew_forge/exceptions/
    ├── agent_not_found_exception.py
    ├── invalid_crew_config_exception.py
    └── repository_error.py
    ```

2.  **Exception Hierarchy:**
    ```python
    class AmshaException(Exception):
        """Base exception for all Amsha errors"""
        pass

    class RepositoryException(AmshaException):
        """Base for all repository errors"""
        pass

    class AgentNotFoundException(RepositoryException):
        """Specific domain error"""
        def __init__(self, agent_id: str):
            super().__init__(f"Agent with ID '{agent_id}' not found")
    ```

3.  **Usage:**
    -   **Domain Errors:** Use custom exceptions (`AgentNotFoundException`)
    -   **Infrastructure Errors:** Wrap external exceptions (`MongoConnectionError`)
    -   **Never:** Raise generic `Exception` or `ValueError` for domain logic

---

## 6. Async/Await Guidelines

**Current State:** Async is used selectively (API layer only).

**Rules:**

1.  **Required for:**
    -   FastAPI endpoints (already async)
    -   Streaming operations (`EventSourceResponse`)

2.  **Optional/Future for:**
    -   Repository implementations (currently synchronous MongoDB operations)
    -   Service layer (can be made async when repos are async)

3.  **Pattern:**
    -   Keep sync and async versions if needed
    -   Use `async def` for IO-bound operations (network, database)
    -   Don't use async for CPU-bound operations (topic modeling, text processing)

**Example:**
```python
# Current (Sync)
def get_agent_by_id(self, agent_id: str) -> AgentResponse:
    return self.db.agents.find_one({"_id": agent_id})

# Future (Async)
async def get_agent_by_id(self, agent_id: str) -> AgentResponse:
    return await self.db.agents.find_one({"_id": agent_id})
```

---

## 7. Orchestration Patterns (Dual-Mode Architecture)

**Core Pattern:** Amsha provides two orchestration modes with identical client interfaces.

### Mode 1: Database-Backed Orchestration
- Agent/Task configs stored in MongoDB
- Use `AmshaCrewDBApplication` base class
- Fetches configs via repositories at runtime

### Mode 2: File-Backed Orchestration
- Agent/Task configs stored in YAML files
- Use `AmshaCrewFileApplication` base class
- Parses configs from filesystem at runtime

### Consistency Requirements

1.  **Identical Client Interface:**
    Both modes must offer the same methods and behavior from the client's perspective.

2.  **Base Class Pattern:**
    ```python
    # DB Mode
    class MyApp(AmshaCrewDBApplication):
        def __init__(self, config_paths, llm_type):
            super().__init__(config_paths, llm_type)

    # File Mode
    class MyApp(AmshaCrewFileApplication):
        def __init__(self, config_paths, llm_type):
            super().__init__(config_paths, llm_type)
    ```

3.  **Shared Responsibilities:**
    -   Load job, app, and LLM configurations
    -   Initialize LLM via LLM Factory
    -   Manage input preparation (files, direct values)
    -   Provide output post-processing (`clean_json()`)

4.  **Adding New Modes:**
    To add a new backend (e.g., REST API source):
1.  **Generic by Default:**
    -   Do NOT hardcode project-specific logic (company names, specific workflows)
    -   Extract project-specific logic to configuration

2.  **Config-Driven Behavior:**
    -   If behavior needs to change between projects, use YAML configuration
    -   Example: LLM model selection, repository backend, output paths

3.  **Abstraction Over Concretion:**
    -   Clients depend on `IAgentRepository`, not `MongoAgentRepository`
    -   Easier to swap implementations (MongoDB → PostgreSQL → DynamoDB)

4.  **Knowledge Source Flexibility:**
    -   Support multiple knowledge sources (Docling, Arxiv, custom)
    -   Define `Protocol` for knowledge source interface
    -   Clients can plug in their own sources

5.  **Example Code Quality:**
    -   Examples are customer-facing documentation
    -   Must be runnable, well-commented, and demonstrate best practices
    -   Test examples as part of CI/CD

---

## 9. Public API & Client Communication

**Rule:** The communication boundary between `Amsha` and Client Apps must be defined by **Protocols**, not Concrete Classes.

### 1. Behavior over Implementation
*   When exposing a service to clients, expose it as a Protocol (e.g., `ICrewBuilder`).
*   Clients should type-hint against the Protocol: `builder: ICrewBuilder`, NOT `builder: AtomicDbBuilderService`.

### 2. The "Ports & Adapters" Rule
*   If `Amsha` needs the client to provide logic (e.g., custom logger, callback), define a Protocol in `Amsha`.
*   Client implements the Protocol and passes an instance.
*   **Example:** `Amsha` defines `class OutputHandler(Protocol): ...`. Client provides implementation.

### 3. DTO Pattern
*   **Do NOT** use Protocols for Data Transfer Objects.
*   Use concrete Pydantic `BaseModel` classes for data schemas (e.g., `AgentData`, `TaskConfig`).
*   **Reason:** Data structures are shared contracts; logic is abstract.

### 4. Public API Exports
*   Only expose public APIs through `__init__.py` exports
*   Internal implementation details should not be imported directly by clients
*   **Example:**
    ```python
    # src/nikhil/amsha/toolkit/crew_forge/__init__.py
    from .orchestrator.db import AmshaCrewDBApplication
    from .orchestrator.file import AmshaCrewFileApplication
    
    __all__ = ['AmshaCrewDBApplication', 'AmshaCrewFileApplication']
    ```

---

## 10. Versioning & Backward Compatibility

**Current Version:** 1.5.3

### Semantic Versioning (MAJOR.MINOR.PATCH)

*   **MAJOR (1.x.x):** Breaking changes to public API
    -   Changing method signatures in `Protocol` interfaces
    -   Removing public classes or methods
    -   Changing required configuration structure

*   **MINOR (x.5.x):** New features, backward-compatible
    -   Adding new orchestration modes
    -   Adding new optional parameters
    -   New guardrails or validators

*   **PATCH (x.x.3):** Bug fixes, backward-compatible
    -   Fixing bugs in existing logic
    -   Performance improvements
    -   Documentation updates

### Deprecation Policy

1.  **Mark as Deprecated:** Add `@deprecated` decorator and warning
    ```python
    import warnings
    
    @deprecated("Use new_method() instead. Will be removed in 2.0.0")
    def old_method(self):
        warnings.warn("old_method is deprecated", DeprecationWarning)
    ```

2.  **Keep for 1 MINOR Version:** Support deprecated methods through next minor version

3.  **Remove in MAJOR Version:** Breaking changes only in major version bumps

### Breaking Change Checklist
- [ ] Document in CHANGELOG
- [ ] Update all examples
- [ ] Create migration guide
- [ ] Bump MAJOR version
- [ ] Notify all known consumers

---

## 11. Testing Standards

**Philosophy:** Common libraries must be thoroughly tested since bugs affect multiple projects.

### Test Structure
```
tests/
├── unit/              # Isolated domain/service tests
├── integration/       # Repository + DB tests
└── examples/          # Example code tests
```

### Testing Rules

1.  **Unit Tests (Domain & Services):**
    -   Test domain logic in isolation
    -   Mock all repository dependencies
    -   Use dependency injection for testability
    ```python
    def test_atomic_builder_adds_agent():
        mock_agent_repo = Mock(spec=IAgentRepository)
        builder = AtomicDbBuilderService(mock_agent_repo, mock_task_repo)
        # Test logic...
    ```

2.  **Integration Tests (Repositories):**
    -   Test against real infrastructure (MongoDB, MinIO)
    -   Use Docker containers for test databases
    -   Clean up after each test

3.  **Example Tests:**
    -   All examples in `example/` must be runnable
    -   Create test that executes example code
    -   Validates example produces expected output

4.  **Test Coverage:**
    -   Aim for 80%+ coverage on service layer
    -   100% coverage on public API methods
    -   All exception paths must be tested

5.  **Test Isolation:**
    -   No test should depend on another test
    -   Use fixtures for common setup
    -   Mock external services (LLM APIs, external APIs)

---

## 12. Documentation Standards

### Code Documentation

1.  **Docstrings Required For:**
    -   All public classes and methods
    -   All Protocol/ABC definitions
    -   Complex algorithms or business logic

2.  **Docstring Format:**
    ```python
    def build_crew(self, process: Process = Process.sequential) -> Crew:
        """
        Builds a CrewAI Crew from configured agents and tasks.
        
        Args:
            process: Execution process (sequential or hierarchical)
            
        Returns:
            Configured Crew instance ready for execution
            
        Raises:
            InvalidCrewConfigException: If required agents/tasks are missing
        """
    ```

3.  **Type Hints:**
    -   All function parameters and return types
    -   Use `Optional`, `Union`, `List` etc. from `typing`
    -   Pydantic models for complex data structures

### Project Documentation

1.  **README.md:** Architecture overview, installation, usage examples
2.  **AGENTS.md (this file):** Coding standards and principles
3.  **CHANGELOG.md:** Version history and migration guides
4.  **examples/README.md:** How to run examples for each component

---

## 13. Common Patterns & Anti-Patterns

### ✅ DO: Patterns to Follow

```python
# ✅ Dependency Injection
class CrewOrchestrator:
    def __init__(self, agent_repo: IAgentRepository):
        self.agent_repo = agent_repo

# ✅ Config-Driven Behavior
llm_type = config.get("llm_type", LLMType.CREATIVE)

# ✅ Custom Exceptions
raise AgentNotFoundException(agent_id)

# ✅ Type Hints
def process(self, data: AgentRequest) -> AgentResponse:

# ✅ Protocol for External APIs
class OutputHandler(Protocol):
    def handle(self, output: str) -> None: ...
```

### ❌ DON'T: Anti-Patterns

```python
# ❌ Manual Instantiation
self.repo = MongoAgentRepository()  # Should be injected

# ❌ Hardcoded Logic
if project == "ProjectX":  # Should be config-driven

# ❌ Generic Exceptions
raise Exception("Failed")  # Use custom exceptions

# ❌ Missing Type Hints
def process(self, data):  # Missing types

# ❌ Leaking Implementation
from .repo.adapters.mongo import MongoRepo  # Should import interface
```

---

## Quick Reference Checklist

Before committing code, verify:

- [ ] **Architecture:** Does it follow dependency rule? (Inner layers don't depend on outer)
- [ ] **DI:** Are dependencies injected, not instantiated?
- [ ] **Interface:** Using `ABC` for repos, `Protocol` for client APIs?
- [ ] **Exceptions:** Using custom exceptions from component `exceptions/` directory?
- [ ] **Types:** All parameters and returns have type hints?
- [ ] **Tests:** Unit tests written with mocked dependencies?
    from .orchestrator.db import AmshaCrewDBApplication
    from .orchestrator.file import AmshaCrewFileApplication
    
    __all__ = ['AmshaCrewDBApplication', 'AmshaCrewFileApplication']
    ```

---

## 10. Versioning & Backward Compatibility

**Current Version:** 1.5.3

### Semantic Versioning (MAJOR.MINOR.PATCH)

*   **MAJOR (1.x.x):** Breaking changes to public API
    -   Changing method signatures in `Protocol` interfaces
    -   Removing public classes or methods
    -   Changing required configuration structure

*   **MINOR (x.5.x):** New features, backward-compatible
    -   Adding new orchestration modes
    -   Adding new optional parameters
    -   New guardrails or validators

*   **PATCH (x.x.3):** Bug fixes, backward-compatible
    -   Fixing bugs in existing logic
    -   Performance improvements
    -   Documentation updates

### Deprecation Policy

1.  **Mark as Deprecated:** Add `@deprecated` decorator and warning
    ```python
    import warnings
    
    @deprecated("Use new_method() instead. Will be removed in 2.0.0")
    def old_method(self):
        warnings.warn("old_method is deprecated", DeprecationWarning)
    ```

2.  **Keep for 1 MINOR Version:** Support deprecated methods through next minor version

3.  **Remove in MAJOR Version:** Breaking changes only in major version bumps

### Breaking Change Checklist
- [ ] Document in CHANGELOG
- [ ] Update all examples
- [ ] Create migration guide
- [ ] Bump MAJOR version
- [ ] Notify all known consumers

---

## 11. Testing Standards

**Philosophy:** Common libraries must be thoroughly tested since bugs affect multiple projects.

### Test Structure
```
tests/
├── unit/              # Isolated domain/service tests
├── integration/       # Repository + DB tests
└── examples/          # Example code tests
```

### Testing Rules

1.  **Unit Tests (Domain & Services):**
    -   Test domain logic in isolation
    -   Mock all repository dependencies
    -   Use dependency injection for testability
    ```python
    def test_atomic_builder_adds_agent():
        mock_agent_repo = Mock(spec=IAgentRepository)
        builder = AtomicDbBuilderService(mock_agent_repo, mock_task_repo)
        # Test logic...
    ```

2.  **Integration Tests (Repositories):**
    -   Test against real infrastructure (MongoDB, MinIO)
    -   Use Docker containers for test databases
    -   Clean up after each test

3.  **Example Tests:**
    -   All examples in `example/` must be runnable
    -   Create test that executes example code
    -   Validates example produces expected output

4.  **Test Coverage:**
    -   Aim for 80%+ coverage on service layer
    -   100% coverage on public API methods
    -   All exception paths must be tested

5.  **Test Isolation:**
    -   No test should depend on another test
    -   Use fixtures for common setup
    -   Mock external services (LLM APIs, external APIs)

---

## 12. Documentation Standards

### Code Documentation

1.  **Docstrings Required For:**
    -   All public classes and methods
    -   All Protocol/ABC definitions
    -   Complex algorithms or business logic

2.  **Docstring Format:**
    ```python
    def build_crew(self, process: Process = Process.sequential) -> Crew:
        """
        Builds a CrewAI Crew from configured agents and tasks.
        
        Args:
            process: Execution process (sequential or hierarchical)
            
        Returns:
            Configured Crew instance ready for execution
            
        Raises:
            InvalidCrewConfigException: If required agents/tasks are missing
        """
    ```

3.  **Type Hints:**
    -   All function parameters and return types
    -   Use `Optional`, `Union`, `List` etc. from `typing`
    -   Pydantic models for complex data structures

### Project Documentation

1.  **README.md:** Architecture overview, installation, usage examples
2.  **AGENTS.md (this file):** Coding standards and principles
3.  **CHANGELOG.md:** Version history and migration guides
4.  **examples/README.md:** How to run examples for each component

---

## 13. Common Patterns & Anti-Patterns

### ✅ DO: Patterns to Follow

```python
# ✅ Dependency Injection
class CrewOrchestrator:
    def __init__(self, agent_repo: IAgentRepository):
        self.agent_repo = agent_repo

# ✅ Config-Driven Behavior
llm_type = config.get("llm_type", LLMType.CREATIVE)

# ✅ Custom Exceptions
raise AgentNotFoundException(agent_id)

# ✅ Type Hints
def process(self, data: AgentRequest) -> AgentResponse:

# ✅ Protocol for External APIs
class OutputHandler(Protocol):
    def handle(self, output: str) -> None: ...
```

### ❌ DON'T: Anti-Patterns

```python
# ❌ Manual Instantiation
self.repo = MongoAgentRepository()  # Should be injected

# ❌ Hardcoded Logic
if project == "ProjectX":  # Should be config-driven

# ❌ Generic Exceptions
raise Exception("Failed")  # Use custom exceptions

# ❌ Missing Type Hints
def process(self, data):  # Missing types

# ❌ Leaking Implementation
from .repo.adapters.mongo import MongoRepo  # Should import interface
```

---

## Quick Reference Checklist

Before committing code, verify:

- [ ] **Architecture:** Does it follow dependency rule? (Inner layers don't depend on outer)
- [ ] **DI:** Are dependencies injected, not instantiated?
- [ ] **Interface:** Using `ABC` for repos, `Protocol` for client APIs?
- [ ] **Exceptions:** Using custom exceptions from component `exceptions/` directory?
- [ ] **Types:** All parameters and returns have type hints?
- [ ] **Tests:** Unit tests written with mocked dependencies?
- [ ] **Docs:** Public methods have docstrings?
- [ ] **Config:** Project-specific logic extracted to YAML config?
- [ ] **Versioning:** Breaking change? Bump MAJOR version?
- [ ] **Examples:** If public API changed, updated examples?

---

## 14. Dependency Management Standards

**Critical Rule:** Dependency management must be consistent across Amsha and client projects.

### Amsha Library (This Project)

**Production Dependencies:** Managed in **`pyproject.toml`**
- This is the library's public API
- Dependencies declared here are installed when clients do `pip install amsha`
- These appear in `[project].dependencies`

**Development Dependencies:** Managed in **`requirements.txt`**
- Tools for development only (pre-commit, mypy, black, pytest)
- NOT installed when clients use Amsha
- Only needed by Amsha developers

**Why this split?**
- Clients shouldn't install dev tools (black, mypy) just to use Amsha
- Keeps client installations lean
- Clear separation of concerns

### Client Projects Using Amsha

**All Dependencies:** Managed in **`pyproject.toml`**
- Client applications use `pyproject.toml` for everything
- Includes Amsha as a dependency: `amsha==1.5.3`
- Follows modern Python packaging standards

### Rules

1. **Adding Production Dependencies to Amsha:**
   ```bash
   # Add to pyproject.toml [project].dependencies
   # Also add to requirements.txt for dev consistency
   ```

2. **Adding Dev Dependencies to Amsha:**
   ```bash
   # Add ONLY to requirements.txt
   # Examples: pre-commit, mypy, black, flake8, pytest
   ```

3. **Client Projects:**
   ```bash
   # Use pyproject.toml exclusively
   # Add amsha as dependency
   dependencies = [
       "amsha==1.5.3",
       "other-deps..."
   ]
   ```

4. **Version Pinning:**
   - **Amsha:** Pin exact versions (`pydantic==2.11.9`)
   - **Clients:** Can use ranges (`amsha>=1.5.0,<2.0.0`)

### Current Setup

**pyproject.toml** (Production):
```toml
[project]
name = "Amsha"
version = "1.5.3"
dependencies = [
    "PyYAML==6.0.2",
    "crewai==0.201.1",
    # ... etc
]
```

**requirements.txt** (Development):
```
# Production dependencies (mirrors pyproject.toml)
PyYAML == 6.0.2
crewai == 0.201.1
# ... etc

# Development-only dependencies
pre-commit == 3.6.0
mypy == 1.8.0
black == 24.2.0
pytest == 7.4.0
```

### Checklist for Dependency Changes

When adding/updating dependencies:

- [ ] Is this a production dependency? → Add to `pyproject.toml` AND `requirements.txt`
- [ ] Is this a dev-only dependency? → Add ONLY to `requirements.txt`
- [ ] Did you pin the exact version? (e.g., `==1.5.3` not `>=1.5.0`)
- [ ] Did you update `DEPENDENCIES.md` if it's a significant framework?
- [ ] Did you test with a clean virtual environment?

---

**Remember:** Every line of code in Amsha affects multiple projects. Code with care, test thoroughly, and maintain backward compatibility.