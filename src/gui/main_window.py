"""The main window: viewport canvas, object list, and navigation controls.

Assembles the GUI and wires user actions to the controller. Layout mirrors the
Blender references from the spec: pan, scroll-zoom, add object, (trabalho 1.2)
transform the selected object, (trabalho 1.7) navigate the window in 3D --
rotate it about its own axes (roll/pitch/yaw) and reset the view -- and
(trabalho 1.8) pick the projection, moving the perspective's center of
projection from wide-angle to telephoto.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.controller import Controller
from app.transform_request import build_matrix
from domain.clipping import LineClipper
from domain.objects import ObjectType
from domain.projection import ParallelProjection, PerspectiveProjection
from domain.window import WindowAxis

from .curve_samples import BSPLINE_SAMPLES, CURVE_SAMPLES
from .object_dialog import ObjectDialog
from .transform_dialog import TransformDialog
from .viewport_widget import ViewportWidget

PAN_STEP = 10.0
_NAME_ROLE = Qt.ItemDataRole.UserRole
# Repo root: src/gui/main_window.py -> up 3 -> repo. samples/ ships beside src.
_SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
# Trabalho 1.7: 3D wireframe models, in their own submenu.
_SAMPLES_3D_DIR = _SAMPLES_DIR / "3d"
# Window rotation axes as offered in the sidebar (the window's own axes).
_WINDOW_AXIS_LABELS = {
    WindowAxis.ROLL: "Roll (about VPN)",
    WindowAxis.PITCH: "Pitch (about right)",
    WindowAxis.YAW: "Yaw (about up)",
}
# Trabalho 1.8: range of the COP distance d, in world units. The slider is
# logarithmic so the wide-angle end (short d) gets as much travel as the
# telephoto end. The default d equals the default window's width: a ~53 degree
# field of view, a "normal" lens.
_COP_DISTANCE_MIN = 25.0
_COP_DISTANCE_MAX = 5000.0
_COP_DISTANCE_DEFAULT = 200.0
_COP_SLIDER_STEPS = 1000

# Sample colouring lives here, not in the .obj files: the files stay 100%
# standard geometry (the trabalho 1.3 decision), and the paint colour is applied
# at load time. `_SAMPLE_DEFAULT` is the theme colour for a whole scene, keyed by
# file stem; `_OBJECT_COLORS` overrides individual objects by name (e.g. a red
# roof on a brown house). Colours are RGB in 0-255, matching domain.objects.Color.
_SAMPLE_DEFAULT: dict[str, tuple[int, int, int]] = {
    "star": (218, 165, 32),          # goldenrod
    "hexagon": (30, 144, 255),       # dodger blue
    "flower": (219, 68, 130),        # rose
    "gear": (90, 100, 110),          # steel grey
    "house": (120, 72, 48),          # brown
    "nested_stars": (148, 0, 211),   # violet
    "star_of_david": (33, 97, 140),  # deep blue
    "axes": (120, 120, 120),         # neutral grey
    # 3D models (trabalho 1.7)
    "axes_3d": (120, 120, 120),      # neutral grey
    "cube": (64, 224, 208),          # turquoise
    "pyramid": (255, 165, 0),        # orange
    "parallelepiped": (186, 85, 211),  # orchid
    "house_3d": (120, 72, 48),       # brown
    # perspective scene (trabalho 1.8)
    "street": (100, 149, 237),       # cornflower-blue buildings
}
_OBJECT_COLORS: dict[str, tuple[int, int, int]] = {
    # house
    "roof": (178, 34, 34),           # firebrick red roof
    "door": (76, 44, 28),            # dark wood door
    "window": (135, 206, 235),       # sky-blue glass
    # flower
    "core": (255, 200, 40),          # yellow center
    # gear
    "gear_bore": (40, 44, 52),       # dark bore
    # axes
    "x_axis": (200, 60, 60),         # red x
    "y_axis": (60, 170, 90),         # green y
    "z_axis": (70, 130, 230),        # blue z
    "origin": (240, 240, 240),       # light origin dot
    # street
    "curbs": (160, 160, 160),        # grey curbs
    "lane": (255, 215, 0),           # gold lane marks
}
# A collision-renamed object ("petal_1" -> "petal_1_2") should still match its
# original palette entry. This strips exactly one trailing "_<digits>".
_COLLISION_SUFFIX = re.compile(r"_\d+$")


def _color_for(name: str, default: tuple[int, int, int]) -> tuple[int, int, int]:
    """Palette colour for an object: exact name, then de-suffixed, then default.

    `name` may carry a collision suffix ("_2") added on append; that is stripped
    once so a renamed duplicate keeps its palette entry.
    """
    if name in _OBJECT_COLORS:
        return _OBJECT_COLORS[name]
    base = _COLLISION_SUFFIX.sub("", name)
    if base in _OBJECT_COLORS:
        return _OBJECT_COLORS[base]
    return default


def _slider_to_cop_distance(position: int) -> float:
    """COP distance for a slider position, logarithmic between the range ends."""
    ratio = _COP_DISTANCE_MAX / _COP_DISTANCE_MIN
    return _COP_DISTANCE_MIN * ratio ** (position / _COP_SLIDER_STEPS)


def _cop_distance_to_slider(distance: float) -> int:
    """Slider position for a COP distance (inverse of _slider_to_cop_distance)."""
    ratio = _COP_DISTANCE_MAX / _COP_DISTANCE_MIN
    return round(_COP_SLIDER_STEPS * math.log(distance / _COP_DISTANCE_MIN) / math.log(ratio))


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
        sidebar.addWidget(self._projection_controls())
        sidebar.addWidget(self._clipping_controls())
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
        # Window rotation is always about the window center (the VRP), so an
        # angle field suffices (spec 1.3); trabalho 1.7 adds which of the
        # window's own axes to turn about. Roll is the 1.3 rotation (positive is
        # counter-clockwise); the scene turns the opposite way on screen.
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Window rotation"))
        self.rotation_axis_field = QComboBox()
        for axis, label in _WINDOW_AXIS_LABELS.items():
            self.rotation_axis_field.addItem(label, axis)
        layout.addWidget(self.rotation_axis_field)
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
        reset = QPushButton("Reset view")
        reset.clicked.connect(self._reset_window)
        layout.addWidget(reset)
        return container

    def _projection_controls(self) -> QWidget:
        # Parallel orthogonal (1.7) or perspective (1.8). In perspective the COP
        # sits d behind the window: a short d works as a wide-angle lens
        # (strong convergence), a long d as a telephoto (flattened depth,
        # approaching the parallel view). The slider and the field both set d.
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Projection"))
        self._projection_group = QButtonGroup(container)
        self._parallel_button = QRadioButton("Parallel orthogonal")
        self._perspective_button = QRadioButton("Perspective")
        for button in (self._parallel_button, self._perspective_button):
            self._projection_group.addButton(button)
            layout.addWidget(button)
        layout.addWidget(QLabel("COP distance d"))
        self._cop_slider = QSlider(Qt.Orientation.Horizontal)
        self._cop_slider.setRange(0, _COP_SLIDER_STEPS)
        layout.addWidget(self._cop_slider)
        lens_labels = QHBoxLayout()
        lens_labels.addWidget(QLabel("wide-angle"))
        lens_labels.addStretch()
        lens_labels.addWidget(QLabel("telephoto"))
        layout.addLayout(lens_labels)
        self._cop_field = QDoubleSpinBox()
        self._cop_field.setRange(_COP_DISTANCE_MIN, _COP_DISTANCE_MAX)
        self._cop_field.setDecimals(1)
        self._cop_field.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        layout.addWidget(self._cop_field)

        # Start from the controller's projection, like the clipping radio does.
        current = self.controller.projection
        perspective = isinstance(current, PerspectiveProjection)
        distance = current.cop_distance if perspective else _COP_DISTANCE_DEFAULT
        self._perspective_button.setChecked(perspective)
        self._parallel_button.setChecked(not perspective)
        self._cop_field.setValue(distance)
        self._cop_slider.setValue(_cop_distance_to_slider(distance))
        self._cop_slider.setEnabled(perspective)
        self._cop_field.setEnabled(perspective)

        self._perspective_button.toggled.connect(self._apply_projection)
        self._cop_slider.valueChanged.connect(self._on_cop_slider_moved)
        self._cop_field.valueChanged.connect(self._on_cop_distance_typed)
        return container

    def _apply_projection(self) -> None:
        perspective = self._perspective_button.isChecked()
        self._cop_slider.setEnabled(perspective)
        self._cop_field.setEnabled(perspective)
        if perspective:
            self.controller.set_projection(PerspectiveProjection(self._cop_field.value()))
        else:
            self.controller.set_projection(ParallelProjection())
        self.viewport.update()

    def _on_cop_slider_moved(self, position: int) -> None:
        # Mirror the slider into the field without the field echoing back.
        self._cop_field.blockSignals(True)
        self._cop_field.setValue(_slider_to_cop_distance(position))
        self._cop_field.blockSignals(False)
        self._apply_projection()

    def _on_cop_distance_typed(self, distance: float) -> None:
        self._cop_slider.blockSignals(True)
        self._cop_slider.setValue(_cop_distance_to_slider(distance))
        self._cop_slider.blockSignals(False)
        self._apply_projection()

    def _clipping_controls(self) -> QWidget:
        # Radio button to swap the line-clipping technique (spec 1.4). Polygon
        # and point clipping are fixed; only the line method is user-selectable.
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Line clipping"))
        self._clipper_group = QButtonGroup(container)
        for clipper in LineClipper:
            button = QRadioButton(clipper.value)
            button.setChecked(clipper is self.controller.line_clipper)
            button.toggled.connect(
                lambda checked, c=clipper: self._on_clipper_selected(checked, c)
            )
            self._clipper_group.addButton(button)
            layout.addWidget(button)
        return container

    def _on_clipper_selected(self, checked: bool, clipper: LineClipper) -> None:
        if not checked:  # ignore the untoggle half of the radio-group signal
            return
        self.controller.set_line_clipper(clipper)
        self.viewport.update()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        import_action = file_menu.addAction("Import .obj...")
        import_action.triggered.connect(self._on_import_obj)
        export_action = file_menu.addAction("Export .obj...")
        export_action.triggered.connect(self._on_export_obj)
        self._build_samples_menu()

    def _build_samples_menu(self) -> None:
        # Predefined scenes shipped as standard .obj files; each entry loads
        # into the current world (append) so several can be combined on screen.
        samples_menu = self.menuBar().addMenu("Samples")
        files = sorted(_SAMPLES_DIR.glob("*.obj")) if _SAMPLES_DIR.is_dir() else []
        if not files:
            action = samples_menu.addAction("(no samples found)")
            action.setEnabled(False)
            return
        for path in files:
            label = path.stem.replace("_", " ").title()
            action = samples_menu.addAction(label)
            action.triggered.connect(lambda _checked, p=path: self._load_sample(p))
        self._build_3d_samples_menu(samples_menu)
        self._build_curve_samples_menu(samples_menu)
        self._build_bspline_samples_menu(samples_menu)
        samples_menu.addSeparator()
        clear_action = samples_menu.addAction("Clear world")
        clear_action.triggered.connect(self._clear_world)

    def _build_3d_samples_menu(self, samples_menu) -> None:
        # 3D wireframe models (trabalho 1.7), shipped as .obj like the 2D
        # scenes and appended the same way. Orbit (left-drag) to see the depth.
        files = sorted(_SAMPLES_3D_DIR.glob("*.obj")) if _SAMPLES_3D_DIR.is_dir() else []
        if not files:
            return
        samples_menu.addSeparator()
        models_menu = samples_menu.addMenu("3D models")
        for path in files:
            label = path.stem.replace("_", " ").title()
            action = models_menu.addAction(label)
            action.triggered.connect(lambda _checked, p=path: self._load_sample(p))

    def _build_curve_samples_menu(self, samples_menu) -> None:
        # Bézier curve demos (trabalho 1.5). They live in code, not .obj (the
        # p/l format cannot carry control points), so they are added straight
        # through the controller instead of loaded as files.
        samples_menu.addSeparator()
        curves_menu = samples_menu.addMenu("Curves (Bézier)")
        for sample in CURVE_SAMPLES:
            label = sample.name.replace("curve_", "").replace("_", " ").title()
            action = curves_menu.addAction(label)
            action.triggered.connect(
                lambda _checked, s=sample: self._add_curve_sample(s, ObjectType.CURVE)
            )

    def _build_bspline_samples_menu(self, samples_menu) -> None:
        # B-Spline demos (trabalho 1.6). Same in-code control points as the Bézier
        # samples, added as ObjectType.BSPLINE via the same controller path.
        bspline_menu = samples_menu.addMenu("B-Splines")
        for sample in BSPLINE_SAMPLES:
            label = sample.name.replace("bspline_", "").replace("_", " ").title()
            action = bspline_menu.addAction(label)
            action.triggered.connect(
                lambda _checked, s=sample: self._add_curve_sample(s, ObjectType.BSPLINE)
            )

    def _add_curve_sample(self, sample, object_type: ObjectType) -> None:
        # Append a curve/B-Spline sample using the mandated (x,y),... input string,
        # so it travels the exact same path as one typed into the dialog. The name
        # is de-duplicated like .obj loads, and the colour is applied here.
        name = self.controller.unique_name(sample.name)
        try:
            obj = self.controller.add_object(
                name, object_type, sample.as_input_string(), sample.color
            )
        except (ValueError, SyntaxError) as error:
            QMessageBox.warning(self, "Sample failed", str(error))
            return
        self._add_list_item(obj)
        self.viewport.update()

    def _load_sample(self, path) -> None:
        try:
            objects = self.controller.load_obj(str(path), replace=False)
        except (OSError, ValueError, IndexError) as error:
            QMessageBox.warning(self, "Sample failed", str(error))
            return
        default = _SAMPLE_DEFAULT.get(path.stem, (0, 0, 0))
        for obj in objects:
            obj.color = _color_for(obj.name, default)
        self._refresh_object_list()
        self.viewport.update()

    def _clear_world(self) -> None:
        self.controller.display_file.clear()
        self._refresh_object_list()
        self.viewport.update()

    def _zoom(self, factor: float) -> None:
        self.controller.zoom(factor)
        self.viewport.update()

    def _pan(self, du: float, dv: float) -> None:
        self.controller.pan(du, dv)
        self.viewport.update()

    def _rotate_window(self, degrees: float) -> None:
        self.controller.rotate_window(degrees, self.rotation_axis_field.currentData())
        self.viewport.update()

    def _reset_window(self) -> None:
        self.controller.reset_window()
        self.viewport.update()

    def _on_add_object(self) -> None:
        dialog = ObjectDialog(self)
        if not dialog.exec():
            return
        name, object_type, raw, color, filled = dialog.values()
        try:
            obj = self.controller.add_object(name, object_type, raw, color, filled)
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
