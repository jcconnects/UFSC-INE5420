"""Projections: 3D world -> 2D view plane (parallel 1.7, perspective 1.8).

This is seam #2 of the 2D->3D plan -- the stage that turns the 3D world into
the 2D picture the rest of the pipeline (clipping, viewport) already handles.
The course gives one algorithm per projection. They differ only in the point
moved to the origin and in the step-4 matrix:

    parallel orthogonal (1.7)            perspective (1.8)
    1. translate the VRP to the origin   1. translate the COP to the origin
    2. find the angles of the VPN with x and y                 (same)
    3. rotate the world about x and y so the VPN aligns
       with z -- it ends as (0, 0, 1)                          (same)
       (+ rotate about z so the VUP points along +y: the window roll, which in
       trabalho 1.3 was the "rotate by -angle" step)
    4. ignore every z coordinate         4. perspective matrix, divide by W
    5. normalize the remaining coordinates  -> domain.normalization
    6. clip, in 2D                          -> domain.clipping
    7. map to viewport coordinates          -> domain.viewport

Steps 1-3 are `view_matrix`; step 4 is `parallel_orthogonal` or `perspective`.
`ParallelProjection` and `PerspectiveProjection` package each algorithm behind
one interface, so the pipeline runs whichever the user picked. Steps 1-5 are
homogeneous matrices, so domain.normalization composes them into a single
world -> SCN matrix per frame; the only non-linear part of the perspective is
the final divide by W.

The center of projection (COP) is virtual: a point d behind the window, on its
normal through the center and on the viewer's side (the VPN points toward the
viewer). It is never drawn and travels with the window. A short d acts as a
wide-angle lens (wide field of view, strong convergence); a long d as a
telephoto (narrow field, flattened depth) that tends to the parallel projection
as d grows.

The divide by W only makes sense in front of the COP: behind it W < 0 mirrors
the geometry through the COP, and at it W = 0 divides by zero. So before the
divide, `trim_segment_to_front` and `trim_polygon_to_front` cut away what lies
behind the COP. That is not clipping against the window -- the window clip
stays 2D, after the projection, as the spec asks -- just the part of space a
perspective cannot map.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .geometry import Point, Vector, compose, transform_point
from .transforms import alignment_with_z, rotation_z, translation
from .window import Window

Matrix = list[list[float]]
# A point after a homogeneous matrix and before the divide: (x, y, z, W).
HomogeneousVector = tuple[float, ...]

# Smallest W kept in front of the COP. In perspective W = depth / d, so this
# keeps geometry at least d/1000 ahead of the COP; a parallel projection has
# W = 1 everywhere and never trims.
_FRONT_W = 1e-3


def view_matrix(origin: Point, vpn: Vector, vup: Vector) -> Matrix:
    """World -> view coordinates: `origin` at 0, VPN on +z, VUP on +y.

    Steps 1-3 of both algorithms: `origin` is the VRP for the parallel
    projection and the COP for the perspective one. After the alignment
    rotation the VUP lies in the xy plane (it is perpendicular to the VPN, now
    z), so a final rotation about z by the VUP's angle from +y sets the user's
    "up".
    """
    align = alignment_with_z(vpn)
    aligned_up = transform_point(align, Point(*vup))
    roll = math.atan2(aligned_up[0], aligned_up[1])
    return compose(
        translation(*(-component for component in origin)),
        align,
        rotation_z(roll),
    )


def parallel_orthogonal() -> Matrix:
    """Step 4 of the parallel projection: onto the view plane z = 0.

    In view coordinates the projectors run along z, so projecting simply zeroes
    z ("ignore todas as coordenadas Z"); x and y pass through untouched.
    """
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def perspective(cop_distance: float) -> Matrix:
    """Step 4 of the perspective projection: onto the window plane.

    In view coordinates the COP is the origin and the window plane lies at
    z = -d: the VPN points from the window toward the viewer (trabalho 1.7), so
    once it is aligned with +z the scene lies along -z. By similar triangles a
    point (x, y, z) in front of the COP (z < 0) lands on that plane at

        x_p = x / (-z/d)        y_p = y / (-z/d)

    which is the course's x_p = x / (z/d) with the plane at z = -d instead of
    z = d. As a homogeneous matrix the division moves into W: the product is
    (x, y, z, -z/d), and dividing it by W = -z/d -- the point's depth in front
    of the COP, in units of d -- gives the projection. A point on the window
    plane has W = 1 and stays put; a farther one has W > 1 and shrinks; a
    nearer one grows. W <= 0 means at or behind the COP.
    """
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, -1.0 / cop_distance, 0.0],
    ]


class Projection(ABC):
    """One of the course's projection algorithms, steps 1-4: world -> view plane."""

    @abstractmethod
    def view_origin(self, window: Window) -> Point:
        """Step 1: the point translated to the origin."""

    @abstractmethod
    def projection_matrix(self) -> Matrix:
        """Step 4, applied in view coordinates."""

    def center_of_projection(self, window: Window) -> Point | None:
        """Where the projectors meet, or None when they are parallel."""
        return None

    def field_of_view(self, window: Window) -> float | None:
        """Horizontal angle the window spans from the COP (radians), if any."""
        return None

    def matrix(self, window: Window) -> Matrix:
        """Steps 1-4 as one homogeneous matrix: place the view, then project."""
        return compose(
            view_matrix(self.view_origin(window), window.vpn, window.vup),
            self.projection_matrix(),
        )


