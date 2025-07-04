import psutil

available_apps = ['chrome.exe', 'firefox.exe', 'notepad.exe']
# available_apps = [proc.name() for proc in psutil.process_iter()]
# print("Available Applications:", available_apps)
unwanted_app = ['chrome.exe', 'firefox.exe',]
import psutil
import os

# List of keywords to ignore in background/utility apps
background_keywords = [
    "update", "tray", "service", "clicktorun", "assistant", "monitor",
    "apmsg", "jusched", "experience", "cloud", "pluginhost", "defense",
    "watchdog", "hid", "svc", "daemon", "arm", "dns", "glidepoint", "safe"
]

# Optional: Whitelist user-facing apps you care about
important_apps = ["chrome.exe", "Code.exe", "WINWORD.EXE", "notepad.exe", "vlc.exe", "python.exe"]

# Function to check if a process name/path is likely a background service
def is_background_process(name, exe):
    lname = name.lower()
    if any(keyword in lname for keyword in background_keywords):
        return True
    if "windowsapps" in exe.lower():
        return True
    if "common files" in exe.lower():
        return True
    return False

apps = []

for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
    try:
        name = proc.info['name']
        exe = proc.info['exe']
        user = proc.info['username']

        if not name or not exe:
            continue

        if user and ('SYSTEM' in user or 'NETWORK SERVICE' in user or 'LOCAL SERVICE' in user):
            continue

        if is_background_process(name, exe):
            continue

        apps.append((name, exe))
        p = psutil.Process

    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        continue

# # Optional: Filter to only apps you care about (whitelist)
# # apps = [app for app in apps if app[0] in important_apps]

# # Remove duplicates
# apps = list(set(apps))

# # Show final list
# for name, exe in sorted(apps):
#     print(f"{name} - {exe}")


# Features
# 1. Time selection
# 2. App blocker selection
# 3. Focus home page with timer running and blocked apps list
# 4. Blocked apps page with password input for removing blocked apps from list

# PYQT5, PSUTIL, 