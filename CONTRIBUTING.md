# Contributing to EdgeADC Octavia Driver

Thank you for your interest in contributing to the EdgeADC Octavia Driver! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Getting Started

### Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/edgeNEXUS/Edgeadc_Octavia_Driver.git
   cd Edgeadc_Octavia_Driver
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=octavia_edgeadc_driver --cov-report=html

# Run specific test file
pytest tests/test_client.py -v

# Run specific test
pytest tests/test_client.py::TestEdgeADCClient::test_login_success -v
```

### Code Style

We use the following tools for code quality:

- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checking

```bash
# Run linter
ruff check octavia_edgeadc_driver/

# Run formatter
ruff format octavia_edgeadc_driver/

# Run type checker
mypy octavia_edgeadc_driver/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-l7-policy-support`
- `fix/connection-timeout-handling`
- `docs/update-installation-guide`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

Examples:
```
feat(driver): add L7 policy support
fix(client): handle connection timeout gracefully
docs(readme): update installation instructions
```

### Pull Request Process

1. **Create a feature branch** from `main` or `develop`
2. **Make your changes** with appropriate tests
3. **Run tests and linting** locally
4. **Push your branch** and create a Pull Request
5. **Fill out the PR template** with details about your changes
6. **Wait for review** and address any feedback

### PR Checklist

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Linting passes (`ruff check .`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventions
- [ ] PR description explains the changes

## Testing Guidelines

### Unit Tests

- Test individual functions and methods in isolation
- Use mocks for external dependencies (EdgeADC API, Octavia)
- Aim for high coverage of critical paths

### Integration Tests

- Test against a real EdgeADC device (when available)
- Use environment variables for credentials
- Mark with `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_real_edgeadc_connection():
    # This test requires a real EdgeADC device
    pass
```

## Architecture Overview

```
octavia_edgeadc_driver/
├── api/
│   ├── __init__.py
│   └── edgeadc_client.py    # REST client for EdgeADC
├── common/
│   ├── __init__.py
│   ├── config.py            # Oslo configuration options
│   └── constants.py         # Constants and mappings
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_client.py       # Client tests
│   └── test_driver.py       # Driver tests
├── __init__.py
├── agent.py                 # Provider agent entry point
└── driver.py                # Main Octavia provider driver
```

## Reporting Issues

When reporting issues, please include:

1. **Description** - Clear description of the problem
2. **Steps to reproduce** - How to trigger the issue
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment** - Python version, OpenStack version, EdgeADC version
6. **Logs** - Relevant log output (sanitize credentials!)

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues to avoid duplicates
2. Describe the use case and expected behavior
3. Explain why this would be valuable

## Questions?

- Open a GitHub issue for questions
- Check existing documentation and issues first

Thank you for contributing! 🎉
