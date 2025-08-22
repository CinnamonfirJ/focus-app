import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QFrame,
    QSizePolicy, QMessageBox,  QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer

from backend.app_logic import FocusGuard
from .app_card import AppCard
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.focus_guard = FocusGuard()
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        self.setWindowTitle("FocusGuard - Distraction Blocker")
        self.setFixedSize(900, 650)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)
         
    
        # Left sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #939B9B;") # Light brown color, kumba edited 
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # Timer controls - UPDATED FOR NEW LOGIC
        timer_label = QLabel("🕒 Total Work Time")
        timer_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        sidebar_layout.addWidget(timer_label)
        
        # Time input
        time_layout = QHBoxLayout()
        self.time_input = QSpinBox()
        self.time_input.setRange(5, 240)  # Minimum 5 minutes
        self.time_input.setValue(30)  # Default 30 minutes total
        self.time_input.setFixedHeight(40)
        self.time_input.valueChanged.connect(self.update_calculated_times)
        time_layout.addWidget(self.time_input)
        
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(40, 40)
        plus_btn.clicked.connect(lambda: self.time_input.setValue(self.time_input.value() + 1))
        time_layout.addWidget(plus_btn)
        
        minus_btn = QPushButton("-")
        minus_btn.setFixedSize(40, 40)
        minus_btn.clicked.connect(lambda: self.time_input.setValue(self.time_input.value() - 1))
        time_layout.addWidget(minus_btn)
        sidebar_layout.addLayout(time_layout)
        
        # Preset times
        presets = [15, 30, 45, 60, 90, 120]
        presets_layout = QGridLayout()
        
        for i, time_val in enumerate(presets):
            btn = QPushButton(str(time_val))
            btn.setCheckable(True)
            btn.setStyleSheet(
        """
            QPushButton {
            background-color: #656D6D; 
            color: white; 
            border-radius: 15px; 
            border: none; 
            font-weight: bold;
            padding: 10px;  /* Recommended for better appearance */
        }
        QPushButton:hover {
            background-color: #7A8585;  /* Slightly lighter color on hover */
            /* Add other hover effects here */
        }
        QPushButton:pressed {
           background-color: #525A5A;  /* Darker color when pressed */
        }
        """
   )
            if time_val == 30:  # Changed default to 30
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, t=time_val: self.time_input.setValue(t))
            presets_layout.addWidget(btn, i//3, i%3)
        sidebar_layout.addLayout(presets_layout)

        # Break time section
        break_label = QLabel("☕ Break Duration")
        break_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        sidebar_layout.addWidget(break_label)

        break_time_layout = QHBoxLayout()
        self.break_time_input = QSpinBox()
        self.break_time_input.setRange(1, 30) # Max 30 minutes break
        self.break_time_input.setValue(5) # 5 minutes default
        self.break_time_input.setFixedHeight(40)
        self.break_time_input.valueChanged.connect(self.update_calculated_times)
        break_time_layout.addWidget(self.break_time_input)
        
        break_plus_btn = QPushButton("+")
        break_plus_btn.setFixedSize(40, 40)
        break_plus_btn.clicked.connect(lambda: self.break_time_input.setValue(self.break_time_input.value() + 1))
        break_time_layout.addWidget(break_plus_btn)
        
        break_minus_btn = QPushButton("-")
        break_minus_btn.setFixedSize(40, 40)
        break_minus_btn.clicked.connect(lambda: self.break_time_input.setValue(self.break_time_input.value() - 1))
        break_time_layout.addWidget(break_minus_btn)

        sidebar_layout.addLayout(break_time_layout)
        
        # NEW: Display calculated focus times
        self.calculation_label = QLabel()
        self.calculation_label.setFont(QFont("Segoe UI", 10))
        self.calculation_label.setWordWrap(True)
        self.calculation_label.setStyleSheet("color: #2c3e50; background-color: rgba(255,255,255,0.8); padding: 8px; border-radius: 5px;")
        sidebar_layout.addWidget(self.calculation_label)
        
        # Timer display
        self.timer_display = QLabel("12:30")
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setFont(QFont("Courier New", 48, QFont.Bold))
        sidebar_layout.addWidget(self.timer_display)
        
        # Status indicator
        status_layout = QHBoxLayout()
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(12, 12)
        self.status_dot.setStyleSheet("background-color: #e74c3c; border-radius: 6px;")
        status_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("Focus session not started")
        status_layout.addWidget(self.status_text)
        sidebar_layout.addLayout(status_layout)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("🚀 Start Focus Session")
        self.start_btn.setStyleSheet(
        """
            QPushButton {
            background-color: #656D6D; 
            color: white; 
            border-radius: 20px; 
            border: none; 
            font-weight: bold;
            padding: 10px;  /* Recommended for better appearance */
        }
        QPushButton:hover {
            background-color: #7A8585;  /* Slightly lighter color on hover */
            /* Add other hover effects here */
        }
        QPushButton:pressed {
           background-color: #525A5A;  /* Darker color when pressed */
        }
        """
   )
        
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.start_session)
        sidebar_layout.addWidget(self.start_btn)
        
        # self.stop_btn = QPushButton("⏹️ Stop Session")
        # self.stop_btn.setStyleSheet(
        #     "background-color: #e9ecef; font-weight: bold;"
        # )
        # self.stop_btn.setFixedHeight(50)
        # self.stop_btn.clicked.connect(self.stop_session)
        # self.stop_btn.setVisible(False)
        # sidebar_layout.addWidget(self.stop_btn)
        
        sidebar_layout.addStretch()
        
        # Right content area
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(15)
        
        # Apps title
        apps_title = QLabel("📱 Select Apps to Allow")
        apps_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        content_layout.addWidget(apps_title)
        
        # Description
        desc = QLabel(
            "Select applications you want to work with. All other apps will be "
            "blocked during your focus sessions."
        )
        desc.setWordWrap(True)
        content_layout.addWidget(desc)
        
        # Apps grid with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.apps_container = QWidget()
        self.apps_grid = QGridLayout(self.apps_container)
        self.apps_grid.setSpacing(20)
        self.apps_grid.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(self.apps_container)
        content_layout.addWidget(scroll_area)
        
        # Add app button
        self.add_app_btn = QPushButton("+ Add Application")
        self.add_app_btn.setStyleSheet(
        """
            QPushButton {
            background-color: #656D6D; 
            color: white; 
            border-radius: 20px; 
            border: none; 
            font-weight: bold;
            padding: 10px;  /* Recommended for better appearance */
        }
        QPushButton:hover {
            background-color: #7A8585;  /* Slightly lighter color on hover */
            /* Add other hover effects here */
        }
        QPushButton:pressed {
           background-color: #525A5A;  /* Darker color when pressed */
        }
        """
   )
        
        self.add_app_btn.setFixedHeight(40)
        self.add_app_btn.clicked.connect(self.add_custom_app)
        content_layout.addWidget(self.add_app_btn)
        
        # Add both sections to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        
        # Load apps and initialize calculated times
        self.load_apps()
        self.update_calculated_times()
        
    def update_calculated_times(self):
        """Update the display of calculated focus times"""
        total_time = self.time_input.value()
        break_time = self.break_time_input.value()
        
        if total_time <= break_time:
            self.calculation_label.setText("⚠️ Total time must be greater than break time!")
            self.calculation_label.setStyleSheet("color: #e74c3c; background-color: rgba(255,255,255,0.8); padding: 8px; border-radius: 5px;")
            self.start_btn.setEnabled(False)
        else:
            focus_time = total_time - break_time
            # Round to nearest 0.5 minutes to avoid weird decimals
            single_focus = round((focus_time / 2) * 2) / 2
            
            self.calculation_label.setText(
                f"📊 Session Plan:\n"
                f"• Focus 1: {single_focus:.1f} min\n"
                f"• Break: {break_time} min\n"
                f"• Focus 2: {single_focus:.1f} min\n"
                f"• Total: {total_time} min"
            )
            self.calculation_label.setStyleSheet("color: #2c3e50; background-color: rgba(255,255,255,0.8); padding: 8px; border-radius: 5px;")
            self.start_btn.setEnabled(True)
            
        # Update timer display to show first focus session time
        if total_time > break_time:
            focus_time = total_time - break_time
            single_focus_minutes = round((focus_time / 2) * 2) / 2
            self.update_timer_display(int(single_focus_minutes), 0)
        
    def connect_signals(self):
        self.focus_guard.session_started.connect(self.on_session_started)
        self.focus_guard.session_stopped.connect(self.on_session_stopped)
        self.focus_guard.app_blocked.connect(self.on_app_blocked)
        self.focus_guard.timer_updated.connect(self.update_timer_display)
        self.focus_guard.status_changed.connect(self.status_text.setText)
        
    def load_apps(self):
        # while self.focus_guard.start_session:
        app_list = self.focus_guard.get_app_list()
        row, col = 0, 0
        for app in app_list:
            card = AppCard(app)
            # Connect the selection changed signal
            card.selectionChanged.connect(self.on_app_selection_changed)
            self.apps_grid.addWidget(card, row, col)
            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1
                
    def get_selected_apps(self):
        selected = []
        for i in range(self.apps_grid.count()):
            widget = self.apps_grid.itemAt(i).widget()
            if isinstance(widget, AppCard) and widget.is_selected:
                selected.append(widget.app_name)
        return selected
        
    def start_session(self):
        selected_apps = self.get_selected_apps()
        total_time = self.time_input.value()
        break_duration = self.break_time_input.value()
        
        if not selected_apps:
            QMessageBox.warning(self, "Selection Required", 
                               "Select at least one app to start session")
            return
        
        if total_time <= break_duration:
            QMessageBox.warning(self, "Invalid Time Settings", 
                               "Total work time must be greater than break time")
            return
                
        self.focus_guard.start_session(selected_apps, total_time, break_duration)
        
    def stop_session(self):
        self.focus_guard.stop_session()
        
    def add_custom_app(self):
        """Prompt user to add custom application"""
        display_name, ok1 = QInputDialog.getText(
            self, "Add Application", "Enter application display name:"
        )
        if not ok1 or not display_name:
            return
        
        process_name, ok2 = QInputDialog.getText(
            self, 
            "Add Application", 
            "Enter process name (e.g., chrome.exe):",
            text=display_name.lower().replace(" ", "") + ".exe"
        )
        if not ok2 or not process_name:
            return
        
        success = self.focus_guard.add_custom_app(display_name, process_name)
        if success:
            QMessageBox.information(
                self, 
                "Success", 
                f"Added {display_name} successfully!"
            )
            # Clear existing apps and reload
            self.clear_apps_grid()
            self.load_apps()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to add {display_name}. Check logs for details."
            )

    def clear_apps_grid(self):
        """Remove all app cards from grid"""
        while self.apps_grid.count():
            child = self.apps_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    def on_session_started(self, message):
        self.start_btn.setVisible(False)
        # self.stop_btn.setVisible(True)
        self.status_dot.setStyleSheet("background-color: #2ecc71; border-radius: 6px;")
        self.status_text.setText("Focus session in progress")
        QMessageBox.information(self, "Session Started", message)
        
    def on_session_stopped(self, message):
        self.start_btn.setVisible(True)
        # self.stop_btn.setVisible(False)
        self.status_dot.setStyleSheet("background-color: #e74c3c; border-radius: 6px;")
        self.status_text.setText("Focus session stopped")
        # Reset to show first focus session time
        self.update_calculated_times()
        QMessageBox.information(self, "Session Stopped", message)
        
    def on_app_blocked(self, app_name):
        # Could show a notification or update UI
        print(f"Blocked: {app_name}")
        
    def update_timer_display(self, mins, secs):
        """Update timer display with proper formatting"""
        self.timer_display.setText(f"{int(mins):02d}:{int(secs):02d}")
    
    def on_app_selection_changed(self, is_selected):
        """Handle when an app card is selected/deselected"""
        # We can use this to update UI state if needed
        pass