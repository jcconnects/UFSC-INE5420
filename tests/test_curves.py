"""Cubic Bézier math via blending functions (trabalho 1.5).

Checks the blending-function evaluation (M_B, Eq. 5.22), chain length rules, and
that chained segments join with G(0) continuity (shared endpoint, no duplicate
generated point at the joint).
"""

import math

import pytest

from domain.curves import sample_curve, segment_count
from domain.geometry import Point
from domain.objects import Curve2D


def test_segment_count_valid_chain_lengths():
    assert segment_count(4) == 1
    assert segment_count(7) == 2
    assert segment_count(10) == 3


def test_segment_count_rejects_invalid_lengths():
    for bad in (0, 1, 2, 3, 5, 6, 8, 9):
        assert segment_count(bad) == 0


def test_curve_passes_through_first_and_last_control_points():
    # A cubic Bézier interpolates P1 (t=0) and P4 (t=1); interior points only
    # pull the curve, they are not on it.
    controls = [Point(0, 0), Point(1, 3), Point(2, -3), Point(3, 0)]
    points = sample_curve(controls, steps_per_segment=10)
    assert points[0] == Point(0, 0)
    assert points[-1] == Point(3, 0)


def test_midpoint_matches_closed_form():
    # Straight blending check: at t=0.5 the standard cubic Bézier value is
    # (P1 + 3P2 + 3P3 + P4) / 8 per component.
    p1, p2, p3, p4 = Point(0, 0), Point(0, 6), Point(6, 6), Point(6, 0)
    points = sample_curve([p1, p2, p3, p4], steps_per_segment=2)  # steps: 0, .5, 1
    mid = points[1]
    expected_x = (0 + 3 * 0 + 3 * 6 + 6) / 8
    expected_y = (0 + 3 * 6 + 3 * 6 + 0) / 8
    assert math.isclose(mid[0], expected_x)
    assert math.isclose(mid[1], expected_y)


def test_chain_shares_joint_without_duplicating_it():
    # Two segments sharing P4: the generated polyline must contain the joint
    # exactly once (G(0), no doubled point that would draw a zero-length span).
    controls = [
        Point(0, 0), Point(1, 1), Point(2, 1), Point(3, 0),  # segment 1
        Point(4, -1), Point(5, -1), Point(6, 0),             # segment 2 (shares P4)
    ]
    k = 5
    points = sample_curve(controls, steps_per_segment=k)
    # First segment: k+1 points; each further segment: k more (start skipped).
    assert len(points) == (k + 1) + k
    # The shared joint P4 = (3, 0) appears once, at the segment boundary.
    joint_hits = [p for p in points if p == Point(3, 0)]
    assert len(joint_hits) == 1


def test_curve2d_rejects_bad_control_count():
    with pytest.raises(ValueError):
        Curve2D("c", [Point(0, 0), Point(1, 1), Point(2, 2)])  # only 3 points


def test_curve2d_to_segments_connects_generated_points():
    controls = [Point(0, 0), Point(1, 2), Point(2, 2), Point(3, 0)]
    curve = Curve2D("c", controls)
    segments = curve.to_segments()
    generated = curve.generated_points()
    assert len(segments) == len(generated) - 1
    # Segments are consecutive generated points, end-to-end.
    assert segments[0][0] == generated[0]
    assert segments[0][1] == generated[1]
