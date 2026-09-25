"""Uniform cubic B-Spline via Forward Differences (trabalho 1.6).

Checks the segment-count rule (N-3 sliding windows), that Forward Differences
reproduce the direct evaluation T . M_BS . G, the defining B-Spline traits (it
does NOT interpolate its endpoints; a segment starts at (P1+4P2+P3)/6), and the
G(0) joint dedup shared with the Bézier code.
"""

import math

import pytest

from domain.bspline import (
    _BSPLINE_MATRIX,
    POINTS_PER_SEGMENT,
    sample_bspline,
    segment_count,
)
from domain.geometry import Point
from domain.objects import BSpline


def _direct_point(window, t):
    """C(t) = T . M_BS . G for one segment, evaluated directly (no differences).

    Reference used only to confirm the Forward Differences result.
    """
    powers = (t * t * t, t * t, t, 1.0)
    # coeffs[row] = row of M_BS . G, per axis; C(t)[axis] = sum_row powers[row]*coeff.
    dimension = window[0].dimension
    components = []
    for axis in range(dimension):
        coeff = [sum(_BSPLINE_MATRIX[r][j] * window[j][axis] for j in range(4)) for r in range(4)]
        components.append(sum(powers[r] * coeff[r] for r in range(4)))
    return Point(*components)


def test_segment_count_uniform_window_rule():
    assert segment_count(4) == 1
    assert segment_count(5) == 2
    assert segment_count(10) == 7


def test_segment_count_rejects_too_few_points():
    for bad in (0, 1, 2, 3):
        assert segment_count(bad) == 0


def test_forward_differences_match_direct_evaluation():
    # The core correctness check: sampling one segment by Forward Differences must
    # equal T . M_BS . G evaluated directly at every step.
    window = [Point(1, 1), Point(2, 3), Point(3, 0), Point(4, 1)]
    k = 30
    fd = sample_bspline(window, steps_per_segment=k)  # single segment: k+1 points
    assert len(fd) == k + 1
    for step in range(k + 1):
        direct = _direct_point(window, step / k)
        assert math.isclose(fd[step][0], direct[0], abs_tol=1e-9)
        assert math.isclose(fd[step][1], direct[1], abs_tol=1e-9)


def test_does_not_interpolate_first_control_point():
    # A uniform B-Spline starts at (P1 + 4 P2 + P3) / 6, not at P1 -- the trait
    # that distinguishes it from a Bézier curve.
    p1, p2, p3, p4 = Point(1, 1), Point(2, 3), Point(3, 0), Point(4, 1)
    points = sample_bspline([p1, p2, p3, p4], steps_per_segment=10)
    expected_x = (p1[0] + 4 * p2[0] + p3[0]) / 6.0
    expected_y = (p1[1] + 4 * p2[1] + p3[1]) / 6.0
    assert math.isclose(points[0][0], expected_x, abs_tol=1e-9)
    assert math.isclose(points[0][1], expected_y, abs_tol=1e-9)
    assert points[0] != p1


def test_chain_shares_joint_without_duplicating_it():
    # N=5 -> 2 segments meeting at a shared joint. The generated polyline holds
    # (k+1) + k points: the second segment's t=0 point is dropped.
    controls = [Point(0, 0), Point(1, 2), Point(2, 2), Point(3, 0), Point(4, -2)]
    k = 5
    points = sample_bspline(controls, steps_per_segment=k)
    assert segment_count(len(controls)) == 2
    assert len(points) == (k + 1) + k


def test_sample_bspline_rejects_bad_step_count():
    with pytest.raises(ValueError):
        sample_bspline([Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)], steps_per_segment=0)


def test_bspline_object_rejects_too_few_points():
    with pytest.raises(ValueError):
        BSpline("b", [Point(0, 0), Point(1, 1), Point(2, 2)])  # only 3 points


def test_bspline_object_accepts_minimum_four_points():
    obj = BSpline("b", [Point(0, 0), Point(1, 1), Point(2, 1), Point(3, 0)])
    assert obj.type.value == "bspline"


def test_bspline_to_segments_connects_generated_points():
    controls = [Point(0, 0), Point(1, 2), Point(2, 2), Point(3, 0), Point(4, -2), Point(5, 0)]
    curve = BSpline("b", controls)
    segments = curve.to_segments()
    generated = curve.generated_points()
    assert len(segments) == len(generated) - 1
    assert segments[0][0] == generated[0]
    assert segments[0][1] == generated[1]


def test_points_per_segment_is_four():
    # Guards the sliding-window assumption the segment-count rule depends on.
    assert POINTS_PER_SEGMENT == 4
