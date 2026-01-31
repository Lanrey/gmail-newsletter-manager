#!/bin/bash
# Quick start script for Gmail Newsletter Manager

set -e

echo "===================================="
echo "Gmail Newsletter Manager - Setup"
echo "===================================="
echo

# Check if gogcli is installed
if ! command -v gog &> /dev/null; then
    echo "❌ gogcli is not installed"
    echo
    echo "Please install gogcli first:"
    echo "  brew install steipete/tap/gogcli"
    echo
    echo "Or build from source:"
    echo "  git clone https://github.com/steipete/gogcli.git"
    echo "  cd gogcli && make"
    exit 1
fi

echo "✅ gogcli is installed"
echo

# Check if authenticated
if ! gog auth list &> /dev/null; then
    echo "⚠️  No Gmail accounts authenticated"
    echo
    read -p "Enter your Gmail address: " gmail_address
    echo
    echo "Setting up authentication for $gmail_address..."
    echo "This will open your browser for OAuth authorization."
    echo
    gog auth add "$gmail_address"
    echo
    echo "✅ Authentication successful"
    export GOG_ACCOUNT="$gmail_address"
else
    echo "✅ Gmail account(s) authenticated"
    # Try to get account from environment or ask user
    if [ -z "$GOG_ACCOUNT" ]; then
        echo
        echo "Available accounts:"
        gog auth list
        echo
        read -p "Enter the Gmail account to use (or press Enter to use default): " gmail_address
        if [ -n "$gmail_address" ]; then
            export GOG_ACCOUNT="$gmail_address"
        fi
    fi
fi

echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or upgrade package
echo "Installing newsletter-manager..."
pip install -e . -q
echo "✅ newsletter-manager installed"
echo

# Verify installation
echo "Verifying installation..."
if newsletter-manager --help &> /dev/null; then
    echo "✅ Installation successful"
else
    echo "❌ Installation verification failed"
    exit 1
fi

echo
echo "===================================="
echo "Setup Complete! 🎉"
echo "===================================="
echo
echo "Quick start commands:"
echo
echo "  # Discover newsletters (scan last 30 days)"
echo "  newsletter-manager discover --days 30"
echo
echo "  # List all newsletters"
echo "  newsletter-manager list"
echo
echo "  # View statistics"
echo "  newsletter-manager stats"
echo
echo "  # Get full help"
echo "  newsletter-manager --help"
echo
echo "For detailed documentation, see:"
echo "  - docs/SETUP.md (detailed setup guide)"
echo "  - docs/EXAMPLES.md (usage examples)"
echo "  - README.md (feature overview)"
echo
echo "Note: Remember to activate the virtual environment:"
echo "  source venv/bin/activate"
echo
