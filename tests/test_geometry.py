"""Geometry: homogeneous points and matrix operations, dimension-agnostic."""

import pytest

from domain.geometry import (
    Point,
    centroid,
    compose,
    cross,
    identity,
    multiply,
    normalized,
    transform_point,
)


def test_point_dimension_from_coords():
    assert Point(1, 2).dimension == 2
    assert Point(1, 2, 3).dimension == 3


def test_homogeneous_appends_one():
    assert Point(4, 5).homogeneous() == (4.0, 5.0, 1.0)
    assert Point(4, 5, 6).homogeneous() == (4.0, 5.0, 6.0, 1.0)


def test_identity_transform_is_a_noop():
    p = Point(3, 7)
    assert transform_point(identity(3), p) == p


def test_translation_matrix_moves_a_point():
    translate = [[1, 0, 10], [0, 1, -5], [0, 0, 1]]
    assert transform_point(translate, Point(1, 1)) == Point(11, -4)


def test_multiply_matches_manual_product():
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    assert multiply(a, b) == [[19, 22], [43, 50]]


def test_compose_applies_left_to_right():
    translate = [[1, 0, 2], [0, 1, 0], [0, 0, 1]]
    scale = [[3, 0, 0], [0, 3, 0], [0, 0, 1]]
    # translate then scale: (1,1) -> (3,1) -> (9,3)
    combined = compose(translate, scale)
    assert transform_point(combined, Point(1, 1)) == Point(9, 3)


def test_works_in_3d_without_renames():
    translate_3d = [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]]
    assert transform_point(translate_3d, Point(0, 0, 0)) == Point(1, 2, 3)


# --- trabalho 1.7: Point as Ponto3D, lifting, vectors -----------------------


def test_point_transforms_itself_with_a_4x4_matrix():
    translate_3d = [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]]
    assert Point(1, 1, 1).transformed(translate_3d) == Point(2, 3, 4)


def test_lifted_puts_a_planar_point_on_z0():
    assert Point(3, 4).lifted(3) == Point(3, 4, 0)
    assert Point(3, 4, 5).lifted(3) == Point(3, 4, 5)
    with pytest.raises(ValueError):
        Point(1, 2, 3).lifted(2)


def test_centroid_averages_each_axis():
    assert centroid([Point(0, 0, 0), Point(2, 4, 6)]) == Point(1, 2, 3)


def test_cross_follows_the_right_hand_rule():
    assert cross((1, 0, 0), (0, 1, 0)) == (0, 0, 1)
    assert cross((0, 1, 0), (0, 0, 1)) == (1, 0, 0)


def test_normalized_has_unit_length_and_rejects_zero():
    assert normalized((0, 3, 4)) == (0.0, 0.6, 0.8)
    with pytest.raises(ValueError):
        normalized((0, 0, 0))
