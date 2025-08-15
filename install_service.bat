@echo off
cd /d "%~dp0"
echo [1/3] Creating Python virtual environment...
if not exist venv (
    python -m venv venv
)
echo [2/3] Installing required packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo [3/3] Installing and starting the EDMSCrawler service...
venv\Scripts\python.exe crawler_service.py install
venv\Scripts\python.exe crawler_service.py --startup auto start
echo.
echo Setup complete. The Simplified Crawler service is now installed and running.
pause