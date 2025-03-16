from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import subprocess
import os
import json
import time
from typing import List, Optional, Dict, Any, AsyncGenerator
import glob
import asyncio

# Load password from environment variable
API_PASSWORD = os.environ.get("PASSWORD", "talktomegoose")
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="Goose Terminal API",
    description="API for interacting with Goose terminal sessions and logs. All endpoints require authentication using the X-API-Key header with the correct API key.",
    version="0.1.0"
)

# Authentication dependency
async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key header is missing")
    if api_key != API_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path where Goose session logs are stored
LOGS_PATH = "/home/coder/.local/share/goose/sessions"
# Default tmux session details
DEFAULT_SESSION = "goose-controller"
DEFAULT_WINDOW = "goose"

# --- Models ---

class TerminalCommand(BaseModel):
    """Model for sending commands to the terminal"""
    command: str
    session: str = DEFAULT_SESSION
    window: str = DEFAULT_WINDOW

class SessionInfo(BaseModel):
    """Model for session information"""
    session_id: str
    file_path: str
    size_bytes: int
    last_modified: float

class LogEntry(BaseModel):
    """Model for a log entry (generic to handle various formats)"""
    data: Dict[str, Any]
    raw: Optional[str] = None

class SessionLog(BaseModel):
    """Model for complete session log"""
    session_id: str
    entries: List[LogEntry]

# --- SSE Endpoint ---

class StreamRequest(BaseModel):
    """Model for streaming requests"""
    command: Optional[str] = None  # Optional command to send
    session_id: Optional[str] = None  # Optional session ID if already known
    tmux_session: str = DEFAULT_SESSION  # tmux session name
    tmux_window: str = DEFAULT_WINDOW  # tmux window name
    poll_interval: float = 0.5  # How often to check for updates
    timeout_seconds: int = 300  # Inactivity timeout
    wait_for_response: bool = True  # Wait for assistant response before disconnecting

