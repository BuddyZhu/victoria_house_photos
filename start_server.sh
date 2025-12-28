#!/bin/bash
# Script to start the Flask server in the background

# Get the directory where this script is located (works when sourced or executed)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Try to activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

nohup python app.py > server.log 2>&1 &
echo "Server started! PID: $!"
echo "Logs are being written to server.log"
echo "To stop the server, run: pkill -f 'python app.py'"

