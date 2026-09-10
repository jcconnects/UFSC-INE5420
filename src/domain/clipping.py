"""Clipping stage: trim geometry to the normalized window before the viewport.

Clipping runs in SCN space (see `domain.normalization`), so the clip region is
always the fixed normalized square [-1, 1] x [-1, 1]. The viewport transform
then receives *only* what survived the clip -- exactly the spec's requirement
that "a transformada de viewport seja aplicada apenas aos objetos resultantes do
clipping". The subcanvas border the GUI draws is that same [-1, 1] box in pixels,
so anything clipped here visibly disappears at the border.

Everything is a pure function operating on `Point`s; no Qt, no pixels.

Three techniques, matching the spec's three clipping cases:
  - point clipping                          -> `clip_point`
  - line clipping, two selectable methods   -> `cohen_sutherland`, `liang_barsky`
  - polygon clipping                        -> `sutherland_hodgman`

The line clippers are interchangeable behind `LineClipper`; the GUI exposes the
choice as a radio button and the pipeline picks the function by that enum.
"""

from __future__ import annotations

from enum import Enum

from .geometry import Point

# The normalized clip window, in SCN coordinates. Clipping is a 2D viewing-plane
# operation, so it reads x/y directly; a projected 3D point arrives here already
# flattened to the plane.
_X_MIN, _Y_MIN, _X_MAX, _Y_MAX = -1.0, -1.0, 1.0, 1.0

Segment = tuple[Point, Point]


class LineClipper(Enum):
    """Selectable line-clipping technique (spec: two, swappable by radio button)."""

    COHEN_SUTHERLAND = "Cohen-Sutherland"
    LIANG_BARSKY = "Liang-Barsky"


def clip_point(point: Point) -> Point | None:
    """Return the point if it lies inside the clip window, else None.

    A point is kept only when it is within the window on every axis (inclusive
    of the border).
    """
    x, y = point[0], point[1]
    if _X_MIN <= x <= _X_MAX and _Y_MIN <= y <= _Y_MAX:
        return point
    return None


# --- Cohen-Sutherland -------------------------------------------------------

# Region outcode bits.
_INSIDE = 0b0000
_LEFT = 0b0001
_RIGHT = 0b0010
_BOTTOM = 0b0100
_TOP = 0b1000


def _outcode(x: float, y: float) -> int:
    """Cohen-Sutherland region code for a point against the clip window."""
    code = _INSIDE
    if x < _X_MIN:
        code |= _LEFT
    elif x > _X_MAX:
        code |= _RIGHT
    if y < _Y_MIN:
        code |= _BOTTOM
    elif y > _Y_MAX:
        code |= _TOP
    return code


def cohen_sutherland(start: Point, end: Point) -> Segment | None:
    """Clip a segment with the Cohen-Sutherland algorithm.

    Returns the trimmed segment, or None if it lies entirely outside the window.
    Trivially accepts when both endpoints are inside, trivially rejects when both
    share an outside region, and otherwise pushes the outside endpoint to the
    border it crosses, iterating until accept or reject.
    """
    x0, y0 = start[0], start[1]
    x1, y1 = end[0], end[1]
    code0 = _outcode(x0, y0)
    code1 = _outcode(x1, y1)

    while True:
        if not (code0 | code1):  # both inside -> accept
            return (Point(x0, y0), Point(x1, y1))
        if code0 & code1:  # share an outside region -> reject
            return None

        # Pick an endpoint that is outside and move it to the crossed border.
        outside = code0 or code1
        if outside & _TOP:
            x = x0 + (x1 - x0) * (_Y_MAX - y0) / (y1 - y0)
            y = _Y_MAX
        elif outside & _BOTTOM:
            x = x0 + (x1 - x0) * (_Y_MIN - y0) / (y1 - y0)
            y = _Y_MIN
        elif outside & _RIGHT:
            y = y0 + (y1 - y0) * (_X_MAX - x0) / (x1 - x0)
            x = _X_MAX
        else:  # _LEFT
            y = y0 + (y1 - y0) * (_X_MIN - x0) / (x1 - x0)
            x = _X_MIN

        if outside == code0:
            x0, y0 = x, y
            code0 = _outcode(x0, y0)
        else:
            x1, y1 = x, y
            code1 = _outcode(x1, y1)


