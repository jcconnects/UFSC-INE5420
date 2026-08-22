"""Window -> viewport transform: world (or normalized) coordinates to screen.

Pure function. Receives a point already normalized/projected and maps it to
pixel coordinates. It never calls Qt.

Anti-distortion (spec requirement: a square stays a square): the window is fit
isotropically into the viewport -- the same scale is used on x and y, and the
image is centered with margins when the aspect ratios differ. The y axis is
inverted because screen y grows downward.
"""

from __future__ import annotations

from .geometry import Point
from .window import Window


class ViewportTransform:
    def __init__(self, window: Window, vp_width: float, vp_height: float) -> None:
        self.window = window
        self.vp_width = vp_width
        self.vp_height = vp_height

    def _scale(self) -> float:
        """Single isotropic scale that fits the window inside the viewport."""
        return min(self.vp_width / self.window.width, self.vp_height / self.window.height)

    def apply(self, point: Point) -> tuple[float, float]:
        """Map a world point to (px, py) pixel coordinates."""
        scale = self._scale()
        used_w = self.window.width * scale
        used_h = self.window.height * scale
        # Center the fitted image so unequal aspect ratios produce margins,
        # not stretch.
        margin_x = (self.vp_width - used_w) / 2
        margin_y = (self.vp_height - used_h) / 2
        px = margin_x + (point[0] - self.window.x_min) * scale
        py = margin_y + (self.window.y_max - point[1]) * scale  # invert y
        return (px, py)
