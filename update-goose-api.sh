#!/bin/bash
# Script to update the Goose API in an existing container

set -e

# Variables
CONTAINER_NAME=${1:-goosecode-server}

echo "Updating Goose API in container: $CONTAINER_NAME"

# Check if container exists and is running
if ! docker ps | grep -q $CONTAINER_NAME; then
  echo "Error: Container $CONTAINER_NAME is not running."
  echo "Usage: $0 [container-name]"
  exit 1
fi

# Copy the updated goose-api files to the container
echo "Copying Goose API files to container..."
docker cp ./goose-api $CONTAINER_NAME:/workspace/

# Make scripts executable
echo "Setting file permissions..."
docker exec $CONTAINER_NAME bash -c "chmod +x /workspace/goose-api/docker-integration.sh && chmod -R +x /workspace/goose-api/examples/"

# Install dependencies using the virtual environment
echo "Updating required packages in virtual environment..."
docker exec $CONTAINER_NAME bash -c "export PATH=/opt/goose-api-venv/bin:\$PATH && cd /workspace/goose-api && pip install -r requirements.txt"

# Restart the API
echo "Restarting the Goose API service..."
docker exec $CONTAINER_NAME bash -c "pkill -f 'python3 /workspace/goose-api/main.py' || true"
docker exec $CONTAINER_NAME bash -c "export PATH=/opt/goose-api-venv/bin:\$PATH && cd /workspace/goose-api && nohup python3 main.py > /tmp/goose-api.log 2>&1 &"

echo "Goose API successfully updated and restarted."
echo "Swagger UI available at: http://localhost:8000/docs"
echo "To view logs: docker exec $CONTAINER_NAME cat /tmp/goose-api.log" 