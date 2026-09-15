"""The clip stage inside the render pipeline (trabalho 1.4).

Confirms the pipeline clips in SCN space before the viewport: objects wholly
outside the window produce no draw commands, filled wireframes become a
DrawPolygon, and unfilled ones stay DrawLines. Uses a window matching the
normalized square so world coordinates equal SCN coordinates and the arithmetic
stays obvious.
"""

from app.render_pipeline import DrawLine, DrawPoint, DrawPolygon, render
from domain.clipping import LineClipper
from domain.display_file import DisplayFile
from domain.geometry import Point
from domain.objects import Curve2D, Line, Point2D, Wireframe
from domain.viewport import ViewportTransform
from domain.window import Window


def _world():
    # Window centered at origin with extent 2 on each axis -> SCN == world.
    return Window(-1, -1, 1, 1)


def _viewport():
    return ViewportTransform(200, 200)


def test_point_outside_window_is_not_drawn():
    df = DisplayFile()
    df.add(Point2D("p", Point(5.0, 5.0)))
    assert render(df, _world(), _viewport()) == []


def test_point_inside_window_is_drawn():
    df = DisplayFile()
    df.add(Point2D("p", Point(0.0, 0.0)))
    commands = render(df, _world(), _viewport())
    assert len(commands) == 1
    assert isinstance(commands[0], DrawPoint)


def test_line_crossing_border_is_clipped():
    df = DisplayFile()
    df.add(Line("l", Point(0.0, 0.0), Point(5.0, 0.0)))
    commands = render(df, _world(), _viewport())
    assert len(commands) == 1
    line = commands[0]
    assert isinstance(line, DrawLine)
    # The far endpoint (world x=5) is clipped to x=1 (SCN), which maps to the
    # right edge of the 200px viewport.
    assert line.x2 == 200.0


def test_line_fully_outside_produces_nothing():
    df = DisplayFile()
    df.add(Line("l", Point(3.0, 3.0), Point(4.0, 4.0)))
    assert render(df, _world(), _viewport()) == []


def test_filled_wireframe_emits_a_polygon_command():
    df = DisplayFile()
    square = [Point(-0.5, -0.5), Point(0.5, -0.5), Point(0.5, 0.5), Point(-0.5, 0.5)]
    df.add(Wireframe("poly", square, filled=True))
    commands = render(df, _world(), _viewport())
    assert len(commands) == 1
    assert isinstance(commands[0], DrawPolygon)
    assert len(commands[0].points) == 4


def test_unfilled_wireframe_stays_lines():
    df = DisplayFile()
    square = [Point(-0.5, -0.5), Point(0.5, -0.5), Point(0.5, 0.5), Point(-0.5, 0.5)]
    df.add(Wireframe("poly", square, filled=False))
    commands = render(df, _world(), _viewport())
    assert commands  # non-empty
    assert all(isinstance(c, DrawLine) for c in commands)


def test_filled_polygon_outside_window_is_dropped():
    df = DisplayFile()
    square = [Point(5.0, 5.0), Point(6.0, 5.0), Point(6.0, 6.0), Point(5.0, 6.0)]
    df.add(Wireframe("poly", square, filled=True))
    assert render(df, _world(), _viewport()) == []


def test_selected_line_clipper_is_passed_through():
    df = DisplayFile()
    df.add(Line("l", Point(0.0, 0.0), Point(5.0, 0.0)))
    # Both techniques must clip this segment identically.
    cs = render(df, _world(), _viewport(), LineClipper.COHEN_SUTHERLAND)
    lb = render(df, _world(), _viewport(), LineClipper.LIANG_BARSKY)
    assert cs == lb


# --- Curve clipping (trabalho 1.5): point-clip the generated points ---------


def test_curve_fully_inside_draws_as_lines():
    df = DisplayFile()
    # All control points inside [-1, 1]; the whole curve stays inside.
    controls = [Point(-0.5, 0.0), Point(-0.2, 0.5), Point(0.2, 0.5), Point(0.5, 0.0)]
    df.add(Curve2D("c", controls))
    commands = render(df, _world(), _viewport())
    assert commands
    assert all(isinstance(c, DrawLine) for c in commands)
    # A curve inside is drawn as its full polyline: STEPS_PER_SEGMENT spans.
    assert len(commands) == Curve2D.STEPS_PER_SEGMENT


def test_curve_fully_outside_produces_nothing():
    df = DisplayFile()
    controls = [Point(5.0, 5.0), Point(6.0, 6.0), Point(7.0, 6.0), Point(8.0, 5.0)]
    df.add(Curve2D("c", controls))
    assert render(df, _world(), _viewport()) == []


def test_curve_crossing_border_is_partially_clipped():
    df = DisplayFile()
    # Curve running left (inside) to far right (outside): some generated points
    # are in the window, some out, so only the in-window spans are drawn.
    controls = [Point(0.0, 0.0), Point(1.0, 0.0), Point(2.0, 0.0), Point(5.0, 0.0)]
    df.add(Curve2D("c", controls))
    commands = render(df, _world(), _viewport())
    assert commands  # part of the curve is visible
    # Clipped: fewer spans than a fully-inside curve, and every drawn endpoint
    # lies within the 200px viewport (nothing leaks past the border).
    assert len(commands) < Curve2D.STEPS_PER_SEGMENT
    for line in commands:
        assert isinstance(line, DrawLine)
        assert 0.0 <= line.x1 <= 200.0 and 0.0 <= line.x2 <= 200.0
