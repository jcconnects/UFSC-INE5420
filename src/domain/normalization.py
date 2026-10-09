"""The view stage: world coordinates -> normalized coordinates (SCN).

Trabalho 1.3 added this stage. The Sistema de Coordenadas Normalizado (SCN) is
a fixed [-1, 1] x [-1, 1] square that the whole scene is mapped into before the
viewport transform. Because the mapping *undoes* the window's position and
orientation, turning the window turns the scene the opposite way on screen --
the spec's "o mundo sera girado na direcao contraria" -- without ever mutating
world coordinates.

Since trabalho 1.7 the world is 3D and the window is a view plane in space, so
the transform runs the parallel orthogonal projection (domain.projection) in
the middle:

    1. view: translate the VRP to the origin, align the VPN with +z and the
       VUP with +y (for the default window: recenter, then rotate by -roll,
       exactly the 1.3 steps)
    2. PROJECT: ignore z
    3. normalize: scale each axis by 2/extent so the window fills [-1, 1]

Everything is linear, so the three compose into one matrix, built once per
frame. A planar point (x, y) is read as (x, y, 0). Everything here is pure.
"""

from __future__ import annotations

from .geometry import Point, compose, transform_point
from .projection import parallel_orthogonal, view_matrix
from .transforms import scaling
from .window import Window

# The world's dimension since trabalho 1.7; planar points sit on z = 0.
_WORLD_DIMENSION = 3


def world_to_scn_matrix(window: Window) -> list[list[float]]:
    """Build the world -> SCN homogeneous (4x4) matrix for the given window.

    compose applies its arguments left-to-right, so this reads as the natural
    sequence: place the view, project, then normalize the extents to [-1, 1].
    """
    return compose(
        view_matrix(window.vrp, window.vpn, window.vup),
        parallel_orthogonal(),
        scaling(2.0 / window.width, 2.0 / window.height, 1.0),
    )


def map_to_scn(matrix: list[list[float]], point: Point) -> Point:
    """Map one world point through a prebuilt world -> SCN matrix.

    Returns the 2D SCN point (x, y): after the projection z carries nothing, so
    clipping and the viewport only ever see the view plane.
    """
    projected = transform_point(matrix, point.lifted(_WORLD_DIMENSION))
    return Point(projected[0], projected[1])


def to_scn(point: Point, window: Window) -> Point:
    """Map a single world point into normalized coordinates."""
    return map_to_scn(world_to_scn_matrix(window), point)
