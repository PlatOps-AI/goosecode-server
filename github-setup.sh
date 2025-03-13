#!/bin/bash
set -e

echo "================================================"
echo "GitHub Setup Script"
echo "================================================"

# Check if environment variables are set
echo "Checking environment variables..."

if [ -n "$GITHUB_TOKEN" ]; then
    echo "✓ GITHUB_TOKEN is set"
else
    echo "✗ GITHUB_TOKEN is not set. GitHub authentication will not work."
fi

if [ -n "$GIT_USER_NAME" ]; then
    echo "✓ GIT_USER_NAME is set to: $GIT_USER_NAME"
else
    echo "✗ GIT_USER_NAME is not set. Using default name."
    GIT_USER_NAME="VS Code Server User"
fi

if [ -n "$GIT_USER_EMAIL" ]; then
    echo "✓ GIT_USER_EMAIL is set to: $GIT_USER_EMAIL"
else
    echo "✗ GIT_USER_EMAIL is not set. Using default email."
    GIT_USER_EMAIL="vscode@example.com"
fi

# Configure Git user information (always do this regardless of token)
echo ""
echo "Configuring Git user information..."
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
echo "✓ Git user configured as: $GIT_USER_NAME <$GIT_USER_EMAIL>"

# Configure Git credentials if GITHUB_TOKEN is provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo ""
    echo "Configuring Git with GitHub token..."
    
    # Configure Git to use the token for https GitHub URLs
    git config --global url."https://${GITHUB_TOKEN}:@github.com/".insteadOf "https://github.com/"
    
    # Store credentials for 1 day (86400 seconds)
    git config --global credential.helper 'cache --timeout=86400'
    
    echo "✓ Git configured with GitHub token successfully!"
    
    # Configure GitHub CLI (gh) with the token
    echo ""
    echo "Configuring GitHub CLI..."
    
    # Create gh config directory if it doesn't exist
    mkdir -p ~/.config/gh
    
    # Create the hosts.yml file with authentication
    cat > ~/.config/gh/hosts.yml << EOF
github.com:
    oauth_token: ${GITHUB_TOKEN}
    user: ${GIT_USER_NAME}
    git_protocol: https
EOF
    
    echo "✓ GitHub CLI configured successfully!"
    echo ""
    echo "You can now use 'gh' commands, including creating PRs:"
    echo "  gh pr create --title 'Title' --body 'Description'"
    echo ""
    echo "You can also clone private repositories without authentication:"
    echo "  git clone https://github.com/username/private-repo.git"
else
    echo ""
    echo "⚠️ No GitHub token provided. You won't be able to access private repositories."
    echo "To fix this, restart the container with GITHUB_TOKEN set in your .env file."
fi

echo ""
echo "Git configuration summary:"
git config --global --list
echo "================================================"

# Continue with the container startup
exit 0 