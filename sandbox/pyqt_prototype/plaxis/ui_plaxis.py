# ui_plaxis.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QListWidget, QStackedWidget
from plaxis.setup.setup_page import SetupPage
from plaxis.utak.utak_page import UtakPage

class PlaxisTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Side-list with pages
        side_list = QListWidget()
        side_list.addItems([
            "Oppsett",
            "Automatisere uttak av spuntberegninger",
            "TEST1"

        ])

        # Page stack
        pages = QStackedWidget()
        # Store reference to setup page for reuse in UtakPage
        self.setup_page = SetupPage()
        pages.addWidget(self.setup_page)
        pages.addWidget(UtakPage(self.setup_page))

        side_list.currentRowChanged.connect(pages.setCurrentIndex)
        side_list.setCurrentRow(0)

        layout.addWidget(side_list)
        layout.addWidget(pages)
        layout.setStretch(1, 1)
