"""Paleta de comandos (Ctrl+K): busca y ejecuta acciones de la app."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel,
)
from PyQt6.QtCore import Qt


class CommandPalette(QDialog):
    def __init__(self, commands, parent=None):
        """``commands``: lista de dicts con id, label, shortcut y callback."""
        super().__init__(parent)
        self.commands = list(commands)
        self.setWindowTitle("Paleta de comandos")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Escribe un comando…  (Esc para cerrar)")
        layout.addWidget(self.buscar)

        self.lista = QListWidget()
        self.lista.setToolTip("Comandos disponibles")
        self.lista.itemActivated.connect(self._ejecutar)
        layout.addWidget(self.lista, 1)

        self.ayuda = QLabel("Enter para ejecutar · ↑↓ para navegar")
        self.ayuda.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.ayuda)

        self.buscar.textChanged.connect(self._filtrar)
        self.buscar.returnPressed.connect(self._ejecutar_actual)
        self._filtrar("")
        self._mover_al_centro()

    def _mover_al_centro(self):
        if self.parent() is None:
            return
        superior = self.parent().mapToGlobal(self.parent().rect().center())
        self.move(superior.x() - self.width() // 2,
                  superior.y() - self.height() // 3)

    def _filtrar(self, texto):
        self.lista.clear()
        filtro = texto.strip().lower()
        for comando in self.commands:
            if filtro and filtro not in comando["label"].lower():
                continue
            item = QListWidgetItem(comando["label"])
            atajo = comando.get("shortcut") or ""
            if atajo:
                item.setText(f"{comando['label']}    [{atajo}]")
            item.setData(Qt.ItemDataRole.UserRole, comando)
            self.lista.addItem(item)
        if self.lista.count():
            self.lista.setCurrentRow(0)

    def _ejecutar_actual(self):
        actual = self.lista.currentItem()
        if actual:
            self._ejecutar(actual)

    def _ejecutar(self, item):
        comando = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        callback = comando.get("callback")
        if callback:
            callback()
