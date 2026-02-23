# Contributing to mkdocs-dataview-plugin

## Development Setup

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -e .
   pip install pytest pylint
   ```

## Running Tests

We use `pytest` for testing. Run as module from src directory, so you don't need to install the package.

```bash
cd src
python3 -m pytest
```

To run a specific test file:
```bash
cd src
python3 -m pytest ../tests/test_table_view.py
```

## Code Style

- **Type Hints**: Please use Python type hints for new code.
- **Docstrings**: Add docstrings to all new classes and functions.
- **Linting**: Run `pylint` to check for errors.
