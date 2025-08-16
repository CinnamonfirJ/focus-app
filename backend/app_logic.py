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
        
        # Updated timer variables for new logic
        self.total_work_time = 0  # Total time user wants to work
        self.break_duration = 0   # Break duration
        self.focus_session_time = 0  # Calculated focus time (total - break)
        self.single_focus_duration = 0  # Each focus session (focus_session_time / 2)
        self.allowed_apps_list = []
        self.current_session_part = 1  # Track which part of session we're in (1, 2, or 3)

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

    def start_session(self, allowed_apps, total_work_time, break_duration):
        """Start focus session with new timer logic: (Focus/2) → Break → (Focus/2)"""
        if self.is_active:
            logging.warning("Session already active, cannot start new one.")
            self.session_started.emit("Session already active.")
            return "Session already active."
            
        if not allowed_apps:
            logging.warning("No apps selected for session.")
            self.session_started.emit("Select at least one app to start session.")
            return "Select at least one app to start session."
        
        # Validate that total work time is greater than break time
        if total_work_time <= break_duration:
            error_msg = "Total work time must be greater than break time."
            logging.warning(error_msg)
            self.session_started.emit(error_msg)
            return error_msg
        
        try:
            # Calculate the new timer values
            self.total_work_time = total_work_time
            self.break_duration = break_duration
            self.focus_session_time = total_work_time - break_duration
            # Round to nearest 0.5 minutes to avoid weird decimals
            self.single_focus_duration = round((self.focus_session_time / 2) * 2) / 2
            self.allowed_apps_list = allowed_apps
            self.current_session_part = 1
            
            # Setup allowed and blocked processes
            self.allowed_processes = []
            self.block_list = []
            
            # Get all unique process names for allowed apps
            allowed_process_names = set()
            for app in self.allowed_apps_list:
                if app in self.app_mappings:
                    process_name = self.app_mappings[app]
                    self.allowed_processes.append(process_name)
                    allowed_process_names.add(process_name.lower())
            
            # Create block list - only include processes NOT in allowed list
            for display, process in self.app_mappings.items():
                if process.lower() not in allowed_process_names:
                    self.block_list.append(process)
            
            logging.info(f"Session setup | Total Work: {total_work_time} mins, Break: {break_duration} mins")
            logging.info(f"Focus Session Time: {self.focus_session_time} mins, Each Focus: {self.single_focus_duration} mins")
            logging.info(f"Allowed: {self.allowed_processes}")
            logging.info(f"Blocking: {self.block_list}")
            
            self.is_active = True
            self.is_focus_session = True # Start with first focus session
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
        # Convert to whole seconds to avoid float issues
        total_seconds = int(duration_minutes * 60)
        logging.info(f"Starting {session_type} timer for {duration_minutes} minutes ({total_seconds} seconds).")
        
        while total_seconds > 0 and self.is_active and not self.stop_event.is_set():
            mins, secs = divmod(total_seconds, 60)
            self.timer_updated.emit(int(mins), int(secs))
            time.sleep(1)
            total_seconds -= 1
        
        # Return True if the timer completed naturally, False if stopped early
        return total_seconds <= 0 and self.is_active and not self.stop_event.is_set()

    def run_session_cycle(self):
        """Manages the new session cycle: (Focus/2) → Break → (Focus/2) → End"""
        logging.info("Session cycle started with new timer logic.")
        
        while self.is_active and not self.stop_event.is_set():
            
            # --- First Focus Session (Part 1) ---
            if self.current_session_part == 1:
                self.is_focus_session = True
                self.is_active_monitoring = True
                self.status_changed.emit(f"Focus Session 1/2 - {self.single_focus_duration:.1f} min")
                logging.info("Entering First Focus Session (1/2).")
                
                if self._run_single_timer(self.single_focus_duration, 'focus part 1'):
                    logging.info("First focus session completed.")
                    self.current_session_part = 2
                    if not self.is_active or self.stop_event.is_set():
                        break
                else:
                    logging.info("First focus session stopped early.")
                    break
            
            # --- Break Session ---
            elif self.current_session_part == 2:
                self.is_focus_session = False
                self.is_active_monitoring = False
                self.status_changed.emit(f"Break Time - {self.break_duration} min")
                logging.info("Entering Break Session.")
                
                if self._run_single_timer(self.break_duration, 'break'):
                    logging.info("Break session completed.")
                    self.current_session_part = 3
                    if not self.is_active or self.stop_event.is_set():
                        break
                else:
                    logging.info("Break session stopped early.")
                    break
            
            # --- Second Focus Session (Part 2) ---
            elif self.current_session_part == 3:
                self.is_focus_session = True
                self.is_active_monitoring = True
                self.status_changed.emit(f"Focus Session 2/2 - {self.single_focus_duration:.1f} min")
                logging.info("Entering Second Focus Session (2/2).")
                
                if self._run_single_timer(self.single_focus_duration, 'focus part 2'):
                    logging.info("Second focus session completed. Session finished!")
                    self.status_changed.emit("Session completed successfully!")
                    break  # Session is complete
                else:
                    logging.info("Second focus session stopped early.")
                    break
        
        logging.info("Session cycle finished.")
        # Clean up from within the timer thread without joining itself
        self._cleanup_session()

    def _cleanup_session(self):
        """Internal cleanup method called from timer thread"""
        self.is_active = False
        self.stop_event.set()
        self.current_session_part = 1
        self.is_active_monitoring = False
        
        success_msg = "Session finished."
        self.session_stopped.emit(success_msg)
        logging.info(success_msg)

    def stop_session(self):
        """Stop focus session and clean up threads (called from UI thread)."""
        if self.is_active:
            self.is_active = False
            self.stop_event.set() # Signal threads to stop
            
            logging.info("Stopping session, waiting for threads to join.")
            
            # Wait for threads to finish (only if we're not in the timer thread)
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)
                if self.monitor_thread.is_alive():
                    logging.warning("Monitor thread did not terminate gracefully.")
            
            if self.timer_thread and self.timer_thread.is_alive() and self.timer_thread != threading.current_thread():
                self.timer_thread.join(timeout=2.0)
                if self.timer_thread.is_alive():
                    logging.warning("Timer thread did not terminate gracefully.")
            
            # Reset session state
            self.current_session_part = 1
            self.is_active_monitoring = False
            
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
        
        # Create a set of allowed process names for faster lookup
        allowed_process_names = set(p.lower() for p in self.allowed_processes)
        
        while not self.stop_event.is_set():
            if self.is_active_monitoring: # Only monitor if this flag is True
                try:
                    # Get current running processes
                    for proc in psutil.process_iter(['name']):
                        process_name = proc.name()
                        
                        # Only terminate if process is in block list AND not in allowed list
                        if (process_name in self.block_list and 
                            process_name.lower() not in allowed_process_names):
                            
                            try:
                                proc.terminate()
                                blocked_count += 1
                                self.app_blocked.emit(process_name)
                                logging.info(f"Blocked: {process_name}")
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                                logging.warning(f"Termination failed for {process_name}: {e}")
                            except Exception as e:
                                logging.error(f"Unexpected termination error for {process_name}: {e}")
                    
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