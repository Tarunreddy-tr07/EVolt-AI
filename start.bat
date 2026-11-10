@echo off
echo Starting ChargeRL: EVolt Charging & Battery Management System...

:: Start FastAPI Backend
start cmd /k "python -m uvicorn backend.app.main:app --reload --port 8000"

:: Start React Vite Frontend
start cmd /k "cd frontend && npm run dev"

echo Both backend (port 8000) and frontend (port 5173) servers launched!
