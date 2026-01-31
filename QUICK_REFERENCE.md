# Quick Reference Guide

## Installation

```bash
cd ~/Development/gmail-newsletter-manager
./setup.sh
source venv/bin/activate
```

## Essential Commands

### Discovery & Analysis
```bash
# Discover newsletters (scan inbox)
newsletter-manager discover --days 90

# List all newsletters
newsletter-manager list

# List by category
newsletter-manager list --category Tech

# Show only unread
newsletter-manager list --unread-only

# Get statistics
newsletter-manager stats

# Generate report
newsletter-manager report
```

### Organization
```bash
# Preview organization (safe)
newsletter-manager organize --dry-run

# Actually organize
newsletter-manager organize

# Auto-categorize
newsletter-manager organize --auto-categorize
```

### Management
```bash
# Get unsubscribe recommendations
newsletter-manager recommend-unsubscribe

# Preview cleanup
newsletter-manager cleanup --older-than 30d --dry-run

# Actually cleanup
newsletter-manager cleanup --older-than 30d

# Cleanup unread only
newsletter-manager cleanup --older-than 90d --unread-only
```

### Export
```bash
# Export to CSV
newsletter-manager export --format csv --output newsletters.csv

# Export to JSON
newsletter-manager export --format json
```

## Configuration File

Location: `~/.gmail-newsletter-manager/config.yaml`

```yaml
# Add your own category
categories:
  MyCategory:
    keywords: [keyword1, keyword2, keyword3]
    domains: [example.com, newsletter.com]

# Adjust detection sensitivity
min_frequency_for_newsletter: 2  # emails per month
max_search_days: 90
batch_size: 100
```

## Multiple Accounts

```bash
# Use specific account
newsletter-manager --account work@company.com discover

# Or set environment variable
export GOG_ACCOUNT=work@company.com
newsletter-manager discover
```

## Common Workflows

### Initial Setup
```bash
newsletter-manager discover --days 90
newsletter-manager list
newsletter-manager report
newsletter-manager organize
```

### Weekly Maintenance
```bash
newsletter-manager discover --days 7
newsletter-manager organize
newsletter-manager cleanup --older-than 30d
```

### Monthly Review
```bash
newsletter-manager report
newsletter-manager recommend-unsubscribe
newsletter-manager export --format csv
```

## Troubleshooting

### gogcli not found
```bash
brew install steipete/tap/gogcli
```

### Authentication issues
```bash
gog auth status
gog auth add your@gmail.com
```

### Reset database
```bash
rm ~/.gmail-newsletter-manager/newsletters.db
newsletter-manager discover
```

## Help

```bash
# General help
newsletter-manager --help

# Command-specific help
newsletter-manager discover --help
newsletter-manager list --help
newsletter-manager organize --help
```

## File Locations

- **Config**: `~/.gmail-newsletter-manager/config.yaml`
- **Database**: `~/.gmail-newsletter-manager/newsletters.db`
- **Project**: `~/Development/gmail-newsletter-manager/`
- **Virtual Env**: `~/Development/gmail-newsletter-manager/venv/`

## Documentation

- **README.md** - Overview
- **docs/SETUP.md** - Detailed setup
- **docs/EXAMPLES.md** - Usage examples
- **docs/ARCHITECTURE.md** - Technical details
- **PROJECT_SUMMARY.md** - Project summary

## Tips

1. Always use `--dry-run` first for destructive operations
2. Run `discover` weekly to keep data fresh
3. Export monthly for backup
4. Customize categories in config.yaml
5. Use `--account` for multiple accounts

## Quick Stats

After running discover, check:
```bash
newsletter-manager stats
newsletter-manager report
```

## Environment

```bash
# Activate virtual environment
source ~/Development/gmail-newsletter-manager/venv/bin/activate

# Set account
export GOG_ACCOUNT=your@gmail.com

# Check installation
newsletter-manager --version
newsletter-manager --help
```
