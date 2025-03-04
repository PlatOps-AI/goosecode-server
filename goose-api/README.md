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

## Path Configuration

The API looks for Goose session logs in the default path:
```
/home/coder/.local/share/goose/sessions
```

If your logs are stored in a different location, update the `LOGS_PATH` variable in `main.py`. 