"""Cubic Bézier curve math via blending functions (trabalho 1.5).

Pure, dimension-agnostic sampling of a Bézier curve. No Qt, no pixels, no
display concepts -- just points in, points out -- so the math is unit-testable
on its own.

The course derives the Bézier geometry matrix from Hermite (slides 5.20-5.22);
the product used here is M_B (Eq. 5.22):

        [ -1   3  -3   1 ]
    M_B =  [  3  -6   3   0 ]
        [ -3   3   0   0 ]
        [  1   0   0   0 ]

A point on one cubic segment with control points P1..P4 is

    C(t) = T . M_B . G ,   T = [t^3  t^2  t  1] ,   G = [P1 P2 P3 P4]^T ,

evaluated per spatial component (x, y[, z]). Expanding T . M_B gives the
Bernstein blending functions, so this is exactly the blending-function form the
trabalho title asks for.

Continuity of a chain (a Curve2D holding several segments) is at least G(0): the
spec's minimum, achieved by consecutive segments sharing an endpoint. So a chain
is a flat control-point list of length 4, 7, 10, ... -- four points for the first
segment, three more per additional segment, the shared point counted once.
"""

from __future__ import annotations

from .geometry import Point

# Bézier basis matrix M_B (Eq. 5.22). Rows multiply the power basis T; columns
# weight the four control points.
_BEZIER_MATRIX = (
    (-1.0, 3.0, -3.0, 1.0),
    (3.0, -6.0, 3.0, 0.0),
    (-3.0, 3.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 0.0),
)

# A cubic segment is defined by four control points; each extra segment adds
# three, reusing the previous segment's last point (G(0) continuity).
POINTS_PER_SEGMENT = 4
POINTS_PER_EXTRA_SEGMENT = 3


def segment_count(control_point_total: int) -> int:
    """How many cubic segments a control-point list of this length encodes.

    Returns 0 when the count is not a valid chain length (4, 7, 10, ...).
    """
    if control_point_total < POINTS_PER_SEGMENT:
        return 0
    if (control_point_total - POINTS_PER_SEGMENT) % POINTS_PER_EXTRA_SEGMENT != 0:
        return 0
    return 1 + (control_point_total - POINTS_PER_SEGMENT) // POINTS_PER_EXTRA_SEGMENT


def _blend(t: float, controls: tuple[Point, Point, Point, Point]) -> Point:
    """Evaluate one cubic Bézier segment at parameter t in [0, 1].

    Computes T . M_B once to get the four blending weights, then takes the
    weighted sum of the control points component by component (works for 2D or
    3D points alike).
    """
    powers = (t * t * t, t * t, t, 1.0)
    # weights[j] = sum_i powers[i] * M_B[i][j]  -> Bernstein blend of control j.
    weights = [
        sum(powers[i] * _BEZIER_MATRIX[i][j] for i in range(4)) for j in range(4)
    ]
    dimension = controls[0].dimension
    components = [
        sum(weights[j] * controls[j][axis] for j in range(4)) for axis in range(dimension)
    ]
    return Point(*components)


def sample_curve(control_points: list[Point], steps_per_segment: int) -> list[Point]:
    """Sample a whole Bézier chain into a polyline of generated points.

    `steps_per_segment` (k) sets the accuracy: each segment is split with step
    t = 1/k, matching slide 5.6's "defino um passo t = 1/k". Consecutive
    segments share their joint point, so it is emitted once (the next segment
    starts at its t=0, skipped to avoid a duplicate).

    Raises ValueError if the control-point count is not a valid chain length.
    """
    if steps_per_segment < 1:
        raise ValueError("steps_per_segment must be at least 1")
    segments = segment_count(len(control_points))
    if segments == 0:
        raise ValueError(
            "a Bézier chain needs 4, 7, 10, ... control points "
            f"(got {len(control_points)})"
        )

    generated: list[Point] = []
    for segment_index in range(segments):
        base = segment_index * POINTS_PER_EXTRA_SEGMENT
        controls = (
            control_points[base],
            control_points[base + 1],
            control_points[base + 2],
            control_points[base + 3],
        )
        # First segment emits its start (step 0); later segments skip step 0
        # because it is the previous segment's shared endpoint.
        start_step = 0 if segment_index == 0 else 1
        for step in range(start_step, steps_per_segment + 1):
            t = step / steps_per_segment
            generated.append(_blend(t, controls))
    return generated
