@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like '*streamlit_app.py*' -and $_.CommandLine -like '*--server.port 8741*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>nul

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":8741 .*LISTENING"') do (
    if not "%%P"=="0" (
        if not defined stopped_%%P (
            set "stopped_%%P=1"
            echo Port 8741 is in use. Stopping process %%P...
            taskkill /pid %%P /t /f >nul 2>nul
        )
    )
)

ping 127.0.0.1 -n 4 >nul

netstat -ano | findstr /r /c:":8741 .*LISTENING" >nul
if not errorlevel 1 (
    echo Error: port 8741 could not be released.
    echo Run this launcher as Administrator or stop the listener manually.
    pause
    exit /b 1
)

curl.exe --silent --fail --max-time 2 http://127.0.0.1:8742/health >nul 2>nul
if not errorlevel 1 (
    echo Stopping the existing NaviDC-OCR worker so its logs attach here...
    wsl.exe -d Ubuntu-24.04 -- pkill -f "uvicorn agentic_document_extraction.worker:app" >nul 2>nul
    ping 127.0.0.1 -n 2 >nul
)

where uv >nul 2>nul
if errorlevel 1 (
    echo Error: uv is not installed or is not available on PATH.
    echo Install uv, then run this launcher again.
    pause
    exit /b 1
)

echo Starting NaviDC-OCR Document Extraction Studio...
echo Open http://localhost:8741 if the browser does not open automatically.
uv run python -m streamlit run streamlit_app.py --server.port 8741 %*

if errorlevel 1 (
    echo.
    echo The application stopped with an error.
    pause
    exit /b 1
)

endlocal
