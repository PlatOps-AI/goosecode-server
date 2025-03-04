#!/bin/bash
# Script to install and run the Goose API in the container

set -e

echo "Setting up Python virtual environment path..."
export PATH="/opt/goose-api-venv/bin:$PATH"

echo "Starting Goose API server..."
cd /workspace/goose-api
python main.py &

echo "Goose API server started at http://localhost:8000"
echo "Swagger documentation available at http://localhost:8000/docs" 