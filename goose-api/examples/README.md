# Goose API Example Scripts

This directory contains example scripts that demonstrate how to interact with the Goose Terminal API.

## Authentication

All API endpoints now require authentication using an API key. The examples in this directory read the API key from the `PASSWORD` environment variable, defaulting to `talktomegoose` if not set.

To use a different API key:

```bash
# Set the API key for your session
export PASSWORD=your_custom_password

# Or use it just for a single command
PASSWORD=your_custom_password python streaming.py "Hello"
```

## Available Examples

### streaming.py

This is a real-time streaming client that uses Server-Sent Events (SSE) to monitor Goose conversations. The client connects to the Goose API's `/api/stream` endpoint and receives events for various stages of a conversation.

**Usage:**

```bash
# Start a new conversation
python streaming.py "Tell me a joke"

# Continue an existing conversation
python streaming.py "Tell me another one" --session-id 20250308_123456

# Monitor an ongoing session
python streaming.py --session-id 20250308_123456 --monitor
```

**Features:**
- Real-time streaming of responses as they're generated
- Automatically reconnects if connection drops
- Tracks session ID for continuing conversations
- Support for monitoring ongoing conversations
- Formats tool requests and responses for better readability

### SSE Event Structure

The streaming client processes Server-Sent Events (SSE) with the following structure:

#### Event Types

1. **command_sent**
   - Sent when a command is successfully sent to the terminal
   - Data: `{"command": "string"}`

2. **session_identified**
   - Provides the session ID for the current conversation
   - Data: `{"session_id": "string"}`

3. **initial_state**
   - Contains the complete conversation history
   - Sent at the beginning of streaming to establish context
   - Data: `{"entries": [{...}, {...}, ...]}`

4. **update**
   - Contains a new message in the conversation
   - Sent as the conversation progresses
   - Data: `{"entry": {...}}`

5. **conversation_complete**
   - Sent when the assistant has finished responding
   - Data: `{"session_id": "string", "message": "string"}`

6. **ping**
   - Periodic keepalive message
   - Data: `{"timestamp": number}`

7. **error**
   - Sent when an error occurs
   - Data: `{"error": "string"}`

#### Event Flow

A typical event flow for a new conversation follows this sequence:
1. Client connects to `/api/stream` with a new message
2. Server responds with `command_sent` event
3. Server identifies the session and sends `session_identified` event
4. Server sends `initial_state` with any existing conversation history
5. As the assistant responds, server sends multiple `update` events
6. When the assistant completes, server sends `conversation_complete` event

#### Entry Structure

The `entry` field in `update` events and the `entries` array in `initial_state` events contain the conversation messages with the following structure:

```json
{
  "data": {
    "role": "user" | "assistant",
    "content": [
      {
        "type": "text",
        "text": "Message content"
      },
      // Or for tool requests:
      {
        "type": "toolRequest",
        "toolCall": {
          "value": {
            "name": "tool_name",
            "arguments": {...}
          }
        }
      },
      // Or for tool responses:
      {
        "type": "toolResponse",
        "toolResult": {
          "status": "success" | "error",
          "value": [...]
        }
      }
    ]
  }
}
```

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