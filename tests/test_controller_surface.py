"""The controller's Bézier surfaces (trabalho 1.9), end to end through the pipeline.

Covers the spec's requirements: a surface typed 16 control points at a time,
matrix rows split by ";", drawn in 3D (parallel or perspective) and clipped in
2D like everything else.
"""

import pytest

from app.controller import Controller
from app.render_pipeline import DrawLine
from domain.geometry import Point
from domain.objects import BezierSurface, ObjectType
from domain.projection import PerspectiveProjection

# Dataset 1 of "Plotagem de Superfície Bézier Bicúbica", scaled by 0.2 and
# centered: a 60 x 60 patch on z = 0 whose four inner points rise to z = 20.
_BUMP = (
    "(-30,-30,0),(-30,-10,0),(-30,10,0),(-30,30,0);"
    "(-10,-30,0),(-10,-10,20),(-10,10,20),(-10,30,0);"
    "(10,-30,0),(10,-10,20),(10,10,20),(10,30,0);"
    "(30,-30,0),(30,-10,0),(30,10,0),(30,30,0)"
)

_N = BezierSurface.STEPS_PER_PATCH
# One patch's mesh: n+1 grid rows and n+1 grid columns of n segments each.
_MESH_LINES = 2 * _N * (_N + 1)


def _endpoints(commands):
    return [point for c in commands for point in ((c.x1, c.y1), (c.x2, c.y2))]


def _extent(commands):
    xs, ys = zip(*_endpoints(commands))
    return min(xs), max(xs), min(ys), max(ys)


def _bump() -> Controller:
    controller = Controller()
    controller.add_object("bump", ObjectType.SURFACE, _BUMP)
    return controller


def test_surface_typed_in_the_spec_format_renders_as_lines():
    controller = _bump()
    [surface] = controller.display_file
    assert surface.type is ObjectType.SURFACE and len(surface.patches) == 1
    commands = controller.render(200, 200)
    assert len(commands) == _MESH_LINES
    assert all(isinstance(command, DrawLine) for command in commands)
    # Head-on, 1 px per world unit: the 60 x 60 patch spans pixels 70..130.
    assert _extent(commands) == pytest.approx((70, 130, 70, 130))


def test_planar_rows_are_lifted_to_z0():
    rows = ";".join(",".join(f"({x},{y})" for y in range(4)) for x in range(4))
    surface = Controller().add_object("flat", ObjectType.SURFACE, rows)
    assert surface.patches[0][3][3] == Point(3, 3, 0)


def test_surface_crossing_the_border_is_clipped_in_2d():
    controller = _bump()
    controller.pan(90, 0)  # the window's left edge, x = -10, now cuts the patch
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
    # The patch's edges lie on the view plane (z = 0) and stay put; the bump,
    # nearer the COP, is drawn larger, so the inner mesh moves.
    assert _extent(perspective) == pytest.approx(_extent(parallel))
    assert perspective != parallel
