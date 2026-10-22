"""Perspective projection through the 3D window (trabalho 1.8).

The algorithm (translate the COP to the origin, align the VPN with z and the
VUP with y, apply the perspective matrix, divide by W, normalize) is checked
against its geometric meaning: a point's image is where the projector from the
COP through it pierces the window plane. The classroom exercise -- a
tetrahedron seen from COP (50, 250, 40) -- pins the numbers down.
"""

import math
import random

import pytest

from domain.geometry import Point, dot, homogeneous_product, transform_point
from domain.normalization import (
    map_polygon_to_scn,
    map_segment_to_scn,
    to_scn,
    world_to_scn_matrix,
)
from domain.projection import (
    ParallelProjection,
    PerspectiveProjection,
    perspective,
    view_matrix,
)
from domain.window import Window, WindowAxis

PARALLEL = ParallelProjection()


def _close(actual, expected, tol: float = 1e-9) -> bool:
    return all(
        math.isclose(a, e, rel_tol=1e-9, abs_tol=tol)
        for a, e in zip(actual, expected, strict=True)
    )


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


def _cop(window: Window, d: float) -> list[float]:
    return [c + d * n for c, n in zip(window.vrp, window.vpn)]


def _depth(point: Point, window: Window, d: float) -> float:
    """How far in front of the COP a point lies, along the view direction -VPN."""
    return dot([c - p for c, p in zip(_cop(window, d), point)], window.vpn)


def _point_in_front(rng: random.Random, window: Window, d: float) -> Point:
    while True:
        point = Point(*(rng.uniform(-300, 300) for _ in range(3)))
        if _depth(point, window, d) > 10.0:
            return point


def _pierce_window_plane(point: Point, window: Window, d: float) -> Point:
    """Where the projector from the COP through `point` meets the window plane."""
    cop = _cop(window, d)
    direction = [p - c for p, c in zip(point, cop)]
    # The COP is d off the plane along the VPN; the projector walks back to it.
    t = -d / dot(direction, window.vpn)
    return Point(*(c + t * v for c, v in zip(cop, direction)))


def test_perspective_matrix_divides_by_depth_over_d():
    # COP at the origin, window plane at z = -100: a point 200 deep has W = 2.
    point = Point(30, -20, -200)
    assert homogeneous_product(perspective(100), point) == (30, -20, -200, 2)
    assert transform_point(perspective(100), point) == Point(15, -10, -100)


def test_view_puts_the_cop_at_the_origin_and_the_window_at_minus_d():
    for seed in range(10):
        window = _navigated_window(seed)
        cop = PerspectiveProjection(150).center_of_projection(window)
        assert _close(cop, _cop(window, 150))
        view = view_matrix(cop, window.vpn, window.vup)
        assert _close(transform_point(view, cop), (0, 0, 0))
        assert _close(transform_point(view, window.vrp), (0, 0, -150))


def test_classroom_exercise_tetrahedron():
    # "Exercício sobre Perspectiva": window on the plane y = 150 spanning
    # x in [-10, 110] and z in [0, 80]; COP (50, 250, 40), so d = 100.
    window = Window(-60, -40, 60, 40)
    window.vrp = Point(50, 150, 40)
    window.vpn = (0.0, 1.0, 0.0)  # toward the COP, the viewer's side
    window.vup = (0.0, 0.0, 1.0)
    projection = PerspectiveProjection(100)
    assert projection.center_of_projection(window) == Point(50, 250, 40)
    # Screen right is world -x (VUP x VPN) and up is world +z. A vertex at
    # height y lies 250 - y below the COP, so its offsets from the window center
    # shrink by 100 / (250 - y): on the window the images are (50, 150, 46.67),
    # (58.70, 150, 35.65), (41.30, 150, 35.65) and (50, 150, 66.09).
    images = {
        (50, 100, 50): (0, 10 * 100 / 150),
        (70, 20, 30): (-20 * 100 / 230, -10 * 100 / 230),
        (30, 20, 30): (20 * 100 / 230, -10 * 100 / 230),
        (50, 20, 100): (0, 60 * 100 / 230),
    }
    for vertex, (right, up) in images.items():
        assert _close(to_scn(Point(*vertex), window, projection), (right / 60, up / 40))


def test_image_is_where_the_projector_pierces_the_window():
    rng = random.Random(11)
    for seed in range(30):
        window = _navigated_window(seed)
        d = rng.uniform(20, 2000)
        for _ in range(5):
            point = _point_in_front(rng, window, d)
            expected = to_scn(_pierce_window_plane(point, window, d), window, PARALLEL)
            assert _close(to_scn(point, window, PerspectiveProjection(d)), expected, tol=1e-7)


