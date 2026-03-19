# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ui import GeotekApp


def main():
    app = QApplication(sys.argv)
    try:
        with open("resources/style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: style.qss not found.")
    window = GeotekApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()