async def find_session_for_message(command: str, max_wait_time: int = 10) -> Optional[str]:
    """
    Find the session ID that contains a specific message.
    Polls recent sessions for the given message.
    
    Args:
        command: The command/message to look for
        max_wait_time: Maximum time to wait for the message to appear (seconds)
    
    Returns:
        The session ID if found, None otherwise
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        # Get all available sessions
        sessions = []
        for file_path in glob.glob(f"{LOGS_PATH}/*.jsonl"):
            file_name = os.path.basename(file_path)
            session_id = file_name.split('.')[0]
            stats = os.stat(file_path)
            
            sessions.append({
                "session_id": session_id,
                "file_path": file_path,
                "last_modified": stats.st_mtime
            })
        
        # Sort sessions by last modified time (newest first)
        sessions.sort(key=lambda x: x["last_modified"], reverse=True)
        
        # Check the most recent sessions first (limit to 5 most recent)
        for session in sessions[:5]:
            log_path = session["file_path"]
            try:
                with open(log_path, 'r') as f:
                    for line in f:
                        try:
                            entry_json = json.loads(line)
                            
                            # Handle the structure where message is inside 'data' field
                            if "data" in entry_json:
                                entry = entry_json["data"]
                            else:
                                entry = entry_json
                            
                            # Check if this is a user message
                            if entry.get("role") == "user" and "content" in entry:
                                content_list = entry["content"]
                                
                                # Check for matching message in content
                                if isinstance(content_list, list):
                                    for content_item in content_list:
                                        # Handle different content formats
                                        if "Text" in content_item and content_item["Text"].get("text") == command:
                                            return session["session_id"]
                                        elif content_item.get("type") == "text" and content_item.get("text") == command:
                                            return session["session_id"]
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error processing session {session['session_id']}: {str(e)}")
                continue
        
        # Wait before polling again
        await asyncio.sleep(0.5)
    
    return None

async def sse_generator(stream_request: StreamRequest) -> AsyncGenerator[str, None]:
    """
    Generator for SSE events from Goose session logs.
    Handles session identification, command sending, and log streaming.
    Automatically ends the stream after receiving an assistant response.
    """
    session_id = stream_request.session_id
    command = stream_request.command
    
    # If a command is provided but no session ID, send the command and identify the session
    if command and not session_id:
        try:
            # Send command to terminal
            escaped_command = command.replace("'", "'\\''")
            tmux_cmd = f"tmux send-keys -t '{stream_request.tmux_session}:{stream_request.tmux_window}' '{escaped_command}' C-m"
            subprocess.run(tmux_cmd, shell=True, check=True)
            
            # Notify that command was sent
            yield f"event: command_sent\ndata: {json.dumps({'command': command})}\n\n"
            
            # Find session ID for this command
            session_id = await find_session_for_message(command)
            if session_id:
                yield f"event: session_identified\ndata: {json.dumps({'session_id': session_id})}\n\n"
            else:
                yield f"event: error\ndata: {json.dumps({'error': 'Could not identify session ID for the command'})}\n\n"
                return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            return
    
    # If a command is provided and session ID is already known, just send the command
    elif command and session_id:
        try:
            # Send command to terminal
            escaped_command = command.replace("'", "'\\''")
            tmux_cmd = f"tmux send-keys -t '{stream_request.tmux_session}:{stream_request.tmux_window}' '{escaped_command}' C-m"
            subprocess.run(tmux_cmd, shell=True, check=True)
            
            # Notify that command was sent
            yield f"event: command_sent\ndata: {json.dumps({'command': command})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            return
    
    # If still no session ID, report error
    if not session_id:
        yield f"event: error\ndata: {json.dumps({'error': 'No session ID provided or found'})}\n\n"
        return
    
    # Verify session log file exists
    log_path = f"{LOGS_PATH}/{session_id}.jsonl"
    if not os.path.exists(log_path):
        yield f"event: error\ndata: {json.dumps({'error': f'Session log file not found: {session_id}'})}\n\n"
        return
    
    # Send initial state of the conversation
    last_position = 0
    assistant_responded = False
    
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            last_position = len(content)
            entries = []
            for line in content.splitlines():
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            if entries:
                yield f"event: initial_state\ndata: {json.dumps({'entries': entries})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': f'Error reading log file: {str(e)}'})}\n\n"
        return
    
    # Monitor for new entries until assistant responds
    try:
        # Poll until we get an assistant response, then close the stream
        while not assistant_responded:
            if os.path.exists(log_path):
                stats = os.stat(log_path)
                if stats.st_size > last_position:
                    with open(log_path, 'r') as f:
                        f.seek(last_position)
                        new_content = f.read()
                        last_position = f.tell()
                        
                        for line in new_content.splitlines():
                            if line.strip():
                                try:
                                    entry = json.loads(line)
                                    yield f"event: update\ndata: {json.dumps({'entry': entry})}\n\n"
                                    
                                    # Check if this is an assistant message
                                    role = None
                                    if "data" in entry and "role" in entry["data"]:
                                        role = entry["data"]["role"]
                                    elif "role" in entry:
                                        role = entry["role"]
                                    
                                    # If this is an assistant message with text content, end the stream
                                    if role == "assistant":
                                        # Check if it contains text content
                                        has_text_content = False
                                        content = None
                                        
                                        if "data" in entry and "content" in entry["data"]:
                                            content = entry["data"]["content"]
                                        elif "content" in entry:
                                            content = entry["content"]
                                        
                                        if content and isinstance(content, list):
                                            for item in content:
                                                if (item.get("type") == "text" and "text" in item) or \
                                                   ("Text" in item and "text" in item["Text"]):
                                                    has_text_content = True
                                                    break
                                        
                                        if has_text_content:
                                            assistant_responded = True
                                            # Send a conversation complete event
                                            yield f"event: conversation_complete\ndata: {json.dumps({'session_id': session_id, 'message': 'Assistant response received'})}\n\n"
                                            # Stream will be closed after this
                                            return
                                except json.JSONDecodeError:
                                    continue
            
            # Quick ping to keep the connection alive while waiting
            yield f"event: ping\ndata: {json.dumps({'timestamp': time.time()})}\n\n"
            
            # Short delay before checking again
            await asyncio.sleep(0.5)
            
    except Exception as e:
        error_msg = str(e)
        print(f"Stream error: {error_msg}")
        yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"

@app.post("/api/stream", summary="Stream Goose session updates using Server-Sent Events (SSE)", dependencies=[Depends(verify_api_key)])
async def stream_session(request: StreamRequest):
    """
    Stream Goose session updates and automatically close after receiving assistant response.
    """
    return StreamingResponse(
        sse_generator(request),
        media_type="text/event-stream"
    )

# --- Health Check Endpoint ---

@app.get("/api/ping", summary="Health check endpoint", dependencies=[Depends(verify_api_key)])
async def ping():
    """
    Comprehensive health check endpoint that verifies:
    1. The API itself is running
    2. The VS Code server is accessible
    3. The tmux session has been started
    
    Returns a JSON response with detailed status information.
    """
    status = "ok"
    services = {
        "api": {"status": "ok", "message": "API is running"},
        "vscode": {"status": "unknown", "message": "Not checked"},
        "tmux": {"status": "unknown", "message": "Not checked"}
    }
    
    # Check if VS Code server is running (port 8080)
    try:
        vscode_check = subprocess.run(
            "ps aux | grep 'code-server' | grep -v grep",
            shell=True, capture_output=True, text=True
        )
        if vscode_check.returncode == 0 and vscode_check.stdout.strip():
            services["vscode"] = {"status": "ok", "message": "VS Code server is running"}
        else:
            services["vscode"] = {"status": "error", "message": "VS Code server not detected"}
            status = "partial"
    except Exception as e:
        services["vscode"] = {"status": "error", "message": f"Failed to check VS Code: {str(e)}"}
        status = "partial"
    
    # Check if tmux session exists
    try:
        tmux_check = subprocess.run(
            f"tmux has-session -t '{DEFAULT_SESSION}' 2>/dev/null",
            shell=True, capture_output=True, text=True
        )
        if tmux_check.returncode == 0:
            services["tmux"] = {"status": "ok", "message": f"Tmux session '{DEFAULT_SESSION}' is running"}
        else:
            services["tmux"] = {"status": "error", "message": f"Tmux session '{DEFAULT_SESSION}' not found"}
            status = "partial"
    except Exception as e:
        services["tmux"] = {"status": "error", "message": f"Failed to check tmux: {str(e)}"}
        status = "partial"
    
    return {
        "status": status,
        "message": "Goose Terminal API health check",
        "version": app.version,
        "services": services
    }

# --- Terminal Endpoints ---

@app.post("/api/terminal/send", summary="Send a command to the tmux terminal", dependencies=[Depends(verify_api_key)])
async def send_terminal_input(command_data: TerminalCommand):
    """
    Send a command to the specified tmux session and window.
    
    The command will be executed in the shared terminal as if typed directly.
    """
    try:
        # Escape single quotes in the command
        escaped_command = command_data.command.replace("'", "'\\''")
        
        # Construct and execute the tmux command
        tmux_cmd = f"tmux send-keys -t '{command_data.session}:{command_data.window}' '{escaped_command}' C-m"
        result = subprocess.run(tmux_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to send command: {result.stderr}")
            
        return {
            "success": True,
            "session": command_data.session,
            "window": command_data.window,
            "command": command_data.command
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/terminal/sessions", summary="List all tmux sessions", dependencies=[Depends(verify_api_key)])
async def list_tmux_sessions():
    """
    List all active tmux sessions on the system.
    
    Returns information about session names and creation times.
    """
    try:
        result = subprocess.run(
            "tmux list-sessions -F '#{session_name},#{session_created}'", 
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return {"sessions": []}
            
        sessions = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 2:
                    sessions.append({
                        "name": parts[0],
                        "created": parts[1]
                    })
        
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Logs Endpoints ---

@app.get("/api/sessions", response_model=List[SessionInfo], summary="List all session log files", dependencies=[Depends(verify_api_key)])
async def list_sessions():
    """
    List all available Goose session log files.
    
    Returns a list of session IDs along with file information.
    """
    try:
        sessions = []
        for file_path in glob.glob(f"{LOGS_PATH}/*.jsonl"):
            file_name = os.path.basename(file_path)
            session_id = file_name.split('.')[0]
            stats = os.stat(file_path)
            
            sessions.append(SessionInfo(
                session_id=session_id,
                file_path=file_path,
                size_bytes=stats.st_size,
                last_modified=stats.st_mtime
            ))
        
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}", summary="Get contents of a specific session log", dependencies=[Depends(verify_api_key)])
async def get_session_log(session_id: str, format: str = "json"):
    """
    Get the contents of a specific session log file.
    
    Parameters:
    - session_id: The ID of the session to retrieve
    - format: Response format ('json' or 'raw')
    
    Returns the complete conversation log for the requested session.
    """
    log_path = f"{LOGS_PATH}/{session_id}.jsonl"
    
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail=f"Session log {session_id} not found")
        
    try:
        if format == "raw":
            with open(log_path, 'r') as f:
                return {"raw_content": f.read()}
        else:
            entries = []
            with open(log_path, 'r') as f:
                for line in f:
                    try:
                        entry_data = json.loads(line)
                        entries.append(LogEntry(data=entry_data))
                    except json.JSONDecodeError:
                        entries.append(LogEntry(data={}, raw=line.strip()))
                        
            return SessionLog(session_id=session_id, entries=entries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/latest/id", summary="Get the ID of the most recent session", dependencies=[Depends(verify_api_key)])
async def get_latest_session_id():
    """
    Get the ID of the most recently modified session log file.
    
    Useful for quickly accessing the current active session.
    """
    try:
        latest_file = None
        latest_mtime = 0
        
        for file_path in glob.glob(f"{LOGS_PATH}/*.jsonl"):
            stats = os.stat(file_path)
            if stats.st_mtime > latest_mtime:
                latest_mtime = stats.st_mtime
                latest_file = file_path
                
        if latest_file:
            session_id = os.path.basename(latest_file).split('.')[0]
            return {"session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="No session logs found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 