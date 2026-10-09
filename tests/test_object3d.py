"""Object3D (trabalho 1.7): a wireframe model as a list of 3D segments."""

import pytest

from domain.geometry import Point, centroid
from domain.objects import Object3D, ObjectType
from domain.transforms import translation

_A = Point(0, 0, 0)
_B = Point(3, 0, 0)
_C = Point(0, 3, 0)
_D = Point(0, 0, 3)


def test_from_points_reads_consecutive_pairs_as_segments():
    obj = Object3D.from_points("o", [_A, _B, _C, _D])
    assert obj.segments == [(_A, _B), (_C, _D)]
    assert obj.to_segments() == obj.segments
    assert obj.type is ObjectType.OBJECT3D


def test_from_points_rejects_an_odd_count():
    with pytest.raises(ValueError):
        Object3D.from_points("o", [_A, _B, _C])


def test_needs_at_least_one_segment():
    with pytest.raises(ValueError):
        Object3D("o", [])


def test_center_is_the_centroid_of_distinct_vertices():
    # A corner shared by three segments: averaging raw endpoints would count A
    # three times and pull the center toward it.
    obj = Object3D("o", [(_A, _B), (_A, _C), (_A, _D)])
    assert obj.vertices() == [_A, _B, _C, _D]
    assert obj.center() == Point(0.75, 0.75, 0.75)
    assert centroid(obj.coordinates) == Point(0.5, 0.5, 0.5)


def test_transform_moves_every_segment_and_keeps_shared_corners_together():
    obj = Object3D("o", [(_A, _B), (_A, _C)])
    obj.transform(translation(1, 1, 1))
    assert obj.segments == [
        (Point(1, 1, 1), Point(4, 1, 1)),
        (Point(1, 1, 1), Point(1, 4, 1)),
    ]
    assert obj.segments[0][0] == obj.segments[1][0]
