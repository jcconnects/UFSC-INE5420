"""Bicubic Bézier surfaces via blending functions (trabalho 1.9).

Pure, dimension-agnostic evaluation of a bicubic Bézier patch ("retalho") --
points in, points out, no Qt, no pixels -- mirroring the curve math in
curves.py, whose basis it reuses.

A patch is its geometry matrix G: 4 rows of 4 control points P_ij. A point on
it is

    Q(s, t) = S . M_B . G . M_B^T . T^T ,   S = [s³ s² s 1] ,  T = [t³ t² t 1] ,

evaluated per spatial component (x, y, z), with M_B the Bézier basis of
trabalho 1.5. S . M_B and M_B^T . T^T are the curves' four Bernstein weights for
s and for t, so Q is the sum of the 16 surface blending functions
B_i(s) . B_j(t), each weighting its control point P_ij. Like a Bézier curve at
its ends, a patch interpolates only its four corner points.
"""

from __future__ import annotations

from . import curves
from .geometry import Point

# A patch's geometry matrix: 4 rows of 4 control points.
Patch = list[list[Point]]


def patch_point(patch: Patch, s: float, t: float) -> Point:
    """Evaluate one bicubic patch at (s, t) in [0, 1] x [0, 1].

    Weights each control point P_ij by its blending function B_i(s) . B_j(t)
    and sums them component by component.
    """
    s_weights = curves.blending_weights(s)
    t_weights = curves.blending_weights(t)
    dimension = patch[0][0].dimension
    return Point(
        *(
            sum(
                s_weights[i] * t_weights[j] * patch[i][j][axis]
                for i in range(4)
                for j in range(4)
            )
            for axis in range(dimension)
        )
    )


def sample_patch(patch: Patch, steps: int) -> list[list[Point]]:
    """Sample one patch on an (n+1) x (n+1) grid, n = steps, step 1/n in s and t.

    grid[a][b] = Q(a/n, b/n): each grid row is a curve of constant s, each
    column a curve of constant t. Connecting neighbours along both draws the
    patch as a mesh.

    Raises ValueError if steps < 1.
    """
    if steps < 1:
        raise ValueError("steps must be at least 1")
    return [
        [patch_point(patch, a / steps, b / steps) for b in range(steps + 1)]
        for a in range(steps + 1)
    ]
