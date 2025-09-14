@echo off
chcp 65001 >nul

REM Switch to script directory
cd /d "%~dp0"

echo ========================================
echo     ArborVista Smart Paper Reader
echo ========================================

REM Check Python environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found, please install Python first
    pause
    exit /b 1
)

REM Check if in virtual environment
echo [INFO] Current Python environment: %CONDA_DEFAULT_ENV%
echo [INFO] Current working directory: %CD%

REM Check if necessary files exist
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found, please run in ArborVista root directory
    pause
    exit /b 1
)

if not exist "app\app.py" (
    echo [ERROR] app\app.py not found, please run in ArborVista root directory
    pause
    exit /b 1
)

if not exist "arborvistavue\package.json" (
    echo [ERROR] arborvistavue\package.json not found, please run in ArborVista root directory
    pause
    exit /b 1
)

REM Set environment variables
echo [INFO] Setting environment variables...
if "%MINERU_API_TOKEN%"=="" (
    echo [WARNING] MINERU_API_TOKEN not set, please set it manually:
    echo   set MINERU_API_TOKEN=your_token_here
    echo [INFO] You can also create a .env file with MINERU_API_TOKEN=your_token_here
) else (
    echo [INFO] MINERU_API_TOKEN is already set
)

REM Install dependencies
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies, please check network or Python environment
    pause
    exit /b 1
)

REM Start backend service
echo [INFO] Starting backend service...
start "ArborVista Backend" cmd /k "cd /d %~dp0 && python app\app.py"

REM Wait for backend to start
echo [INFO] Waiting for backend service to start...
timeout /t 3 /nobreak >nul

REM Check frontend dependencies
echo [INFO] Checking frontend dependencies...
cd arborvistavue
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    npm install
)

REM Start frontend service
echo [INFO] Starting frontend service...
start "ArborVista Frontend" cmd /k "cd /d \"%~dp0arborvistavue\" & npm run serve"

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set LOCAL_IP=%%b
        goto :ip_found
    )
)
:ip_found

echo.
echo ========================================
echo Project started successfully!
echo.
echo Local access addresses:
echo   Backend: http://127.0.0.1:5000
echo   Frontend: http://127.0.0.1:8080
echo.
echo Network access addresses:
echo   Backend: http://%LOCAL_IP%:5000
echo   Frontend: http://%LOCAL_IP%:8080
echo.
echo Notes:
echo   - MINERU_API_TOKEN environment variable is set
echo   - Stable network connection required for MinerU API
echo   - Other devices can access via network addresses
echo   - Ensure firewall allows ports 5000 and 8080
echo ========================================
echo Press any key to exit...
pause >nul