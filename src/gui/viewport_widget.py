"""The canvas widget: executes neutral draw commands with points and lines only.

Per the spec, only drawPoint/drawLine primitives are used -- never drawPolygon.
The widget asks the controller for draw commands and paints them; it also turns
mouse drags into pan and wheel scrolls into zoom, delegating both to the
controller. It never reaches into the domain directly.
"""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from app.controller import Controller
from app.render_pipeline import DrawLine, DrawPoint

ZOOM_IN_FACTOR = 0.9
ZOOM_OUT_FACTOR = 1.1


class ViewportWidget(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._last_drag: QPoint | None = None
        self.setMinimumSize(400, 400)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        commands = self.controller.render(self.width(), self.height())
        for command in commands:
            painter.setPen(QPen(QColor(*command.color)))
            if isinstance(command, DrawPoint):
                painter.drawPoint(int(command.x), int(command.y))
            elif isinstance(command, DrawLine):
                painter.drawLine(int(command.x1), int(command.y1), int(command.x2), int(command.y2))

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
        # Screen pixels -> world units: scale by window size over widget size,
        # invert both axes so the world follows the drag naturally.
        scale_x = self.controller.window.width / max(self.width(), 1)
        scale_y = self.controller.window.height / max(self.height(), 1)
        self.controller.pan(-delta.x() * scale_x, delta.y() * scale_y)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        self._last_drag = None
