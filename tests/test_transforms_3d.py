"""3D transforms (trabalho 1.7): basic rotations, VPN alignment, arbitrary axis."""

import math

import pytest

from app.transform_request import X_AXIS, Pivot, Rotate, Scale, Translate, build_matrix
from domain import transforms
from domain.geometry import Point, cross, dot, transform_point
from domain.objects import Object3D, Point2D

_DIRECTIONS = [
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
    (1, 1, 1),
    (-2, 3, -5),
    (0.3, -0.2, 0.01),
]


def _close(actual, expected, tol: float = 1e-9) -> bool:
    return all(math.isclose(a, e, abs_tol=tol) for a, e in zip(actual, expected, strict=True))


def _same_matrix(a, b, tol: float = 1e-9) -> bool:
    return all(_close(row_a, row_b, tol) for row_a, row_b in zip(a, b, strict=True))


def _rodrigues(point, axis_point, direction, angle):
    """Independent reference: rotate `point` about the axis with Rodrigues' formula."""
    length = math.sqrt(dot(direction, direction))
    k = tuple(c / length for c in direction)
    v = tuple(p - a for p, a in zip(point, axis_point))
    k_cross_v = cross(k, v)
    k_dot_v = dot(k, v)
    cos, sin = math.cos(angle), math.sin(angle)
    rotated = tuple(
        v[i] * cos + k_cross_v[i] * sin + k[i] * k_dot_v * (1 - cos) for i in range(3)
    )
    return tuple(r + a for r, a in zip(rotated, axis_point))


# --- the basic rotations -----------------------------------------------------


def test_rotation_x_turns_y_toward_z():
    m = transforms.rotation_x(math.radians(90))
    assert _close(transform_point(m, Point(0, 1, 0)), (0, 0, 1))


def test_rotation_y_turns_z_toward_x():
    m = transforms.rotation_y(math.radians(90))
    assert _close(transform_point(m, Point(0, 0, 1)), (1, 0, 0))


def test_rotation_z_turns_x_toward_y_like_the_2d_rotation():
    angle = math.radians(30)
    in_3d = transform_point(transforms.rotation_z(angle), Point(4, 2, 0))
    in_2d = transform_point(transforms.rotation(angle), Point(4, 2))
    assert _close(in_3d, (*in_2d, 0.0))


def test_translation_and_scaling_are_4x4_in_3d():
    assert transform_point(transforms.translation(1, 2, 3), Point(1, 1, 1)) == Point(2, 3, 4)
    assert transform_point(transforms.scaling(2, 3, 4), Point(1, 1, 1)) == Point(2, 3, 4)


# --- aligning a direction with z (the VPN step of the projection) -----------


@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_alignment_sends_the_direction_to_plus_z(direction):
    # "Ao final do algoritmo o VPN deve ser (0, 0, 1)": the alignment rotation
    # leaves any direction on +z, keeping its length.
    length = math.sqrt(dot(direction, direction))
    aligned = transform_point(transforms.alignment_with_z(direction), Point(*direction))
    assert _close(aligned, (0, 0, length))


def test_alignment_rejects_a_zero_direction():
    with pytest.raises(ValueError):
        transforms.alignment_with_z((0, 0, 0))


# --- rotation about an arbitrary axis ---------------------------------------


@pytest.mark.parametrize(
    ("direction", "basic"),
    [((1, 0, 0), transforms.rotation_x), ((0, 1, 0), transforms.rotation_y),
     ((0, 0, 1), transforms.rotation_z)],
)
def test_principal_axis_through_origin_is_the_basic_rotation(direction, basic):
    angle = math.radians(37)
    origin = Point(0, 0, 0)
    assert _same_matrix(transforms.rotation_about_axis(origin, direction, angle), basic(angle))


@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_arbitrary_axis_matches_rodrigues(direction):
    axis_point = Point(3, -1, 2)
    angle = math.radians(73)
    m = transforms.rotation_about_axis(axis_point, direction, angle)
    for point in (Point(1, 2, 3), Point(-4, 0, 5), Point(0, 0, 0)):
        expected = _rodrigues(point, axis_point, direction, angle)
        assert _close(transform_point(m, point), expected)


def test_points_on_the_axis_stay_fixed():
    axis_point = Point(1, 1, 1)
    direction = (1, 2, 3)
    m = transforms.rotation_about_axis(axis_point, direction, math.radians(120))
    on_axis = Point(*(a + 2 * d for a, d in zip(axis_point, direction)))
    assert _close(transform_point(m, axis_point), axis_point)
    assert _close(transform_point(m, on_axis), on_axis)


# --- composed 3D requests on an Object3D (the transform dialog's model) -----


def _unit_cube_edges_from(corner):
    x, y, z = corner
    return [
        (Point(x, y, z), Point(x + 2, y, z)),
        (Point(x, y, z), Point(x, y + 2, z)),
        (Point(x, y, z), Point(x, y, z + 2)),
    ]


def test_translate_moves_an_object3d_in_3d():
    obj = Object3D("o", _unit_cube_edges_from((0, 0, 0)))
    obj.transform(build_matrix([Translate(1, 2, 3)], obj))
    assert obj.segments[0] == (Point(1, 2, 3), Point(3, 2, 3))


def test_scale_about_object_center_keeps_it_fixed():
    obj = Object3D("o", _unit_cube_edges_from((0, 0, 0)))
    before = obj.center()
    obj.transform(build_matrix([Scale(2, 3, 4)], obj))
    assert _close(obj.center(), before)


def test_rotate_about_x_through_object_center():
    # Edges from the origin along x, y, z; the center is (0.5, 0.5, 0.5).
    obj = Object3D("o", _unit_cube_edges_from((0, 0, 0)))
    center = obj.center()
    obj.transform(build_matrix([Rotate(90, axis=X_AXIS)], obj))
    assert _close(obj.center(), center)
    # The edge along +y now runs along +z (right-hand rule about +x).
    start, end = obj.segments[1]
    assert _close([e - s for e, s in zip(end, start)], (0, 0, 2))


def test_rotate_about_an_arbitrary_axis_through_the_world_origin():
    obj = Object3D("o", [(Point(1, 0, 0), Point(0, 1, 0))])
    steps = [Rotate(180, pivot=Pivot.WORLD_ORIGIN, axis=(1, 1, 0))]
    obj.transform(build_matrix(steps, obj))
    # Half a turn about the x=y diagonal swaps the x and y axes.
    start, end = obj.segments[0]
    assert _close(start, (0, 1, 0)) and _close(end, (1, 0, 0))


def test_planar_object_rejects_a_non_z_axis():
    with pytest.raises(ValueError):
        build_matrix([Rotate(90, axis=X_AXIS)], Point2D("p", Point(1, 0)))


def test_planar_object_ignores_z_components():
    obj = Point2D("p", Point(1, 1))
    obj.transform(build_matrix([Translate(1, 1, 99)], obj))
    assert obj.coordinates == [Point(2, 2)]
