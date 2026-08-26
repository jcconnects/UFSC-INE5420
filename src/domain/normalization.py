"""The view stage: world coordinates -> normalized coordinates (SCN).

This is the stage trabalho 1.3 adds. The Sistema de Coordenadas Normalizado
(SCN) is a fixed [-1, 1] x [-1, 1] square that the whole scene is mapped into
before the viewport transform. Because the mapping *undoes* the window's
position and orientation, rotating the window by +theta rotates the scene by
-theta on screen -- exactly the spec's "o mundo sera girado na direcao
contraria" -- without ever mutating world coordinates.

The transform is the inverse of "place the window in the world":
    1. translate the window center to the origin
    2. rotate by -angle (undo the window's orientation)
    3. scale each axis by 2/extent so the window fills [-1, 1]

Everything here is pure and dimension-agnostic (it reuses the generic matrix
factories). In trabalho 1.1 this stage was a placeholder identity; here it
becomes the real view transform.
"""

from __future__ import annotations

from .geometry import Point, compose, transform_point
from .transforms import rotation, scaling, translation
from .window import Window


def world_to_scn_matrix(window: Window) -> list[list[float]]:
    """Build the world -> SCN homogeneous matrix for the given window.

    compose applies its arguments left-to-right, so this reads as the natural
    sequence: recenter, unrotate, then normalize the extents to [-1, 1].
    """
    cx, cy = window.center
    return compose(
        translation(-cx, -cy),
        rotation(-window.angle),
        scaling(2.0 / window.width, 2.0 / window.height),
    )


def to_scn(point: Point, window: Window) -> Point:
    """Map a single world point into normalized coordinates."""
    return transform_point(world_to_scn_matrix(window), point)
