#!/usr/bin/env python3
"""
Example script to fetch and display a Goose session log via the API.
"""
import requests
import sys
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def get_latest_session_id():
    """Get the ID of the most recent session."""
    url = f"{API_BASE}/api/sessions/latest/id"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["session_id"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting latest session ID: {e}")
        return None

def get_session_logs(session_id, format="json"):
    """Fetch the logs for a specific session."""
    url = f"{API_BASE}/api/sessions/{session_id}"
    
    if format != "json":
        url += f"?format={format}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching session logs: {e}")
        return None

def list_available_sessions():
    """List all available session logs."""
    url = f"{API_BASE}/api/sessions"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing sessions: {e}")
        return None

def display_conversation(log_data):
    """Display the conversation in a human-readable format."""
    print("\n=== GOOSE CONVERSATION LOG ===\n")
    
    for entry in log_data["entries"]:
        data = entry["data"]
        if "role" in data:
            role = data["role"].upper()
            content = data.get("content", "")
            timestamp = data.get("timestamp", "")
            
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    time_str = str(timestamp)
            else:
                time_str = "unknown time"
                
            print(f"[{time_str}] {role}:")
            print(f"{content}\n{'-' * 50}\n")

if __name__ == "__main__":
    # Check for session ID argument
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        print(f"Fetching logs for session: {session_id}")
    else:
        # Get the most recent session
        print("No session ID provided, fetching most recent session...")
        session_id = get_latest_session_id()
        if not session_id:
            print("Could not retrieve latest session ID.")
            sys.exit(1)
        print(f"Using latest session: {session_id}")
    
    # Get and display session logs
    logs = get_session_logs(session_id)
    if logs:
        display_conversation(logs)
    else:
        print("Failed to retrieve session logs.") 