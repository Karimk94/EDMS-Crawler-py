@echo off
REM =================================================================
REM  Stops the EDMS Crawler Windows Service.
REM =================================================================

REM Change directory to the script's location
cd /d "%~dp0"

echo Stopping the EDMSCrawler service...
REM Use the python from the virtual environment
venv\Scripts\python.exe crawler_service.py stop

echo.
pause
