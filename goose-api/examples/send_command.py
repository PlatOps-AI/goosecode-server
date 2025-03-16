#!/usr/bin/env python3
"""
Example script to send a command to the shared tmux terminal via the Goose API.
"""
import requests
import sys
import json
import os

API_BASE = "http://localhost:8000"
API_KEY = os.environ.get("PASSWORD", "talktomegoose")

def send_command(cmd, session="goose-controller", window="goose"):
    """Send a command to the specified tmux session."""
    url = f"{API_BASE}/api/terminal/send"
    
    payload = {
        "command": cmd,
        "session": session,
        "window": window
    }
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending command: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_command.py 'command to execute'")
        sys.exit(1)
    
    command = sys.argv[1]
    result = send_command(command)
    
    if result:
        print(json.dumps(result, indent=2))
        print(f"Command successfully sent: '{command}'") 