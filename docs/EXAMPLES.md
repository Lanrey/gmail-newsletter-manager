# Examples

## Setup

First, ensure gogcli is installed and authenticated:

```bash
# Install gogcli
brew install steipete/tap/gogcli

# Authenticate with your Gmail account
gog auth add your@gmail.com

# Set your default account
export GOG_ACCOUNT=your@gmail.com
```

Install newsletter-manager:

```bash
cd gmail-newsletter-manager
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Basic Workflow

### 1. Discover Newsletters

Scan your inbox to find all newsletters:

```bash
# Scan the last 90 days (default)
newsletter-manager discover

# Scan the last 30 days with fewer messages
newsletter-manager discover --days 30 --max-results 200

# Scan with custom minimum frequency
newsletter-manager discover --days 90 --min-frequency 3
```

Output:
```
Discovering newsletters from the last 90 days...
✓ Discovered 45 newsletters from 1,234 messages
Scan took 23.4 seconds

Summary:
  Total newsletters: 45
  Auto-categorized: 32
  Uncategorized: 13
```

### 2. List Newsletters

View all detected newsletters:

```bash
# List all newsletters
newsletter-manager list

# Filter by category
newsletter-manager list --category Tech

# Show only with unread messages
newsletter-manager list --unread-only

# Sort by count
newsletter-manager list --sort count
```

Example output:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Sender                    ┃ Category  ┃ Count ┃ Unread ┃ Last Seen  ┃ Platform      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ TechCrunch Daily          │ Tech      │    87 │     12 │ 2026-01-30 │ mailchimp.com │
│ Morning Brew              │ Business  │    65 │      3 │ 2026-01-30 │ substack.com  │
│ Python Weekly             │ Tech      │    52 │     25 │ 2026-01-29 │ -             │
└───────────────────────────┴───────────┴───────┴────────┴────────────┴───────────────┘
```

### 3. View Statistics

```bash
# Overall statistics
newsletter-manager stats

# Detailed report
newsletter-manager report

# With custom period
newsletter-manager report --period 60d
```

### 4. Organize Newsletters

Create labels and organize newsletters:

```bash
# Preview what would be organized (dry run)
newsletter-manager organize --dry-run

# Actually organize newsletters
newsletter-manager organize

# Organize without auto-categorization
newsletter-manager organize --no-auto-categorize
```

This creates a label hierarchy like:
```
Newsletters/
├── Tech/
├── Business/
├── News/
├── Finance/
└── Design/
```

### 5. Get Unsubscribe Recommendations

Find newsletters you never read:

```bash
newsletter-manager recommend-unsubscribe
```

Output:
```
Unsubscribe Recommendations

Never Read (8 newsletters):
  • Marketing Daily (15 messages, 0 read)
  • Sales Tips Weekly (12 messages, 0 read)
  • Product Updates (10 messages, 0 read)

Rarely Read (5 newsletters):
  • Design Inspiration (25 messages, 8% read)
  • Startup News (18 messages, 11% read)
```

### 6. Cleanup Old Newsletters

Archive or delete old newsletters:

```bash
# Preview cleanup (dry run)
newsletter-manager cleanup --older-than 30d --dry-run

# Actually cleanup
newsletter-manager cleanup --older-than 30d

# Cleanup only unread
newsletter-manager cleanup --older-than 90d --unread-only
```

### 7. Export Newsletter List

Export your newsletters to CSV or JSON:

```bash
# Export to CSV
newsletter-manager export --format csv --output my-newsletters.csv

# Export to JSON
newsletter-manager export --format json --output my-newsletters.json
```

## Advanced Usage

### Using with Multiple Accounts

```bash
# Specify account per command
newsletter-manager --account work@company.com discover
newsletter-manager --account personal@gmail.com list

# Or use environment variable
export GOG_ACCOUNT=work@company.com
newsletter-manager discover
```

### Custom Configuration

Edit `~/.gmail-newsletter-manager/config.yaml`:

```yaml
categories:
  Tech:
    keywords: [programming, developer, tech, software, ai, ml]
    domains: [dev.to, hashnode.com, medium.com]
  
  MyCustomCategory:
    keywords: [custom, keywords]
    domains: [example.com]

# Adjust detection sensitivity
min_frequency_for_newsletter: 3  # Require at least 3 emails per month

# Adjust scan limits
max_search_days: 120
batch_size: 200
```

### Workflow Example

Complete workflow for a new setup:

```bash
# 1. Initial discovery
newsletter-manager discover --days 90

# 2. Review what was found
newsletter-manager list

# 3. Check the report
newsletter-manager report

# 4. Get unsubscribe recommendations
newsletter-manager recommend-unsubscribe

# 5. Organize into labels (preview first)
newsletter-manager organize --dry-run
newsletter-manager organize

# 6. Export for backup
newsletter-manager export --format csv

# 7. Cleanup old newsletters
newsletter-manager cleanup --older-than 60d --dry-run
newsletter-manager cleanup --older-than 60d
```

## Automation

### Weekly Newsletter Cleanup

Create a script for weekly maintenance:

```bash
#!/bin/bash
# weekly-newsletter-cleanup.sh

source ~/Development/gmail-newsletter-manager/venv/bin/activate
export GOG_ACCOUNT=your@gmail.com

echo "=== Weekly Newsletter Cleanup ==="
echo

echo "1. Discovering new newsletters..."
newsletter-manager discover --days 7

echo
echo "2. Organizing newsletters..."
newsletter-manager organize

echo
echo "3. Cleaning up old newsletters..."
newsletter-manager cleanup --older-than 30d

echo
echo "4. Generating report..."
newsletter-manager report

echo
echo "=== Done! ==="
```

Make it executable and add to cron:

```bash
chmod +x weekly-newsletter-cleanup.sh

# Add to crontab (run every Sunday at 9 AM)
# crontab -e
# 0 9 * * 0 /path/to/weekly-newsletter-cleanup.sh
```

## Troubleshooting

### gogcli not found

```bash
# Install gogcli
brew install steipete/tap/gogcli

# Or build from source
git clone https://github.com/steipete/gogcli.git
cd gogcli
make
```

### Authentication issues

```bash
# Check authentication status
gog auth status

# List accounts
gog auth list

# Re-authenticate
gog auth add your@gmail.com
```

### Database issues

```bash
# Database is stored in ~/.gmail-newsletter-manager/newsletters.db
# To reset, simply remove it:
rm ~/.gmail-newsletter-manager/newsletters.db

# Then re-discover:
newsletter-manager discover
```

### Rate limiting

If you hit Gmail API rate limits:

1. Reduce `--max-results` when discovering
2. Scan smaller time windows with `--days`
3. Wait a few minutes between operations

## Tips

1. **Regular Scans**: Run `discover` weekly to keep database up to date
2. **Backup Exports**: Export your newsletter list monthly for backup
3. **Review Recommendations**: Check unsubscribe recommendations quarterly
4. **Custom Categories**: Add your own categories in config.yaml
5. **Dry Run First**: Always use `--dry-run` for destructive operations
