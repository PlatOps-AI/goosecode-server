# Goose Terminal API

A lightweight API for interacting with Goose terminal sessions and accessing session logs in a VSCode Server environment.

## Features

- Send commands to shared tmux sessions
- List active tmux sessions
- Access Goose session logs (conversation history)
- Get information about available session logs
- Swagger documentation for API exploration

## Container Integration

The Goose Terminal API is now integrated directly into the Goosecode Server container. When you start the container using `run.sh`, the API will automatically start and be accessible at port 8000.

### Command-line Options

New options available in `run.sh`:

```bash
# Disable the Goose API
./run.sh --no-goose-api

# Change the API port (default is 8000)
./run.sh --api-port=9000
```

### Accessing the API

- API Base URL: `http://localhost:8000/api/`
- Swagger Documentation: `http://localhost:8000/docs`

### Viewing API Logs

```bash
docker exec goosecode-server cat /tmp/goose-api.log
```

## Manual Setup

### Dependencies

```bash
pip install -r requirements.txt
```

### Running the API (Manual)

```bash
python main.py
```

## API Endpoints

### Terminal Commands

- **POST /api/terminal/send** - Send a command to the tmux terminal
- **GET /api/terminal/sessions** - List all tmux sessions

### Session Logs

- **GET /api/sessions** - List all available session log files
- **GET /api/sessions/{session_id}** - Get contents of a specific session log
- **GET /api/sessions/latest/id** - Get the ID of the most recent session

### Streaming Events

- **POST /api/stream** - Stream Goose conversation updates in real-time using Server-Sent Events (SSE)

## SSE Event Structure

The `/api/stream` endpoint uses [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) to provide real-time updates. Each event has a type and JSON data payload.

### Event Types

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `command_sent` | Sent when a command is successfully sent to the terminal | `{"command": "string"}` |
| `session_identified` | Sent when a session ID is identified for a command | `{"session_id": "string"}` |
| `initial_state` | Contains the complete history of the conversation | `{"entries": [{...}, {...}]}` |
| `update` | Sent when a new message is added to the conversation | `{"entry": {...}}` |
| `conversation_complete` | Sent when the assistant has completed its response | `{"session_id": "string", "message": "string"}` |
| `ping` | Periodic keepalive message | `{"timestamp": number}` |
| `error` | Sent when an error occurs | `{"error": "string"}` |

### Event Flow

1. Client connects to `/api/stream` with a command and/or session ID
2. If a command is sent:
   - Server sends `command_sent` event
   - If no session ID was provided, server identifies session and sends `session_identified` event
3. Server sends `initial_state` event with conversation history
4. As new messages arrive, server sends `update` events
5. When assistant completes its response, server sends `conversation_complete` event
6. Server closes the connection

### Entry Structure

The `entry` field in `update` events and each item in the `entries` array of `initial_state` events has the following structure:

```json
{
  "data": {
    "role": "user|assistant",
    "created": 1234567890,
    "content": [
      {
        "type": "text",
        "text": "Message content"
      },
      // Or for tool requests
      {
        "type": "toolRequest",
        "toolCall": {
          "value": {
            "name": "tool_name",
            "arguments": {...}
          }
        }
      },
      // Or for tool responses
      {
        "type": "toolResponse",
        "toolResult": {
          "status": "success|error",
          "value": [...]
        }
      }
    ]
  }
}
```

### Example SSE Event Sequence

```
event: command_sent
data: {"command": "Tell me a joke"}

event: session_identified
data: {"session_id": "20250308_123456"}

event: initial_state
data: {"entries": [{...}, {...}]}

event: update
data: {"entry": {"data": {"role": "assistant", "content": [...]}}}

event: conversation_complete
data: {"session_id": "20250308_123456", "message": "Assistant response received"}
```

## Examples

### Send a Terminal Command

```python
import requests

response = requests.post("http://localhost:8000/api/terminal/send", json={
    "command": "echo 'Hello from API'"
})
print(response.json())
```

### Get Session Log Data

```python
import requests

# Get latest session ID
response = requests.get("http://localhost:8000/api/sessions/latest/id")
latest_session = response.json()["session_id"]

# Get session log contents
response = requests.get(f"http://localhost:8000/api/sessions/{latest_session}")
log_data = response.json()

# Process log entries
for entry in log_data["entries"]:
    if "role" in entry["data"]:
        print(f"{entry['data']['role']}: {entry['data'].get('content', '')[:100]}...")
```

### Streaming Goose Conversations

Use Server-Sent Events (SSE) to stream Goose conversations in real-time:

```python
import requests
import sseclient

# For a new conversation
payload = {
    "command": "Tell me a joke",
    "tmux_session": "goose-controller",
    "tmux_window": "goose"
}

# For continuing an existing conversation
# payload = {
#     "command": "Tell me another one",
#     "session_id": "YOUR_SESSION_ID", 
#     "tmux_session": "goose-controller",
#     "tmux_window": "goose"
# }

# Connect to the streaming endpoint
response = requests.post("http://localhost:8000/api/stream", json=payload, stream=True)
client = sseclient.SSEClient(response)

# Process events
for event in client.events():
    if event.event == "command_sent":
        print(f"Command sent: {event.data}")
    elif event.event == "session_identified":
        data = json.loads(event.data)
        print(f"Session ID: {data['session_id']}")
    elif event.event == "update":
        data = json.loads(event.data)
        entry = data["entry"]
        # Process and display new message
        print(entry)
    elif event.event == "conversation_complete":
        print("Conversation complete")
        break
```

## Streaming Client Tool

A simple command-line client is provided to stream Goose conversations:

```bash
# Start a new conversation
python streaming.py "Tell me a joke"

# Continue an existing conversation
python streaming.py "Tell me another one" --session-id YOUR_SESSION_ID

# Monitor a session
python streaming.py --session-id YOUR_SESSION_ID --monitor
```

The client automatically handles:
- Sending commands to the terminal
- Streaming real-time updates
- Displaying tool operations (file creation, shell commands, etc.)
- Showing the session ID for follow-up messages

## Path Configuration

The API looks for Goose session logs in the default path:
```
/home/coder/.local/share/goose/sessions
```

If your logs are stored in a different location, update the `LOGS_PATH` variable in `main.py`. 