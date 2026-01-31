#!/usr/bin/env python
"""
Gmail Newsletter Manager - Makefile Alternative

Common development tasks for the project.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and print the result."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        sys.exit(1)
    print(f"✅ Success: {description}")


def install():
    """Install package in development mode."""
    run_command(
        "pip install -e '.[dev]'",
        "Installing package with dev dependencies"
    )


def test():
    """Run tests with coverage."""
    run_command(
        "pytest tests/ -v --cov=newsletter_manager --cov-report=html --cov-report=term",
        "Running tests with coverage"
    )


def lint():
    """Run all linting checks."""
    run_command("black --check src tests", "Checking code formatting with black")
    run_command("ruff check src tests", "Linting with ruff")
    run_command("flake8 src tests", "Linting with flake8")


def format_code():
    """Format code with black and isort."""
    run_command("black src tests", "Formatting code with black")
    run_command("isort src tests", "Sorting imports with isort")


def security():
    """Run security checks."""
    run_command("bandit -r src -ll", "Running security checks with bandit")


def clean():
    """Clean build artifacts and cache files."""
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.egg-info",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
    ]
    
    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            if path.is_dir():
                print(f"Removing directory: {path}")
                subprocess.run(["rm", "-rf", str(path)])
            else:
                print(f"Removing file: {path}")
                path.unlink()
    
    print("✅ Cleaned build artifacts and cache files")


def build():
    """Build distribution packages."""
    run_command("python -m build", "Building distribution packages")


def check_all():
    """Run all checks (format, lint, security, test)."""
    format_code()
    lint()
    security()
    test()
    print("\n" + "="*60)
    print("✅ All checks passed!")
    print("="*60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python make.py [command]")
        print("\nAvailable commands:")
        print("  install    - Install package with dev dependencies")
        print("  test       - Run tests with coverage")
        print("  lint       - Run linting checks")
        print("  format     - Format code with black and isort")
        print("  security   - Run security checks")
        print("  clean      - Clean build artifacts")
        print("  build      - Build distribution packages")
        print("  check-all  - Run all checks")
        sys.exit(1)
    
    command = sys.argv[1]
    commands = {
        "install": install,
        "test": test,
        "lint": lint,
        "format": format_code,
        "security": security,
        "clean": clean,
        "build": build,
        "check-all": check_all,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    commands[command]()


if __name__ == "__main__":
    main()
