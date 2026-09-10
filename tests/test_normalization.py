"""World -> SCN view transform (trabalho 1.3)."""

import math

from domain.geometry import Point
from domain.normalization import to_scn
from domain.window import Window


def _close(p: Point, x: float, y: float, tol: float = 1e-9) -> bool:
    return math.isclose(p[0], x, abs_tol=tol) and math.isclose(p[1], y, abs_tol=tol)


def test_center_maps_to_origin():
    window = Window(-100, -100, 100, 100)
    assert _close(to_scn(Point(0, 0), window), 0.0, 0.0)


def test_corners_map_to_unit_square():
    window = Window(-100, -100, 100, 100)
    assert _close(to_scn(Point(100, 100), window), 1.0, 1.0)
    assert _close(to_scn(Point(-100, -100), window), -1.0, -1.0)


def test_offcenter_window_recenters():
    # A window centered at (50, 50): its center is the SCN origin.
    window = Window(0, 0, 100, 100)
    assert _close(to_scn(Point(50, 50), window), 0.0, 0.0)
    assert _close(to_scn(Point(100, 100), window), 1.0, 1.0)


def test_point_on_window_up_axis_maps_to_scn_plus_y():
    # Rotate the window +90 deg. Its up axis now points along world -x
    # (up_vector = (-1, 0)). A world point one half-extent up that axis, i.e.
    # at (-100, 0), must land on SCN +y = (0, 1).
    window = Window(-100, -100, 100, 100, angle=math.radians(90))
    assert _close(to_scn(Point(-100, 0), window), 0.0, 1.0)


def test_window_rotation_counter_rotates_the_world():
    # A fixed world point on +x. With the window rotated +90 deg, undoing the
    # orientation (-90) sends it to -y in SCN: the scene counter-rotates.
    window = Window(-100, -100, 100, 100, angle=math.radians(90))
    assert _close(to_scn(Point(100, 0), window), 0.0, -1.0)
