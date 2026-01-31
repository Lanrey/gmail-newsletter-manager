# Installation Guide

This guide will walk you through installing and setting up Gmail Newsletter Manager.

## Table of Contents

- [System Requirements](#system-requirements)
- [Step 1: Install Python](#step-1-install-python)
- [Step 2: Install gogcli](#step-2-install-gogcli)
- [Step 3: Get OAuth Credentials](#step-3-get-oauth-credentials)
- [Step 4: Install Gmail Newsletter Manager](#step-4-install-gmail-newsletter-manager)
- [Step 5: Initial Configuration](#step-5-initial-configuration)
- [Troubleshooting](#troubleshooting)

## System Requirements

- **Operating System**: macOS, Linux, or Windows (with WSL)
- **Python**: 3.8 or higher
- **Go**: 1.19 or higher (for building gogcli from source)
- **Git**: For cloning the repository

## Step 1: Install Python

### macOS

```bash
# Using Homebrew
brew install python@3.11

# Verify installation
python3 --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.11 python3-pip python3-venv

# Verify installation
python3 --version
```

### Windows (WSL)

Follow the Linux instructions after setting up WSL.

## Step 2: Install gogcli

[gogcli](https://github.com/steipete/gogcli) is a command-line interface for Google APIs.

### Option A: Install via Homebrew (macOS/Linux)

```bash
brew install steipete/tap/gogcli

# Verify installation
gog version
```

### Option B: Install from Source

```bash
# Install Go if not already installed
brew install go  # macOS
# or
sudo apt install golang  # Linux

# Install gogcli
go install github.com/steipete/gogcli/cmd/gog@latest

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$PATH:$(go env GOPATH)/bin"

# Verify installation
gog version
```

## Step 3: Get OAuth Credentials

You need Google OAuth 2.0 credentials to access Gmail API.

### 3.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "Newsletter Manager")
4. Click "Create"

### 3.2 Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click "Enable"

### 3.3 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "Newsletter Manager"
   - User support email: Your email
   - Developer contact: Your email
   - Add scope: `https://www.googleapis.com/auth/gmail.modify`
4. For "Application type", select "Desktop app"
5. Name it "Newsletter Manager Desktop"
6. Click "Create"
7. Download the JSON file

### 3.4 Configure gogcli with Credentials

```bash
# Set the credentials file
gog auth credentials set /path/to/downloaded-credentials.json

# Add your Gmail account
gog auth add your.email@gmail.com
```

This will open a browser for authentication. Grant the necessary permissions.

### 3.5 Verify Authentication

```bash
# List authenticated accounts
gog auth list

# Test Gmail access
gog gmail search "in:inbox" --max 1
```

## Step 4: Install Gmail Newsletter Manager

### Option A: Install from PyPI (Coming Soon)

```bash
pip install gmail-newsletter-manager
```

### Option B: Install from Source (Current Method)

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/gmail-newsletter-manager.git
cd gmail-newsletter-manager

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install the package
pip install -e .

# Verify installation
newsletter-manager --help
```

### For Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests to verify everything works
pytest
```

## Step 5: Initial Configuration

### 5.1 Create Configuration Directory

The configuration directory is created automatically on first run, but you can create it manually:

```bash
mkdir -p ~/.gmail-newsletter-manager
```

### 5.2 Copy Example Configuration

```bash
cp config.example.yaml ~/.gmail-newsletter-manager/config.yaml
```

### 5.3 Edit Configuration

```bash
nano ~/.gmail-newsletter-manager/config.yaml
```

Update the following:

```yaml
# Add your Gmail account(s)
accounts:
  - your.email@gmail.com

# Set default account
default_account: your.email@gmail.com

# Customize categories if desired
categories:
  Technology:
    - tech
    - programming
  # Add more...
```

### 5.4 Add Your Gmail Account to Newsletter Manager

```bash
# Add account
newsletter-manager account add your.email@gmail.com

# Set as default
newsletter-manager account set-default your.email@gmail.com

# Verify
newsletter-manager account list
```

## First Run

Now you're ready to discover newsletters!

```bash
# Scan last 90 days for newsletters
newsletter-manager discover

# View discovered newsletters
newsletter-manager list

# Apply labels to organize them
newsletter-manager apply-labels
```

## Troubleshooting

### gogcli Not Found

```bash
# Check if gog is in PATH
which gog

# If not, add Go bin to PATH
export PATH="$PATH:$(go env GOPATH)/bin"

# Add to ~/.bashrc or ~/.zshrc to make permanent
echo 'export PATH="$PATH:$(go env GOPATH)/bin"' >> ~/.zshrc
```

### Authentication Errors

```bash
# Check authentication status
gog auth list

# Re-authenticate if needed
gog auth add your.email@gmail.com

# Clear and re-authenticate
gog auth logout your.email@gmail.com
gog auth add your.email@gmail.com
```

### Permission Denied Errors

```bash
# Ensure OAuth consent screen includes Gmail scope
# Re-create OAuth credentials if necessary
# Make sure you grant all requested permissions during auth flow
```

### "No newsletters found"

This could mean:
- Your account doesn't have newsletters (check manually)
- Detection threshold is too strict (lower `min_frequency` in config)
- Need to scan more days or all emails:
  ```bash
  newsletter-manager discover --all --max-results 10000
  ```

### Database Errors

```bash
# Remove and recreate database
rm ~/.gmail-newsletter-manager/newsletters.db
newsletter-manager discover
```

### ImportError or ModuleNotFoundError

```bash
# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall
```

## Upgrading

### From Source

```bash
cd gmail-newsletter-manager
git pull origin main
pip install -e . --upgrade
```

### From PyPI (When Available)

```bash
pip install --upgrade gmail-newsletter-manager
```

## Uninstalling

```bash
# Uninstall package
pip uninstall gmail-newsletter-manager

# Remove configuration (optional)
rm -rf ~/.gmail-newsletter-manager

# Revoke OAuth access (optional)
# Go to: https://myaccount.google.com/permissions
# Find "Newsletter Manager" and revoke access
```

## Next Steps

- Read the [README](README.md) for usage examples
- Check [EXAMPLES](docs/EXAMPLES.md) for common workflows
- Read [CONTRIBUTING](CONTRIBUTING.md) if you want to contribute
- Report issues on [GitHub Issues](https://github.com/YOUR-USERNAME/gmail-newsletter-manager/issues)

## Getting Help

- **Documentation**: [README.md](README.md)
- **Examples**: [docs/EXAMPLES.md](docs/EXAMPLES.md)
- **Issues**: [GitHub Issues](https://github.com/YOUR-USERNAME/gmail-newsletter-manager/issues)
- **Email**: olusolaakinsulere@gmail.com
