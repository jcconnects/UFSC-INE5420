"""Display file collection and object segment decomposition."""

import pytest

from domain.display_file import DisplayFile
from domain.geometry import Point
from domain.objects import Line, ObjectType, Point2D, Wireframe


def test_add_and_get():
    df = DisplayFile()
    line = Line("l1", Point(0, 0), Point(1, 1))
    df.add(line)
    assert df.get("l1") is line
    assert "l1" in df
    assert len(df) == 1


def test_duplicate_name_rejected():
    df = DisplayFile()
    df.add(Point2D("p", Point(0, 0)))
    with pytest.raises(ValueError):
        df.add(Point2D("p", Point(1, 1)))


def test_point_is_degenerate_segment():
    p = Point2D("p", Point(2, 3))
    assert p.to_segments() == [(Point(2, 3), Point(2, 3))]


def test_line_has_one_segment():
    line = Line("l", Point(0, 0), Point(4, 4))
    assert line.to_segments() == [(Point(0, 0), Point(4, 4))]


def test_wireframe_closes_the_polygon():
    tri = Wireframe("t", [Point(0, 0), Point(1, 0), Point(0, 1)])
    segments = tri.to_segments()
    assert len(segments) == 3  # closed: last vertex connects back to first
    assert segments[-1] == (Point(0, 1), Point(0, 0))


def test_wireframe_center_is_centroid():
    square = Wireframe("s", [Point(0, 0), Point(2, 0), Point(2, 2), Point(0, 2)])
    assert square.center() == Point(1, 1)


def test_object_types():
    assert Point2D("p", Point(0, 0)).type is ObjectType.POINT
    assert Line("l", Point(0, 0), Point(1, 1)).type is ObjectType.LINE
    assert Wireframe("w", [Point(0, 0), Point(1, 1)]).type is ObjectType.WIREFRAME


def test_color_defaults_to_black():
    assert Point2D("p", Point(0, 0)).color == (0, 0, 0)


def test_color_is_stored_per_object():
    red = (255, 0, 0)
    line = Line("l", Point(0, 0), Point(1, 1), color=red)
    assert line.color == red
