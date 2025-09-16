#!/bin/bash
# Start both backend and frontend servers

echo "🚀 Starting TFT Composition Analyzer UI"
echo "========================================="

# Kill existing processes on these ports if they exist
echo "Checking for existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
sleep 2

# Store project root
PROJECT_ROOT=$(pwd)

# Start backend in background (from project root for proper imports)
echo "Starting FastAPI backend on port 8000..."
cd "$PROJECT_ROOT" && uv run uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend
echo "Starting Next.js frontend on port 3001..."
cd "$PROJECT_ROOT/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "📱 Frontend: http://localhost:3001"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait $FRONTEND_PID $BACKEND_PID