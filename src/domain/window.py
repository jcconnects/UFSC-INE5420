"""The window: the rectangular region of the world currently visible.

In 1.1 it supports panning and zooming. Later trabalhos extend it: rotation
(1.3, the window is treated as a graphic object rotated in world coordinates)
and navigation in 3D space (1.7). Keeping pan/zoom here isolates all "what part
of the world do we see" logic from the viewport mapping.
"""

from __future__ import annotations


class Window:
    def __init__(self, x_min: float, y_min: float, x_max: float, y_max: float) -> None:
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("window bounds must be strictly increasing")
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    def pan(self, dx: float, dy: float) -> None:
        """Shift the visible region by a world-space delta (navigation)."""
        self.x_min += dx
        self.x_max += dx
        self.y_min += dy
        self.y_max += dy

    def zoom(self, factor: float) -> None:
        """Scale the window about its center.

        factor < 1 zooms in (window shrinks); factor > 1 zooms out.
        """
        if factor <= 0:
            raise ValueError("zoom factor must be positive")
        cx, cy = self.center
        half_w = self.width * factor / 2
        half_h = self.height * factor / 2
        self.x_min, self.x_max = cx - half_w, cx + half_w
        self.y_min, self.y_max = cy - half_h, cy + half_h
