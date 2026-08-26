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
