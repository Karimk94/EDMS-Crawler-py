import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import servicemanager
    import win32service
    import win32serviceutil
    import win32event
    import threading
    from app import main_crawler_loop
except Exception as e:
    # If imports fail, we can write to a simple log file
    with open("crawler_service_debug.log", "a") as f:
        f.write(f"FATAL ERROR during import: {e}\n")
    sys.exit(1)

class EDMSCrawlerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "EDMSCrawler"
    _svc_display_name_ = "EDMS Document Crawler Service"
    _svc_description_ = "Triggers the EDMS middleware to process documents every 10 minutes."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        
        worker_thread = threading.Thread(target=main_crawler_loop)
        worker_thread.daemon = True
        worker_thread.start()

        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(EDMSCrawlerService)
