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