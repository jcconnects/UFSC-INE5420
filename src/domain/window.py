"""The window: the region of the world currently visible.

The window is treated as a graphic object with its own orientation (trabalho
1.3): besides panning and zooming it can be *rotated* in world coordinates. Its
state is a center (in WC), half-extents, and a rotation `angle`. The extents are
interpreted in the window's own frame, so `width`/`height`/`center`/`zoom` stay
oblivious to rotation; only the basis vectors and `pan` consult the angle.

Rotating the window does not move world objects: the rotation is undone when
mapping the world into normalized coordinates (see `domain.normalization`), so
the scene appears to counter-rotate. All "what part of the world do we see"
logic lives here, isolated from the viewport mapping.
"""

from __future__ import annotations

import math


class Window:
    def __init__(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        angle: float = 0.0,
    ) -> None:
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("window bounds must be strictly increasing")
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
        # Window orientation in world coordinates, in radians. 0 is the default
        # axis-aligned window; positive is counter-clockwise.
        self.angle = angle

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    def right_vector(self) -> tuple[float, float]:
        """Unit vector along the window's +x axis, expressed in world coords."""
        return (math.cos(self.angle), math.sin(self.angle))

    def up_vector(self) -> tuple[float, float]:
        """Unit vector along the window's +y ("up") axis, in world coords."""
        return (-math.sin(self.angle), math.cos(self.angle))

    def pan(self, du: float, dv: float) -> None:
        """Shift the visible region along the window's own axes (navigation).

        `du` moves along the window's right vector and `dv` along its up vector,
        so panning always respects the user's "up" even when the window is
        rotated. With angle 0 this reduces to a plain world-space shift.
        """
        cos = math.cos(self.angle)
        sin = math.sin(self.angle)
        dx = du * cos - dv * sin
        dy = du * sin + dv * cos
        self.x_min += dx
        self.x_max += dx
        self.y_min += dy
        self.y_max += dy

    def zoom(self, factor: float) -> None:
        """Scale the window about its center.

        factor < 1 zooms in (window shrinks); factor > 1 zooms out. Rotation
        does not affect zoom: the extents live in the window's own frame.
        """
        if factor <= 0:
            raise ValueError("zoom factor must be positive")
        cx, cy = self.center
        half_w = self.width * factor / 2
        half_h = self.height * factor / 2
        self.x_min, self.x_max = cx - half_w, cx + half_w
        self.y_min, self.y_max = cy - half_h, cy + half_h

    def rotate(self, delta_radians: float) -> None:
        """Rotate the window about its center by a delta (accumulates)."""
        self.angle += delta_radians
