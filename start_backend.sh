#!/bin/bash
# Start the backend server with network access enabled

echo "Starting Drone Visualizer Backend..."
echo "Binding to 0.0.0.0:8000 (accessible from network)"
echo ""

# Get local IP address
IP=$(hostname -I | awk '{print $1}')
echo "Your local IP: $IP"
echo "Frontend can connect from phone using: http://$IP:8000"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"

python3 -m uvicorn src.server.app:app --reload --host 0.0.0.0 --port 8000
