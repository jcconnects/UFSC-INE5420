"""Wavefront .obj read/write round-trip (trabalho 1.3)."""

from domain.geometry import Point
from domain.objects import Line, ObjectType, Point2D, Wireframe
from persistence.obj_descriptor import from_obj, to_obj


def _square():
    return Wireframe(
        "square",
        [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)],
    )


def test_to_obj_golden_string():
    text = to_obj([_square()])
    assert text == (
        "# SGI - INE5420 world export (Wavefront .obj)\n"
        "o square\n"
        "v 0 0 0\n"
        "v 10 0 0\n"
        "v 10 10 0\n"
        "v 0 10 0\n"
        "l 1 2 3 4 1\n"
    )


def test_point_and_line_elements():
    text = to_obj([Point2D("p", Point(1, 2)), Line("seg", Point(0, 0), Point(3, 4))])
    # Global 1-based indices: the point is vertex 1, the line is vertices 2-3.
    assert "p 1" in text
    assert "l 2 3" in text


def test_roundtrip_preserves_geometry_and_types():
    world = [
        Point2D("dot", Point(5, 5)),
        Line("edge", Point(-1, -1), Point(2, 3)),
        _square(),
    ]
    restored = from_obj(to_obj(world))

    assert [o.name for o in restored] == ["dot", "edge", "square"]
    assert [o.type for o in restored] == [
        ObjectType.POINT,
        ObjectType.LINE,
        ObjectType.WIREFRAME,
    ]
    assert [o.coordinates for o in restored] == [o.coordinates for o in world]


def test_roundtrip_of_a_triangle_stays_closed_wireframe():
    tri = Wireframe("tri", [Point(0, 0), Point(4, 0), Point(2, 3)])
    restored = from_obj(to_obj([tri]))
    assert len(restored) == 1
    assert restored[0].type is ObjectType.WIREFRAME
    assert restored[0].coordinates == tri.coordinates  # no duplicated closing vertex
