"""Uniform cubic B-Spline sampled by Forward Differences (trabalho 1.6).

Pure, dimension-agnostic sampling of a uniform cubic B-Spline -- points in,
points out, no Qt, no pixels -- so the math is unit-testable on its own, exactly
like the Bézier code in curves.py.

Two things set this apart from the Bézier curve of trabalho 1.5:

1. Sampling method. The trabalho title asks for Forward Differences. Instead of
   evaluating T . M_BS . G at every t (the blending-function form used for
   Bézier), we precompute the difference state [f, Δf, Δ²f, Δ³f] of the cubic and
   advance it with additions only -- three adds per step, no matrix product per
   point. That is the whole point of the method.

2. Segment structure. A uniform cubic B-Spline over N control points has N-3
   segments, each a sliding window of four consecutive points (P1-P4, P2-P5,
   ...). Any N >= 4 is valid (contrast the Bézier chain's 4, 7, 10, ...), and the
   curve does NOT interpolate its endpoints: at t=0 the basis row is [1,4,1,0]/6,
   so a segment starts at (Pi + 4 Pi+1 + Pi+2) / 6, not at a control point.

The geometry matrix (uniform cubic B-Spline basis), with the 1/6 folded in:

              [ -1   3  -3   1 ]
    M_BS = 1/6 [  3  -6   3   0 ]     C(t) = T . M_BS . G ,  T = [t³ t² t 1] ,
              [ -3   0   3   0 ]      G = [Pi Pi+1 Pi+2 Pi+3]^T
              [  1   4   1   0 ]

Per axis, [a, b, c, d] = M_BS . G gives C(t) = a t³ + b t² + c t + d. With step
Δ = 1/n, the Forward Differences initial state is

    f   = d
    Δf  = a Δ³ + b Δ² + c Δ
    Δ²f = 6 a Δ³ + 2 b Δ²
    Δ³f = 6 a Δ³

and each of the n updates is  f += Δf ;  Δf += Δ²f ;  Δ²f += Δ³f.

The math is ported from the class exercise
`docs/trabalhos/1.4.3 - Prática manual de B-Spline em Sala de Aula utilizando
Foward Differences.py`, rewritten over the pure Point type (no numpy: numpy is a
dev/notebook dependency, the domain stays dependency-free).
"""

from __future__ import annotations

from .geometry import Point

# Uniform cubic B-Spline basis matrix M_BS, 1/6 already distributed into the
# entries. Rows multiply the power basis T = [t³, t², t, 1]; columns weight the
# four control points of the sliding window.
_SIXTH = 1.0 / 6.0
_BSPLINE_MATRIX = (
    (-_SIXTH, 3.0 * _SIXTH, -3.0 * _SIXTH, _SIXTH),
    (3.0 * _SIXTH, -6.0 * _SIXTH, 3.0 * _SIXTH, 0.0),
    (-3.0 * _SIXTH, 0.0, 3.0 * _SIXTH, 0.0),
    (_SIXTH, 4.0 * _SIXTH, _SIXTH, 0.0),
)

# One cubic segment spans four consecutive control points; the window slides by
# one point per segment, so N points yield N-3 segments.
POINTS_PER_SEGMENT = 4


def segment_count(control_point_total: int) -> int:
    """How many cubic segments a control-point list of this length encodes.

    A uniform cubic B-Spline has one segment per sliding window of four, so N
    points give N-3 segments. Returns 0 when there are fewer than four points.
    """
    if control_point_total < POINTS_PER_SEGMENT:
        return 0
    return control_point_total - (POINTS_PER_SEGMENT - 1)


def _coefficients(window: tuple[Point, Point, Point, Point]) -> list[list[float]]:
    """Cubic coefficients [a, b, c, d] per spatial axis for one window.

    Computes M_BS . G, where G stacks the four control points. Returns one
    [a, b, c, d] list per axis, so the result works for 2D or 3D points alike.
    """
    dimension = window[0].dimension
    return [
        [
            sum(_BSPLINE_MATRIX[row][j] * window[j][axis] for j in range(4))
            for row in range(4)
        ]
        for axis in range(dimension)
    ]


def _forward_difference_state(
    coeffs: list[float], delta: float
) -> tuple[float, float, float, float]:
    """Initial Forward Differences state [f, Δf, Δ²f, Δ³f] of one cubic axis.

    `coeffs` is [a, b, c, d] with C(t) = a t³ + b t² + c t + d; `delta` is the
    step 1/n. These are the initial conditions the addition-only loop advances.
    """
    a, b, c, d = coeffs
    d1 = delta
    d2 = delta * delta
    d3 = d2 * delta
    return (
        d,
        a * d3 + b * d2 + c * d1,
        6.0 * a * d3 + 2.0 * b * d2,
        6.0 * a * d3,
    )


def _sample_segment(
    window: tuple[Point, Point, Point, Point], steps: int
) -> list[Point]:
    """Sample one B-Spline segment at steps+1 points via Forward Differences.

    Builds the difference state per axis, then advances it with additions only,
    emitting a Point at each of t = 0, 1/steps, ..., 1.
    """
    delta = 1.0 / steps
    axis_coeffs = _coefficients(window)
    # states[axis] = [f, Δf, Δ²f, Δ³f], mutated in place as the curve advances.
    states = [list(_forward_difference_state(coeffs, delta)) for coeffs in axis_coeffs]

    points: list[Point] = []
    for _ in range(steps + 1):
        points.append(Point(*(state[0] for state in states)))
        # Forward Differences update: additions only -- the essence of the method.
        for state in states:
            state[0] += state[1]
            state[1] += state[2]
            state[2] += state[3]
    return points


def sample_bspline(control_points: list[Point], steps_per_segment: int) -> list[Point]:
    """Sample a whole uniform cubic B-Spline into one polyline of points.

    Slides a four-point window across the control points (N-3 segments) and
    samples each by Forward Differences. Consecutive segments meet at a shared
    joint, so every segment after the first drops its t=0 point to avoid a
    duplicate (mirrors curves.sample_curve's joint dedup).

    Raises ValueError if steps_per_segment < 1 or there are fewer than four
    control points.
    """
    if steps_per_segment < 1:
        raise ValueError("steps_per_segment must be at least 1")
    segments = segment_count(len(control_points))
    if segments == 0:
        raise ValueError(
            "a uniform cubic B-Spline needs at least 4 control points "
            f"(got {len(control_points)})"
        )

    generated: list[Point] = []
    for segment_index in range(segments):
        window = (
            control_points[segment_index],
            control_points[segment_index + 1],
            control_points[segment_index + 2],
            control_points[segment_index + 3],
        )
        segment_points = _sample_segment(window, steps_per_segment)
        # First segment emits its start; later segments skip step 0, the shared
        # joint with the previous segment's end.
        generated.extend(segment_points if segment_index == 0 else segment_points[1:])
    return generated
