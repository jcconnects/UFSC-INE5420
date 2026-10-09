"""The canvas widget: executes neutral draw commands with points and lines only.

Wireframes and lines are drawn with drawPoint/drawLine only. The single
exception is trabalho 1.4's filled polygon: the spec asks for it explicitly
("polígonos preenchidos, utilizando as primitivas de preenchimento"), so a
DrawPolygon command is filled with drawPolygon. The widget asks the controller
for draw commands and paints them; it also turns mouse drags into navigation
and wheel scrolls into zoom, delegating both to the controller. It never reaches
into the domain directly.

Mouse navigation (trabalho 1.7 adds the orbit, like Blender's view drag):
    middle-drag  pan the window along its own axes
    left-drag    orbit: yaw/pitch the window about its center (VRP), so the
                 scene turns as if grabbed
    wheel        zoom
The current VRP/VPN is printed in the top margin as the view moves.

Subcanvas: the drawable widget is larger than the *subcanvas* -- the red-bordered
inner rectangle the normalized window maps into. Geometry outside the window
still paints into the margin between the subcanvas and the widget edge, so once
clipping lands (trabalho 1.4) it will visibly trim at the red border. The border
and its labels are pure decoration drawn here; the mapping itself lives in the
domain's ViewportTransform.
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

from app.controller import Controller
from app.render_pipeline import DrawLine, DrawPoint, DrawPolygon
from domain.window import WindowAxis

ZOOM_IN_FACTOR = 0.9
ZOOM_OUT_FACTOR = 1.1
# Left-drag orbit sensitivity: window rotation per dragged pixel.
ORBIT_DEGREES_PER_PIXEL = 0.5

# Pixel inset of the subcanvas (red border) from each widget edge.
SUBCANVAS_MARGIN = 20.0
_CANVAS_COLOR = QColor(0, 0, 0)
_SUBCANVAS_COLOR = QColor(220, 60, 60)
_LABEL_COLOR = QColor(255, 255, 255)


class ViewportWidget(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        # The button that started the current drag and the last mouse position.
        self._drag: tuple[Qt.MouseButton, QPoint] | None = None
        self.setMinimumSize(400, 400)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), _CANVAS_COLOR)
        commands = self.controller.render(self.width(), self.height(), SUBCANVAS_MARGIN)
        for command in commands:
            color = QColor(*command.color)
            if isinstance(command, DrawPolygon):
                # The one fill case (trabalho 1.4): a polygon the user chose to
                # fill, already clipped, painted with the language's fill
                # primitive. Everything else stays point/line only.
                painter.setPen(QPen(color))
                painter.setBrush(QBrush(color))
                painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in command.points]))
                painter.setBrush(Qt.BrushStyle.NoBrush)
            elif isinstance(command, DrawPoint):
                painter.setPen(QPen(color))
                painter.drawPoint(int(command.x), int(command.y))
            elif isinstance(command, DrawLine):
                painter.setPen(QPen(color))
                painter.drawLine(int(command.x1), int(command.y1), int(command.x2), int(command.y2))
        self._draw_subcanvas(painter)

    def _draw_subcanvas(self, painter: QPainter) -> None:
        x0, y0, x1, y1 = self.controller.subcanvas_rect(
            self.width(), self.height(), SUBCANVAS_MARGIN
        )
        painter.setPen(QPen(_SUBCANVAS_COLOR))
        painter.drawRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        painter.setPen(QPen(_LABEL_COLOR))
        # "Subcanvas" in the widget's top-left margin, above the red border.
        painter.drawText(int(x0), int(y0) - 6, "Subcanvas")
        # A reminder that the viewport (window) sits inside the subcanvas.
        label = "Sua Viewport < Subcanvas"
        metrics = painter.fontMetrics()
        painter.drawText(
            int(x1) - metrics.horizontalAdvance(label) - 8,
            int(y1) - 8,
            label,
        )
        # Where the window is in 3D, right-aligned in the top margin.
        vrp, vpn, _ = self.controller.view_vectors()
        readout = f"VRP {_triple(vrp, 0)}   VPN {_triple(vpn, 2)}"
        painter.drawText(int(x1) - metrics.horizontalAdvance(readout), int(y0) - 6, readout)

    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt override
        factor = ZOOM_IN_FACTOR if event.angleDelta().y() > 0 else ZOOM_OUT_FACTOR
        self.controller.zoom(factor)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._drag = (event.button(), event.position().toPoint())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._drag is None:
            return
        button, last = self._drag
        position = event.position().toPoint()
        delta = position - last
        self._drag = (button, position)
        if button == Qt.MouseButton.LeftButton:
            self._orbit(delta)
        else:
            self._pan(delta)
        self.update()

    def _orbit(self, delta: QPoint) -> None:
        # Turning the window one way turns the scene the other, so negate both:
        # dragging right swings the near side of the scene right, dragging down
        # swings it down -- the scene follows the hand, as when grabbing it.
        self.controller.rotate_window(-delta.x() * ORBIT_DEGREES_PER_PIXEL, WindowAxis.YAW)
        self.controller.rotate_window(-delta.y() * ORBIT_DEGREES_PER_PIXEL, WindowAxis.PITCH)

    def _pan(self, delta: QPoint) -> None:
        # Screen pixels -> world units using the viewport's own isotropic scale,
        # the single source of truth for the SCN->pixel mapping. Deriving it here
        # separately (widget minus margin) over-panned the y axis on a non-square
        # widget, drifting the scene off-centre until it clipped against the
        # fitted square. Invert both axes so the world follows the drag.
        scale_x, scale_y = self.controller.pan_world_per_pixel(
            self.width(), self.height(), SUBCANVAS_MARGIN
        )
        self.controller.pan(-delta.x() * scale_x, delta.y() * scale_y)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._drag = None


def _triple(values: tuple[float, ...], decimals: int) -> str:
    """'(x, y, z)' rounded for display; rounding first avoids printing '-0'."""
    rounded = [round(value, decimals) + 0.0 for value in values]
    return "(" + ", ".join(f"{value:.{decimals}f}" for value in rounded) + ")"
