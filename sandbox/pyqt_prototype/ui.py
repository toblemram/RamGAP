# ui.py
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from plaxis.ui_plaxis import PlaxisTab


class GeotekApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Geoteknikk Automatisering")
        self.resize(1000, 600)
        self._init_ui()

    def _init_ui(self):
        tabs = QTabWidget()
        tabs.setObjectName("MainTabWidget")
        tabs.addTab(PlaxisTab(),"Plaxis")
        tabs.addTab(PlaxisTab(),"TEST1")
        tabs.addTab(PlaxisTab(),"TEST2")

        self.setCentralWidget(tabs)

