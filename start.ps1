# CrimeGuard ChatBot - Automated Startup Script
# This script starts ngrok, updates .env with the URL, and starts the backend server

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CrimeGuard ChatBot - Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NGROK_PATH = "AI_backend\app\ngrok\ngrok.exe"
$BACKEND_PORT = 8000
$ENV_FILE = "AI_backend\.env"

# Step 0: Check and free port 8000
Write-Host "[0/5] Checking if port $BACKEND_PORT is available..." -ForegroundColor Yellow
$portProcess = Get-NetTCPConnection -LocalPort $BACKEND_PORT -State Listen -ErrorAction SilentlyContinue
if ($portProcess) {
    $processId = $portProcess.OwningProcess
    $processName = (Get-Process -Id $processId).ProcessName
    Write-Host "      Port $BACKEND_PORT is in use by process: $processName (PID: $processId)" -ForegroundColor Yellow
    Write-Host "      Stopping process..." -ForegroundColor Yellow
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "      Port $BACKEND_PORT is now free" -ForegroundColor Green
} else {
    Write-Host "      Port $BACKEND_PORT is available" -ForegroundColor Green
}
Write-Host ""

# Step 1: Kill any existing ngrok processes
Write-Host "[1/5] Checking for existing ngrok processes..." -ForegroundColor Yellow
$ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($ngrokProcesses) {
    Write-Host "      Found existing ngrok process(es). Stopping them..." -ForegroundColor Yellow
    Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "      Stopped existing ngrok processes" -ForegroundColor Green
} else {
    Write-Host "      No existing ngrok processes found" -ForegroundColor Green
}

# Step 2: Start ngrok in background
Write-Host ""
Write-Host "[2/5] Starting ngrok tunnel..." -ForegroundColor Yellow

if (-Not (Test-Path $NGROK_PATH)) {
    Write-Host "      Error: ngrok.exe not found at $NGROK_PATH" -ForegroundColor Red
    Write-Host "      Please ensure ngrok is installed in the correct location." -ForegroundColor Red
    exit 1
}

# Start ngrok in background
$ngrokJob = Start-Process -FilePath $NGROK_PATH -ArgumentList "http", $BACKEND_PORT -WindowStyle Hidden -PassThru

Write-Host "      Waiting for ngrok to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 3: Get ngrok URL from API
Write-Host ""
Write-Host "[3/5] Retrieving ngrok public URL..." -ForegroundColor Yellow

try {
    $ngrokApi = "http://127.0.0.1:4040/api/tunnels"
    $response = Invoke-RestMethod -Uri $ngrokApi -Method Get -ErrorAction Stop
    $publicUrl = $response.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1 -ExpandProperty public_url
    
    if ($publicUrl) {
        Write-Host "      ngrok URL obtained: $publicUrl" -ForegroundColor Green
    } else {
        Write-Host "      Could not retrieve ngrok URL from API" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "      Error connecting to ngrok API" -ForegroundColor Red
    Write-Host "      Make sure ngrok started successfully" -ForegroundColor Red
    exit 1
}

# Step 4: Update .env file
Write-Host ""
Write-Host "[4/5] Updating .env file with ngrok URL..." -ForegroundColor Yellow

if (-Not (Test-Path $ENV_FILE)) {
    Write-Host "      Error: .env file not found at $ENV_FILE" -ForegroundColor Red
    exit 1
}

$envContent = Get-Content $ENV_FILE -Raw

if ($envContent -match "BASE_URL=.*") {
    $envContent = $envContent -replace "BASE_URL=.*", "BASE_URL=$publicUrl"
    Write-Host "      Updated existing BASE_URL" -ForegroundColor Green
} else {
    $addition = "`n`n# Base URL for audio file serving`nBASE_URL=$publicUrl"
    $envContent = $envContent -replace "(LOG_LEVEL=.*)", "`$1$addition"
    Write-Host "      Added BASE_URL to .env" -ForegroundColor Green
}

Set-Content -Path $ENV_FILE -Value $envContent -NoNewline
Write-Host "      .env file updated successfully" -ForegroundColor Green
Write-Host "      BASE_URL=$publicUrl" -ForegroundColor Cyan

# Step 5: Start backend
Write-Host ""
Write-Host "[5/5] Starting backend server..." -ForegroundColor Yellow
Write-Host "      Activating conda environment: MAIN" -ForegroundColor Yellow

# Activate conda MAIN environment
$condaPath = "C:\Users\DEATHSEC\anaconda3"
$activateScript = "$condaPath\Scripts\activate.bat"

Write-Host "      Backend will start on http://localhost:$BACKEND_PORT" -ForegroundColor Cyan
Write-Host "      Public URL (for Twilio): $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  STARTUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services Status:" -ForegroundColor Yellow
Write-Host "   ngrok tunnel: RUNNING" -ForegroundColor Green
Write-Host "   Public URL: $publicUrl" -ForegroundColor Green
Write-Host "   Backend: Starting now..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Wait for backend to fully start" -ForegroundColor White
Write-Host "   2. Start frontend: cd Frontend && npm start" -ForegroundColor White
Write-Host "   3. Test emergency call feature" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "   - Keep this window open (ngrok runs in background)" -ForegroundColor White
Write-Host "   - Press Ctrl+C to stop backend and cleanup" -ForegroundColor White
Write-Host ""

try {
    Set-Location "AI_backend"
    
    # Run python with conda MAIN environment
    & cmd /c "conda activate MAIN && python main.py"
} finally {
    Write-Host ""
    Write-Host ""
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
    Write-Host "   Stopped ngrok" -ForegroundColor Green
    Write-Host "   Cleanup complete" -ForegroundColor Green
    Write-Host ""
}
