"""The generic transform engine trabalho 1.2 asks for.

`apply(matrix, obj)` is the single routine that transforms *any* graphic object
by *any* homogeneous matrix -- a minimal graphics engine, exactly as the spec
frames it. It is fed by matrix *factories* (translation / scaling / rotation),
one per transform, each returning a plain homogeneous matrix.

Everything here is dimension-agnostic and pure. The 2D factories build 3x3
matrices today; the 3D siblings (rotation about an arbitrary axis, 1.7) will be
added alongside without touching `apply`. This is seam #1 of the 2D->3D plan.

Composition follows geometry.compose: `compose(A, B)` applies A then B
(left-to-right). So a rotation about an arbitrary point p reads in the natural
order -- translate p to the origin, rotate, translate back:

    compose(translation(-px, -py), rotation(theta), translation(px, py))
"""

from __future__ import annotations

import math

from .geometry import Point, compose
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

    Positive angle rotates counter-clockwise. 3D rotation (about an axis) is a
    separate factory added in trabalho 1.7; this 2D form stays as is.
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
