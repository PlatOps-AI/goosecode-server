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

# Set the API key
if [ -n "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY: $OPENAI_API_KEY" >> $HOME/.config/goose/config.yaml
  echo "API key configured."
else
  echo "Warning: OPENAI_API_KEY not set. Goose will not function correctly."
fi

# Shared terminal variables
CONTROLLER_SESSION="goose-controller"
WINDOW_NAME="goose"

# Setup shared terminal with tmux
if [ "$ENABLE_TERMINAL_SHARING" = "true" ]; then
  echo "Setting up shared terminal with Goose..."
  
  # Create an improved tmux config for better multi-user experience
  cat > $HOME/.tmux.conf << EOF
# Set a more accessible prefix key
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# Enable mouse support (but don't rely on it for scrolling independence)
set -g mouse on

# Increase history limit
set-option -g history-limit 100000

# Set the default terminal mode
set -g default-terminal "screen-256color"

# Status bar customization with session name
set -g status-style bg=black,fg=green
set -g status-left "[#S] "
set -g status-right "#{?client_prefix,#[reverse]<Prefix>#[noreverse] ,}%H:%M"

# Window status
set-window-option -g window-status-current-style bg=green,fg=black,bold

# Improve terminal responsiveness
set -sg escape-time 0

# When in scroll mode, use vi keys
setw -g mode-keys vi

# Make copy mode more accessible
bind v copy-mode
bind [ copy-mode
bind C-u copy-mode -u

# Set terminal-overrides to enable better scrolling
set -g terminal-overrides 'xterm*:smcup@:rmcup@'

# Disable automatic renaming of windows
set -g allow-rename off
set -g set-titles on
set -g set-titles-string "#T"
EOF

  # Create shared session script
  cat > $HOME/shared-goose.sh << EOF
#!/bin/bash

# The main session name that runs the actual command
CONTROLLER_SESSION="goose-controller"
# Window name within the controller session
WINDOW_NAME="goose"

# Generate a unique session name for this client
CLIENT_SESSION="goose-client-\$(date +%s)-\$\$"

# Start by checking if the controller session exists
if ! tmux has-session -t "\$CONTROLLER_SESSION" 2>/dev/null; then
    # Create the controller session with a window named "goose"
    tmux new-session -d -s "\$CONTROLLER_SESSION" -n "\$WINDOW_NAME"
    
    # Start Goose directly without the intro messages
    tmux send-keys -t "\$CONTROLLER_SESSION:\$WINDOW_NAME" "clear && goose session" C-m
fi

# Create a new client session linked to the controller session's window
tmux new-session -d -s "\$CLIENT_SESSION" -t "\$CONTROLLER_SESSION:\$WINDOW_NAME"

# Set a custom status line that reminds the user which client they're on
tmux set-option -t "\$CLIENT_SESSION" status-left "[#S] "

# Attach to our new client-specific session
exec tmux attach-session -t "\$CLIENT_SESSION"
EOF
  chmod +x $HOME/shared-goose.sh
  
  # Create a read-only script using the same session linking approach
  cat > $HOME/goose-view.sh << 'EOF'
#!/bin/bash

# The main session name that runs the actual command
CONTROLLER_SESSION="goose-controller"
# Window name within the controller session
WINDOW_NAME="goose"

# Generate a unique session name for this viewer
VIEWER_SESSION="goose-viewer-$(date +%s)-$$"

# Start by checking if the controller session exists
if ! tmux has-session -t "$CONTROLLER_SESSION" 2>/dev/null; then
    # Start a new interactive session if controller doesn't exist
    $HOME/shared-goose.sh
    exit
fi

# Create a new client session linked to the controller session's window
tmux new-session -d -s "$VIEWER_SESSION" -t "$CONTROLLER_SESSION:$WINDOW_NAME"

# Set status line to indicate view-only mode
tmux set-option -t "$VIEWER_SESSION" status-style "bg=black,fg=yellow"
tmux set-option -t "$VIEWER_SESSION" status-left "[READ-ONLY] "

# Attach in read-only mode
exec tmux attach-session -t "$VIEWER_SESSION" -r
EOF
  chmod +x $HOME/goose-view.sh

  # We no longer need a hook script since VS Code will use the default terminal profile
  # which is already configured to use shared-goose.sh

  echo "Shared terminal with Goose setup complete."
fi

echo "✅ Goose configured successfully"

# Create workspace README
if [ ! -f /workspace/README.md ]; then
  cat > /workspace/README.md << EOF
# Goosecode Server Workspace

Welcome to your VS Code Server workspace with Goose AI assistant integration.

<div align="center">
  <img src="./static/img/logo.png" alt="Goose AI Logo" width="200">
</div>

## Shared Goose Terminal

This workspace automatically starts a shared terminal with Goose AI running.
All browser windows connected to this server will see the same terminal session.


## Troubleshooting

| Issue | Solution |
|-------|----------|
| Configuration Check | \`cat ~/.config/goose/config.yaml\` |
| Configuration Wizard | \`goose configure\` |
| API Key Verification | Check that your OpenAI API key is set correctly |
| Start New Session | Run \`~/shared-goose.sh\` to create a new client session |
| Get Session Name | Look at your tmux status bar for your session name |
| Read-Only Access | Use \`~/goose-view.sh\` to connect without typing ability |

---

Documentation: [Goose AI Documentation](https://block.github.io/goose/docs/category/getting-started)
EOF
fi

# Create a workspace configuration file
mkdir -p /workspace/.vscode
cat > /workspace/.vscode/settings.json << EOF
{
    "workbench.startupEditor": "none",
    "terminal.integrated.defaultProfile.linux": "shared-goose",
    "terminal.integrated.profiles.linux": {
        "shared-goose": {
            "path": "bash",
            "args": ["-c", "~/shared-goose.sh"]
        },
        "goose-view": {
            "path": "bash",
            "args": ["-c", "~/goose-view.sh"]
        },
        "bash": {
            "path": "bash",
            "icon": "terminal-bash"
        }
    }
}
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

# Start the shared Goose session before launching VS Code
if [ "$ENABLE_TERMINAL_SHARING" = "true" ]; then
  echo "Starting shared Goose controller session..."
  # Initialize the controller session in the background
  # but don't connect to it yet - VS Code will do that with the default terminal
  tmux has-session -t "$CONTROLLER_SESSION" 2>/dev/null || {
    tmux new-session -d -s "$CONTROLLER_SESSION" -n "$WINDOW_NAME"
    tmux send-keys -t "$CONTROLLER_SESSION:$WINDOW_NAME" "clear && goose session" C-m
  }
  echo "Shared Goose controller session ready. VS Code will open it automatically."
  echo "For additional terminals, use regular bash (independent) or manually run ~/shared-goose.sh to connect to shared session."
fi

# Start VS Code Server
echo "Starting code-server..."
exec code-server --config $HOME/.config/code-server/config.yaml /workspace 