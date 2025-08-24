import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QFrame,
    QSizePolicy, QMessageBox, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap,QPalette, QColor
from PyQt5.QtWidgets import QInputDialog

from backend.app_logic import FocusGuard
from .app_card import AppCard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.focus_guard = FocusGuard()
        self.session_active = False  # Track session state
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
        sidebar.setStyleSheet("background-color: #939B9B;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # Timer controls
        timer_label = QLabel("🕒 Total Work Time")
        timer_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        sidebar_layout.addWidget(timer_label)
        
        # Time input
        time_layout = QHBoxLayout()
        self.time_input = QSpinBox()
        self.time_input.setStyleSheet("""
    QSpinBox {
        background-color: #F0F0F0;
        color: black;
    }
""")

        self.time_input.setRange(5, 240)
        self.time_input.setValue(30)
        self.time_input.setFixedHeight(40)
        self.time_input.valueChanged.connect(self.update_calculated_times)
        time_layout.addWidget(self.time_input)
        
        plus_btn = QPushButton("+")
        plus_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: #939B9B;   /* normal state */
        color: black;
    }}
    QPushButton:hover {{
        background-color: #7f8989;   /* slightly darker on hover */
    }}
""")

        plus_btn.setFixedSize(40, 40)
        plus_btn.clicked.connect(lambda: self.time_input.setValue(self.time_input.value() + 1))
        time_layout.addWidget(plus_btn)
        
        minus_btn = QPushButton("-")
        minus_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: #939B9B;   /* normal state */
        color: black;
    }}
    QPushButton:hover {{
        background-color: #7f8989;   /* slightly darker on hover */
    }}
""")
        
    
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
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #7A8585;
                }
                QPushButton:pressed {
                    background-color: #525A5A;
                }
                """
            )
            if time_val == 30:
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
        self.break_time_input.setStyleSheet("""
    QSpinBox {
        background-color: #F0F0F0;
        color: black;
    }