@dataclass(frozen=True)
class ParallelProjection(Projection):
    """Parallel orthogonal projection (trabalho 1.7): projectors along the VPN."""

    def view_origin(self, window: Window) -> Point:
        return window.vrp

    def projection_matrix(self) -> Matrix:
        return parallel_orthogonal()


@dataclass(frozen=True)
class PerspectiveProjection(Projection):
    """Perspective projection (trabalho 1.8) from a COP behind the window.

    `cop_distance` is d, the distance from the COP to the projection plane (the
    window). The COP sits on the window's normal through its center, on the
    viewer's side: COP = VRP + d * VPN.
    """

    cop_distance: float

    def __post_init__(self) -> None:
        if self.cop_distance <= 0:
            raise ValueError("the COP must sit a positive distance behind the window")

    def center_of_projection(self, window: Window) -> Point:
        return Point(
            *(center + self.cop_distance * n for center, n in zip(window.vrp, window.vpn))
        )

    def field_of_view(self, window: Window) -> float:
        return 2.0 * math.atan(window.width / 2.0 / self.cop_distance)

    def view_origin(self, window: Window) -> Point:
        return self.center_of_projection(window)

    def projection_matrix(self) -> Matrix:
        return perspective(self.cop_distance)


# --- what lies behind the COP -----------------------------------------------


def in_front(vector: HomogeneousVector) -> bool:
    """Whether a projected (undivided) point lies in front of the COP."""
    return vector[-1] >= _FRONT_W


def trim_segment_to_front(
    start: HomogeneousVector, end: HomogeneousVector
) -> tuple[HomogeneousVector, HomogeneousVector] | None:
    """The part of a segment in front of the COP, still undivided.

    Both ends in front: unchanged. Both behind: None. One of each: the hidden
    end moves to where the segment crosses the front limit. The matrices are
    linear, so interpolating the homogeneous vectors finds the same point as
    interpolating in the world.
    """
    start_in_front, end_in_front = in_front(start), in_front(end)
    if start_in_front and end_in_front:
        return start, end
    if not (start_in_front or end_in_front):
        return None
    crossing = _front_crossing(start, end)
    return (start, crossing) if start_in_front else (crossing, end)


def trim_polygon_to_front(vertices: list[HomogeneousVector]) -> list[HomogeneousVector]:
    """The part of a closed polygon in front of the COP, still undivided.

    One Sutherland-Hodgman pass, as in domain.clipping, against the single
    boundary in front of the COP instead of the four window borders.
    """
    output: list[HomogeneousVector] = []
    for index, current in enumerate(vertices):
        previous = vertices[index - 1]
        if in_front(current) != in_front(previous):
            output.append(_front_crossing(previous, current))
        if in_front(current):
            output.append(current)
    return output


def _front_crossing(a: HomogeneousVector, b: HomogeneousVector) -> HomogeneousVector:
    """Where segment a->b crosses the front limit W = _FRONT_W."""
    t = (_FRONT_W - a[-1]) / (b[-1] - a[-1])
    return tuple(p + t * (q - p) for p, q in zip(a, b))
