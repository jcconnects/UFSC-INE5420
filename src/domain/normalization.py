"""The view stage: world coordinates -> normalized coordinates (SCN).

Trabalho 1.3 added this stage. The Sistema de Coordenadas Normalizado (SCN) is
a fixed [-1, 1] x [-1, 1] square that the whole scene is mapped into before the
viewport transform. Because the mapping *undoes* the window's position and
orientation, turning the window turns the scene the opposite way on screen --
the spec's "o mundo sera girado na direcao contraria" -- without ever mutating
world coordinates.

Since trabalho 1.7 the world is 3D and the window is a view plane in space, so
the transform runs a projection (domain.projection) in the middle:

    1. view: translate the VRP -- or, in perspective (1.8), the COP -- to the
       origin, align the VPN with +z and the VUP with +y (for the default
       window in parallel: recenter, then rotate by -roll, exactly the 1.3
       steps)
    2. PROJECT: parallel ignores z (1.7); perspective divides by W = depth/d
       (1.8)
    3. normalize: scale each axis by 2/extent so the window fills [-1, 1]

Up to the divide everything is linear, so the three compose into one matrix,
built once per frame; mapping a point is that product followed by the divide
by W, which is always 1 in parallel. Both projections leave the image on the
window plane centered on the window, so the same normalization fits both.

The perspective divide is only defined in front of the COP, so the mapping
functions report -- or, for segments and polygons, trim away -- what lies
behind it (see domain.projection). A planar point (x, y) is read as (x, y, 0).
Everything here is pure.
"""

from __future__ import annotations

from .geometry import Point, compose, homogeneous_product
from .projection import (
    HomogeneousVector,
    ParallelProjection,
    Projection,
    in_front,
    trim_polygon_to_front,
    trim_segment_to_front,
)
from .transforms import scaling
from .window import Window

# The world's dimension since trabalho 1.7; planar points sit on z = 0.
_WORLD_DIMENSION = 3


def world_to_scn_matrix(
    window: Window, projection: Projection = ParallelProjection()
) -> list[list[float]]:
    """Build the world -> SCN homogeneous (4x4) matrix for the given window.

    compose applies its arguments left-to-right, so this reads as the natural
    sequence: place the view and project, then normalize the extents to
    [-1, 1]. The parallel orthogonal projection of trabalho 1.7 is the default.
    """
    return compose(
        projection.matrix(window),
        scaling(2.0 / window.width, 2.0 / window.height, 1.0),
    )


def map_to_scn(matrix: list[list[float]], point: Point) -> Point | None:
    """Map one world point through a prebuilt world -> SCN matrix.

    Returns the 2D SCN point (x, y) -- after the projection z carries nothing,
    so clipping and the viewport only ever see the view plane -- or None for a
    point behind the COP, which a perspective cannot map.
    """
    vector = _homogeneous(matrix, point)
    if not in_front(vector):
        return None
    return _divide(vector)


def map_segment_to_scn(
    matrix: list[list[float]], start: Point, end: Point
) -> tuple[Point, Point] | None:
    """Map a world segment to SCN, keeping only its part in front of the COP."""
    front = trim_segment_to_front(_homogeneous(matrix, start), _homogeneous(matrix, end))
    if front is None:
        return None
    return _divide(front[0]), _divide(front[1])


def map_polygon_to_scn(matrix: list[list[float]], vertices: list[Point]) -> list[Point]:
    """Map a closed polygon to SCN, keeping only its part in front of the COP."""
    front = trim_polygon_to_front([_homogeneous(matrix, vertex) for vertex in vertices])
    return [_divide(vector) for vector in front]


def to_scn(
    point: Point, window: Window, projection: Projection = ParallelProjection()
) -> Point | None:
    """Map a single world point into normalized coordinates."""
    return map_to_scn(world_to_scn_matrix(window, projection), point)


def _homogeneous(matrix: list[list[float]], point: Point) -> HomogeneousVector:
    return homogeneous_product(matrix, point.lifted(_WORLD_DIMENSION))


def _divide(vector: HomogeneousVector) -> Point:
    """The divide by W, keeping the view-plane coordinates (x, y)."""
    w = vector[-1]
    return Point(vector[0] / w, vector[1] / w)
