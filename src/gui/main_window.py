"""The main window: viewport canvas, object list, and pan/zoom controls.

Assembles the GUI and wires user actions to the controller. Layout mirrors the
Blender Top-Orthographic reference from the spec: pan, scroll-zoom, add object,
and (trabalho 1.2) apply 2D transforms to the selected object.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controller import Controller
from app.transform_request import build_matrix

from .object_dialog import ObjectDialog
from .transform_dialog import TransformDialog
from .viewport_widget import ViewportWidget

PAN_STEP = 10.0
_NAME_ROLE = Qt.ItemDataRole.UserRole


class MainWindow(QMainWindow):
    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SGI - INE5420")

        self.viewport = ViewportWidget(controller)
        self.object_list = QListWidget()

        add_button = QPushButton("Add object")
        add_button.clicked.connect(self._on_add_object)
        transform_button = QPushButton("Transform")
        transform_button.clicked.connect(self._on_transform_object)

        sidebar = QVBoxLayout()
        sidebar.addWidget(self.object_list)
        sidebar.addWidget(add_button)
        sidebar.addWidget(transform_button)
        sidebar.addWidget(self._pan_zoom_controls())
        sidebar.addWidget(self._window_rotation_controls())
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setMaximumWidth(200)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(self.viewport, stretch=1)
        layout.addWidget(sidebar_widget)
        self.setCentralWidget(central)

        self._build_menu()

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

    def _window_rotation_controls(self) -> QWidget:
        # Window rotation is always about the window center, so a single angle
        # field suffices (spec). Positive is counter-clockwise; the scene
        # counter-rotates on screen.
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Window rotation"))
        self.rotation_field = QDoubleSpinBox()
        self.rotation_field.setRange(-360.0, 360.0)
        self.rotation_field.setDecimals(1)
        self.rotation_field.setSingleStep(15.0)
        self.rotation_field.setValue(15.0)
        self.rotation_field.setSuffix(" deg")
        layout.addWidget(self.rotation_field)
        rotate_ccw = QPushButton("Rotate window")
        rotate_ccw.clicked.connect(lambda: self._rotate_window(self.rotation_field.value()))
        rotate_cw = QPushButton("Rotate opposite")
        rotate_cw.clicked.connect(lambda: self._rotate_window(-self.rotation_field.value()))
        layout.addWidget(rotate_ccw)
        layout.addWidget(rotate_cw)
        return container

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        import_action = file_menu.addAction("Import .obj...")
        import_action.triggered.connect(self._on_import_obj)
        export_action = file_menu.addAction("Export .obj...")
        export_action.triggered.connect(self._on_export_obj)

    def _zoom(self, factor: float) -> None:
        self.controller.zoom(factor)
        self.viewport.update()

    def _pan(self, du: float, dv: float) -> None:
        self.controller.pan(du, dv)
        self.viewport.update()

    def _rotate_window(self, degrees: float) -> None:
        self.controller.rotate_window(degrees)
        self.viewport.update()

    def _on_add_object(self) -> None:
        dialog = ObjectDialog(self)
        if not dialog.exec():
            return
        name, object_type, raw, color = dialog.values()
        try:
            obj = self.controller.add_object(name, object_type, raw, color)
        except (ValueError, SyntaxError) as error:
            QMessageBox.warning(self, "Invalid object", str(error))
            return
        self._add_list_item(obj)
        self.viewport.update()

    def _add_list_item(self, obj) -> None:
        item = QListWidgetItem(f"{obj.name} ({obj.type.value})")
        item.setData(_NAME_ROLE, obj.name)
        self.object_list.addItem(item)

    def _refresh_object_list(self) -> None:
        self.object_list.clear()
        for obj in self.controller.display_file:
            self._add_list_item(obj)

    def _on_transform_object(self) -> None:
        item = self.object_list.currentItem()
        if item is None:
            QMessageBox.information(self, "No selection", "Select an object first.")
            return
        name = item.data(_NAME_ROLE)
        dialog = TransformDialog(name, self)
        if not dialog.exec():
            return
        try:
            obj = self.controller.display_file.get(name)
            matrix = build_matrix(dialog.steps(), obj)
            self.controller.transform_object(name, matrix)
        except (ValueError, KeyError) as error:
            QMessageBox.warning(self, "Transform failed", str(error))
            return
        self.viewport.update()

    def _on_import_obj(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import .obj", "", "Wavefront OBJ (*.obj)"
        )
        if not path:
            return
        try:
            self.controller.load_obj(path)
        except (OSError, ValueError, IndexError) as error:
            QMessageBox.warning(self, "Import failed", str(error))
            return
        self._refresh_object_list()
        self.viewport.update()

    def _on_export_obj(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export .obj", "", "Wavefront OBJ (*.obj)"
        )
        if not path:
            return
        if not path.endswith(".obj"):
            path += ".obj"
        try:
            self.controller.save_obj(path)
        except OSError as error:
            QMessageBox.warning(self, "Export failed", str(error))
