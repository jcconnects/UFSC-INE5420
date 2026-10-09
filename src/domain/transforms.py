"""The generic transform engine trabalho 1.2 asks for.

`apply(matrix, obj)` is the single routine that transforms *any* graphic object
by *any* homogeneous matrix -- a minimal graphics engine, exactly as the spec
frames it. It is fed by matrix *factories* (translation / scaling / rotation),
one per transform, each returning a plain homogeneous matrix.

Everything here is dimension-agnostic and pure. `translation`/`scaling` size
their matrix by the number of components (3x3 in 2D, 4x4 in 3D); the 3D
rotations of trabalho 1.7 (`rotation_x/y/z`, `rotation_about_axis`) sit beside
the 2D `rotation` without touching `apply`. This is seam #1 of the 2D->3D plan.

Composition follows geometry.compose: `compose(A, B)` applies A then B
(left-to-right). So a rotation about an arbitrary point p reads in the natural
order -- translate p to the origin, rotate, translate back:

    compose(translation(-px, -py), rotation(theta), translation(px, py))

All rotations follow the right-hand rule: a positive angle turns
counter-clockwise when seen from the tip of the axis looking at the origin.
"""

from __future__ import annotations

import math

from .geometry import Point, Vector, compose, normalized
from .objects import GraphicObject


def apply(matrix, obj: GraphicObject) -> GraphicObject:
    """Transform any object in place by a homogeneous matrix and return it.

    The generic engine: it neither knows nor cares what the object is or what
    the matrix does. Object types decompose to segments elsewhere; here they are
    just a bag of homogeneous vertices to be multiplied.
    """
    obj.transform(matrix)
    return obj


def translation(*deltas: float) -> list[list[float]]:
    """Homogeneous translation matrix for a per-axis displacement vector.

    2D: translation(dx, dy) -> 3x3. 3D: translation(dx, dy, dz) -> 4x4. The size
    follows the number of deltas, so nothing here assumes a dimension.
    """
    if not deltas:
        raise ValueError("translation needs at least one delta")
    size = len(deltas) + 1  # spatial axes + homogeneous row/column
    matrix = [[1.0 if r == c else 0.0 for c in range(size)] for r in range(size)]
    for axis, delta in enumerate(deltas):
        matrix[axis][-1] = float(delta)
    return matrix


def scaling(*factors: float) -> list[list[float]]:
    """Homogeneous scaling matrix about the origin, one factor per axis.

    This scales about the world origin. Scaling about the object center -- the
    "natural" scaling the spec wants -- is that origin scaling conjugated with a
    translation; build it with `scaling_about`.
    """
    if not factors:
        raise ValueError("scaling needs at least one factor")
    size = len(factors) + 1
    matrix = [[0.0] * size for _ in range(size)]
    for axis, factor in enumerate(factors):
        matrix[axis][axis] = float(factor)
    matrix[-1][-1] = 1.0
    return matrix


def rotation(angle_radians: float) -> list[list[float]]:
    """Homogeneous 2D rotation matrix about the origin (counter-clockwise).

    Positive angle rotates counter-clockwise. The 3D rotations (trabalho 1.7)
    are the separate factories below; this 2D form stays as is.
    """
    cos = math.cos(angle_radians)
    sin = math.sin(angle_radians)
    return [
        [cos, -sin, 0.0],
        [sin, cos, 0.0],
        [0.0, 0.0, 1.0],
    ]


def scaling_about(center: Point, *factors: float) -> list[list[float]]:
    """Scaling by `factors` about an arbitrary center (the object's centroid).

    Conjugates origin scaling with a translation: move the center to the origin,
    scale, move it back. This is the "natural" scaling of the spec -- the object
    appears to shrink or swell in place.
    """
    to_origin = translation(*(-component for component in center))
    back = translation(*center)
    return compose(to_origin, scaling(*factors), back)


def rotation_about(center: Point, angle_radians: float) -> list[list[float]]:
    """2D rotation by `angle_radians` about an arbitrary center point.

    The workhorse behind all three rotation modes the spec lists: pass the world
    origin, the object center, or any user-chosen point as `center`.
    """
    to_origin = translation(*(-component for component in center))
    back = translation(*center)
    return compose(to_origin, rotation(angle_radians), back)


# --- 3D rotations (trabalho 1.7) --------------------------------------------


def rotation_x(angle_radians: float) -> list[list[float]]:
    """Homogeneous 3D rotation about the x axis (y turns toward z)."""
    cos = math.cos(angle_radians)
    sin = math.sin(angle_radians)
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, cos, -sin, 0.0],
        [0.0, sin, cos, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def rotation_y(angle_radians: float) -> list[list[float]]:
    """Homogeneous 3D rotation about the y axis (z turns toward x)."""
    cos = math.cos(angle_radians)
    sin = math.sin(angle_radians)
    return [
        [cos, 0.0, sin, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-sin, 0.0, cos, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def rotation_z(angle_radians: float) -> list[list[float]]:
    """Homogeneous 3D rotation about the z axis (x turns toward y).

    The 3D form of the plane rotation: on z = 0 it matches `rotation`.
    """
    cos = math.cos(angle_radians)
    sin = math.sin(angle_radians)
    return [
        [cos, -sin, 0.0, 0.0],
        [sin, cos, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def angles_to_z(direction: Vector) -> tuple[float, float]:
    """The angles (about x, then about y) that turn `direction` onto +z.

    The step of the course's projection algorithm "determine os ângulos do VPN
    com X e Y": rotating about x by the first angle drops the y component (the
    vector lands in the xz plane), then rotating about y by the second drops the
    x component, leaving (0, 0, |direction|). atan2 keeps every case defined,
    including a direction already along x (first angle 0) or along -z.
    """
    x, y, z = normalized(direction)
    angle_x = math.atan2(y, z)
    angle_y = -math.atan2(x, math.hypot(y, z))
    return angle_x, angle_y


def alignment_with_z(direction: Vector) -> list[list[float]]:
    """Rotation about x then y that maps `direction` onto +z.

    Shared by the parallel projection (it aligns the VPN with z, so the VPN
    ends as (0, 0, 1)) and by `rotation_about_axis` (it aligns the axis).
    """
    angle_x, angle_y = angles_to_z(direction)
    return compose(rotation_x(angle_x), rotation_y(angle_y))


def rotation_about_axis(
    point: Point, direction: Vector, angle_radians: float
) -> list[list[float]]:
    """3D rotation by `angle_radians` about an arbitrary axis.

    The axis passes through `point` along `direction`. The course's algorithm:
    move the axis to the origin, rotate about x and y until it lies on z, rotate
    about z by the angle, undo the two alignment rotations (reverse order,
    negated angles), and move back. A principal axis is just a special case --
    direction (1, 0, 0) through the origin is `rotation_x`. A planar `point`
    (x, y) is read as (x, y, 0).
    """
    point = point.lifted(3)
    angle_x, angle_y = angles_to_z(direction)
    return compose(
        translation(*(-component for component in point)),
        rotation_x(angle_x),
        rotation_y(angle_y),
        rotation_z(angle_radians),
        rotation_y(-angle_y),
        rotation_x(-angle_x),
        translation(*point),
    )
