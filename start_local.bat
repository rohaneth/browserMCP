@echo off
echo ==============================================
echo Starting Browser Agent (Local Mode / No Docker)
echo ==============================================

echo [1/3] Setting up local SQLite database variables...
set DATABASE_URL=sqlite:///./demo.db

echo [2/3] Starting FastAPI Backend...
start cmd /k "cd apps\api && uvicorn main:app --reload --port 8000"

echo [3/3] Starting Next.js Frontend...
start cmd /k "cd apps\web && npm run dev"

echo Done!
echo - API Docs available at: http://localhost:8000/docs
echo - Chat UI available at: http://localhost:3000/chat
