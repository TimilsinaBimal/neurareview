# Pre-commit Hooks Setup

This project uses pre-commit hooks to ensure code quality and consistency.

## Installed Hooks

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML files
- **check-added-large-files**: Prevents large files from being committed
- **check-merge-conflict**: Detects merge conflict markers
- **check-json**: Validates JSON files
- **check-toml**: Validates TOML files
- **debug-statements**: Detects debug statements (pdb, etc.)
- **check-docstring-first**: Ensures docstrings come before code
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **bandit**: Security vulnerability scanning

## Usage

### Install pre-commit hooks
```bash
pip install pre-commit
pre-commit install
```

### Run hooks on all files
```bash
pre-commit run --all-files
```

### Run hooks on staged files only
```bash
pre-commit run
```

### Update hook versions
```bash
pre-commit autoupdate
```

## Configuration

- `.pre-commit-config.yaml`: Main pre-commit configuration
- `setup.cfg`: Flake8 configuration
- `pyproject.toml`: Black, isort, and other tool configurations

## Development Dependencies

Install development dependencies:
```bash
pip install -e ".[dev]"
```

This will install all the tools needed for pre-commit hooks.
