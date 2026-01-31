# Gmail Newsletter Manager - Setup Guide

## Prerequisites

### 1. Install gogcli

**Option A: Using Homebrew (macOS)**
```bash
brew install steipete/tap/gogcli
```

**Option B: Build from Source**
```bash
git clone https://github.com/steipete/gogcli.git
cd gogcli
make
# Add to PATH or use ./bin/gog
```

### 2. Set Up Google Cloud Project

Follow these steps to enable Gmail API access:

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/projectcreate)
   - Create a new project (e.g., "Newsletter Manager")

2. **Enable Gmail API**
   - Visit [Gmail API Page](https://console.cloud.google.com/apis/api/gmail.googleapis.com)
   - Click "Enable"

3. **Configure OAuth Consent Screen**
   - Go to [OAuth Consent Screen](https://console.cloud.google.com/auth/branding)
   - Select "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email as a test user

4. **Create OAuth Client**
   - Go to [Credentials](https://console.cloud.google.com/auth/clients)
   - Click "Create Credentials" > "OAuth Client ID"
   - Application type: "Desktop app"
   - Name it "Newsletter Manager"
   - Download the JSON file (it will be named something like `client_secret_...json`)

### 3. Authenticate gogcli

```bash
# Store your OAuth credentials
gog auth credentials ~/Downloads/client_secret_*.json

# Authenticate with your Gmail account
gog auth add your@gmail.com

# This will open a browser window for OAuth authorization
# Grant the necessary permissions

# Verify authentication
gog auth status

# Set default account (optional but recommended)
export GOG_ACCOUNT=your@gmail.com
# Add to your ~/.zshrc or ~/.bashrc to make it permanent
echo 'export GOG_ACCOUNT=your@gmail.com' >> ~/.zshrc
```

## Installation

### Option 1: From Source (Recommended for Development)

```bash
# Clone or navigate to the project
cd ~/Development/gmail-newsletter-manager

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install in editable mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Option 2: Using pipx (Recommended for Usage)

```bash
# Install pipx if you haven't
brew install pipx

# Install newsletter-manager
pipx install /path/to/gmail-newsletter-manager
```

## Verification

Test that everything is working:

```bash
# Activate virtual environment (if using Option 1)
source venv/bin/activate

# Check newsletter-manager is installed
newsletter-manager --help

# Should show:
# Usage: newsletter-manager [OPTIONS] COMMAND [ARGS]...
#   Gmail Newsletter Manager - Intelligent newsletter management.
```

## First Run

### 1. Initialize Configuration

On first run, the tool will create default configuration:

```bash
newsletter-manager discover --days 7
```

This creates `~/.gmail-newsletter-manager/config.yaml` with default settings.

### 2. Customize Configuration (Optional)

Edit the configuration file:

```bash
# Open in your preferred editor
vim ~/.gmail-newsletter-manager/config.yaml
# or
code ~/.gmail-newsletter-manager/config.yaml
```

Example customization:

```yaml
categories:
  Tech:
    keywords: [programming, developer, tech, software, coding, devops, cloud, ai, ml]
    domains: [dev.to, hashnode.com, medium.com, hackernoon.com]
  
  Business:
    keywords: [business, entrepreneur, startup, marketing, sales, growth]
    domains: [inc.com, entrepreneur.com, hbr.org]
  
  # Add your own categories
  Crypto:
    keywords: [bitcoin, ethereum, crypto, blockchain, web3, defi]
    domains: [coindesk.com, cointelegraph.com]
  
  Personal-Development:
    keywords: [productivity, habits, mindfulness, self-improvement, learning]
    domains: [jamesclear.com, markmanson.net]

# Adjust detection sensitivity
min_frequency_for_newsletter: 2  # Minimum emails per month
max_search_days: 90
batch_size: 100

# Auto-archive settings
auto_archive_days: 30
```

### 3. Initial Discovery

Run your first full scan:

```bash
# Scan the last 90 days
newsletter-manager discover --days 90 --max-results 500

# This will:
# 1. Search your Gmail for potential newsletters
# 2. Analyze each message
# 3. Auto-categorize when possible
# 4. Store results in local database
```

Expected output:
```
Discovering newsletters from the last 90 days...
✓ Discovered 45 newsletters from 1,234 messages
Scan took 23.4 seconds

Summary:
  Total newsletters: 45
  Auto-categorized: 32
  Uncategorized: 13
```

### 4. Review Results

```bash
# List all newsletters
newsletter-manager list

# See statistics
newsletter-manager stats

# Generate report
newsletter-manager report
```

## Quick Start Workflow

```bash
# 1. Discover newsletters
newsletter-manager discover

# 2. Review what was found
newsletter-manager list

# 3. Get recommendations for newsletters to unsubscribe from
newsletter-manager recommend-unsubscribe

# 4. Organize newsletters into labels
newsletter-manager organize --dry-run  # Preview first
newsletter-manager organize            # Actually organize

# 5. Export for backup
newsletter-manager export --format csv

# 6. Cleanup old newsletters
newsletter-manager cleanup --older-than 30d --dry-run
newsletter-manager cleanup --older-than 30d
```

## Multiple Accounts

If you have multiple Gmail accounts:

```bash
# Add additional accounts to gogcli
gog auth add work@company.com
gog auth add personal@gmail.com

# Use specific account
newsletter-manager --account work@company.com discover
newsletter-manager --account personal@gmail.com list

# Or set different account in environment
export GOG_ACCOUNT=work@company.com
newsletter-manager discover
```

Each account maintains separate data in the database.

## Troubleshooting

### "gogcli is not installed"

```bash
# Check if gog command is available
which gog

# If not found, install:
brew install steipete/tap/gogcli
```

### "Authentication failed"

```bash
# Check auth status
gog auth status

# List authenticated accounts
gog auth list

# Try re-authenticating
gog auth add your@gmail.com

# Verify tokens
gog auth list --check
```

### "Rate limit exceeded"

Gmail API has rate limits. If you hit them:

1. Wait a few minutes
2. Reduce `--max-results` parameter
3. Scan smaller time windows with `--days`

```bash
# Instead of scanning 90 days at once:
newsletter-manager discover --days 90 --max-results 1000

# Try scanning in smaller chunks:
newsletter-manager discover --days 30 --max-results 300
```

### "No newsletters found"

This could mean:
1. You genuinely don't have newsletters (rare!)
2. The search query needs adjustment
3. Messages aren't being classified correctly

Try:
```bash
# Lower the frequency threshold
# Edit ~/.gmail-newsletter-manager/config.yaml
# Set: min_frequency_for_newsletter: 1

# Then re-scan
newsletter-manager discover
```

### Database Issues

If you encounter database errors:

```bash
# Backup current database
cp ~/.gmail-newsletter-manager/newsletters.db ~/.gmail-newsletter-manager/newsletters.db.backup

# Remove database (will lose history)
rm ~/.gmail-newsletter-manager/newsletters.db

# Re-discover
newsletter-manager discover
```

## Uninstallation

```bash
# If installed with pipx
pipx uninstall gmail-newsletter-manager

# If installed in venv
pip uninstall gmail-newsletter-manager

# Remove configuration and database (optional)
rm -rf ~/.gmail-newsletter-manager
```

## Next Steps

- See [EXAMPLES.md](EXAMPLES.md) for detailed usage examples
- See [README.md](../README.md) for feature overview
- Check the configuration file for customization options

## Getting Help

Common commands to get help:

```bash
# General help
newsletter-manager --help

# Help for specific command
newsletter-manager discover --help
newsletter-manager list --help
newsletter-manager organize --help
```

## Tips for Best Results

1. **Run Regular Scans**: Schedule weekly scans to keep data fresh
2. **Customize Categories**: Add your own categories in config.yaml
3. **Use Dry Run**: Always preview with `--dry-run` before destructive operations
4. **Export Regularly**: Back up your newsletter list monthly
5. **Review Recommendations**: Check unsubscribe suggestions quarterly
6. **Start Small**: Begin with `--days 30` to test, then expand to 90 days
