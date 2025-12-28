#!/bin/bash
# Script to start the Flask server in the background

cd "$(dirname "$0")"
source venv/bin/activate
nohup python app.py > server.log 2>&1 &
echo "Server started! PID: $!"
echo "Logs are being written to server.log"
echo "To stop the server, run: pkill -f 'python app.py'"

