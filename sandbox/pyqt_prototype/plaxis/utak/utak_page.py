from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QPushButton, QMessageBox, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from plaxis.utak.level1 import level1


class UtakPage(QWidget):
    def __init__(self, setup_page, parent=None):
        super().__init__(parent)
        self.setup_page = setup_page
        self._apply_styles()
        self._build_ui()

    def _apply_styles(self):
        # Basisfont og innrykk
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # Gruppe for uttak
        utk_group = QGroupBox("Spuntuttak")
        utk_layout = QVBoxLayout(utk_group)
        utk_layout.setSpacing(10)

        # Beskrivelse av skriptet
        desc = QLabel(
            "Skriptet kobler til Plaxis, henter ut navnet og x-posisjon for alle "
            "Plates og EmbeddedBeamRows og lister alle faser."
        )
        desc.setWordWrap(True)
        utk_layout.addWidget(desc)

        # Kjør-knapp
        self.run_btn = QPushButton("Kjør uttak av spuntberegninger")
        self.run_btn.clicked.connect(self._run)
        utk_layout.addWidget(self.run_btn)

        # Tekstfelt for resultater
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_text.setPlaceholderText("Resultater vises her...")
        utk_layout.addWidget(self.result_text)

        main_layout.addWidget(utk_group)
        main_layout.addStretch(1)

    def _run(self):
        port = self.setup_page.port_input.text()
        password = self.setup_page.password_input.text()
        try:
            struct_list, phase_names, phase_ids = level1(port, password)

            # Vis resultater
            self.result_text.clear()
            self.result_text.append(f"Uttak fullført: {len(struct_list)} strukturer, {len(phase_names)} faser.")
            self.result_text.append("\nStrukturer:")
            for s in struct_list:
                self.result_text.append(f"  • {s}")
            self.result_text.append("\nFaser:")
            for name in phase_names:
                self.result_text.append(f"  • {name}")

            QMessageBox.information(
                self, "Ferdig",
                "Uttak fullført og resultater vises i tekstfeltet."
            )
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Uttak feilet: {e}")
