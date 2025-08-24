import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.app_card import AppCard


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()