""")
        self.break_time_input.setRange(1, 30)
        self.break_time_input.setValue(5)
        self.break_time_input.setFixedHeight(40)
        self.break_time_input.valueChanged.connect(self.update_calculated_times)
        break_time_layout.addWidget(self.break_time_input)
        
        break_plus_btn = QPushButton("+")
        break_plus_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: #939B9B;   /* normal state */
        color: black;
    }}
    QPushButton:hover {{
        background-color: #7f8989;   /* slightly darker on hover */
    }}
""")
        break_plus_btn.setFixedSize(40, 40)
        break_plus_btn.clicked.connect(lambda: self.break_time_input.setValue(self.break_time_input.value() + 1))
        break_time_layout.addWidget(break_plus_btn)
        
        break_minus_btn = QPushButton("-")
        break_minus_btn.setStyleSheet(f"""
    QPushButton {{
        background-color: #939B9B;   /* normal state */
        color: black;
    }}
    QPushButton:hover {{
        background-color: #7f8989;   /* slightly darker on hover */
    }}
""")
        break_minus_btn.setFixedSize(40, 40)
        break_minus_btn.clicked.connect(lambda: self.break_time_input.setValue(self.break_time_input.value() - 1))
        break_time_layout.addWidget(break_minus_btn)

        sidebar_layout.addLayout(break_time_layout)
        
        # Display calculated focus times
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
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7A8585;
            }
            QPushButton:pressed {
                background-color: #525A5A;
            }
            """
        )
        
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.start_session)
        sidebar_layout.addWidget(self.start_btn)
        
        # self.stop_btn = QPushButton("⏹️ Stop Session")
        # self.stop_btn.setStyleSheet(
        #     """
        #     QPushButton {
        #         background-color: #e74c3c; 
        #         color: white;
        #         border-radius: 20px;
        #         border: none;
        #         font-weight: bold;
        #         padding: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #c0392b;
        #     }
        #     """
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
        self.apps_title = QLabel("📱 Select Apps to Allow")
        self.apps_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        content_layout.addWidget(self.apps_title)
        
        # Description
        self.desc = QLabel(
            "Select applications you want to work with. All other apps will be "
            "blocked during your focus sessions."
        )
        self.desc.setWordWrap(True)
        content_layout.addWidget(self.desc)
        
        # Apps grid with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.apps_container = QWidget()
        self.apps_grid = QGridLayout(self.apps_container)
        self.apps_grid.setSpacing(20)
        self.apps_grid.setContentsMargins(10, 10, 10, 10)
        
        # Create placeholder widget for session mode
        self.session_placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.session_placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        
        # Placeholder image label
        self.placeholder_image = QLabel()
        self.placeholder_image.setAlignment(Qt.AlignCenter)
        self.placeholder_image.setStyleSheet("padding: 20px;")
        placeholder_layout.addWidget(self.placeholder_image)
        
        # Placeholder text
        self.placeholder_text = QLabel("Focus session in progress!\nTake a deep breath and stay focused. 💪")
        self.placeholder_text.setAlignment(Qt.AlignCenter)
        self.placeholder_text.setFont(QFont("Segoe UI", 12))
        self.placeholder_text.setStyleSheet("color: #2c3e50; padding: 20px;")
        placeholder_layout.addWidget(self.placeholder_text)
        
        # Initially hide placeholder
        self.session_placeholder.setVisible(False)
        
        scroll_area.setWidget(self.apps_container)
        content_layout.addWidget(scroll_area)
        
        # Add placeholder to content layout (hidden by default)
        content_layout.addWidget(self.session_placeholder)
        
        # Store scroll area reference
        self.scroll_area = scroll_area
        
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
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7A8585;
            }
            QPushButton:pressed {
                background-color: #525A5A;
            }
            """
        )
        
        self.add_app_btn.setFixedHeight(40)
        self.add_app_btn.clicked.connect(self.add_custom_app)
        content_layout.addWidget(self.add_app_btn)
        
        # Add both sections to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        
        # Load apps and initialize
        self.load_apps()
        self.update_calculated_times()
        self.load_placeholder_images()
        
    def load_placeholder_images(self):
        """Load placeholder images for session mode"""
        # Store multiple image paths for variety
        self.placeholder_images = [
            "assets/cat_working.png",     # Cat with laptop
            "assets/coffee_break.png",    # Coffee cup
            # "assets/focus_mode.png",      # Focus icon
            # "assets/meditation.png",      # Meditation figure
        ]
        self.current_image_index = 0
        
        # Try to load the first image, fallback to text if not found
        self.update_placeholder_image()
    
    def update_placeholder_image(self):
        """Update the placeholder image based on session state"""
        try:
            # Choose image based on whether it's focus or break time
            if hasattr(self.focus_guard, 'is_focus_session'):
                if self.focus_guard.is_focus_session:
                    # Focus mode - use cat or focus image
                    image_path = "assets/cat_working.png"
                    self.placeholder_text.setText("Focus session in progress!\nStay focused and productive! 🎯")
                else:
                    # Break mode - use coffee image
                    image_path = "assets/coffee_break.png"
                    self.placeholder_text.setText("Break time! ☕\nRelax and recharge for the next session.")
            else:
                image_path = "assets/focus_mode.png"
            
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale image to fit nicely
                scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.placeholder_image.setPixmap(scaled_pixmap)
            else:
                # Fallback to emoji if image not found
                self.placeholder_image.setText("🐱‍💻" if self.focus_guard.is_focus_session else "☕")
                self.placeholder_image.setFont(QFont("Segoe UI", 72))
        except:
            # Fallback to emoji
            self.placeholder_image.setText("🎯")
            self.placeholder_image.setFont(QFont("Segoe UI", 72))
    
    def toggle_session_mode(self, session_active):
        """Toggle between app selection and session placeholder"""
        self.session_active = session_active
        
        if session_active:
            # Hide app selection UI
            self.scroll_area.setVisible(False)
            self.add_app_btn.setVisible(False)
            self.apps_title.setVisible(False)
            self.desc.setVisible(False)
            
            # Show placeholder
            self.update_placeholder_image()
            self.session_placeholder.setVisible(True)
            
            # Disable time inputs
            self.time_input.setEnabled(False)
            self.break_time_input.setEnabled(False)
            
            # Show stop button
            self.start_btn.setVisible(False)
            # self.stop_btn.setVisible(True)
        else:
            # Show app selection UI
            self.scroll_area.setVisible(True)
            self.add_app_btn.setVisible(True)
            self.apps_title.setVisible(True)
            self.desc.setVisible(True)
            
            # Hide placeholder
            self.session_placeholder.setVisible(False)
            
            # Enable time inputs
            self.time_input.setEnabled(True)
            self.break_time_input.setEnabled(True)
            
            # Show start button
            self.start_btn.setVisible(True)
            # self.stop_btn.setVisible(False)
    
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
            
        if total_time > break_time:
            focus_time = total_time - break_time
            single_focus_minutes = round((focus_time / 2) * 2) / 2
            self.update_timer_display(int(single_focus_minutes), 0)
    
    def connect_signals(self):
        self.focus_guard.session_started.connect(self.on_session_started)
        self.focus_guard.session_stopped.connect(self.on_session_stopped)
        self.focus_guard.app_blocked.connect(self.on_app_blocked)
        self.focus_guard.timer_updated.connect(self.update_timer_display)
        self.focus_guard.status_changed.connect(self.on_status_changed)
        
    def load_apps(self):
        app_list = self.focus_guard.get_app_list()
        row, col = 0, 0
        for app in app_list:
            card = AppCard(app)
            card.selectionChanged.connect(self.on_app_selection_changed)
            self.apps_grid.addWidget(card, row, col)
            col += 1
            if col > 2:
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
        reply = QMessageBox.question(self, 'Stop Session', 
                                    'Are you sure you want to stop the current session?',
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.focus_guard.stop_session()
        
    def add_custom_app(self):
        """Prompt user to add custom application"""
        if self.session_active:
            QMessageBox.information(self, "Session Active", 
                                  "Cannot add apps during an active session.")
            return
            
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
        self.toggle_session_mode(True)
        self.status_dot.setStyleSheet("background-color: #2ecc71; border-radius: 6px;")
        self.status_text.setText("Focus session in progress")
        QMessageBox.information(self, "Session Started", message)
        
    def on_session_stopped(self, message):
        self.toggle_session_mode(False)
        self.status_dot.setStyleSheet("background-color: #e74c3c; border-radius: 6px;")
        self.status_text.setText("Focus session stopped")
        self.update_calculated_times()
        QMessageBox.information(self, "Session Stopped", message)
        
    def on_app_blocked(self, app_name):
        print(f"Blocked: {app_name}")
        
    def on_status_changed(self, status):
        self.status_text.setText(status)
        # Update placeholder image when status changes (focus/break transition)
        if self.session_active:
            self.update_placeholder_image()
        
    def update_timer_display(self, mins, secs):
        """Update timer display with proper formatting"""
        self.timer_display.setText(f"{int(mins):02d}:{int(secs):02d}")
    
    def on_app_selection_changed(self, is_selected):
        """Handle when an app card is selected/deselected"""
        pass