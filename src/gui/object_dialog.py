"""Dialog to add a new object: name, type, coordinates in the spec format.

The dialog only gathers raw input and hands it to the controller; it performs
no parsing itself (that lives in io.parser). Color (1.2) and wireframe/filled
(1.4) fields will be added here later.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)

from domain.objects import ObjectType


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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Name", self.name_field)
        layout.addRow("Type", self.type_field)
        layout.addRow("Coordinates", self.coordinates_field)
        layout.addRow(buttons)

    def values(self) -> tuple[str, ObjectType, str]:
        """(name, type, raw coordinates string) as entered by the user."""
        return (
            self.name_field.text().strip(),
            self.type_field.currentData(),
            self.coordinates_field.text().strip(),
        )
