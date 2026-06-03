@echo off
:: Jarvis Windows setup script
:: Run once after cloning. Requires Python 3.11+ and an internet connection.
setlocal

echo.
echo ============================================================
echo  Jarvis - Windows Setup
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Download from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause & exit /b 1
)

:: Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not found. Run: python -m ensurepip
    pause & exit /b 1
)

echo [1/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo.
echo [2/5] Installing Windows-only extras (audio, screen control)...
pip install sounddevice numpy faster-whisper openwakeword pyttsx3 ^
            pycaw comtypes pygetwindow pyautogui mss Pillow
:: Not fatal if some fail on this machine — voice/desktop features just won't work

echo.
echo [3/5] Installing Playwright browser and Chromium...
playwright install chromium
if errorlevel 1 ( echo WARNING: Playwright install failed. Browser tasks won't work. )

echo.
echo [4/5] Pulling Ollama models...
echo  (Ollama must already be installed from https://ollama.com/download)
echo  Checking for ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: ollama not found in PATH. Skipping model pulls.
    echo          Install it from https://ollama.com/download and run:
    echo            ollama pull qwen2.5:7b
    echo            ollama pull qwen2.5:32b
    echo            ollama pull qwen2.5-vl:7b
) else (
    echo Pulling qwen2.5:7b  ^(fast tier - ~4GB^)...
    ollama pull qwen2.5:7b
    echo Pulling qwen2.5:32b ^(smart tier - ~20GB^)...
    ollama pull qwen2.5:32b
    echo Pulling qwen2.5-vl:7b ^(vision tier - ~5GB^)...
    ollama pull qwen2.5-vl:7b
)

echo.
echo [5/5] Setup complete!
echo.
echo ============================================================
echo  How to run Jarvis:
echo.
echo    Browser UI (recommended):
echo      python -m jarvis.main --ui
echo      Then open http://127.0.0.1:8765 in your browser.
echo.
echo    Text mode (terminal):
echo      python -m jarvis.main --text
echo.
echo    Voice mode (say "Jarvis" to activate):
echo      python -m jarvis.main --voice
echo ============================================================
echo.
pause
