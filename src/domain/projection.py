"""Parallel orthogonal projection: 3D world -> 2D view plane (trabalho 1.7).

This is seam #2 of the 2D->3D plan -- the stage that turns the 3D world into
the 2D picture the rest of the pipeline (clipping, viewport) already handles.
The course's algorithm for a parallel orthogonal projection, and where each
step lives:

    1. translate the VRP to the origin            -> `view_matrix`
    2. find the angles of the VPN with x and y    -> transforms.angles_to_z
    3. rotate the world about x and y so the VPN
       aligns with z -- it ends as (0, 0, 1)      -> `view_matrix`
       (+ rotate about z so the VUP points along +y: the window roll, which in
       trabalho 1.3 was the "rotate by -angle" step)
    4. ignore every z coordinate                  -> `parallel_orthogonal`
    5. normalize the remaining coordinates        -> domain.normalization
    6. clip                                       -> domain.clipping
    7. map to viewport coordinates                -> domain.viewport

Steps 1-5 are all linear, so domain.normalization composes them into a single
world -> SCN matrix per frame. Trabalho 1.8 (perspective) changes the view
translation and swaps the step-4 matrix; nothing downstream moves.
"""

from __future__ import annotations

import math

from .geometry import Point, Vector, compose, transform_point
from .transforms import alignment_with_z, rotation_z, translation


def view_matrix(vrp: Point, vpn: Vector, vup: Vector) -> list[list[float]]:
    """World -> view coordinates: VRP at the origin, VPN on +z, VUP on +y.

    Steps 1-3 of the algorithm. After the alignment rotation the VUP lies in
    the xy plane (it is perpendicular to the VPN, now z), so a final rotation
    about z by the VUP's angle from +y sets the user's "up".
    """
    align = alignment_with_z(vpn)
    aligned_up = transform_point(align, Point(*vup))
    roll = math.atan2(aligned_up[0], aligned_up[1])
    return compose(
        translation(*(-component for component in vrp)),
        align,
        rotation_z(roll),
    )


def parallel_orthogonal() -> list[list[float]]:
    """Step 4: the orthogonal projection onto the view plane z = 0.

    In view coordinates the projectors run along z, so projecting simply zeroes
    z ("ignore todas as coordenadas Z"); x and y pass through untouched.
    """
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
