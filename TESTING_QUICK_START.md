# MJlog Testing - Quick Start Guide

## ✅ Current Status
- **Framework**: pytest 9.0.3 ✅
- **Tests**: 18 passing ✅
- **Coverage**: 25.16% (tracking enabled) ✅
- **Fixtures**: Database, config, mocking ✅

## 🚀 Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/mjlog --cov-report=html

# Specific test
uv run pytest tests/db/test_models.py::TestMode::test_mode_creation -v

# Show slowest 10 tests
uv run pytest --durations=10

# Parallel execution
uv run pytest -n auto
```

## 📝 Write a Test

```python
# tests/db/test_example.py
"""Tests for example module."""

def test_something(db_session):
    """Test description.
    
    Args:
        db_session: Database session fixture.
    """
    # Arrange
    obj = MyClass(name="test")
    db_session.add(obj)
    db_session.commit()
    
    # Act
    result = db_session.query(MyClass).filter_by(name="test").first()
    
    # Assert
    assert result.name == "test"
```

## 🧹 Code Quality

```bash
# Format code
uv run black src/mjlog tests

# Sort imports
uv run isort src/mjlog tests

# Type check
uv run mypy src/mjlog/ --strict

# Check docstrings
uv run pydocstyle src/mjlog/

# Lint
uv run flake8 src/mjlog/
```

## 📊 Coverage Report

```bash
# Generate HTML report
uv run pytest --cov=src/mjlog --cov-report=html

# View report
open htmlcov/index.html
```

## 🎯 Phase 2 Goals

- [ ] Add tests/db/test_session.py (4-6 tests)
- [ ] Add tests/test_config.py (4-6 tests)
- [ ] Add tests/test_cli.py (6-8 tests)
- [ ] Test DXCCEntity.get_big_cty() (5-8 tests)
- [ ] Target: 40-50% coverage

## 📚 Available Fixtures

```python
def test_example(
    db_session,        # Fresh database session
    app_config,        # Mocked configuration
    mock_qapp,         # Mock QApplication
    monkeypatch,       # pytest monkeypatch
):
    pass
```

## 🔗 Test Data Factories

```python
from tests.fixtures.factories import (
    ModeFactory,
    StationFactory,
    MembershipFactory,
)

def test_with_factory(db_session):
    station = StationFactory(callsign="W5ABC")
    db_session.add(station)
    db_session.commit()
```

## ⚙️ Configuration

**pyproject.toml** contains:
- `[tool.pytest.ini_options]` - pytest config
- `[tool.coverage.*]` - coverage settings
- `[tool.black]` - formatter config
- `[tool.isort]` - import sorter config
- `[tool.mypy]` - type checker config

## 📖 More Info

See full documentation:
- `PYTEST_SETUP_COMPLETE.md` - Detailed setup guide
- `TESTING_RECOMMENDATION.md` - Framework comparison & best practices
