# Contributing to SeenSlide

Thank you for your interest in contributing to SeenSlide! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Plugin Development](#plugin-development)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/seenslide.git
   cd seenslide
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/seenslide.git
   ```

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Ubuntu Linux (or other Linux distribution)
- Git

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_capture/test_mss_provider.py

# Run with verbose output
pytest -v
```

### Running the Application

```bash
# Run admin GUI
python -m modules.admin.main

# Run web server
python -m modules.server.main

# Run capture daemon
python -m modules.capture.daemon
```

## Project Structure

```
seenslide/
├── core/           # Core interfaces and infrastructure
├── modules/        # Pluggable modules
├── config/         # Configuration files
├── tests/          # Test suite
└── docs/           # Documentation
```

See [DEVELOPMENT_INSTRUCTIONS.md](DEVELOPMENT_INSTRUCTIONS.md) for detailed architecture.

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Error messages/logs
   - Screenshots if applicable

### Suggesting Enhancements

1. **Check existing issues** for similar suggestions
2. **Create a new issue** describing:
   - The problem/limitation
   - Proposed solution
   - Alternative solutions considered
   - Use cases

### Contributing Code

1. **Find or create an issue** to work on
2. **Comment on the issue** to let others know you're working on it
3. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following coding standards
5. **Write/update tests**
6. **Run tests** to ensure everything passes
7. **Commit your changes** with clear messages
8. **Push to your fork**
9. **Create a Pull Request**

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Type hints**: Required for all function signatures
- **Docstrings**: Required for all public functions/classes (Google style)
- **Imports**: Organized with isort

### Code Formatting

We use automated formatters:

```bash
# Format code with black
black .

# Sort imports
isort .

# Check style with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Example Code Style

```python
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Example:
    """Example class demonstrating our coding standards.
    
    Attributes:
        name: The name of the example
        count: The count value
    """
    name: str
    count: int = 0
    
    def process(self, items: List[str]) -> Optional[str]:
        """Process a list of items.
        
        Args:
            items: List of strings to process
            
        Returns:
            Processed result or None if empty
            
        Raises:
            ValueError: If items contain invalid data
        """
        if not items:
            return None
        
        # Process items
        result = " ".join(items)
        return result.upper()
```

### Naming Conventions

- **Classes**: PascalCase (`CaptureProvider`)
- **Functions/Methods**: snake_case (`capture_screen`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Private members**: Leading underscore (`_internal_state`)
- **Modules**: lowercase (`capture`, `dedup`)

### Documentation

- **Docstrings**: Use Google style for all public APIs
- **Comments**: Explain "why", not "what"
- **Type hints**: Always use for function signatures
- **README**: Update if adding features

### Error Handling

```python
# Good: Specific exception, helpful message
try:
    result = risky_operation()
except FileNotFoundError as e:
    logger.error(f"Config file not found: {e}")
    raise ConfigurationError("Missing config file") from e

# Bad: Bare except, no context
try:
    result = risky_operation()
except:
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("Normal operation message")
logger.warning("Something unexpected but handled")
logger.error("Error that needs attention")
logger.critical("System is unusable")

# Include context in messages
logger.info(f"Captured slide {slide_id} from session {session_id}")
```

## Testing

### Test Organization

```
tests/
├── test_capture/
│   ├── test_mss_provider.py
│   └── test_capture_daemon.py
├── test_dedup/
│   ├── test_hash_strategy.py
│   └── test_perceptual_strategy.py
└── test_integration/
    └── test_full_pipeline.py
```

### Writing Tests

```python
import pytest
from modules.capture.providers.mss_provider import MSSCaptureProvider


class TestMSSProvider:
    """Tests for MSS capture provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a provider instance for testing."""
        provider = MSSCaptureProvider()
        provider.initialize({})
        yield provider
        provider.cleanup()
    
    def test_initialization(self, provider):
        """Test that provider initializes correctly."""
        assert provider.name == "mss"
        assert provider.initialize({}) is True
    
    def test_capture(self, provider):
        """Test that capture returns valid data."""
        capture = provider.capture()
        assert capture.image is not None
        assert capture.width > 0
        assert capture.height > 0
    
    def test_list_monitors(self, provider):
        """Test that monitors are listed correctly."""
        monitors = provider.list_monitors()
        assert len(monitors) > 0
        assert "id" in monitors[0]
```

### Test Coverage

- Aim for >80% code coverage
- Test both happy path and error cases
- Include integration tests for critical flows
- Mock external dependencies appropriately

## Submitting Changes

### Commit Messages

Follow conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(capture): add Wayland support

Implement Wayland screen capture using wlroots protocol.
Includes automatic detection of Wayland vs X11.

Closes #42

fix(dedup): handle zero-size images

Add check for empty images before hashing to prevent crashes.

test(storage): add SQLite integration tests
```

### Pull Request Process

1. **Update documentation** if needed
2. **Add/update tests** for your changes
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** (if applicable)
5. **Create PR** with:
   - Clear title and description
   - Link to related issue(s)
   - Screenshots for UI changes
   - Testing notes

### PR Review

- Maintainers will review your PR
- Address any feedback/changes requested
- Once approved, your PR will be merged
- Your contribution will be credited in releases

## Plugin Development

### Creating a New Capture Provider

```python
# modules/capture/providers/my_provider.py
from core.interfaces.capture import ICaptureProvider
from core.models.slide import RawCapture

class MyCustomProvider(ICaptureProvider):
    """My custom capture provider."""
    
    def initialize(self, config: dict) -> bool:
        # Initialize your provider
        return True
    
    def list_monitors(self):
        # Return list of monitors
        return [{"id": 1, "width": 1920, "height": 1080}]
    
    def capture(self, monitor_id=None):
        # Capture and return RawCapture
        pass
    
    def cleanup(self):
        # Clean up resources
        pass
    
    @property
    def name(self):
        return "my_custom"
    
    @property
    def supported_platforms(self):
        return ["linux"]

# modules/capture/plugin.py
from .providers.my_provider import MyCustomProvider

def register():
    registry = PluginRegistry()
    registry.register_capture_provider("my_custom", MyCustomProvider)

register()
```

### Creating a New Deduplication Strategy

Similar pattern - implement `IDeduplicationStrategy` interface.

See [docs/plugin_development.md](docs/plugin_development.md) for detailed guide.

## Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our community chat (link TBD)

## Recognition

Contributors will be:
- Listed in [AUTHORS.md](AUTHORS.md)
- Mentioned in release notes
- Credited in the project README

Thank you for contributing to SeenSlide! 👁️✨
