# Agent Guidelines for Miles Repository

PRIMARY GOAL: deliver timely Telegram alerts for mileage-transfer bonuses via an autonomous CI pipeline that self-repairs.

## Commands
- **Test all**: `pytest` or `pytest -q` for quiet output
- **Test single file**: `pytest tests/test_filename.py`
- **Test single function**: `pytest tests/test_filename.py::test_function_name`
- **Lint**: `ruff check .` and `black --check .`
- **Type check**: `mypy --strict miles`
- **Pre-commit**: `pre-commit run --all-files`
- **Install dev deps**: `pip install -e .[dev]`

## Code Style
- Use `black` formatting and `ruff` linting (enforced by pre-commit)
- Import order: standard library, third-party, local modules (`from miles.module import`)
- Strict typing with mypy (`--strict` mode)
- Logger setup: `import logging; logger = logging.getLogger("miles.module_name")` (setup_logging() called automatically via miles.__init__)
- Exception handling: Use `logger.exception()` for fatal errors
- Test setup: Use `fakeredis.FakeRedis.from_url` for Redis mocking via monkeypatch
- File paths: Use `tmp_path` fixture for temporary files in tests

This repository is maintained by Codex. All changes should keep the project functioning and maintainable. Run the full test suite and `pre-commit` before each commit.
