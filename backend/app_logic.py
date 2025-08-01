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
        self.is_active = False # Overall session active state
        self.is_focus_session = True # True if current session is focus, False if break
        self.is_active_monitoring = False # Controls if processes are being monitored/blocked
        self.monitor_thread = None
        self.timer_thread = None
        self.stop_event = threading.Event()
        self.load_app_mappings()
        
        self.focus_duration = 0 # Stores the set focus duration
        self.break_duration = 0 # Stores the set break duration
        self.allowed_apps_list = [] # Stores the list of display names for allowed apps

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

    def start_session(self, allowed_apps, focus_duration, break_duration):
        """Start focus session with allowed apps and duration, including break logic."""
        if self.is_active:
            logging.warning("Session already active, cannot start new one.")
            self.session_started.emit("Session already active.")
            return "Session already active."
            
        if not allowed_apps:
            logging.warning("No apps selected for session.")
            self.session_started.emit("Select at least one app to start session.")
            return "Select at least one app to start session."
        
        try:
            self.focus_duration = focus_duration
            self.break_duration = break_duration
            self.allowed_apps_list = allowed_apps # Store for use in run_timer loop
            
            # Initial setup for allowed and blocked processes based on selected apps
            self.allowed_processes = [
                self.app_mappings[app] for app in self.allowed_apps_list
                if app in self.app_mappings
            ]
            self.block_list = [
                process for display, process in self.app_mappings.items()
                if display not in self.allowed_apps_list
            ]
            
            logging.info(f"Session setup | Focus: {focus_duration} mins, Break: {break_duration} mins")
            logging.info(f"Allowed: {self.allowed_processes}")
            logging.info(f"Blocking: {self.block_list}")
            
            self.is_active = True
            self.is_focus_session = True # Start with focus session
            self.is_active_monitoring = True # Monitoring is active during focus
            self.stop_event.clear()
            
            # Start monitoring in a separate thread
            self.monitor_thread = threading.Thread(target=self.monitor_processes)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Start the main timer loop in a separate thread
            self.timer_thread = threading.Thread(target=self.run_session_cycle)
            self.timer_thread.daemon = True
            self.timer_thread.start()
            
            success_msg = "Focus session started successfully."
            self.session_started.emit(success_msg)
            logging.info(success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"Error starting session: {str(e)}"
            logging.error(f"Start session error: {e}")
            self.session_started.emit(error_msg)
            return error_msg

    def _run_single_timer(self, duration_minutes, session_type):
        """Internal function to run a single timer session (focus or break)."""
        total_seconds = duration_minutes * 60
        logging.info(f"Starting {session_type} timer for {duration_minutes} minutes.")
        
        while total_seconds > 0 and self.is_active and not self.stop_event.is_set():
            mins, secs = divmod(total_seconds, 60)
            self.timer_updated.emit(mins, secs)
            time.sleep(1)
            total_seconds -= 1
        
        # Return True if the timer completed naturally, False if stopped early
        return total_seconds <= 0 and self.is_active and not self.stop_event.is_set()

    def run_session_cycle(self):
        """Manages the cycle between focus and break sessions."""
        logging.info("Session cycle started.")
        while self.is_active and not self.stop_event.is_set():
            # --- Focus Session ---
            self.is_focus_session = True
            self.is_active_monitoring = True # Activate monitoring for focus
            self.status_changed.emit("Focus session in progress")
            logging.info("Entering Focus Session.")
            
            # Run the focus timer
            if self._run_single_timer(self.focus_duration, 'focus'):
                logging.info("Focus session completed.")
                if not self.is_active or self.stop_event.is_set():
                    break # Stop if session was cancelled during focus timer
                
                # --- Break Session ---
                self.is_focus_session = False
                self.is_active_monitoring = False # Deactivate monitoring for break
                self.status_changed.emit("Break session!")
                logging.info("Entering Break Session.")

                # Run the break timer
                if self._run_single_timer(self.break_duration, 'break'):
                    logging.info("Break session completed. Returning to Focus.")
                    # Loop will continue to start another focus session
                else:
                    logging.info("Break session stopped early.")
                    break # Stop if session was cancelled during break timer
            else:
                logging.info("Focus session stopped early.")
                break # Stop if session was cancelled during focus timer
        
        logging.info("Session cycle finished.")
        self.stop_session() # Ensure full stop if loop exits

    def stop_session(self):
        """Stop focus session and clean up threads."""
        if self.is_active:
            self.is_active = False
            self.stop_event.set() # Signal threads to stop
            
            logging.info("Stopping session, waiting for threads to join.")
            
            # Wait for threads to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)
                if self.monitor_thread.is_alive():
                    logging.warning("Monitor thread did not terminate gracefully.")
            
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=2.0)
                if self.timer_thread.is_alive():
                    logging.warning("Timer thread did not terminate gracefully.")
            
            success_msg = "Session stopped."
            self.session_stopped.emit(success_msg)
            logging.info(success_msg)
            return success_msg
            
        logging.info("No active session to stop.")
        return "No active session."

    def monitor_processes(self):
        """Monitor and block unselected processes only when monitoring is active."""
        logging.info("Process monitoring thread started.")
        blocked_count = 0
        
        while not self.stop_event.is_set():
            if self.is_active_monitoring: # Only monitor if this flag is True
                try:
                    current_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
                    
                    for process in self.block_list:
                        if process.lower() in current_processes:
                            if self.terminate_process(process):
                                blocked_count += 1
                                self.app_blocked.emit(process)
                                logging.info(f"Blocked: {process}")
                    
                except Exception as e:
                    logging.error(f"Monitoring error: {e}")
                    self.status_changed.emit(f"Monitoring error: {e}")
            
            time.sleep(5) # Check every 5 seconds
        
        logging.info(f"Process monitoring thread stopped | Total blocked: {blocked_count}")

    def terminate_process(self, process_name):
        """Terminate a process by name."""
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
        """Get list of apps with display names."""
        return list(self.app_mappings.keys())

    def add_custom_app(self, display_name, process_name):
        """Add custom app to mappings and save."""
        try:
            self.app_mappings[display_name] = process_name
            with open(Path(__file__).parent / 'process_map.json', 'w') as f:
                json.dump(self.app_mappings, f, indent=2)
            logging.info(f"Added custom app: {display_name} -> {process_name}")
            return True
        except Exception as e:
            logging.error(f"Add app error: {e}")
            return False

