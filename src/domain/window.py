"""The window: the region of the world currently visible.

The window is treated as a graphic object with its own placement and
orientation. Since trabalho 1.7 it lives in 3D space, described the way the
course describes a view plane:

    VRP  View Reference Point -- the window center, a 3D point. The spec allows
         taking a point of the window as the VRP; the center is used so every
         rotation pivots on the middle of the view.
    VPN  View Plane Normal -- unit vector perpendicular to the window, pointing
         from the window toward the viewer (the scene is seen along -VPN).
    VUP  View Up vector -- unit vector of the window's "up", perpendicular to
         the VPN. The window's right vector is VUP x VPN.

plus `width` and `height` measured along the window's own right/up axes. The
default window lies on the z = 0 plane facing +z with +y up, which is exactly
the 2D window of trabalhos 1.1-1.6, so the planar world looks unchanged.

Navigation (trabalho 1.7, "navegação da window no espaço 3D"): `pan` slides the
VRP along the window's own right/up axes, `zoom` scales the extents, and
`rotate` turns the window about one of its own axes -- roll about the VPN (the
2D window rotation of trabalho 1.3), pitch about the right vector, yaw about
the up vector. As in 1.3, the window is rotated like any graphic object (the
arbitrary-axis rotation from domain.transforms, applied to its VPN/VUP), and
world objects never move: the view transform undoes the window's placement, so
the scene appears to turn the opposite way (see `domain.projection`).
"""

from __future__ import annotations

import math
from enum import Enum

from .geometry import Point, Vector, cross, dot, normalized, transform_point
from .transforms import rotation_about_axis

_ORIGIN = Point(0.0, 0.0, 0.0)


class WindowAxis(Enum):
    """The window's own axes it can rotate about (trabalho 1.7)."""

    ROLL = "roll"  # about the VPN: the 2D window rotation of trabalho 1.3
    PITCH = "pitch"  # about the right vector: tilt up/down
    YAW = "yaw"  # about the up vector (VUP): turn left/right


class Window:
    def __init__(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        angle: float = 0.0,
    ) -> None:
        """A window over [x_min, x_max] x [y_min, y_max] on the z = 0 plane.

        `angle` is the initial roll in radians (counter-clockwise), as in
        trabalho 1.3. The 3D orientation then changes through `rotate`.
        """
        if x_max <= x_min or y_max <= y_min:
            raise ValueError("window bounds must be strictly increasing")
        self.vrp = Point((x_min + x_max) / 2, (y_min + y_max) / 2, 0.0)
        self.width = x_max - x_min
        self.height = y_max - y_min
        self.vpn: Vector = (0.0, 0.0, 1.0)
        self.vup: Vector = (-math.sin(angle), math.cos(angle), 0.0)

    def right_vector(self) -> Vector:
        """Unit vector along the window's +x axis, in world coords (VUP x VPN)."""
        return cross(self.vup, self.vpn)

    def up_vector(self) -> Vector:
        """Unit vector along the window's +y ("up") axis, in world coords."""
        return self.vup

    def pan(self, du: float, dv: float) -> None:
        """Slide the window along its own axes (navigation).

        `du` moves along the window's right vector and `dv` along its up vector,
        so panning always follows the screen -- the user's "up" -- however the
        window is oriented in space.
        """
        right = self.right_vector()
        self.vrp = Point(
            *(
                center + du * r + dv * u
                for center, r, u in zip(self.vrp, right, self.vup)
            )
        )

    def zoom(self, factor: float) -> None:
        """Scale the window about its center.

        factor < 1 zooms in (window shrinks); factor > 1 zooms out. Orientation
        does not affect zoom: the extents live in the window's own frame.
        """
        if factor <= 0:
            raise ValueError("zoom factor must be positive")
        self.width *= factor
        self.height *= factor

    def rotate(self, delta_radians: float, axis: WindowAxis = WindowAxis.ROLL) -> None:
        """Rotate the window about one of its own axes by a delta (accumulates).

        Positive follows the right-hand rule about that axis; for the default
        roll it is counter-clockwise on screen, exactly the 1.3 rotation. The
        VPN/VUP are re-orthonormalized so repeated rotations cannot drift.
        """
        direction = {
            WindowAxis.ROLL: self.vpn,
            WindowAxis.PITCH: self.right_vector(),
            WindowAxis.YAW: self.vup,
        }[axis]
        matrix = rotation_about_axis(_ORIGIN, direction, delta_radians)
        vpn = normalized(transform_point(matrix, Point(*self.vpn)).coords)
        vup = transform_point(matrix, Point(*self.vup)).coords
        # Remove any VPN component rounding left in the VUP, then renormalize.
        along_vpn = dot(vup, vpn)
        self.vpn = vpn
        self.vup = normalized(tuple(u - along_vpn * n for u, n in zip(vup, vpn)))
