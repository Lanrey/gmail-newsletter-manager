# Contributing to Gmail Newsletter Manager

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- gogcli installed and configured
- Git for version control

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/gmail-newsletter-manager.git
   cd gmail-newsletter-manager
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes
- Write clear, concise code
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 3. Run Tests and Linting
```bash
# Run tests
pytest tests/ -v

# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add new feature" # or "fix: resolve bug"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions and classes

Example:
```python
def search_newsletters(query: str, max_results: Optional[int] = None) -> List[Dict]:
    """Search for newsletters matching the query.
    
    Args:
        query: Gmail search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of newsletter dictionaries
        
    Raises:
        GogCLIError: If gogcli command fails
    """
    # Implementation
```

### Code Organization
- Keep functions focused and small
- Group related functionality into classes
- Use meaningful module and file names
- Avoid circular dependencies

## Testing Guidelines

### Writing Tests
- Write tests for all new features
- Test edge cases and error conditions
- Use descriptive test names
- Mock external dependencies (gogcli calls)

Example:
```python
def test_newsletter_detection_with_list_unsubscribe():
    """Test that newsletters are detected via List-Unsubscribe header."""
    # Arrange
    message = create_test_message(has_unsubscribe=True)
    detector = NewsletterDetector(config)
    
    # Act
    is_newsletter, platform, reasons = detector.is_newsletter(message)
    
    # Assert
    assert is_newsletter is True
    assert 'has_list_unsubscribe_header' in reasons
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_newsletter_detector.py

# Run with coverage
pytest tests/ --cov=newsletter_manager --cov-report=html
```

## Adding New Features

### Adding a New Command
1. Add command function to `src/newsletter_manager/cli.py`:
   ```python
   # Add to NewsletterCLI class
   def cmd_your_command(self, args):
       """Command description."""
       # Implementation
       
   # Add parser in main() function
   parser_your_cmd = subparsers.add_parser('your-command', help='Description')
   parser_your_cmd.add_argument('--your-option', help='Option description')
   ```

2. Add tests in `tests/test_cli.py`
3. Update documentation in `docs/EXAMPLES.md`
4. Update README.md if needed

### Adding Detection Logic
1. Update `NewsletterDetector` in `src/newsletter_manager/newsletter_detector.py`
2. Add tests in `tests/test_newsletter_detector.py`
3. Document in code comments

### Adding Configuration Options
1. Update `Config.DEFAULT_CONFIG` in `src/newsletter_manager/config.py`
2. Update documentation in `docs/SETUP.md`
3. Add example in README.md

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints

### User Documentation
Update these files as needed:
- `README.md` - Project overview and quick start
- `docs/SETUP.md` - Detailed setup instructions
- `docs/EXAMPLES.md` - Usage examples
- `docs/ARCHITECTURE.md` - Technical architecture

## Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
How has this been tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code formatted with black
- [ ] No linting errors
```

## Issue Reporting

### Bug Reports
Include:
- Python version
- gogcli version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## Code Review Process

### For Contributors
- Be open to feedback
- Respond to review comments
- Make requested changes promptly
- Ask questions if unclear

### For Reviewers
- Be constructive and respectful
- Explain reasoning for suggestions
- Approve when ready
- Test changes locally if needed

## Release Process

(For maintainers)

1. Update version in `src/newsletter_manager/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md
4. Create git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
5. Push tag: `git push origin v0.2.0`
6. Create GitHub release

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues and documentation first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort! 🙏
