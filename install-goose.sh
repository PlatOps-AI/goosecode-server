#!/bin/bash
# Simplified Goose installation script

set -e

echo "=== Installing Goose AI Agent ==="

# Install dependencies
echo "Installing dependencies..."
apt-get update && apt-get install -y bzip2 libdbus-1-3

# Download and install Goose
echo "Downloading and installing Goose..."
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash

# Move Goose to standard location
if [ -f "$HOME/.local/bin/goose" ]; then
  cp "$HOME/.local/bin/goose" /usr/local/bin/goose
  chmod +x /usr/local/bin/goose
elif [ -f "/root/.local/bin/goose" ]; then
  cp "/root/.local/bin/goose" /usr/local/bin/goose
  chmod +x /usr/local/bin/goose
fi

# Verify installation
if ! command -v goose &> /dev/null; then
  echo "ERROR: Installation failed."
  exit 1
fi

echo "Goose installed: $(goose --version)"

echo "=== Installation Complete ==="
echo "Start a Goose session with: goose session"
echo ""

exit 0 