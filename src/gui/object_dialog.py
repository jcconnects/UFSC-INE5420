"""Dialog to add a new object: name, type, coordinates, and paint colour.

The dialog only gathers raw input and hands it to the controller; it performs
no coordinate parsing itself (that lives in persistence.parser). Trabalho 1.2
adds the colour picker: the chosen RGB colours the object's lines/borders.
Wireframe/filled (1.4) fields will be added here later.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
)

from domain.objects import BLACK, Color, ObjectType


class ObjectDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add object")

        self.name_field = QLineEdit()
        self.type_field = QComboBox()
        for object_type in ObjectType:
            self.type_field.addItem(object_type.value, object_type)
        self.coordinates_field = QLineEdit()
        self.coordinates_field.setPlaceholderText("(x1, y1),(x2, y2),...")

        self._color: Color = BLACK
        self.color_button = QPushButton()
        self.color_button.clicked.connect(self._pick_color)
        self._refresh_color_button()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Name", self.name_field)
        layout.addRow("Type", self.type_field)
        layout.addRow("Coordinates", self.coordinates_field)
        layout.addRow("Color", self.color_button)
        layout.addRow(buttons)

    def _pick_color(self) -> None:
        initial = QColor(*self._color)
        chosen = QColorDialog.getColor(initial, self, "Pick paint color")
        if chosen.isValid():
            self._color = (chosen.red(), chosen.green(), chosen.blue())
            self._refresh_color_button()

    def _refresh_color_button(self) -> None:
        r, g, b = self._color
        self.color_button.setText(f"rgb({r}, {g}, {b})")
        # A readable swatch: fill with the colour, flip text to keep contrast.
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        text_color = "black" if luminance > 140 else "white"
        self.color_button.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); color: {text_color};"
        )

    def values(self) -> tuple[str, ObjectType, str, Color]:
        """(name, type, raw coordinates string, RGB color) as entered."""
        return (
            self.name_field.text().strip(),
            self.type_field.currentData(),
            self.coordinates_field.text().strip(),
            self._color,
        )
