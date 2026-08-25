"""Transform engine: matrix factories, the generic apply, composed requests."""

import math

import pytest

from app.transform_request import Pivot, Rotate, Scale, Translate, build_matrix
from domain import transforms
from domain.geometry import Point, transform_point
from domain.objects import Line, Point2D, Wireframe


def _almost(p: Point, x: float, y: float, tol: float = 1e-9) -> bool:
    return abs(p[0] - x) < tol and abs(p[1] - y) < tol


# --- matrix factories -------------------------------------------------------


def test_translation_moves_a_point():
    m = transforms.translation(10, -5)
    assert transform_point(m, Point(1, 1)) == Point(11, -4)


def test_scaling_about_origin_scales_from_origin():
    m = transforms.scaling(2, 3)
    assert transform_point(m, Point(2, 2)) == Point(4, 6)


def test_rotation_90_degrees_ccw():
    m = transforms.rotation(math.radians(90))
    # (1, 0) rotated +90 deg -> (0, 1)
    assert _almost(transform_point(m, Point(1, 0)), 0, 1)


def test_scaling_about_center_keeps_center_fixed():
    center = Point(5, 5)
    m = transforms.scaling_about(center, 3, 3)
    # the center is a fixed point of a scaling about itself
    assert _almost(transform_point(m, center), 5, 5)
    # a corner moves outward by the factor
    assert _almost(transform_point(m, Point(6, 5)), 8, 5)


def test_rotation_about_center_keeps_center_fixed():
    center = Point(2, 2)
    m = transforms.rotation_about(center, math.radians(90))
    assert _almost(transform_point(m, center), 2, 2)
    # a point 1 to the right of center swings to 1 above it
    assert _almost(transform_point(m, Point(3, 2)), 2, 3)


def test_factories_reject_empty_input():
    with pytest.raises(ValueError):
        transforms.translation()
    with pytest.raises(ValueError):
        transforms.scaling()


# --- generic apply ----------------------------------------------------------


def test_apply_transforms_any_object_in_place_and_returns_it():
    line = Line("l", Point(0, 0), Point(2, 0))
    result = transforms.apply(transforms.translation(1, 1), line)
    assert result is line  # same object, mutated in place
    assert line.coordinates == [Point(1, 1), Point(3, 1)]


def test_apply_on_a_point_object():
    p = Point2D("p", Point(4, 4))
    transforms.apply(transforms.scaling(0.5, 0.5), p)
    assert p.coordinates == [Point(2, 2)]


# --- composed transform requests (the "list of transforms" the spec wants) --


def test_build_matrix_empty_is_identity():
    obj = Point2D("p", Point(7, 3))
    m = build_matrix([], obj)
    assert transform_point(m, Point(7, 3)) == Point(7, 3)


def test_build_matrix_composes_in_list_order():
    obj = Point2D("p", Point(1, 1))
    # translate by (2,0) then scale x2 about the world origin
    steps = [Translate(2, 0), Scale(2, 2, pivot=Pivot.WORLD_ORIGIN)]
    m = build_matrix(steps, obj)
    # (1,1) -> (3,1) -> (6,2)
    assert _almost(transform_point(m, Point(1, 1)), 6, 2)


def test_scale_about_object_center_uses_centroid():
    square = Wireframe("s", [Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)])
    m = build_matrix([Scale(2, 2)], square)  # default pivot: object center (1,1)
    # centroid stays put, object doubles in size about it
    assert _almost(transform_point(m, Point(1, 1)), 1, 1)
    assert _almost(transform_point(m, Point(0, 0)), -1, -1)


def test_rotate_about_arbitrary_point():
    obj = Point2D("p", Point(1, 0))
    steps = [Rotate(90, pivot=Pivot.ARBITRARY_POINT, point=Point(0, 0))]
    m = build_matrix(steps, obj)
    assert _almost(transform_point(m, Point(1, 0)), 0, 1)


def test_arbitrary_point_transform_requires_a_point():
    obj = Point2D("p", Point(1, 0))
    with pytest.raises(ValueError):
        build_matrix([Rotate(90, pivot=Pivot.ARBITRARY_POINT)], obj)


def test_rotate_about_world_origin():
    obj = Point2D("p", Point(2, 0))
    m = build_matrix([Rotate(180, pivot=Pivot.WORLD_ORIGIN)], obj)
    assert _almost(transform_point(m, Point(2, 0)), -2, 0)
