"""SCN -> viewport transform: normalized coordinates to screen pixels.

Pure function. It receives a point already in the normalized [-1, 1] x [-1, 1]
square (see `domain.normalization`) and maps it to pixel coordinates. It never
calls Qt and, since trabalho 1.3, no longer needs the window at all -- the SCN
square is fixed, so window position/orientation are already baked into the
normalized coordinates upstream.

Anti-distortion (spec requirement: a square stays a square): the [-1, 1] square
is fit isotropically into the viewport -- the same scale on x and y, centered
with margins when the viewport is not itself square. The y axis is inverted
because screen y grows downward.
"""

from __future__ import annotations

from .geometry import Point

# The normalized square spans 2 units on each axis: [-1, 1].
_SCN_SPAN = 2.0


class ViewportTransform:
    def __init__(self, vp_width: float, vp_height: float) -> None:
        self.vp_width = vp_width
        self.vp_height = vp_height

    def _scale(self) -> float:
        """Isotropic scale that fits the [-1, 1] square inside the viewport."""
        return min(self.vp_width, self.vp_height) / _SCN_SPAN

    def apply(self, point: Point) -> tuple[float, float]:
        """Map a normalized (SCN) point to (px, py) pixel coordinates."""
        scale = self._scale()
        used = _SCN_SPAN * scale
        # Center the fitted square so a non-square viewport yields margins, not
        # stretch.
        margin_x = (self.vp_width - used) / 2
        margin_y = (self.vp_height - used) / 2
        px = margin_x + (point[0] + 1.0) * scale
        py = margin_y + (1.0 - point[1]) * scale  # invert y
        return (px, py)
