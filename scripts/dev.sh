#!/usr/bin/env bash
set -e

echo "🚀 Starting MATHRIX Full Stack Development Environment..."

# 1. Ensure docker db + pgadmin are running
echo "🐘 Starting PostgreSQL & pgAdmin containers..."
docker compose up -d

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL container to become healthy..."
until docker compose exec -T postgres pg_isready -U quiz_user -d quiz_db > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready on localhost:5432"
echo "✅ pgAdmin Web Console is accessible on http://localhost:5050"

# Cleanup trap on Ctrl+C
cleanup() {
    echo -e "\n🛑 Shutting down backend and frontend..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 2. Start Backend
echo "🐍 Starting FastAPI Backend on http://localhost:8000..."
cd backend
~/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 3. Start Frontend
echo "⚛️  Starting Vite React Frontend on http://localhost:5173..."
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo "=========================================================="
echo "✨ MATHRIX System is up and running!"
echo "   - Frontend UI:    http://localhost:5173"
echo "   - Backend API:    http://localhost:8000/docs"
echo "   - pgAdmin Web:    http://localhost:5050"
echo "     (Login: admin@mathrix.edu.vn / admin)"
echo "=========================================================="

wait
