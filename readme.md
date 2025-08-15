 EDMS Crawler Service
This application is a lightweight Windows service responsible for triggering the EDMS Middleware API. Its sole purpose is to run continuously in the background on a Windows Server and send an HTTP POST request every 10 minutes.
This decoupled design makes the crawler extremely reliable and easy to maintain, as all complex logic is handled by the middleware.
Features
Runs as a persistent Windows background service.
Automatically starts on server boot.
Calls a configurable middleware endpoint at a 10-minute interval.
Minimal dependencies for high reliability.
Setup and Installation
Ensure Python is installed on the server.
Place the project files in a permanent directory (e.g., C:\EDMS_Crawler_Service).
Configure the MIDDLEWARE_API_URL in the .env file to point to your running middleware API.
Right-click on setup.bat and select "Run as administrator".
This will create the virtual environment, install packages, and set up the Windows service to run automatically.
