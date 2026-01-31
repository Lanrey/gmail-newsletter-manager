# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation
- Comprehensive documentation
- CI/CD workflows
- Security policy

## [0.1.0] - 2026-01-31

### Added
- **Newsletter Discovery**: Intelligent newsletter detection using multiple heuristics
  - Header analysis (List-Unsubscribe, Precedence: bulk)
  - Sender pattern matching (newsletter@, updates@, etc.)
  - Frequency-based detection (configurable threshold)
  - Platform detection (Substack, Beehiiv, Mailchimp, etc.)
- **Hierarchical Labels**: Create and manage nested Gmail labels
  - Root label: "Newsletters"
  - Category-based organization (Technology, Business, etc.)
  - Newsletter-specific sublabels
- **Multi-Account Support**: Manage newsletters across multiple Gmail accounts
  - Account management CLI (add, remove, list, set-default)
  - Per-account credential management
  - Account-specific operations
- **Label Migration**: Bulk migrate existing labels into organized hierarchies
  - Dry-run mode for preview
  - Thread-level and message-level operations
  - Automatic label cleanup
- **Takeout Import**: Import and analyze newsletters from Gmail Takeout MBOX files
  - Full MBOX parsing with proper header decoding
  - Newsletter detection during import
  - Progress tracking with rich console output
- **Statistics & Reporting**: View newsletter inventory and engagement metrics
  - Total newsletters count
  - Category breakdown
  - Per-sender statistics
  - Uncategorized newsletter listing
- **Auto-Categorization**: Intelligent categorization based on content
  - Technology, Business, News, Design, Education, Health, Entertainment
  - Customizable category patterns
  - Fallback to uncategorized
- **SQLite Database**: Local storage for newsletter data
  - Newsletter tracking
  - Message tracking
  - Scan history
  - Operations log
- **Rate Limiting**: Automatic rate limiting for Gmail API
  - Configurable delays between requests
  - Batch size management
  - Progress callbacks
- **CLI Interface**: Rich command-line interface with argparse
  - Discover command with pagination
  - Label management commands
  - Account management commands
  - Statistics commands
  - Import command
- **Configuration System**: YAML-based configuration
  - Custom categories
  - Detection patterns
  - Rate limiting settings
  - Multi-account settings

### Developer Features
- Comprehensive test suite with pytest
- Code formatting with black
- Linting with ruff and flake8
- Type hints support (mypy compatible)
- CI/CD workflows with GitHub Actions
- Security scanning with bandit
- Code coverage reporting
- EditorConfig for consistent formatting

### Documentation
- Comprehensive README with examples
- API documentation in docstrings
- Architecture documentation
- Setup guide
- Contributing guidelines
- Security policy
- Example configuration file

[Unreleased]: https://github.com/YOUR-USERNAME/gmail-newsletter-manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YOUR-USERNAME/gmail-newsletter-manager/releases/tag/v0.1.0
