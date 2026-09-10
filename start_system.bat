@echo off
echo ======================================================================
echo    UAV Propulsion Digital Twin & Predictive Maintenance System
echo ======================================================================
echo Launching Digital Twin Backend (Python FastAPI) and GCS Dashboard...

cd /d "%~dp0backend"
start "Digital Twin Backend (Port 8000)" cmd /k "python -m pip install -r requirements.txt && python main.py"

timeout /t 3 /nobreak >nul

cd /d "%~dp0frontend"
start "GCS Dashboard Frontend (Port 3000)" cmd /k "npm install && npm run dev"

echo System services launched! 
echo GCS Dashboard running at: http://localhost:3000
echo Backend API & WebSocket running at: http://localhost:8000
echo ======================================================================
