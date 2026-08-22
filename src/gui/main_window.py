"""The main window: viewport canvas, object list, and pan/zoom controls.

Assembles the GUI and wires user actions to the controller. Layout mirrors the
Blender Top-Orthographic reference from the spec: pan, scroll-zoom, add object.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controller import Controller

from .object_dialog import ObjectDialog
from .viewport_widget import ViewportWidget

PAN_STEP = 10.0


class MainWindow(QMainWindow):
    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SGI - INE5420")

        self.viewport = ViewportWidget(controller)
        self.object_list = QListWidget()

        add_button = QPushButton("Add object")
        add_button.clicked.connect(self._on_add_object)

        sidebar = QVBoxLayout()
        sidebar.addWidget(self.object_list)
        sidebar.addWidget(add_button)
        sidebar.addWidget(self._pan_zoom_controls())
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setMaximumWidth(200)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.viewport, stretch=1)
        layout.addWidget(sidebar_widget)
        self.setCentralWidget(central)

    def _pan_zoom_controls(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        for label, action in (
            ("Zoom in", lambda: self._zoom(0.9)),
            ("Zoom out", lambda: self._zoom(1.1)),
            ("Left", lambda: self._pan(-PAN_STEP, 0)),
            ("Right", lambda: self._pan(PAN_STEP, 0)),
            ("Up", lambda: self._pan(0, PAN_STEP)),
            ("Down", lambda: self._pan(0, -PAN_STEP)),
        ):
            button = QPushButton(label)
            button.clicked.connect(action)
            layout.addWidget(button)
        return container

    def _zoom(self, factor: float) -> None:
        self.controller.zoom(factor)
        self.viewport.update()

    def _pan(self, dx: float, dy: float) -> None:
        self.controller.pan(dx, dy)
        self.viewport.update()

    def _on_add_object(self) -> None:
        dialog = ObjectDialog(self)
        if not dialog.exec():
            return
        name, object_type, raw = dialog.values()
        try:
            self.controller.add_object(name, object_type, raw)
        except (ValueError, SyntaxError) as error:
            QMessageBox.warning(self, "Invalid object", str(error))
            return
        self.object_list.addItem(f"{name} ({object_type.value})")
        self.viewport.update()
