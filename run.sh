#!/bin/bash
set -e

# Variables
IMAGE_NAME="goosecode-server"
CONTAINER_NAME="goosecode-server"
HOST_PORT=8080
CONTAINER_PORT=8080

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --rebuild)
      REBUILD=true
      ;;
    --port=*)
      HOST_PORT="${arg#*=}"
      ;;
    --image=*)
      IMAGE_NAME="${arg#*=}"
      ;;
    --container=*)
      CONTAINER_NAME="${arg#*=}"
      ;;
    --openai-key=*)
      OPENAI_API_KEY="${arg#*=}"
      ;;
    --password=*)
      PASSWORD="${arg#*=}"
      ;;
    --github-token=*)
      GITHUB_TOKEN="${arg#*=}"
      ;;
    --git-user=*)
      GIT_USER_NAME="${arg#*=}"
      ;;
    --git-email=*)
      GIT_USER_EMAIL="${arg#*=}"
      ;;
    *)
      # unknown option
      ;;
  esac
done

# Check if .env file exists and load environment variables if not overridden by command line
if [ -f .env ]; then
  # Source the .env file
  set -o allexport
  source .env
  set +o allexport
  
  # Command line arguments take precedence over .env variables
  # No need to reassign variables that were already set from command line
else
  echo "Warning: .env file not found. Using environment variables from command line or defaults."
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q $CONTAINER_NAME; then
  echo "Stopping and removing existing container..."
  docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
  docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
fi

# Build Docker image if it doesn't exist or if --rebuild flag is provided
if [ "$REBUILD" = true ] || ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
  echo "Building Docker image..."
  
  # If this is a forced rebuild, delete the workspace directory for a clean start
  if [ "$REBUILD" = true ] && [ -d "$(pwd)/workspace" ]; then
    echo "Rebuild flag detected. Removing existing workspace directory for clean installation..."
    rm -rf "$(pwd)/workspace"
    echo "Workspace directory removed."
  fi
  
  docker build -t $IMAGE_NAME .
fi

# Create workspace directory if it doesn't exist
if [ ! -d "$(pwd)/workspace" ]; then
  mkdir -p "$(pwd)/workspace"
  echo "Created workspace directory."
fi

# Start the container with environment variables
echo "Starting Goosecode Server container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $HOST_PORT:$CONTAINER_PORT \
  -v "$(pwd)/workspace:/workspace" \
  -v "$(pwd)/static:/workspace/static" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  -e PASSWORD="${PASSWORD:-vscode-password}" \
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
  -e GIT_USER_NAME="${GIT_USER_NAME:-PlatOps AI}" \
  -e GIT_USER_EMAIL="${GIT_USER_EMAIL:-hello@platops.ai}" \
  $IMAGE_NAME

echo "Goosecode Server is running!"
echo "Access it at: http://localhost:$HOST_PORT"
echo "Default password: ${PASSWORD:-vscode-password}" 