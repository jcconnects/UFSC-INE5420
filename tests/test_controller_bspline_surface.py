"""The controller's B-Spline surfaces (trabalho 1.10), end to end through the pipeline.

Covers the spec's requirements: a control matrix of 4x4 up to 20x20 typed with
its rows split by ";", split into 4x4 sub-matrices by the SGI itself, drawn in
3D (parallel or perspective) and clipped in 2D like everything else.
"""

import pytest

from app.controller import Controller
from app.render_pipeline import DrawLine
from domain.geometry import Point
from domain.objects import BSplineSurface, ObjectType
from domain.projection import PerspectiveProjection

# The Bézier tests' bump: dataset 1 of the class exercise, scaled by 0.2 and
# centered -- a control net over -30..30 whose four inner points rise to z = 20.
_BUMP = (
    "(-30,-30,0),(-30,-10,0),(-30,10,0),(-30,30,0);"
    "(-10,-30,0),(-10,-10,20),(-10,10,20),(-10,30,0);"
    "(10,-30,0),(10,-10,20),(10,10,20),(10,30,0);"
    "(30,-30,0),(30,-10,0),(30,10,0),(30,30,0)"
)

_N = BSplineSurface.STEPS_PER_PATCH
# One patch's mesh: n+1 curves per parameter, n segments each.
_MESH_LINES = 2 * _N * (_N + 1)


def _endpoints(commands):
    return [point for c in commands for point in ((c.x1, c.y1), (c.x2, c.y2))]


def _extent(commands):
    xs, ys = zip(*_endpoints(commands))
    return min(xs), max(xs), min(ys), max(ys)


def _bump() -> Controller:
    controller = Controller()
    controller.add_object("bump", ObjectType.BSPLINE_SURFACE, _BUMP)
    return controller


def test_surface_typed_in_the_spec_format_renders_as_lines():
    controller = _bump()
    [surface] = controller.display_file
    assert surface.type is ObjectType.BSPLINE_SURFACE and len(surface.patches) == 1
    commands = controller.render(200, 200)
    assert len(commands) == _MESH_LINES
    assert all(isinstance(command, DrawLine) for command in commands)


def test_the_surface_does_not_interpolate_its_control_net():
    # Its border runs at (P1 + 4 P2 + P3) / 6 = (-30 - 40 + 10) / 6 = -10, so
    # head-on, 1 px per world unit, the patch spans pixels 90..110 -- where
    # the Bézier patch over the same net reaches its corners, 70..130.
    assert _extent(_bump().render(200, 200)) == pytest.approx((90, 110, 90, 110))


def test_a_larger_matrix_is_split_into_submatrices_by_itself():
    # 4 planar rows of 6 points: z = 0, and (4-3)(6-3) = 3 patches.
    rows = ";".join(",".join(f"({10 * x},{10 * y})" for y in range(6)) for x in range(4))
    surface = Controller().add_object("strip", ObjectType.BSPLINE_SURFACE, rows)
    assert surface.control_net[3][5] == Point(30, 50, 0)
    assert len(surface.patches) == 3
    assert len(surface.to_segments()) == 3 * _MESH_LINES


def test_surface_crossing_the_border_is_clipped_in_2d():
    controller = _bump()
    controller.pan(95, 0)  # the window's left edge, x = -5, now cuts the patch
    left, top, right, bottom = controller.subcanvas_rect(200, 200)
    commands = controller.render(200, 200)
    assert 0 < len(commands) < _MESH_LINES
    for x, y in _endpoints(commands):
        assert left - 1e-6 <= x <= right + 1e-6 and top - 1e-6 <= y <= bottom + 1e-6
    # Lines crossing the border are cut at it, not just dropped.
    assert any(abs(x - left) < 1e-6 for x, _ in _endpoints(commands))


def test_surface_renders_in_perspective():
    controller = _bump()
    parallel = controller.render(200, 200)
    controller.set_projection(PerspectiveProjection(200))
    perspective = controller.render(200, 200)
    assert len(perspective) == _MESH_LINES
    assert all(isinstance(command, DrawLine) for command in perspective)
    # Unlike the Bézier patch, no border lies on the view plane: the whole
    # patch floats at z > 0, nearer the COP, so it is drawn larger.
    left, right, top, bottom = _extent(parallel)
    p_left, p_right, p_top, p_bottom = _extent(perspective)
    assert p_left < left and p_right > right and p_top < top and p_bottom > bottom
