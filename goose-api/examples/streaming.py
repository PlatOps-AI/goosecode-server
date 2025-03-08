#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dead simple Goose AI conversation client.

This client connects to the Goose Terminal API, sends a message, waits for a response, and exits.
No fancy stuff, no continuous mode, just sends and receives.

Usage:
    # New conversation
    python streaming.py "Tell me a joke"
    
    # Continue an existing conversation
    python streaming.py "Tell me another one" --session-id 20250308_123456
    
    # Monitor a session
    python streaming.py --session-id 20250308_123456 --monitor

SSE Event Structure:
    The server sends events with the following types:
    
    - command_sent: Confirms a command was sent to the terminal
      Data: {"command": "string"}
    
    - session_identified: Provides the session ID for the conversation
      Data: {"session_id": "string"}
    
    - initial_state: Contains the complete conversation history
      Data: {"entries": [{...}, {...}]}
    
    - update: Contains a new message in the conversation
      Data: {"entry": {...}}
    
    - conversation_complete: Sent when the assistant has finished responding
      Data: {"session_id": "string", "message": "string"}
    
    - ping: Periodic keepalive message
      Data: {"timestamp": number}
    
    - error: Sent when an error occurs
      Data: {"error": "string"}
"""
import requests
import sseclient
import json
import sys
import argparse
from datetime import datetime

API_BASE = "http://localhost:8000"

def format_tool_request(content):
    """Format a tool request message for display."""
    try:
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "toolRequest":
                    tool_call = item.get("toolCall", {})
                    tool_data = tool_call.get("value", {})
                    tool_name = tool_data.get("name", "unknown_tool")
                    tool_args = tool_data.get("arguments", {})
                    
                    # Format based on tool type
                    if tool_name == "developer__shell":
                        command = tool_args.get("command", "")
                        return f"🛠️  [Shell Command] $ {command}"
                    elif tool_name == "developer__text_editor":
                        cmd = tool_args.get("command", "")
                        path = tool_args.get("path", "")
                        if cmd == "write":
                            return f"🛠️  [File Write] Creating {path}"
                        else:
                            return f"🛠️  [Editor] {cmd} on {path}"
                    else:
                        return f"🛠️  [Tool] {tool_name} with args: {json.dumps(tool_args, indent=2)}"
    except Exception as e:
        return f"🛠️  [Tool Request] (Error parsing: {e})"
    
    return "🛠️  [Tool Request]"

def format_tool_response(content):
    """Format a tool response message for display."""
    try:
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "toolResponse":
                    result = item.get("toolResult", {})
                    status = result.get("status", "unknown")
                    
                    # Get result value, which might contain multiple parts
                    value = result.get("value", [])
                    if isinstance(value, list):
                        # Look for user-visible text parts
                        user_text = ""
                        for part in value:
                            if part.get("type") == "text" and part.get("annotations", {}).get("audience") == ["user"]:
                                user_text += part.get("text", "")
                        
                        if user_text:
                            # Return the complete user-visible text
                            return f"🔄 [Tool Response]\n{user_text}"
                    
                    return f"🔄 [Tool Response] Status: {status}"
    except Exception as e:
        return f"🔄 [Tool Response] (Error parsing: {e})"
    
    return "🔄 [Tool Response]"

def extract_content_text(content_data):
    """Extract text content from various formats."""
    text = ""
    if "content" in content_data and isinstance(content_data["content"], list):
        for item in content_data["content"]:
            # Handle regular text
            if "type" in item and item["type"] == "text":
                text += item["text"]
            elif "Text" in item and "text" in item["Text"]:
                text += item["Text"]["text"]
            # Handle tool requests/responses
            elif item.get("type") == "toolRequest":
                text += format_tool_request([item])
            elif item.get("type") == "toolResponse":
                text += format_tool_response([item])
    return text

def stream_conversation(command=None, session_id=None, monitor_only=False):
    """
    Simple streaming function - sends command, waits for response, exits.
    """
    # Skip sending command if monitoring only
    if monitor_only:
        command = None
    
    # Print a header message
    if command and not monitor_only:
        if session_id:
            print(f"\n💬 Continuing conversation {session_id}")
            print(f"Sending: \"{command}\"")
        else:
            print(f"\n💬 Starting new conversation")
            print(f"Sending: \"{command}\"")
    elif session_id:
        print(f"\n👁️ Monitoring conversation {session_id}")
    
    print("─" * 70)
    
    # Prepare request payload
    payload = {
        "command": command,
        "session_id": session_id,
        "tmux_session": "goose-controller",
        "tmux_window": "goose"
    }
    
    try:
        # Send request and start streaming
        response = requests.post(f"{API_BASE}/api/stream", json=payload, stream=True)
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        current_session_id = session_id
        
        # Process events
        for event in client.events():
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if event.event == "command_sent":
                # This event confirms that the command was successfully sent to the terminal
                # It provides confirmation that the API received and processed the request
                data = json.loads(event.data)
                print(f"[{timestamp}] ✓ Command sent: \"{data['command']}\"")
            
            elif event.event == "session_identified":
                # This event provides the session ID for the conversation
                # The session ID can be used to continue the conversation later
                data = json.loads(event.data)
                current_session_id = data["session_id"]
                print(f"[{timestamp}] ✓ Session ID: {current_session_id}")
            
            elif event.event == "initial_state":
                # This event contains the complete conversation history
                # For monitoring, it provides the current state before updates
                data = json.loads(event.data)
                entries = data.get("entries", [])
                print(f"[{timestamp}] ℹ️ Received conversation history ({len(entries)} entries)")
                # We don't print the whole history for simplicity
                # Uncomment to process history:
                # for entry in entries:
                #     # Process each entry
            
            elif event.event == "update":
                # This event contains new messages in the conversation
                # It's sent whenever there's a new user or assistant message
                data = json.loads(event.data)
                entry = data["entry"]
                
                # Skip metadata entries
                if "data" in entry and "description" in entry["data"]:
                    continue
                
                # Extract user/assistant messages
                role = "UNKNOWN"
                content = []
                
                # Handle data wrapper
                if "data" in entry:
                    content_data = entry["data"]
                else:
                    content_data = entry
                
                # Get role
                if "role" in content_data:
                    role = content_data["role"].upper()
                
                # Handle content based on type
                if "content" in content_data and isinstance(content_data["content"], list):
                    # Check content type (text or tool)
                    for item in content_data["content"]:
                        if item.get("type") == "toolRequest":
                            print(f"[{timestamp}] {role}: {format_tool_request([item])}")
                        elif item.get("type") == "toolResponse":
                            # Format tool response with proper spacing and line breaks
                            tool_response = format_tool_response([item])
                            # Split into lines and format for better readability
                            lines = tool_response.split("\n")
                            print(f"[{timestamp}] {role}: {lines[0]}")  # Print the header
                            # Print remaining lines with proper indentation
                            for line in lines[1:]:
                                print(f"    {line}")
                        elif "type" in item and item["type"] == "text":
                            print(f"[{timestamp}] {role}: {item['text']}")
                        elif "Text" in item and "text" in item["Text"]:
                            print(f"[{timestamp}] {role}: {item['Text']['text']}")
                
            elif event.event == "conversation_complete":
                # This event signals that the assistant has finished responding
                # It's a good point to exit the streaming or prompt for the next user input
                data = json.loads(event.data)
                current_session_id = data["session_id"]
                print(f"\n✓ Response complete. To continue: python streaming.py \"your message\" --session-id {current_session_id}")
                return
            
            elif event.event == "ping":
                # Ping events are sent periodically to keep the connection alive
                # No need to display these, but we could log them for debugging
                pass
            
            elif event.event == "error":
                # Error events indicate problems with the streaming connection or request
                data = json.loads(event.data)
                print(f"[{timestamp}] ⚠️ Error: {data.get('error', 'Unknown error')}")
            
            # Ignore other events
    
    except KeyboardInterrupt:
        print("\n✋ Streaming stopped by user")
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection error: {e}")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Final message if we didn't get a conversation_complete event
    if current_session_id:
        print(f"\nTo continue this conversation: python streaming.py \"your message\" --session-id {current_session_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Goose AI client")
    
    parser.add_argument("command", nargs="?", help="Message to send")
    parser.add_argument("--session-id", "-s", help="Session ID to connect to")
    parser.add_argument("--monitor", "-m", action="store_true", help="Just monitor without sending commands")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.monitor and not args.session_id:
        parser.error("--monitor requires --session-id")
    
    if not args.command and not args.session_id:
        parser.error("Either command or --session-id is required")
    
    # Start streaming
    stream_conversation(
        command=args.command,
        session_id=args.session_id,
        monitor_only=args.monitor
    ) 