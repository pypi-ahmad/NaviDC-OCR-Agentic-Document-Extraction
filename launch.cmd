@echo off
setlocal

cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo Error: uv is not installed or is not available on PATH.
    echo Install uv, then run this launcher again.
    pause
    exit /b 1
)

echo Starting NaviDC-OCR Document Extraction Studio...
echo Open http://localhost:8741 if the browser does not open automatically.
uv run streamlit run streamlit_app.py --server.port 8741 %*

if errorlevel 1 (
    echo.
    echo The application stopped with an error.
    pause
    exit /b 1
)

endlocal
