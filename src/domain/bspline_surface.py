"""Bicubic B-Spline surfaces drawn by Forward Differences (trabalho 1.10).

Pure, dimension-agnostic math -- points in, points out, no Qt, no pixels --
mirroring surfaces.py (the Bézier patch of 1.9) and bspline.py (the B-Spline
curve of 1.6), whose basis M_BS and addition-only curve loop it reuses.

The user types one m x n control net, 4x4 up to 20x20. As the curve slides a
window of four points, the surface slides a 4x4 window over the net: each
window is the geometry matrix G of one patch, so the net holds (m-3)(n-3)
patches, and neighbouring patches join with C2 continuity on their own. On a
patch, per spatial component (x, y, z),

    Q(s, t) = S . C . T^T ,   C = M_BS . G . M_BS^T ,
    S = [s³ s² s 1] ,   T = [t³ t² t 1] .

Forward Differences draw the patch as curves of constant s and of constant t,
with additions only (Foley & van Dam's DrawSurfaceFwdDif, Fig. 11.46). With
the step δ = 1/n,

            [ 0     0    0   1 ]
    E(δ) =  [ δ³    δ²   δ   0 ]      E . [a b c d]^T = [f Δf Δ²f Δ³f]^T ,
            [ 6δ³   2δ²  0   0 ]      the initial state of a cubic, as in
            [ 6δ³   0    0   0 ]      bspline.py

and DD = E(δ) . C . E(δ)^T. Row 0 of DD is the difference state, along t, of
the curve s = 0; rows 1-3 hold its first three differences along s. Drawing
row 0 as a curve, then updating the rows top-down (row0 += row1, row1 += row2,
row2 += row3), steps s by δ: n+1 rounds draw the curves s = 0, δ, ..., 1. The
transposed DD swaps the roles and draws the curves t = 0, δ, ..., 1.

The book's algorithm has one error and omits two steps, which the professor's
corrected version (the gist ForwardDiff_Foley_vanDam.pde) points out:

1. Error: it draws each curve with an arbitrary point count. A curve must take
   exactly the n steps of the δ = 1/n that built E, or it misses the border.
2. Omitted: it never builds the E(δ) matrices.
3. Omitted: the row updates consume DD, so it must be rebuilt from C after the
   curves of constant s, then transposed for the curves of constant t.

One more trap when porting the gist: it computes C = M . G . M, which holds
only because the Bézier basis is symmetric. M_BS is not, so C here takes the
real transpose M_BS^T.
"""

from __future__ import annotations

from .bspline import BSPLINE_MATRIX, forward_difference_points
from .geometry import Point, multiply, transpose
from .surfaces import Patch

Matrix = list[list[float]]


def submatrices(net: list[list[Point]]) -> list[Patch]:
    """The (m-3)(n-3) sliding 4x4 windows of an m x n control net, row by row.

    Window (i, j) takes rows i..i+3 and columns j..j+3: the geometry matrix of
    one patch.
    """
    return [
        [row[j : j + 4] for row in net[i : i + 4]]
        for i in range(len(net) - 3)
        for j in range(len(net[0]) - 3)
    ]


def forward_difference_matrix(delta: float) -> Matrix:
    """E(δ): turns a cubic's coefficients [a, b, c, d] into [f, Δf, Δ²f, Δ³f]."""
    d2 = delta * delta
    d3 = d2 * delta
    return [
        [0.0, 0.0, 0.0, 1.0],
        [d3, d2, delta, 0.0],
        [6.0 * d3, 2.0 * d2, 0.0, 0.0],
        [6.0 * d3, 0.0, 0.0, 0.0],
    ]


def patch_curves(patch: Patch, steps: int) -> list[list[Point]]:
    """Draw one patch by Forward Differences: DrawSurfaceFwdDif, corrected.

    With n = steps and δ = 1/n in s and t, returns the n+1 curves of constant
    s (s = 0, δ, ..., 1, each running along t), then the n+1 curves of
    constant t, each of n+1 points: point b of the a-th curve of constant s is
    Q(a/n, b/n). Joining consecutive points draws the patch as a mesh.

    Raises ValueError if steps < 1.
    """
    if steps < 1:
        raise ValueError("steps must be at least 1")
    # C = M_BS . G . M_BS^T per axis -- the real transpose, M_BS is not symmetric.
    coefficients = [
        multiply(
            multiply(BSPLINE_MATRIX, [[point[axis] for point in row] for row in patch]),
            transpose(BSPLINE_MATRIX),
        )
        for axis in range(patch[0][0].dimension)
    ]
    e = forward_difference_matrix(1.0 / steps)
    constant_s = _curve_family(_difference_matrices(coefficients, e), steps)
    # The curves of constant s consumed DD: rebuild it from C, then transpose it.
    constant_t = _curve_family(
        [transpose(dd) for dd in _difference_matrices(coefficients, e)], steps
    )
    return constant_s + constant_t


def _difference_matrices(coefficients: list[Matrix], e: Matrix) -> list[Matrix]:
    """DD = E . C . E^T per axis: a curve's state in row 0, its steps in rows 1-3."""
    e_transposed = transpose(e)
    return [multiply(multiply(e, c), e_transposed) for c in coefficients]


def _curve_family(differences: list[Matrix], steps: int) -> list[list[Point]]:
    """The steps+1 curves drawn from row 0 of each axis's DD, consuming DD.

    Each round draws row 0 as a curve of exactly `steps` steps -- the count
    that matches δ, which the book gets wrong -- then steps the other
    parameter by updating the rows top-down.
    """
    curves: list[list[Point]] = []
    for _ in range(steps + 1):
        curves.append(forward_difference_points([dd[0] for dd in differences], steps))
        for dd in differences:
            for row in range(3):  # top-down: each row adds the next row's old value
                dd[row] = [a + b for a, b in zip(dd[row], dd[row + 1])]
    return curves
