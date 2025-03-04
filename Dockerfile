FROM codercom/code-server:latest

USER root

# Create a workspace directory at root level
RUN mkdir -p /workspace
WORKDIR /workspace

# Install dependencies including those needed for Goose
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bzip2 \
    libdbus-1-3 \
    sudo \
    expect \
    tmux \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy goose-api requirements.txt for dependency installation
COPY ./goose-api/requirements.txt /tmp/requirements.txt

# Set up a Python virtual environment for the Goose API
RUN python3 -m venv /opt/goose-api-venv
ENV PATH="/opt/goose-api-venv/bin:$PATH"
RUN pip3 install --upgrade pip && pip3 install -r /tmp/requirements.txt

# Install Goose AI agent (simple one-step process)
RUN curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash \
    && chmod +x /root/.local/bin/goose \
    && mv /root/.local/bin/goose /usr/local/bin/goose

# Add the coder user to sudoers
RUN echo "coder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Copy scripts and static files
COPY ./github-setup.sh /usr/local/bin/github-setup.sh
RUN chmod +x /usr/local/bin/github-setup.sh

COPY ./install-goose.sh /usr/local/bin/install-goose.sh
RUN chmod +x /usr/local/bin/install-goose.sh

COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy static resources
COPY ./static /workspace/static
RUN chmod -R 755 /workspace/static

# Copy goose-api directory
COPY ./goose-api /workspace/goose-api
RUN chmod +x /workspace/goose-api/docker-integration.sh
RUN chmod -R +x /workspace/goose-api/examples/

# Create configuration directories
RUN mkdir -p /home/coder/.local/share/code-server/User/
RUN mkdir -p /home/coder/.config/code-server/

# Create settings.json with dark theme and material icons configuration
RUN echo '{ \
    "workbench.colorTheme": "Default Dark+", \
    "workbench.iconTheme": "material-icon-theme", \
    "workbench.productIconTheme": "material-product-icons", \
    "workbench.colorCustomizations": { \
        "editor.background": "#1e1e1e", \
        "sideBar.background": "#1e1e1e", \
        "activityBar.background": "#1e1e1e", \
        "terminal.background": "#1e1e1e", \
        "statusBar.background": "#1e1e1e", \
        "editor.foreground": "#e0e0e0", \
        "editor.selectionBackground": "#515c6a", \
        "editorCursor.foreground": "#00ff33", \
        "panel.background": "#1e1e1e" \
    }, \
    "workbench.startupEditor": "none", \
    "workbench.settings.editor": "json", \
    "editor.fontSize": 14, \
    "workbench.preferredDarkColorTheme": "Default Dark+", \
    "workbench.welcomePage.enabled": false, \
    "workbench.tips.enabled": false, \
    "update.showReleaseNotes": false, \
    "telemetry.telemetryLevel": "off", \
    "window.dialogStyle": "native" \
}' > /home/coder/.local/share/code-server/User/settings.json

# Configure code-server to use the dark theme and disable welcome page
RUN echo "bind-addr: 0.0.0.0:8080\nauth: password\ncert: false\nuser-data-dir: /home/coder/.local/share/code-server\nextensions-dir: /home/coder/.local/share/code-server/extensions\ndisable-telemetry: true\ndisable-update-check: true" > /home/coder/.config/code-server/config.yaml

# Fix for product.json directory vs file issue
RUN rm -rf /home/coder/.local/share/code-server/product.json && \
    echo '{ \
    "welcomePage": false, \
    "welcomePageVisible": false, \
    "showWelcomeDialog": false \
}' > /home/coder/.local/share/code-server/product.json

# Set proper permissions
RUN chown -R coder:coder /workspace && chmod -R 755 /workspace
RUN chown -R coder:coder /home/coder

# Switch back to coder user
USER coder

# Set environment variables to disable welcome
ENV CS_DISABLE_GETTING_STARTED_OVERRIDE=1
ENV CS_DISABLE_WELCOME=true

# Expose the port
EXPOSE 8080

# Use the entrypoint script to start everything
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"] 