# --- Liang-Barsky -----------------------------------------------------------


def liang_barsky(start: Point, end: Point) -> Segment | None:
    """Clip a segment with the parametric Liang-Barsky algorithm.

    Walks the four boundaries as p/q pairs, narrowing the parameter interval
    [t0, t1] along the segment. Returns the trimmed segment, or None if the
    interval collapses (the segment misses the window).
    """
    x0, y0 = start[0], start[1]
    x1, y1 = end[0], end[1]
    dx = x1 - x0
    dy = y1 - y0

    # p_k < 0: entering the window on boundary k; p_k > 0: leaving it.
    p = (-dx, dx, -dy, dy)
    q = (x0 - _X_MIN, _X_MAX - x0, y0 - _Y_MIN, _Y_MAX - y0)

    t0, t1 = 0.0, 1.0
    for pk, qk in zip(p, q):
        if pk == 0:
            if qk < 0:  # parallel to this edge and outside it -> reject
                return None
            continue  # parallel but inside: this edge cannot clip
        t = qk / pk
        if pk < 0:  # entering: pull t0 forward
            if t > t1:
                return None
            t0 = max(t0, t)
        else:  # leaving: pull t1 back
            if t < t0:
                return None
            t1 = min(t1, t)

    clipped_start = Point(x0 + t0 * dx, y0 + t0 * dy)
    clipped_end = Point(x0 + t1 * dx, y0 + t1 * dy)
    return (clipped_start, clipped_end)


# --- Sutherland-Hodgman (polygon) -------------------------------------------

# Each clip edge as (predicate "is this point inside the edge?", intersector).
# Kept as data so the clip loop stays one small pass over the four borders.
_EDGES = (
    (lambda x, y: x >= _X_MIN, _X_MIN, "x"),  # left
    (lambda x, y: x <= _X_MAX, _X_MAX, "x"),  # right
    (lambda x, y: y >= _Y_MIN, _Y_MIN, "y"),  # bottom
    (lambda x, y: y <= _Y_MAX, _Y_MAX, "y"),  # top
)


def _intersect(ax: float, ay: float, bx: float, by: float, bound: float, axis: str) -> Point:
    """Point where segment a->b crosses a vertical/horizontal clip boundary."""
    if axis == "x":
        t = (bound - ax) / (bx - ax)
        return Point(bound, ay + t * (by - ay))
    t = (bound - ay) / (by - ay)
    return Point(ax + t * (bx - ax), bound)


def sutherland_hodgman(vertices: list[Point]) -> list[Point]:
    """Clip a polygon against the window with the Sutherland-Hodgman algorithm.

    Takes the polygon's vertices (the border is implicitly closed: last connects
    to first) and returns the clipped polygon's vertices, or an empty list if the
    polygon falls entirely outside. Clips against each of the four window edges
    in turn, feeding each pass's output to the next.
    """
    output = list(vertices)
    for inside, bound, axis in _EDGES:
        if not output:
            break
        input_list = output
        output = []
        previous = input_list[-1]
        prev_inside = inside(previous[0], previous[1])
        for current in input_list:
            curr_inside = inside(current[0], current[1])
            if curr_inside:
                if not prev_inside:  # entering: add the crossing then the point
                    output.append(
                        _intersect(previous[0], previous[1], current[0], current[1], bound, axis)
                    )
                output.append(current)
            elif prev_inside:  # leaving: add only the crossing
                output.append(
                    _intersect(previous[0], previous[1], current[0], current[1], bound, axis)
                )
            previous = current
            prev_inside = curr_inside
    return output


def clip_line(start: Point, end: Point, method: LineClipper) -> Segment | None:
    """Clip a segment with the selected technique."""
    if method is LineClipper.LIANG_BARSKY:
        return liang_barsky(start, end)
    return cohen_sutherland(start, end)
