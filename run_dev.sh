#!/bin/bash

# Start the FastAPI backend
echo "Starting FastAPI backend..."
cd /Users/zackkhan/Projects/chat/sevensky
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start the React frontend
echo "Starting React frontend..."
cd /Users/zackkhan/Projects/chat/frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend running on http://localhost:8000"
echo "Frontend running on http://localhost:5173"
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait

# Cleanup
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
