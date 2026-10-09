"""Window navigation: up-aware panning (trabalho 1.3) and 3D navigation (1.7).

Since 1.7 the window is a view plane in space (VRP, VPN, VUP), so positions and
basis vectors are 3D. The default window lies on z = 0 facing +z, so the 1.3
scenarios keep their meaning with a zero z component.
"""

import math
import random

from domain.geometry import cross, dot
from domain.window import Window, WindowAxis


def _close(actual, expected, tol: float = 1e-9) -> bool:
    return all(math.isclose(a, e, abs_tol=tol) for a, e in zip(actual, expected, strict=True))


# --- trabalho 1.3 behaviour on the default (z = 0) window --------------------


def test_rotate_accumulates():
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(30))
    window.rotate(math.radians(15))
    # Two rolls add up: the up vector sits 45 degrees counter-clockwise.
    angle = math.radians(45)
    assert _close(window.up_vector(), (-math.sin(angle), math.cos(angle), 0.0))


def test_basis_vectors_at_zero_angle():
    window = Window(-10, -10, 10, 10)
    assert _close(window.right_vector(), (1.0, 0.0, 0.0))
    assert _close(window.up_vector(), (0.0, 1.0, 0.0))
    assert _close(window.vpn, (0.0, 0.0, 1.0))


def test_pan_up_at_zero_angle_moves_world_up():
    window = Window(-10, -10, 10, 10)
    window.pan(0, 5)  # dv=5 along up
    assert _close(window.vrp, (0.0, 5.0, 0.0))


def test_pan_up_when_rotated_90_moves_along_world_x():
    # up_vector at 90 deg = (-sin90, cos90, 0) = (-1, 0, 0): up points to world -x.
    window = Window(-10, -10, 10, 10, angle=math.radians(90))
    window.pan(0, 5)  # move 5 along the window's up axis
    assert _close(window.vrp, (-5.0, 0.0, 0.0))


def test_pan_right_when_rotated_90_moves_along_world_y():
    # right_vector at 90 deg = (cos90, sin90, 0) = (0, 1, 0): right points to world +y.
    window = Window(-10, -10, 10, 10, angle=math.radians(90))
    window.pan(5, 0)  # move 5 along the window's right axis
    assert _close(window.vrp, (0.0, 5.0, 0.0))


def test_zoom_unaffected_by_rotation():
    window = Window(-10, -10, 10, 10, angle=math.radians(37))
    window.zoom(2.0)
    assert window.width == 40.0
    assert window.height == 40.0
    assert _close(window.vrp, (0.0, 0.0, 0.0))


# --- trabalho 1.7: navigation in 3D space ------------------------------------


def test_bounds_set_vrp_at_the_window_center():
    window = Window(0, 0, 100, 50)
    assert _close(window.vrp, (50.0, 25.0, 0.0))
    assert (window.width, window.height) == (100, 50)


def test_roll_keeps_the_vpn():
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(70), WindowAxis.ROLL)
    assert _close(window.vpn, (0.0, 0.0, 1.0))


def test_yaw_turns_the_vpn_about_the_up_vector():
    # Yaw +90 about up (+y): the VPN swings from +z to +x; up is unchanged.
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(90), WindowAxis.YAW)
    assert _close(window.vpn, (1.0, 0.0, 0.0))
    assert _close(window.vup, (0.0, 1.0, 0.0))
    assert _close(window.right_vector(), (0.0, 0.0, -1.0))


def test_pitch_turns_the_vpn_about_the_right_vector():
    # Pitch +90 about right (+x): the VPN goes from +z to -y and up becomes +z.
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(90), WindowAxis.PITCH)
    assert _close(window.vpn, (0.0, -1.0, 0.0))
    assert _close(window.vup, (0.0, 0.0, 1.0))
    assert _close(window.right_vector(), (1.0, 0.0, 0.0))


def test_pan_moves_the_vrp_in_3d_after_a_yaw():
    # After yaw 90 the window's right vector is world -z, so panning right
    # moves the VRP off the z = 0 plane.
    window = Window(-10, -10, 10, 10)
    window.rotate(math.radians(90), WindowAxis.YAW)
    window.pan(5, 0)
    assert _close(window.vrp, (0.0, 0.0, -5.0))


def test_orientation_stays_orthonormal_after_many_rotations():
    rng = random.Random(1)
    window = Window(-10, -10, 10, 10)
    for _ in range(2000):
        window.rotate(rng.uniform(-math.pi, math.pi), rng.choice(list(WindowAxis)))
    assert math.isclose(dot(window.vpn, window.vpn), 1.0, abs_tol=1e-12)
    assert math.isclose(dot(window.vup, window.vup), 1.0, abs_tol=1e-12)
    assert math.isclose(dot(window.vpn, window.vup), 0.0, abs_tol=1e-12)
    # right, up and VPN stay a right-handed frame: right x up = VPN.
    assert _close(cross(window.right_vector(), window.vup), window.vpn, tol=1e-12)
