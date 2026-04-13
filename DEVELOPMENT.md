# Development Guide

Contributing guide for kakao2notion developers.

## Development Setup

### Clone and Setup Environment

```bash
git clone https://github.com/leehogwang/kakao2notion.git
cd kakao2notion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Project Structure

```
kakao2notion/
├── kakao2notion/          # Main package
│   ├── __init__.py        # Package exports
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration management
│   ├── parser.py          # KakaoTalk message parser
│   ├── vectorizer.py      # Text vectorization
│   ├── clusterer.py       # Message clustering
│   ├── merger.py          # Message merging
│   ├── notion_client.py   # Notion API integration
│   └── llm.py             # LLM providers (Codex, Claude)
├── tests/                 # Test suite
├── examples/              # Example files
├── README.md              # User documentation
├── INSTALLATION.md        # Installation guide
├── DEVELOPMENT.md         # This file
├── setup.py               # Package configuration
└── requirements.txt       # Dependencies
```

## Code Style

### Formatting

Use Black for code formatting:

```bash
black kakao2notion/
```

Configure in `setup.cfg` or `pyproject.toml`:

```ini
[tool.black]
line-length = 100
target-version = ['py310']
```

### Linting

Use Ruff for linting:

```bash
ruff check kakao2notion/
ruff check --fix kakao2notion/  # Auto-fix issues
```

### Type Hints

Always use type hints in function signatures:

```python
def process_messages(
    messages: List[Message],
    n_clusters: int = 5,
) -> Dict[str, List[Message]]:
    """Process and cluster messages."""
    ...
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kakao2notion

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_json_messages
```

### Write Tests

Create test files in `tests/` directory:

```python
# tests/test_module.py
import pytest
from kakao2notion.module import some_function

def test_some_function():
    """Test description"""
    result = some_function(input_data)
    assert result == expected_output

def test_some_function_error():
    """Test error handling"""
    with pytest.raises(ValueError):
        some_function(invalid_input)
```

## Adding Features

### Adding a New Command

1. Create command function in `cli.py`:

```python
@cli.command()
@click.option('--option', default='value')
def new_command(option):
    """Command description"""
    console.print("Output")
```

2. Add tests in `tests/test_cli.py`

3. Update README.md with command documentation

### Adding LLM Provider

1. Extend `LLMProvider` class in `llm.py`:

```python
class MyProvider(LLMProvider):
    def generate_category_name(self, messages, existing_names=None):
        # Implementation
        return (name, description)
```

2. Register in `get_llm_provider()` function

3. Add tests

4. Update documentation

### Modifying Parser

1. Edit `parser.py`
2. Add test cases for new format in `tests/test_parser.py`
3. Update README.md examples

## API Design

### Message Class

```python
@dataclass
class Message:
    content: str                      # Main message text
    sender: Optional[str] = None      # Message sender
    timestamp: Optional[datetime] = None  # When sent
    chat_name: Optional[str] = None   # Chat room name
    original_id: Optional[str] = None # Original position tracking
```

### Cluster Class

```python
@dataclass
class Cluster:
    label: int                        # Cluster ID
    indices: List[int]                # Message indices in cluster
    center: Optional[np.ndarray] = None
    category_name: Optional[str] = None
    category_description: Optional[str] = None
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> Dict:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary with keys 'x' and 'y'
        
    Raises:
        ValueError: If param2 is negative
    """
```

### Update Documentation

- Update README.md for user-facing changes
- Update DEVELOPMENT.md for development-related changes
- Add docstrings to new functions
- Update examples if needed

## Git Workflow

### Branching

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bug
```

### Commit Messages

```
[type] brief description

Longer explanation if needed.

- Bullet points for changes
- Another point
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Requests

1. Push your branch
2. Create PR on GitHub
3. Ensure CI passes
4. Request review
5. Merge after approval

## Release Process

### Bump Version

Update version in:
- `kakao2notion/__init__.py`
- `setup.py`
- `README.md` (if needed)

### Create Release

```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### Publish to PyPI

```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

pr = cProfile.Profile()
pr.enable()

# Code to profile
process_messages(messages)

pr.disable()
stats = pstats.Stats(pr)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Common Bottlenecks

1. **Vectorization**: Use sparse matrices for large datasets
2. **Clustering**: Adjust n_clusters or use approximate algorithms
3. **LLM calls**: Cache results or use batch processing

## Dependencies

### Adding New Dependencies

1. Add to `requirements.txt`
2. Add to `setup.py` install_requires
3. Update INSTALLATION.md
4. Add tests for new features using the dependency

### Removing Dependencies

1. Ensure no code uses it
2. Remove from both requirements.txt and setup.py
3. Test thoroughly

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Memory usage high**
- Check for message duplication
- Reduce n_clusters
- Use sparse vectorization

**LLM calls slow**
- Use faster model
- Reduce sample size
- Cache results

**Notion upload fails**
- Check API key
- Verify database exists
- Check message content encoding

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Format code: `black kakao2notion/`
5. Run tests: `pytest`
6. Push branch
7. Create pull request

## Questions?

- Check existing issues on GitHub
- See README.md for usage examples
- Look at existing code for patterns

Happy developing! 🚀
