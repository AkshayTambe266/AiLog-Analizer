@echo off
REM ============================================
REM AI Log Analyzer - Complete Setup & Start Script
REM Uses Ollama for local AI analysis
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo 🚀 AI LOG ANALYZER - SETUP & START
echo Powered by Ollama AI
echo ============================================
echo.

REM Step 1: Check Prerequisites
echo [Step 1] Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python OK

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 14+
    pause
    exit /b 1
)
echo ✅ Node.js OK

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama not found. Please install from https://ollama.ai
    pause
    exit /b 1
)
echo ✅ Ollama installed

echo.
echo [Step 2] Checking Ollama models...
REM List available models
for /f "tokens=*" %%a in ('ollama list 2^>nul') do (
    if not "%%a"=="NAME" (
        echo   - %%a
    )
)

echo.
echo [Step 3] Starting Ollama service...
REM Check if Ollama is already running
powershell -NoProfile -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -Method GET; Write-Host 'running' } catch { Write-Host 'notrunning' }" > temp_ollama.txt
set /p OLLAMA_STATUS=<temp_ollama.txt
del temp_ollama.txt 2>nul

if "!OLLAMA_STATUS!"=="notrunning" (
    echo ⏳ Starting Ollama...
    start "" "C:\Program Files\Ollama\ollama app.exe"
    timeout /t 3 /nobreak
    echo ✅ Ollama started
) else (
    echo ✅ Ollama already running
)

echo.
echo ============================================
echo 🎯 STARTING APPLICATION
echo ============================================
echo.
echo This will open 3 terminals:
echo   1. Ollama Service (if needed)
echo   2. Backend API (Python)
echo   3. Frontend UI (React)
echo.
echo ⏳ Starting in 5 seconds...
echo.
timeout /t 5 /nobreak

echo.
echo ============================================
echo Terminal 1: BACKEND API
echo ============================================
start "AI Log Analyzer Backend" python -m uvicorn ai_engine.api.main:app --reload --host 127.0.0.1 --port 8000

timeout /t 5 /nobreak

echo.
echo ============================================
echo Terminal 2: FRONTEND UI
echo ============================================
start "AI Log Analyzer Frontend" cmd /k "cd frontend && npm start"

timeout /t 3 /nobreak

echo.
echo ============================================
echo ✅ APPLICATION STARTED!
echo ============================================
echo.
echo 📊 Access Dashboard: http://localhost:3000
echo 🔧 API: http://127.0.0.1:8000
echo 🦙 Ollama: http://localhost:11434
echo.
echo Next steps:
echo   1. Open http://localhost:3000 in your browser
echo   2. Click "Load Logs" to fetch ERROR logs
echo   3. Ollama AI will automatically analyze them
echo   4. Results appear below the logs
echo.
echo 💡 Tips:
echo   - First load may take 30-60 seconds (Ollama processing)
echo   - Check browser console (F12) for detailed logs
echo   - Each error gets AI analysis with:
echo     * Root cause detection
echo     * Severity assessment
echo     * Recommended actions
echo.
echo Press Ctrl+C in any terminal to stop
echo ============================================
echo.

pause

