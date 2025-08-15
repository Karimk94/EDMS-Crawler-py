@echo off
REM =================================================================
REM  Starts the EDMS Crawler Windows Service.
REM =================================================================

REM Change directory to the script's location
cd /d "%~dp0"

echo Starting the EDMSCrawler service...
REM Use the python from the virtual environment
venv\Scripts\python.exe crawler_service.py start

echo.
pause
