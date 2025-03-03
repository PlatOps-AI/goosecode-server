#!/bin/bash
set -e

echo "Starting VS Code Server with Goose AI..."

# Run the GitHub setup script
/usr/local/bin/github-setup.sh

# Install VSCode extensions
echo "Installing Material icon themes..."
code-server --install-extension PKief.material-icon-theme >/dev/null 2>&1 || echo "Failed to install material-icon-theme extension"
code-server --install-extension PKief.material-product-icons >/dev/null 2>&1 || echo "Failed to install material-product-icons extension"

# Configure Goose
echo "Configuring Goose..."

# Create config directory
mkdir -p $HOME/.config/goose

# Create config file with the exact YAML format
cat > $HOME/.config/goose/config.yaml << EOF
GOOSE_PROVIDER: openai
extensions:
  developer:
    enabled: true
    name: developer
    type: builtin
GOOSE_MODE: auto
GOOSE_MODEL: o3-mini-2025-01-31
OPENAI_BASE_PATH: v1/chat/completions
OPENAI_HOST: https://api.openai.com
EOF

# Add only the API key to bashrc for persistence
grep -q "OPENAI_API_KEY" $HOME/.bashrc || {
  echo '
# Goose API key
export OPENAI_API_KEY="'$OPENAI_API_KEY'"
' >> $HOME/.bashrc
}

echo "✅ Goose configured successfully with YAML configuration"

# Create workspace README
if [ ! -f /workspace/README.md ]; then
  cat > /workspace/README.md << EOF
# Goosecode Server Workspace

Welcome to your VS Code Server workspace with Goose AI assistant integration.

<div align="center">
  <img src="./static/img/logo.png" alt="Goose AI Logo" width="200">
</div>

## Getting Started with Goose

1. **Open a terminal** in VS Code Server (Terminal → New Terminal)
2. **Start a Goose session**:
   \`\`\`bash
   goose session
   \`\`\`
3. **Begin collaborating** with Goose by typing your questions or instructions


## Troubleshooting

If you encounter any issues:

| Issue | Solution |
|-------|----------|
| Configuration Check | \`cat ~/.config/goose/config.yaml\` |
| Configuration Wizard | \`goose configure\` |
| API Key Verification | Check that your OpenAI API key is set correctly |
| Session Restart | Exit and restart your Goose session |

## Useful Commands

- List available models: \`goose model list\`
- Show Goose version: \`goose --version\`
- View Goose help: \`goose --help\`

---

Documentation: [Goose AI Documentation](https://goose.ai/docs)
EOF
fi

# Create a workspace configuration file to automatically open README.md in preview
mkdir -p /workspace/.vscode
cat > /workspace/.vscode/settings.json << EOF
{
    "workbench.startupEditor": "none",
    "workbench.editorAssociations": {
        "README.md": "vscode.markdown.preview.editor"
    }
}
EOF

# Create a workspace tasks configuration to open README.md on startup
cat > /workspace/.vscode/tasks.json << EOF
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Open README in preview",
            "type": "shell",
            "command": "sleep 2 && code-server /workspace/README.md -r",
            "runOptions": {
                "runOn": "folderOpen"
            },
            "presentation": {
                "reveal": "never",
                "focus": false
            }
        },
        {
            "label": "Start Goose Session",
            "type": "shell",
            "command": "sleep 3 && echo 'Starting Goose AI session...' && goose session",
            "runOptions": {
                "runOn": "folderOpen"
            },
            "presentation": {
                "reveal": "always",
                "focus": true,
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}
EOF

# Create a keybindings file to automatically open terminal on startup
cat > /workspace/.vscode/keybindings.json << EOF
[
    {
        "key": "ctrl+shift+alt+t",
        "command": "workbench.action.terminal.new",
        "when": "workbench.state == 'started'"
    }
]
EOF

# Create a workspace welcome script to trigger terminal operations
mkdir -p /workspace/.vscode/scripts
cat > /workspace/.vscode/scripts/welcome.js << EOF
const vscode = require('vscode');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // Wait for VS Code to fully load
    setTimeout(() => {
        vscode.commands.executeCommand('workbench.action.terminal.new').then(() => {
            vscode.window.activeTerminal.sendText('echo "Welcome to Goosecode Server!"');
            vscode.window.activeTerminal.sendText('echo "Starting Goose AI session..."');
            vscode.window.activeTerminal.sendText('goose session');
        });
    }, 3000);
}

module.exports = { activate };
EOF

# Create code-server config with password
mkdir -p $HOME/.config/code-server
cat > $HOME/.config/code-server/config.yaml << EOF
bind-addr: 0.0.0.0:8080
auth: password
password: ${PASSWORD}
cert: false
disable-telemetry: true
disable-update-check: true
user-data-dir: $HOME/.local/share/code-server
extensions-dir: $HOME/.local/share/code-server/extensions
EOF

# Start VS Code Server
echo "Starting code-server..."
exec code-server --config $HOME/.config/code-server/config.yaml /workspace 