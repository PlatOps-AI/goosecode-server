#!/bin/bash
# Script to integrate the Goose API into the Docker container's entrypoint

set -e

echo "This script will modify the container's entrypoint to automatically start the Goose API."
echo "It should be run on the host machine, not inside the container."

# Get container name - default or user specified
CONTAINER_NAME=${1:-goosecode-server}
echo "Using container name: $CONTAINER_NAME"

# Check if container exists
if ! docker ps -a | grep -q $CONTAINER_NAME; then
  echo "Error: Container '$CONTAINER_NAME' not found."
  echo "Usage: $0 [container-name]"
  exit 1
fi

# Create Python virtual environment if it doesn't exist
echo "Setting up Python virtual environment..."
docker exec $CONTAINER_NAME bash -c "if [ ! -d /opt/goose-api-venv ]; then python3 -m venv /opt/goose-api-venv; fi"

# Copy the API files to the container
echo "Copying Goose API files to container..."
docker cp ./goose-api $CONTAINER_NAME:/workspace/

# Make scripts executable in the container
docker exec $CONTAINER_NAME chmod +x /workspace/goose-api/docker-integration.sh
docker exec $CONTAINER_NAME chmod -R +x /workspace/goose-api/examples/

# Install dependencies in the virtual environment
echo "Installing dependencies in virtual environment..."
docker exec $CONTAINER_NAME bash -c "export PATH=/opt/goose-api-venv/bin:\$PATH && pip install --upgrade pip && pip install -r /workspace/goose-api/requirements.txt"

# Modify entrypoint to start API
echo "Adding API startup to the container configuration..."
docker exec $CONTAINER_NAME bash -c "echo '# Start Goose API' >> /home/coder/.bashrc"
docker exec $CONTAINER_NAME bash -c "echo 'if [ -f /workspace/goose-api/docker-integration.sh ]; then' >> /home/coder/.bashrc"
docker exec $CONTAINER_NAME bash -c "echo '  export PATH=/opt/goose-api-venv/bin:\$PATH' >> /home/coder/.bashrc"
docker exec $CONTAINER_NAME bash -c "echo '  /workspace/goose-api/docker-integration.sh' >> /home/coder/.bashrc"
docker exec $CONTAINER_NAME bash -c "echo 'fi' >> /home/coder/.bashrc"

echo "Installation completed successfully."
echo "The Goose API will start automatically when the container is restarted."
echo "To start it immediately, run:"
echo "  docker exec $CONTAINER_NAME /workspace/goose-api/docker-integration.sh" 