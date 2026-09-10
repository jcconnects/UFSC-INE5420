"""The canvas widget: executes neutral draw commands with points and lines only.

Wireframes and lines are drawn with drawPoint/drawLine only. The single
exception is trabalho 1.4's filled polygon: the spec asks for it explicitly
("polígonos preenchidos, utilizando as primitivas de preenchimento"), so a
DrawPolygon command is filled with drawPolygon. The widget asks the controller
for draw commands and paints them; it also turns mouse drags into pan and wheel
scrolls into zoom, delegating both to the controller. It never reaches into the
domain directly.

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

ZOOM_IN_FACTOR = 0.9
ZOOM_OUT_FACTOR = 1.1

# Pixel inset of the subcanvas (red border) from each widget edge.
SUBCANVAS_MARGIN = 20.0
_CANVAS_COLOR = QColor(0, 0, 0)
_SUBCANVAS_COLOR = QColor(220, 60, 60)
_LABEL_COLOR = QColor(255, 255, 255)


class ViewportWidget(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._last_drag: QPoint | None = None
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

    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt override
        factor = ZOOM_IN_FACTOR if event.angleDelta().y() > 0 else ZOOM_OUT_FACTOR
        self.controller.zoom(factor)
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.MiddleButton:
            self._last_drag = event.position().toPoint()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._last_drag is None:
            return
        position = event.position().toPoint()
        delta = position - self._last_drag
        self._last_drag = position
        # Screen pixels -> world units: scale by window size over the subcanvas
        # size (the box the window maps into), invert both axes so the world
        # follows the drag naturally.
        inner_w = max(self.width() - 2 * SUBCANVAS_MARGIN, 1)
        inner_h = max(self.height() - 2 * SUBCANVAS_MARGIN, 1)
        scale_x = self.controller.window.width / inner_w
        scale_y = self.controller.window.height / inner_h
        self.controller.pan(-delta.x() * scale_x, delta.y() * scale_y)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._last_drag = None
