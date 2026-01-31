# Gmail Newsletter Manager

[![CI](https://github.com/YOUR-USERNAME/gmail-newsletter-manager/workflows/CI/badge.svg)](https://github.com/YOUR-USERNAME/gmail-newsletter-manager/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 🚀 Intelligent Gmail newsletter management utility built on [gogcli](https://github.com/steipete/gogcli)

Take control of your newsletter subscriptions with automated detection, smart categorization, and hierarchical organization directly in Gmail.

## ✨ Features

- 📧 **Smart Newsletter Detection** - Automatically identify newsletters using advanced heuristics (headers, patterns, frequency analysis)
- 🤖 **Hybrid AI Categorization** - ML-powered topic modeling with keyword fallback for intelligent categorization
- 🏷️ **Hierarchical Labels** - Organize with nested labels: `Newsletters/Technology/Dev Weekly`
- 📊 **Multi-Account Support** - Manage newsletters across multiple Gmail accounts
- 🔄 **Label Migration** - Bulk move existing labels into organized hierarchies
- 📥 **Takeout Import** - Import and analyze newsletters from Gmail Takeout (MBOX format)
- 📈 **Statistics & Reports** - View engagement metrics and newsletter inventory
- 🎯 **Topic Modeling** - LDA-based unsupervised learning discovers newsletter topics automatically
- 💾 **SQLite Database** - Fast local storage with scan history and analytics
- 🔧 **Flexible Configuration** - YAML-based configuration with customizable patterns and categories

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 📦 Prerequisites

### 1. Install gogcli

[gogcli](https://github.com/steipete/gogcli) is a command-line interface for Google APIs.

**macOS:**
```bash
brew install steipete/tap/gogcli
```

**From source:**
```bash
go install github.com/steipete/gogcli/cmd/gog@latest
```

### 2. Authenticate with Gmail

```bash
# Set up OAuth credentials
gog auth credentials set /path/to/credentials.json

# Authenticate your Gmail account
gog auth add your@gmail.com

# Verify authentication
gog auth list
```

> 💡 **Getting OAuth Credentials:** Follow [Google's OAuth setup guide](https://developers.google.com/gmail/api/quickstart) to create OAuth 2.0 credentials.

## 🚀 Installation

### From Source (Recommended for now)

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/gmail-newsletter-manager.git
cd gmail-newsletter-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install gmail-newsletter-manager
```

## ⚡ Quick Start

### 1. Initial Discovery

Scan your inbox to discover newsletters:

```bash
# Discover from last 90 days (default)
newsletter-manager discover

# Scan all emails (may take time)
newsletter-manager discover --all --max-results 10000

# Scan last 30 days
newsletter-manager discover --days 30
```

### 2. View Discovered Newsletters

```bash
# List all newsletters
newsletter-manager list

# List with statistics
newsletter-manager stats

# Show by category
newsletter-manager list --by-category
```

### 3. Apply Labels

Organize newsletters with hierarchical labels in Gmail:

```bash
# Apply labels to all discovered newsletters
newsletter-manager apply-labels

# Dry run to preview changes
newsletter-manager apply-labels --dry-run

# Apply to specific category
newsletter-manager apply-labels --category Technology
```

### 4. Migrate Existing Labels

Move existing root-level newsletter labels into hierarchy:

```bash
# Preview migration
newsletter-manager migrate-labels --dry-run

# Migrate all matching labels
newsletter-manager migrate-labels

# Migrate specific label
newsletter-manager migrate-labels --label "Node Weekly"
```

## 📖 Usage

### Discovery

```bash
# Basic discovery
newsletter-manager discover --days 90

# Full scan with custom limits
newsletter-manager discover --all --max-results 50000 --batch-size 5000

# Adjust frequency threshold
newsletter-manager discover --min-frequency 3
```

**Options:**
- `--days N` - Scan last N days (default: 90)
- `--all` - Scan all emails from inception
- `--max-results N` - Maximum messages to scan (default: 10000)
- `--batch-size N` - Messages per batch (default: 5000)
- `--min-frequency N` - Minimum emails/month to be considered newsletter (default: 2)

### Label Management

```bash
# Apply labels to all newsletters
newsletter-manager apply-labels

# Dry run mode (preview only)
newsletter-manager apply-labels --dry-run

# Apply to specific sender
newsletter-manager apply-labels --sender "newsletter@example.com"

# Apply to category
newsletter-manager apply-labels --category Technology

# Apply to threads instead of individual messages
newsletter-manager apply-labels --use-threads
```

**Label Migration:**

```bash
# Migrate labels from root to hierarchy
newsletter-manager migrate-labels --dry-run
newsletter-manager migrate-labels

# Migrate specific label
newsletter-manager migrate-labels --label "Weekly Digest"
```

### Multi-Account Management

```bash
# Add account
newsletter-manager account add another@gmail.com

# List accounts
newsletter-manager account list

# Set default account
newsletter-manager account set-default another@gmail.com

# Remove account
newsletter-manager account remove old@gmail.com

# Use specific account for command
newsletter-manager --account work@gmail.com discover
```

### Statistics

```bash
# Overall statistics
newsletter-manager stats

# Filter by category
newsletter-manager stats --category Technology

# Filter by sender
newsletter-manager stats --sender "newsletter@example.com"

# View uncategorized newsletters
newsletter-manager list --uncategorized
```

### Import from Takeout

Import newsletters from [Google Takeout](https://takeout.google.com/) MBOX files:

```bash
# Import from MBOX file
newsletter-manager import-takeout /path/to/All\ mail.mbox

# Dry run
newsletter-manager import-takeout /path/to/file.mbox --dry-run

# Limit messages
newsletter-manager import-takeout /path/to/file.mbox --max-messages 10000
```

### Topic Modeling (ML-Powered Categorization)

Train a machine learning model to automatically categorize newsletters:

```bash
# Train topic model on existing newsletters
newsletter-manager train-topics

# Specify number of topics (default: 10)
newsletter-manager train-topics --n-topics 12

# Advanced training options
newsletter-manager train-topics --n-topics 15 --min-df 2 --max-df 0.7 --max-newsletters 1000
```

The hybrid approach:
1. **Topic Model (Primary)**: Uses LDA to discover topics from your newsletters
2. **Keywords (Fallback)**: Uses config.yaml keywords when model confidence is low

See [Topic Modeling Guide](docs/TOPIC_MODELING.md) for detailed information.

# Limit number of messages
newsletter-manager import-takeout /path/to/file.mbox --max-messages 10000
```

## ⚙️ Configuration

Configuration is stored at `~/.gmail-newsletter-manager/config.yaml`.

### Create Configuration

```bash
# Copy example configuration
cp config.example.yaml ~/.gmail-newsletter-manager/config.yaml

# Edit with your preferences
nano ~/.gmail-newsletter-manager/config.yaml
```

### Configuration Options

```yaml
# Database location
db_path: ~/.gmail-newsletter-manager/newsletters.db

# Gmail accounts
accounts:
  - primary@gmail.com
  - work@gmail.com

default_account: primary@gmail.com

# Detection settings
detection:
  min_frequency: 2
  frequency_window_days: 90

# Custom categories
categories:
  Technology:
    - tech
    - programming
    - developer
  Business:
    - business
    - startup
    - entrepreneur
  
# Newsletter patterns
patterns:
  newsletters:
    - newsletter
    - digest
    - weekly
    - daily
  sender_indicators:
    - news@
    - newsletter@
    - updates@
    - no-reply@

# Label management
labels:
  root: Newsletters
  auto_apply: true
  hierarchical: true

# Rate limiting
rate_limiting:
  request_delay: 2.0
  batch_size: 500
  max_scan_per_run: 10000
```

See [config.example.yaml](config.example.yaml) for full configuration options.

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/gmail-newsletter-manager.git
cd gmail-newsletter-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=newsletter_manager --cov-report=html

# Run specific test file
pytest tests/test_newsletter_detector.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests
flake8 src tests

# Type checking (if mypy installed)
mypy src
```

### Project Structure

```
gmail-newsletter-manager/
├── src/
│   └── newsletter_manager/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── config.py           # Configuration management
│       ├── database.py         # SQLite database operations
│       ├── gogcli_wrapper.py   # gogcli command wrapper
│       ├── label_manager.py    # Gmail label operations
│       ├── newsletter_detector.py  # Newsletter detection logic
│       └── takeout_importer.py # MBOX import functionality
├── tests/
│   ├── test_label_manager.py
│   └── test_newsletter_detector.py
├── docs/
│   ├── ARCHITECTURE.md         # System architecture
│   ├── EXAMPLES.md             # Usage examples
│   └── SETUP.md                # Setup guide
├── .github/
│   └── workflows/              # CI/CD workflows
├── config.example.yaml         # Example configuration
├── pyproject.toml              # Project metadata
├── CONTRIBUTING.md             # Contribution guidelines
├── SECURITY.md                 # Security policy
└── README.md                   # This file
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute

- 🐛 Report bugs via [GitHub Issues](https://github.com/YOUR-USERNAME/gmail-newsletter-manager/issues)
- 💡 Suggest features or improvements
- 📝 Improve documentation
- 🔧 Submit pull requests

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [gogcli](https://github.com/steipete/gogcli) by Peter Steinberger
- Inspired by the need to tame newsletter overload
- Thanks to all contributors and users

## 📧 Contact

- GitHub: [@YOUR-USERNAME](https://github.com/YOUR-USERNAME)
- Email: olusolaakinsulere@gmail.com

## 🗺️ Roadmap

- [ ] Web dashboard for newsletter management
- [ ] Newsletter engagement scoring
- [ ] Automated unsubscribe suggestions
- [ ] Smart digest creation
- [ ] Browser extension for quick actions
- [ ] Integration with RSS readers
- [ ] Machine learning-based categorization

---

**Star ⭐ this repository if you find it useful!**