def test_window_plane_looks_the_same_in_both_projections():
    rng = random.Random(7)
    for seed in range(20):
        window = _navigated_window(seed)
        right, up = window.right_vector(), window.up_vector()
        for d in (30, 200, 5000):
            a, b = rng.uniform(-100, 100), rng.uniform(-100, 100)
            on_plane = Point(*(c + a * r + b * u for c, r, u in zip(window.vrp, right, up)))
            expected = (a / (window.width / 2), b / (window.height / 2))
            assert _close(to_scn(on_plane, window, PerspectiveProjection(d)), expected)


def test_projectors_meet_at_the_cop():
    # Sliding a point along its projector never moves its image.
    rng = random.Random(3)
    for seed in range(10):
        window = _navigated_window(seed)
        d = rng.uniform(50, 500)
        cop = _cop(window, d)
        point = _point_in_front(rng, window, d)
        farther = Point(*(c + 2.5 * (p - c) for c, p in zip(cop, point)))
        projection = PerspectiveProjection(d)
        assert _close(to_scn(point, window, projection), to_scn(farther, window, projection))


def test_twice_as_deep_looks_half_as_big():
    window = Window(-100, -100, 100, 100)  # COP at (0, 0, 200)
    projection = PerspectiveProjection(200)
    assert _close(to_scn(Point(50, 20, 0), window, projection), (0.5, 0.2))
    assert _close(to_scn(Point(50, 20, -200), window, projection), (0.25, 0.1))
    assert _close(to_scn(Point(50, 20, 100), window, projection), (1.0, 0.4))  # nearer


def test_short_d_is_wide_angle_and_long_d_tends_to_parallel():
    window = Window(-100, -100, 100, 100)
    wide, normal, tele = (
        math.degrees(PerspectiveProjection(d).field_of_view(window)) for d in (50, 200, 2000)
    )
    assert wide > 90 > normal > 30 > tele
    point = Point(60, 40, -150)
    parallel = to_scn(point, window, PARALLEL)
    gaps = [
        abs(to_scn(point, window, PerspectiveProjection(d))[0] - parallel[0])
        for d in (50, 200, 2000, 1e7)
    ]
    assert gaps == sorted(gaps, reverse=True)
    assert gaps[-1] < 1e-4


def test_parallel_projection_has_no_cop():
    window = Window(-1, -1, 1, 1)
    assert PARALLEL.center_of_projection(window) is None
    assert PARALLEL.field_of_view(window) is None


def test_cop_must_be_a_positive_distance_behind_the_window():
    with pytest.raises(ValueError):
        PerspectiveProjection(0)
    with pytest.raises(ValueError):
        PerspectiveProjection(-10)


# --- behind the COP ---------------------------------------------------------


def test_point_at_or_behind_the_cop_is_not_projected():
    window = Window(-100, -100, 100, 100)  # COP at (0, 0, 200)
    projection = PerspectiveProjection(200)
    assert to_scn(Point(10, 10, 250), window, projection) is None
    assert to_scn(Point(10, 10, 200), window, projection) is None
    assert to_scn(Point(10, 10, 150), window, projection) is not None  # between


def test_segment_through_the_cop_plane_keeps_its_front_part():
    window = Window(-100, -100, 100, 100)
    matrix = world_to_scn_matrix(window, PerspectiveProjection(200))
    front = map_segment_to_scn(matrix, Point(20, 0, 0), Point(20, 0, 400))
    assert front is not None
    assert _close(front[0], (0.2, 0.0))
    # The kept end sits just in front of the COP: far off the window, same side.
    assert front[1][0] > 100 and math.isclose(front[1][1], 0.0, abs_tol=1e-9)
    assert map_segment_to_scn(matrix, Point(0, 0, 300), Point(5, 5, 500)) is None


def test_parallel_projection_never_trims():
    matrix = world_to_scn_matrix(Window(-100, -100, 100, 100), PARALLEL)
    segment = map_segment_to_scn(matrix, Point(20, 0, 0), Point(20, 0, 400))
    assert _close(segment[0], (0.2, 0.0)) and _close(segment[1], (0.2, 0.0))


def test_polygon_partly_behind_the_cop_is_cut_there():
    window = Window(-100, -100, 100, 100)  # COP at (0, 0, 200)
    matrix = world_to_scn_matrix(window, PerspectiveProjection(200))
    # A floor tile from 100 beyond the window to 100 behind the COP.
    tile = [Point(-50, -50, -100), Point(50, -50, -100), Point(50, -50, 300), Point(-50, -50, 300)]
    front = map_polygon_to_scn(matrix, tile)
    # Two original corners (300 deep, scale 2/3) and two cuts near the COP.
    assert len(front) == 4
    assert _close(front[1], (-1 / 3, -1 / 3)) and _close(front[2], (1 / 3, -1 / 3))
    assert front[0][1] < -100 and front[3][1] < -100
    behind = [Point(-50, -50, 250), Point(50, -50, 250), Point(0, 50, 300)]
    assert map_polygon_to_scn(matrix, behind) == []
