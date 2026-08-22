"""Viewport transform: correctness and the no-distortion requirement."""

from domain.geometry import Point
from domain.viewport import ViewportTransform
from domain.window import Window


def test_corners_map_to_viewport_when_aspect_matches():
    window = Window(0, 0, 100, 100)
    vt = ViewportTransform(window, 200, 200)
    # bottom-left world corner -> bottom-left screen (y inverted)
    assert vt.apply(Point(0, 0)) == (0.0, 200.0)
    # top-right world corner -> top-right screen
    assert vt.apply(Point(100, 100)) == (200.0, 0.0)


def test_center_maps_to_center():
    window = Window(0, 0, 100, 100)
    vt = ViewportTransform(window, 200, 200)
    assert vt.apply(Point(50, 50)) == (100.0, 100.0)


def test_no_distortion_a_square_stays_square():
    # A square window mapped into a wide viewport must not stretch: equal
    # world extents must produce equal pixel extents on both axes.
    window = Window(0, 0, 10, 10)
    vt = ViewportTransform(window, 400, 200)  # 2:1 viewport
    bottom_left = vt.apply(Point(0, 0))
    top_right = vt.apply(Point(10, 10))
    width_px = abs(top_right[0] - bottom_left[0])
    height_px = abs(top_right[1] - bottom_left[1])
    assert width_px == height_px  # isotropic fit, no stretch
