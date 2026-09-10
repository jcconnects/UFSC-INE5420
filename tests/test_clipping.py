"""Clipping against the normalized [-1, 1] window (trabalho 1.4).

Covers point clipping, both selectable line techniques (Cohen-Sutherland and
Liang-Barsky must agree on the geometry), and Sutherland-Hodgman polygon
clipping. Inputs are SCN points, since clipping runs in normalized space.
"""

import math

import pytest

from domain.clipping import (
    LineClipper,
    clip_line,
    clip_point,
    cohen_sutherland,
    liang_barsky,
    sutherland_hodgman,
)
from domain.geometry import Point


# --- point clipping ---------------------------------------------------------


def test_point_inside_is_kept():
    assert clip_point(Point(0.0, 0.0)) == Point(0.0, 0.0)


def test_point_on_border_is_kept():
    assert clip_point(Point(1.0, -1.0)) == Point(1.0, -1.0)


def test_point_outside_is_dropped():
    assert clip_point(Point(1.5, 0.0)) is None
    assert clip_point(Point(0.0, -2.0)) is None


# --- line clipping: both techniques must agree ------------------------------

# (start, end) -> expected clipped (start, end) or None. Coordinates chosen so
# every intersection is exact in floating point.
_LINE_CASES = [
    # fully inside: unchanged
    ((-0.5, -0.5), (0.5, 0.5), ((-0.5, -0.5), (0.5, 0.5))),
    # fully outside, same side: rejected
    ((2.0, 0.0), (3.0, 0.0), None),
    ((0.0, 2.0), (0.0, 3.0), None),
    # crosses the right edge: trimmed at x = 1
    ((0.0, 0.0), (2.0, 0.0), ((0.0, 0.0), (1.0, 0.0))),
    # crosses the left edge: trimmed at x = -1
    ((0.0, 0.0), (-2.0, 0.0), ((0.0, 0.0), (-1.0, 0.0))),
    # spans the whole window horizontally: both ends clipped to the borders
    ((-2.0, 0.5), (2.0, 0.5), ((-1.0, 0.5), (1.0, 0.5))),
    # diagonal exiting through the top-right corner region
    ((0.0, 0.0), (2.0, 2.0), ((0.0, 0.0), (1.0, 1.0))),
    # both endpoints outside but the segment crosses the window (the case that
    # breaks a naive endpoint-only test)
    ((-2.0, 0.0), (2.0, 0.0), ((-1.0, 0.0), (1.0, 0.0))),
    # both endpoints outside on opposite corners; the diagonal still crosses the
    # window and is trimmed to the two border crossings
    ((-2.0, 1.5), (1.5, -2.0), ((-1.0, 0.5), (0.5, -1.0))),
    # outside diagonal that stays past a corner and never enters: rejected
    ((-2.0, 1.5), (1.5, 2.0), None),
]


def _normalize(result):
    if result is None:
        return None
    (ax, ay), (bx, by) = result[0], result[1]
    return ((ax, ay), (bx, by))


@pytest.mark.parametrize("start, end, expected", _LINE_CASES)
def test_cohen_sutherland_cases(start, end, expected):
    got = cohen_sutherland(Point(*start), Point(*end))
    assert _tuple(got) == expected


@pytest.mark.parametrize("start, end, expected", _LINE_CASES)
def test_liang_barsky_cases(start, end, expected):
    got = liang_barsky(Point(*start), Point(*end))
    assert _tuple(got) == expected


def _tuple(result):
    if result is None:
        return None
    return ((result[0][0], result[0][1]), (result[1][0], result[1][1]))


def test_both_line_clippers_agree_on_many_segments():
    # Cross-check the two implementations on a grid of segments: for the spec's
    # "swappable" requirement to be meaningful, they must produce the same clip.
    coords = [-2.0, -1.0, -0.3, 0.4, 1.0, 2.0]
    for x0 in coords:
        for y0 in coords:
            for x1 in coords:
                for y1 in coords:
                    a, b = Point(x0, y0), Point(x1, y1)
                    cs = cohen_sutherland(a, b)
                    lb = liang_barsky(a, b)
                    assert (cs is None) == (lb is None)
                    if cs is not None:
                        for got, want in zip(_flatten(cs), _flatten(lb)):
                            assert math.isclose(got, want, abs_tol=1e-9)


def _flatten(segment):
    return [segment[0][0], segment[0][1], segment[1][0], segment[1][1]]


def test_clip_line_selects_technique():
    a, b = Point(0.0, 0.0), Point(2.0, 0.0)
    assert clip_line(a, b, LineClipper.COHEN_SUTHERLAND) == cohen_sutherland(a, b)
    assert clip_line(a, b, LineClipper.LIANG_BARSKY) == liang_barsky(a, b)


# --- polygon clipping (Sutherland-Hodgman) ----------------------------------


def test_polygon_fully_inside_is_unchanged():
    square = [Point(-0.5, -0.5), Point(0.5, -0.5), Point(0.5, 0.5), Point(-0.5, 0.5)]
    assert sutherland_hodgman(square) == square


def test_polygon_fully_outside_is_empty():
    triangle = [Point(2.0, 2.0), Point(3.0, 2.0), Point(2.5, 3.0)]
    assert sutherland_hodgman(triangle) == []


def test_polygon_straddling_right_edge_is_trimmed_to_the_border():
    # A square from x=0 to x=2 clipped to the window keeps x in [0, 1]; the two
    # vertices past x=1 become border crossings at x=1.
    square = [Point(0.0, -0.5), Point(2.0, -0.5), Point(2.0, 0.5), Point(0.0, 0.5)]
    clipped = sutherland_hodgman(square)
    xs = [p[0] for p in clipped]
    ys = [p[1] for p in clipped]
    assert max(xs) == pytest.approx(1.0)
    assert min(xs) == pytest.approx(0.0)
    assert min(ys) == pytest.approx(-0.5)
    assert max(ys) == pytest.approx(0.5)


def test_polygon_larger_than_window_becomes_the_window():
    # A big square around the window clips down to exactly the [-1, 1] square.
    big = [Point(-3.0, -3.0), Point(3.0, -3.0), Point(3.0, 3.0), Point(-3.0, 3.0)]
    clipped = sutherland_hodgman(big)
    corners = {(round(p[0], 6), round(p[1], 6)) for p in clipped}
    assert corners == {(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)}
