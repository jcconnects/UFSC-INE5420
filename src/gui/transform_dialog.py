"""Dialog to compose a list of transforms for the selected object.

Mirrors the SGI reference in the spec: the user builds a *list* of transforms
(translation, scaling, rotation) and only when they confirm is the combined
matrix computed and applied. The dialog produces neutral `TransformStep` value
objects; the app layer (transform_request.build_matrix) turns them into one
matrix. No matrix math or domain mutation happens here.

Rotation and scaling offer the three pivots the spec lists: world origin,
object center, and an arbitrary point. Angles are entered in degrees
(counter-clockwise positive), matching the Blender R reference.

Trabalho 1.7 makes it 3D: translation and scaling gain z, and a rotation picks
its axis -- x, y, z (z is the plane rotation of 1.2) or an arbitrary direction
-- which passes through the chosen pivot. That covers the three basic rotations
and the rotation about an arbitrary axis the spec asks of an Objeto3D.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.transform_request import (
    X_AXIS,
    Y_AXIS,
    Z_AXIS,
    Pivot,
    Rotate,
    Scale,
    TransformStep,
    Translate,
)
from domain.geometry import Point

_TRANSLATE, _SCALE, _ROTATE = "Translation", "Scaling", "Rotation"
# Rotation axis choices: label -> direction, None for a user-typed direction.
_AXES = (("x axis", X_AXIS), ("y axis", Y_AXIS), ("z axis", Z_AXIS), ("arbitrary axis", None))


def _spin(minimum: float, maximum: float, value: float, step: float = 1.0) -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(3)
    box.setSingleStep(step)
    box.setValue(value)
    return box


def _xyz_spins(value: float = 0.0, step: float = 1.0) -> tuple[QDoubleSpinBox, ...]:
    return tuple(_spin(-1e6, 1e6, value, step) for _ in range(3))


class TransformDialog(QDialog):
    def __init__(self, object_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Transform: {object_name}")
        self._steps: list[TransformStep] = []

        self.kind_field = QComboBox()
        self.kind_field.addItems([_TRANSLATE, _SCALE, _ROTATE])
        self.kind_field.currentIndexChanged.connect(self._on_kind_changed)

        self._params = QStackedWidget()
        self._params.addWidget(self._translate_panel())
        self._params.addWidget(self._scale_panel())
        self._params.addWidget(self._rotate_panel())

        add_button = QPushButton("Add to list")
        add_button.clicked.connect(self._add_step)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self._remove_selected)

        self.step_list = QListWidget()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        # OK ("Apply") is meaningful only once at least one transform is queued.
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("Apply")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Transform", self.kind_field)
        layout.addLayout(form)
        layout.addWidget(self._params)
        edit_row = QHBoxLayout()
        edit_row.addWidget(add_button)
        edit_row.addWidget(remove_button)
        layout.addLayout(edit_row)
        layout.addWidget(QLabel("Transforms to apply (in order):"))
        layout.addWidget(self.step_list)
        layout.addWidget(buttons)

        self._refresh_ok()

    # --- parameter panels ---------------------------------------------------

    def _translate_panel(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        self.tx, self.ty, self.tz = _xyz_spins()
        form.addRow("dx", self.tx)
        form.addRow("dy", self.ty)
        form.addRow("dz", self.tz)
        return panel

    def _scale_panel(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        self.sx, self.sy, self.sz = _xyz_spins(1.0, step=0.1)
        # Scaling defaults to the object center (the "natural" scaling); an
        # arbitrary point is offered, but not the world origin (it would just
        # translate the object away from the origin, which the spec does not ask
        # for here).
        self.scale_pivot = QComboBox()
        self.scale_pivot.addItem(Pivot.OBJECT_CENTER.value, Pivot.OBJECT_CENTER)
        self.scale_pivot.addItem(Pivot.ARBITRARY_POINT.value, Pivot.ARBITRARY_POINT)
        self.scale_pivot.currentIndexChanged.connect(self._on_scale_pivot_changed)
        self._scale_point = _xyz_spins()
        form.addRow("sx", self.sx)
        form.addRow("sy", self.sy)
        form.addRow("sz", self.sz)
        form.addRow("About", self.scale_pivot)
        for label, field in zip(("point x", "point y", "point z"), self._scale_point):
            form.addRow(label, field)
        self._on_scale_pivot_changed()
        return panel

    def _rotate_panel(self) -> QWidget:
        panel = QWidget()
        form = QFormLayout(panel)
        self.angle = _spin(-3600.0, 3600.0, 0.0)
        # The axis direction; it passes through the pivot chosen below. Z is
        # the default so a plain rotation behaves exactly as in 2D.
        self.rotate_axis = QComboBox()
        for label, direction in _AXES:
            self.rotate_axis.addItem(label, direction)
        self.rotate_axis.setCurrentIndex(2)
        self.rotate_axis.currentIndexChanged.connect(self._on_rotate_axis_changed)
        self._axis_direction = _xyz_spins()
        self._axis_direction[2].setValue(1.0)
        self.rotate_pivot = QComboBox()
        for pivot in (Pivot.OBJECT_CENTER, Pivot.WORLD_ORIGIN, Pivot.ARBITRARY_POINT):
            self.rotate_pivot.addItem(pivot.value, pivot)
        self.rotate_pivot.currentIndexChanged.connect(self._on_rotate_pivot_changed)
        self._rotate_point = _xyz_spins()
        form.addRow("angle (deg)", self.angle)
        form.addRow("Axis", self.rotate_axis)
        for label, field in zip(("axis dx", "axis dy", "axis dz"), self._axis_direction):
            form.addRow(label, field)
        form.addRow("Through", self.rotate_pivot)
        for label, field in zip(("point x", "point y", "point z"), self._rotate_point):
            form.addRow(label, field)
        self._on_rotate_axis_changed()
        self._on_rotate_pivot_changed()
        return panel

    # --- reactions ----------------------------------------------------------

    def _on_kind_changed(self, index: int) -> None:
        self._params.setCurrentIndex(index)

    def _on_scale_pivot_changed(self, *_args) -> None:
        arbitrary = self.scale_pivot.currentData() is Pivot.ARBITRARY_POINT
        for field in self._scale_point:
            field.setEnabled(arbitrary)

    def _on_rotate_axis_changed(self, *_args) -> None:
        arbitrary = self.rotate_axis.currentData() is None
        for field in self._axis_direction:
            field.setEnabled(arbitrary)

    def _on_rotate_pivot_changed(self, *_args) -> None:
        arbitrary = self.rotate_pivot.currentData() is Pivot.ARBITRARY_POINT
        for field in self._rotate_point:
            field.setEnabled(arbitrary)

    # --- list editing -------------------------------------------------------

    def _current_step(self) -> TransformStep:
        kind = self.kind_field.currentText()
        if kind == _TRANSLATE:
            return Translate(self.tx.value(), self.ty.value(), self.tz.value())
        if kind == _SCALE:
            pivot = self.scale_pivot.currentData()
            point = _point(self._scale_point) if pivot is Pivot.ARBITRARY_POINT else None
            return Scale(
                self.sx.value(), self.sy.value(), self.sz.value(), pivot=pivot, point=point
            )
        pivot = self.rotate_pivot.currentData()
        point = _point(self._rotate_point) if pivot is Pivot.ARBITRARY_POINT else None
        axis = self.rotate_axis.currentData() or tuple(f.value() for f in self._axis_direction)
        return Rotate(self.angle.value(), pivot=pivot, point=point, axis=axis)

    def _add_step(self) -> None:
        step = self._current_step()
        self._steps.append(step)
        self.step_list.addItem(_describe(step))
        self._refresh_ok()

    def _remove_selected(self) -> None:
        row = self.step_list.currentRow()
        if row < 0:
            return
        self.step_list.takeItem(row)
        del self._steps[row]
        self._refresh_ok()

    def _refresh_ok(self) -> None:
        self._ok_button.setEnabled(bool(self._steps))

    def steps(self) -> list[TransformStep]:
        """The ordered list of transforms the user queued."""
        return list(self._steps)


def _point(fields: tuple[QDoubleSpinBox, ...]) -> Point:
    return Point(*(field.value() for field in fields))


def _describe(step: TransformStep) -> str:
    if isinstance(step, Translate):
        return f"Translate ({step.dx:g}, {step.dy:g}, {step.dz:g})"
    if isinstance(step, Scale):
        where = _where(step.pivot, step.point)
        return f"Scale ({step.sx:g}, {step.sy:g}, {step.sz:g}) about {where}"
    where = _where(step.pivot, step.point)
    return f"Rotate {step.degrees:g}° about {_axis_name(step.axis)} through {where}"


def _axis_name(axis) -> str:
    for label, direction in _AXES:
        if direction == axis:
            return label
    return "axis ({:g}, {:g}, {:g})".format(*axis)


def _where(pivot: Pivot, point: Point | None) -> str:
    if pivot is Pivot.ARBITRARY_POINT and point is not None:
        return "({:g}, {:g}, {:g})".format(*point.lifted(3))
    return pivot.value
