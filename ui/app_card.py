# Update ui/app_card.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class AppCard(QWidget):
    # Signal to notify selection changes
    selectionChanged = pyqtSignal(bool)
    
    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.is_selected = False
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
        
        # Icon container
        self.icon = QLabel("📱")
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet("""
            font-size: 24px; 
            background-color: #f8f9fa;
            border-radius: 10px;
        """)
        layout.addWidget(self.icon)
        
        # App name
        self.name_label = QLabel(app_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("""
            font-weight: bold; 
            padding: 5px;
            background-color: white;
        """)
        layout.addWidget(self.name_label)
        
        # Set initial style
        self.update_style()
        self.setFixedSize(120, 120)
        
    def mousePressEvent(self, event):
        self.toggle_selection()
        
    def toggle_selection(self):
        """Toggle selection state and update appearance"""
        self.is_selected = not self.is_selected
        self.update_style()
        self.selectionChanged.emit(self.is_selected)
        
    def update_style(self):
        """Update widget appearance based on selection state"""
        # border_color = "red" if self.is_selected else "white"
        # border_width = "3px" if self.is_selected else "2px"
        bgcolor = "blue" if self.is_selected else "white"
        self.name_label.setStyleSheet(f"""
            font-weight: bold; 
            padding: 5px;
            background-color: {bgcolor};
        """)
        # self.setStyleSheet(f"""
        #     AppCard {{
        #         border: {border_width} solid {border_color};
        #         border-radius: 12px;
        #         background-color: white;
        #     }}
        #     AppCard:hover {{
        #         border-color: #3498db;
        #     }}
        # """)