@echo off
cd /d "%~dp0"
echo Stopping and uninstalling the EDMSCrawler service...
venv\Scripts\python.exe crawler_service.py stop >nul 2>&1
venv\Scripts\python.exe crawler_service.py remove
echo.
echo Service uninstalled successfully.
pause