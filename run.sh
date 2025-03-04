#!/bin/bash
set -e

# Variables
IMAGE_NAME="goosecode-server"
CONTAINER_NAME="goosecode-server"
HOST_PORT=8080
CONTAINER_PORT=8080
ENABLE_TERMINAL_SHARING=true
ENABLE_GOOSE_API=true
API_PORT=8000

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
    --no-terminal-sharing)
      ENABLE_TERMINAL_SHARING=false
      ;;
    --no-goose-api)
      ENABLE_GOOSE_API=false
      ;;
    --api-port=*)
      API_PORT="${arg#*=}"
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

# Check if goose-api directory exists
GOOSE_API_DIR="$(pwd)/goose-api"
ENABLE_API_MOUNT=false
if [ "$ENABLE_GOOSE_API" = "true" ] && [ -d "$GOOSE_API_DIR" ]; then
  ENABLE_API_MOUNT=true
  echo "Goose API directory found, will mount for container access"
else
  echo "Goose API directory not found or API disabled, skipping mount"
fi

# Start the container with environment variables
echo "Starting Goosecode Server container..."
if [ "$ENABLE_API_MOUNT" = "true" ]; then
  docker run -d \
    --name $CONTAINER_NAME \
    -p $HOST_PORT:$CONTAINER_PORT \
    -p $API_PORT:8000 \
    -v "$(pwd)/workspace:/workspace" \
    -v "$(pwd)/static:/workspace/static" \
    -v "$GOOSE_API_DIR:/workspace/goose-api" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e PASSWORD="${PASSWORD:-talktomegoose}" \
    -e GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
    -e GIT_USER_NAME="${GIT_USER_NAME:-PlatOps AI}" \
    -e GIT_USER_EMAIL="${GIT_USER_EMAIL:-hello@platops.ai}" \
    -e ENABLE_TERMINAL_SHARING="${ENABLE_TERMINAL_SHARING}" \
    -e ENABLE_GOOSE_API="${ENABLE_GOOSE_API}" \
    $IMAGE_NAME
else
  docker run -d \
    --name $CONTAINER_NAME \
    -p $HOST_PORT:$CONTAINER_PORT \
    -p $API_PORT:8000 \
    -v "$(pwd)/workspace:/workspace" \
    -v "$(pwd)/static:/workspace/static" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e PASSWORD="${PASSWORD:-talktomegoose}" \
    -e GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
    -e GIT_USER_NAME="${GIT_USER_NAME:-PlatOps AI}" \
    -e GIT_USER_EMAIL="${GIT_USER_EMAIL:-hello@platops.ai}" \
    -e ENABLE_TERMINAL_SHARING="${ENABLE_TERMINAL_SHARING}" \
    -e ENABLE_GOOSE_API="${ENABLE_GOOSE_API}" \
    $IMAGE_NAME
fi

# Function to create a divider line
print_divider() {
  printf "\033[34m%s\033[0m\n" "+---------------------------------------------------------------------------+"
}

# Print header box
print_header() {
  local text="$1"
  local text_length=${#text}
  local padding=$(( (73 - text_length) / 2 ))
  local pad_str=$(printf "%${padding}s" "")
  
  printf "\033[34m| %s%s%s |\033[0m\n" "$pad_str" "$text" "$pad_str"
}

# Clear the terminal before showing output
clear

# Print retro-style divider line
print_divider() {
  printf "\033[34m%s\033[0m\n" "+---------------------------------------------------------------------------+"
}

# Print header box
print_header() {
  local text="$1"
  local text_length=${#text}
  local padding=$(( (73 - text_length) / 2 ))
  local pad_str=$(printf "%${padding}s" "")
  
  printf "\033[34m| %s%s%s |\033[0m\n" "$pad_str" "$text" "$pad_str"
}

# Print banner with IBM/Windows style
echo -e "\033[1;34m"
cat << "EOF"
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                          GOOSECODE SERVER v1.0                          │
│                             >< HONK! ><                                 │
│                                                                         │
│                      Copyright (c) 2025 PlatOps AI                      │
│                     Licensed under Apache License 2.0                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
EOF
echo -e "\033[0m"

print_divider
printf "\033[34m| %-73s |\033[0m\n" "                         SYSTEM INFORMATION"
print_divider

printf "\033[34m| %-73s |\033[0m\n" " STATUS: Server is running successfully."
printf "\033[34m| %-73s |\033[0m\n" " URL:    http://localhost:$HOST_PORT"
printf "\033[34m| %-73s |\033[0m\n" " ACCESS: ${PASSWORD:-talktomegoose}"

if [ "$ENABLE_GOOSE_API" = "true" ]; then
  printf "\033[34m| %-73s |\033[0m\n" " API:     http://localhost:$API_PORT/docs (Swagger UI)"
fi

print_divider

printf "\033[34m| %-73s |\033[0m\n" "                         SYSTEM COMMANDS"
print_divider
printf "\033[34m| %-73s |\033[0m\n" " STOP SERVER:  docker stop $CONTAINER_NAME"
printf "\033[34m| %-73s |\033[0m\n" " VIEW LOGS:    docker logs $CONTAINER_NAME"
printf "\033[34m| %-73s |\033[0m\n" " API LOGS:     docker exec $CONTAINER_NAME cat /tmp/goose-api.log"
print_divider

printf "\033[1;34m| %-73s |\033[0m\n" "                 SERVER INITIALIZATION COMPLETE"
print_divider