import json
import psutil
import threading
import time
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='focusguard.log',
    filemode='w'
)

class FocusGuard(QObject):
    # Define signals for UI communication
    session_started = pyqtSignal(str)
    session_stopped = pyqtSignal(str)
    app_blocked = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    timer_updated = pyqtSignal(int, int)  # minutes, seconds
    
    def __init__(self):
        super().__init__()
        self.allowed_processes = []
        self.block_list = []
        self.is_active = False
        self.monitor_thread = None
        self.timer_thread = None
        self.stop_event = threading.Event()
        self.load_app_mappings()
        logging.info("FocusGuard initialized")

    def load_app_mappings(self):
        """Load app display name to process name mappings"""
        try:
            with open(Path(__file__).parent / 'process_map.json', 'r') as f:
                self.app_mappings = json.load(f)
            logging.info(f"Loaded {len(self.app_mappings)} app mappings")
        except Exception as e:
            logging.error(f"Error loading process map: {e}")
            self.app_mappings = {}

    def start_session(self, allowed_apps, duration):
        """Start focus session with allowed apps and duration"""
        if not allowed_apps:
            logging.warning("No apps selected for session")
            self.session_started.emit("Select at least one app to start session")
            return
            
        try:
            # Convert display names to process names
            self.allowed_processes = [
                self.app_mappings[app] for app in allowed_apps 
                if app in self.app_mappings
            ]
            
            # Create block list (unselected apps from our list)
            self.block_list = [
                process for display, process in self.app_mappings.items()
                if display not in allowed_apps
            ]
            
            logging.info(f"Session started | Duration: {duration} mins")
            logging.info(f"Allowed: {self.allowed_processes}")
            logging.info(f"Blocking: {self.block_list}")
            
            self.is_active = True
            self.stop_event.clear()
            
            # Start monitoring in separate thread
            self.monitor_thread = threading.Thread(target=self.monitor_processes)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Start timer in separate thread
            self.timer_thread = threading.Thread(target=self.run_timer, args=(duration,))
            self.timer_thread.daemon = True
            self.timer_thread.start()
            
            success_msg = "Session started successfully"
            self.session_started.emit(success_msg)
            logging.info(success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logging.error(f"Start session error: {e}")
            self.session_started.emit(error_msg)
            return error_msg

    def run_timer(self, duration_minutes):
        """Run the focus session timer and emit updates"""
        total_seconds = duration_minutes * 60
        while total_seconds > 0 and self.is_active:
            mins, secs = divmod(total_seconds, 60)
            self.timer_updated.emit(mins, secs)
            time.sleep(1)
            total_seconds -= 1
            
        # If timer completed naturally, stop session
        if self.is_active:
            self.stop_session()

    def stop_session(self):
        """Stop focus session"""
        if self.is_active:
            self.is_active = False
            self.stop_event.set()
            
            # Wait for threads to finish
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
            if self.timer_thread:
                self.timer_thread.join(timeout=2.0)
                
            success_msg = "Session stopped"
            self.session_stopped.emit(success_msg)
            logging.info(success_msg)
            return success_msg
            
        return "No active session"

    def monitor_processes(self):
        """Monitor and block unselected processes"""
        logging.info("Monitoring started")
        blocked_count = 0
        
        while not self.stop_event.is_set():
            try:
                # Get current processes
                current_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
                
                # Check against block list
                for process in self.block_list:
                    if process.lower() in current_processes:
                        if self.terminate_process(process):
                            blocked_count += 1
                            self.app_blocked.emit(process)
                            logging.info(f"Blocked: {process}")
            
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                self.status_changed.emit(f"Monitoring error: {e}")
            
            # Check every 5 seconds
            time.sleep(5)
        
        logging.info(f"Monitoring stopped | Total blocked: {blocked_count}")

    def terminate_process(self, process_name):
        """Terminate a process by name"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.name().lower() == process_name.lower():
                    proc.terminate()
                    logging.debug(f"Terminated: {proc.name()} (PID: {proc.pid})")
                    return True
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.warning(f"Termination failed for {process_name}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected termination error: {e}")
            return False

    def get_app_list(self):
        """Get list of apps with display names"""
        return list(self.app_mappings.keys())

    def add_custom_app(self, display_name, process_name):
        """Add custom app to mappings"""
        try:
            self.app_mappings[display_name] = process_name
            with open(Path(__file__).parent / 'process_map.json', 'w') as f:
                json.dump(self.app_mappings, f, indent=2)
            logging.info(f"Added custom app: {display_name} -> {process_name}")
            return True
        except Exception as e:
            logging.error(f"Add app error: {e}")
            return False