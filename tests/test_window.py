"""Window navigation: rotation and up-vector-aware panning (trabalho 1.3)."""

import math

from domain.window import Window


def test_rotate_accumulates():
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(30))
    window.rotate(math.radians(15))
    assert math.isclose(window.angle, math.radians(45))


def test_basis_vectors_at_zero_angle():
    window = Window(-10, -10, 10, 10)
    assert window.right_vector() == (1.0, 0.0)
    ux, uy = window.up_vector()
    assert math.isclose(ux, 0.0, abs_tol=1e-12)
    assert math.isclose(uy, 1.0)


def test_pan_up_at_zero_angle_moves_world_up():
    window = Window(-10, -10, 10, 10)
    window.pan(0, 5)  # dv=5 along up
    assert window.center == (0.0, 5.0)


def test_pan_up_when_rotated_90_moves_along_world_x():
    # At +90 degrees the window's "up" points along world -x... actually +x?
    # up_vector at 90 deg = (-sin90, cos90) = (-1, 0): up points to world -x.
    window = Window(-10, -10, 10, 10, angle=math.radians(90))
    window.pan(0, 5)  # move 5 along the window's up axis
    cx, cy = window.center
    assert math.isclose(cx, -5.0, abs_tol=1e-9)
    assert math.isclose(cy, 0.0, abs_tol=1e-9)


def test_pan_right_when_rotated_90_moves_along_world_y():
    # right_vector at 90 deg = (cos90, sin90) = (0, 1): right points to world +y.
    window = Window(-10, -10, 10, 10, angle=math.radians(90))
    window.pan(5, 0)  # move 5 along the window's right axis
    cx, cy = window.center
    assert math.isclose(cx, 0.0, abs_tol=1e-9)
    assert math.isclose(cy, 5.0, abs_tol=1e-9)


def test_zoom_unaffected_by_rotation():
    window = Window(-10, -10, 10, 10, angle=math.radians(37))
    window.zoom(2.0)
    assert window.width == 40.0
    assert window.height == 40.0
    assert window.center == (0.0, 0.0)
