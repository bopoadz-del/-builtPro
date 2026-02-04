# Contributing to BuilTPro Brain AI

Thank you for your interest in contributing to BuilTPro Brain AI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Pull Request Checklist](#pull-request-checklist)
- [License](#license)

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bopoadz-del/BuilTPro-ai-demo.git
   cd BuilTPro-ai-demo
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose:**
   ```bash
   docker compose up --build
   ```
   
   Or use the Makefile if available:
   ```bash
   make up
   ```

4. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

## Running Tests

Run all tests:
```bash
pytest -q
```

Run specific test files:
```bash
pytest backend/tests/test_services.py -v
```

Run with coverage:
```bash
pytest --cov=backend --cov-report=html
```

## Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting (line length: 88)
- **Ruff** - Fast Python linter
- **MyPy** - Static type checking

Format your code before committing:
```bash
black backend/
ruff check backend/
mypy backend/
```

Configuration for these tools is in `pyproject.toml`.

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality. Install them:

```bash
pre-commit install
```

Run hooks manually on all files:
```bash
pre-commit run --all-files
```

The pre-commit configuration is in `.pre-commit-config.yaml`.

## Pull Request Checklist

Before submitting a PR, please ensure:

- [ ] Code follows the project's style guidelines (Black, Ruff)
- [ ] All tests pass (`pytest -q`)
- [ ] New tests added for new functionality
- [ ] Type hints are included where applicable
- [ ] Documentation is updated (README, docstrings)
- [ ] Pre-commit hooks pass
- [ ] Commit messages are clear and descriptive

### PR Description

Include in your PR description:
- What changes were made
- Why the changes were made
- Any breaking changes
- Related issues (if any)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Questions?

If you have questions or need help, please:
- Open an issue on GitHub
- Contact the maintainers at [maintainers@builtpro.ai](mailto:maintainers@builtpro.ai)

Thank you for contributing!
