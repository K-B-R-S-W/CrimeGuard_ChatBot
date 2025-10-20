@echo off
REM CrimeGuard ChatBot - Quick Start (Windows Batch)
REM This script starts all services automatically

echo ========================================
echo   CrimeGuard ChatBot - Quick Start
echo ========================================
echo.

REM Use PowerShell to run the full startup script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0start.ps1"

pause
