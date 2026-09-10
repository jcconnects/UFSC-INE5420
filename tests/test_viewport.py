"""Viewport transform: SCN square -> pixels, and the no-distortion requirement.

Since trabalho 1.3 the viewport maps the fixed normalized square [-1, 1]^2, not
the window directly. Inputs here are SCN points.
"""

from domain.geometry import Point
from domain.viewport import ViewportTransform


def test_scn_corners_map_to_viewport_when_square():
    vt = ViewportTransform(200, 200)
    # bottom-left SCN corner -> bottom-left screen (y inverted)
    assert vt.apply(Point(-1, -1)) == (0.0, 200.0)
    # top-right SCN corner -> top-right screen
    assert vt.apply(Point(1, 1)) == (200.0, 0.0)


def test_scn_origin_maps_to_center():
    vt = ViewportTransform(200, 200)
    assert vt.apply(Point(0, 0)) == (100.0, 100.0)


def test_no_distortion_a_square_stays_square():
    # The SCN square mapped into a wide viewport must not stretch: equal SCN
    # extents must produce equal pixel extents on both axes.
    vt = ViewportTransform(400, 200)  # 2:1 viewport
    bottom_left = vt.apply(Point(-1, -1))
    top_right = vt.apply(Point(1, 1))
    width_px = abs(top_right[0] - bottom_left[0])
    height_px = abs(top_right[1] - bottom_left[1])
    assert width_px == height_px  # isotropic fit, no stretch


def test_wide_viewport_centers_with_horizontal_margins():
    # A 400x200 viewport fits the square to 200px and centers it: 100px margins.
    vt = ViewportTransform(400, 200)
    assert vt.apply(Point(-1, -1)) == (100.0, 200.0)
    assert vt.apply(Point(1, 1)) == (300.0, 0.0)


def test_subcanvas_margin_insets_the_square():
    # 240x240 widget with a 20px margin -> the SCN square fits a 200px subcanvas
    # centered in the widget: corners at 20 and 220.
    vt = ViewportTransform(240, 240, margin=20)
    assert vt.subcanvas_rect() == (20.0, 20.0, 220.0, 220.0)
    assert vt.apply(Point(-1, -1)) == (20.0, 220.0)
    assert vt.apply(Point(1, 1)) == (220.0, 20.0)
    assert vt.apply(Point(0, 0)) == (120.0, 120.0)


def test_points_outside_window_land_in_the_margin():
    # A normalized coordinate beyond +1 must map beyond the subcanvas edge but
    # can still fall inside the widget -- that is the margin where unclipped
    # geometry shows. At x=1.1 the pixel is past the 220 subcanvas edge.
    vt = ViewportTransform(240, 240, margin=20)
    px, _ = vt.apply(Point(1.1, 0))
    assert px > 220.0  # outside the subcanvas
    assert px < 240.0  # still inside the widget -> visible in the margin


def test_no_distortion_with_margin_on_wide_viewport():
    vt = ViewportTransform(400, 200, margin=20)
    bottom_left = vt.apply(Point(-1, -1))
    top_right = vt.apply(Point(1, 1))
    width_px = abs(top_right[0] - bottom_left[0])
    height_px = abs(top_right[1] - bottom_left[1])
    assert width_px == height_px
