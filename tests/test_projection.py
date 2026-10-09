"""Parallel orthogonal projection through the 3D window (trabalho 1.7).

The angle-based algorithm (translate the VRP, rotate about x and y until the
VPN is z, rotate about z until the VUP is y, drop z, normalize) is checked
against its geometric meaning: a point's SCN coordinates are its offsets from
the VRP along the window's right and up vectors, over the half extents.
"""

import math
import random

from domain.geometry import Point, dot, transform_point
from domain.normalization import to_scn
from domain.projection import parallel_orthogonal, view_matrix
from domain.window import Window, WindowAxis


def _close(actual, expected, tol: float = 1e-9) -> bool:
    return all(math.isclose(a, e, abs_tol=tol) for a, e in zip(actual, expected, strict=True))


def _navigated_window(seed: int) -> Window:
    """A window after a random sequence of 3D navigation operations."""
    rng = random.Random(seed)
    window = Window(-100, -80, 100, 80)
    for _ in range(25):
        operation = rng.choice(("rotate", "pan", "zoom"))
        if operation == "rotate":
            window.rotate(rng.uniform(-math.pi, math.pi), rng.choice(list(WindowAxis)))
        elif operation == "pan":
            window.pan(rng.uniform(-50, 50), rng.uniform(-50, 50))
        else:
            window.zoom(rng.uniform(0.5, 1.5))
    return window


def _expected_scn(point: Point, window: Window) -> tuple[float, float]:
    offset = [p - c for p, c in zip(point, window.vrp)]
    return (
        dot(offset, window.right_vector()) / (window.width / 2),
        dot(offset, window.up_vector()) / (window.height / 2),
    )


def test_parallel_orthogonal_ignores_z():
    projected = transform_point(parallel_orthogonal(), Point(3, -4, 12))
    assert projected == Point(3, -4, 0)


def test_default_window_projects_along_z():
    # The default window faces +z: depth is dropped, x/y read as in 2D.
    window = Window(-100, -100, 100, 100)
    assert _close(to_scn(Point(50, 25, 999), window), (0.5, 0.25))
    assert _close(to_scn(Point(50, 25, -999), window), (0.5, 0.25))


def test_scn_points_are_2d():
    assert to_scn(Point(1, 2, 3), Window(-10, -10, 10, 10)).dimension == 2


def test_view_matrix_puts_vrp_at_origin_vpn_on_z_and_vup_on_y():
    for seed in range(20):
        window = _navigated_window(seed)
        view = view_matrix(window.vrp, window.vpn, window.vup)

        def through(vector):
            return Point(*(c + v for c, v in zip(window.vrp, vector)))

        assert _close(transform_point(view, window.vrp), (0, 0, 0))
        # "Ao final do algoritmo o VPN deve ser (0, 0, 1)".
        assert _close(transform_point(view, through(window.vpn)), (0, 0, 1))
        assert _close(transform_point(view, through(window.vup)), (0, 1, 0))
        assert _close(transform_point(view, through(window.right_vector())), (1, 0, 0))


def test_side_view_after_yaw():
    # Yaw 90: the window faces +x, so screen-right is world -z and up is +y.
    window = Window(-100, -100, 100, 100)
    window.rotate(math.radians(90), WindowAxis.YAW)
    assert _close(to_scn(Point(0, 0, 50), window), (-0.5, 0.0))
    assert _close(to_scn(Point(0, 50, 0), window), (0.0, 0.5))
    assert _close(to_scn(Point(77, 0, 0), window), (0.0, 0.0))  # along the VPN


def test_projection_matches_the_window_basis_after_any_navigation():
    rng = random.Random(42)
    for seed in range(30):
        window = _navigated_window(seed)
        for _ in range(5):
            point = Point(*(rng.uniform(-200, 200) for _ in range(3)))
            assert _close(to_scn(point, window), _expected_scn(point, window))


def test_projectors_run_along_the_vpn():
    # Orthogonal projection: sliding a point along the VPN never moves its image.
    for seed in range(10):
        window = _navigated_window(seed)
        point = Point(10, -20, 30)
        shifted = Point(*(p + 123.0 * n for p, n in zip(point, window.vpn)))
        assert _close(to_scn(point, window), to_scn(shifted, window))
