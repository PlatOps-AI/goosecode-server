# Goose API Example Scripts

This directory contains example scripts that demonstrate how to interact with the Goose Terminal API.

## Available Examples

### streaming.py

A real-time streaming client that uses Server-Sent Events (SSE) to monitor Goose conversations as they happen.

```bash
# Start a new conversation
python streaming.py "Tell me a joke"

# Continue an existing conversation
python streaming.py "Tell me another joke" --session-id YOUR_SESSION_ID

# Monitor an existing session without sending a new command
python streaming.py --session-id YOUR_SESSION_ID --monitor
```

Features:
- Real-time streaming of Goose's responses as they're generated
- Clearly formatted tool responses (file creation, terminal commands, etc.)
- Automatic reconnection if the connection is lost
- Session ID tracking for continuing conversations
- Support for monitoring ongoing conversations

### list_sessions.py

Lists all available Goose conversation session logs.

```bash
python list_sessions.py
```

### get_session_log.py

Retrieves and displays the contents of a specific session log.

```bash
# Get the latest session log
python get_session_log.py

# Get a specific session log
python get_session_log.py --session-id YOUR_SESSION_ID
```

### send_command.py

Sends a command to the tmux terminal.

```bash
python send_command.py "echo Hello from API"
```

## Requirements

These example scripts require the Python packages listed in the main `requirements.txt` file:

- fastapi
- uvicorn
- pydantic
- requests
- python-multipart
- sseclient-py

Install these dependencies with:

```bash
pip install -r ../requirements.txt
```

## API Configuration

By default, these scripts connect to the API at `http://localhost:8000`. If you've changed the API port or host, you'll need to update the `BASE_URL` variable in each script. 