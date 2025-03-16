#!/usr/bin/env python3
"""
Example script to list all available Goose session logs via the API.
"""
import requests
import json
import os
from datetime import datetime

API_BASE = "http://localhost:8000"
API_KEY = os.environ.get("PASSWORD", "talktomegoose")

def list_sessions():
    """List all available session logs."""
    url = f"{API_BASE}/api/sessions"
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing sessions: {e}")
        return None

def list_terminal_sessions():
    """List all active tmux sessions."""
    url = f"{API_BASE}/api/terminal/sessions"
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing terminal sessions: {e}")
        return None

def human_readable_size(size_bytes):
    """Convert a size in bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} GB"

if __name__ == "__main__":
    # Get and display session log files
    print("\n=== AVAILABLE GOOSE SESSION LOGS ===\n")
    sessions = list_sessions()
    
    if sessions:
        print(f"{'SESSION ID':<15} {'SIZE':<10} {'LAST MODIFIED':<20} {'FILE PATH'}")
        print(f"{'-'*15} {'-'*10} {'-'*20} {'-'*50}")
        
        for session in sorted(sessions, key=lambda x: x["last_modified"], reverse=True):
            session_id = session["session_id"]
            size = human_readable_size(session["size_bytes"])
            modified = datetime.fromtimestamp(session["last_modified"]).strftime("%Y-%m-%d %H:%M:%S")
            path = session["file_path"]
            
            print(f"{session_id:<15} {size:<10} {modified:<20} {path}")
    else:
        print("No session logs found or failed to retrieve the list.")
    
    # Get and display active terminal sessions
    print("\n=== ACTIVE TMUX SESSIONS ===\n")
    terminal_sessions = list_terminal_sessions()
    
    if terminal_sessions and terminal_sessions.get("sessions"):
        print(f"{'SESSION NAME':<20} {'CREATED AT'}")
        print(f"{'-'*20} {'-'*30}")
        
        for session in terminal_sessions["sessions"]:
            name = session["name"]
            created = session["created"]
            
            print(f"{name:<20} {created}")
    else:
        print("No active tmux sessions found or failed to retrieve the list.") 