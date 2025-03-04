from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import json
from typing import List, Optional, Dict, Any
import glob

app = FastAPI(
    title="Goose Terminal API",
    description="API for interacting with Goose terminal sessions and logs",
    version="0.1.0"
)

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

# --- Terminal Endpoints ---

@app.post("/api/terminal/send", summary="Send a command to the tmux terminal")
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

@app.get("/api/terminal/sessions", summary="List all tmux sessions")
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

@app.get("/api/sessions", response_model=List[SessionInfo], summary="List all session log files")
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

@app.get("/api/sessions/{session_id}", summary="Get contents of a specific session log")
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

@app.get("/api/sessions/latest/id", summary="Get the ID of the most recent session")
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