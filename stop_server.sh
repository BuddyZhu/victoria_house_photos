#!/bin/bash
# Script to stop the Flask server

pkill -f 'python app.py'
echo "Server stopped"

