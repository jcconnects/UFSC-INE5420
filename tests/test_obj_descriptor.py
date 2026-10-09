"""Wavefront .obj read/write round-trip (trabalho 1.3, 3D since 1.7)."""

import pytest

from domain.geometry import Point
from domain.objects import BSpline, Curve2D, Line, Object3D, ObjectType, Point2D, Wireframe
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
    # The world is 3D since 1.7, and import keeps z.
    world = [
        Point2D("dot", Point(5, 5, 1)),
        Line("edge", Point(-1, -1, 0), Point(2, 3, -4)),
        Wireframe("square", [Point(0, 0, 2), Point(10, 0, 2), Point(10, 10, 2), Point(0, 10, 2)]),
    ]
    restored = from_obj(to_obj(world))

    assert [o.name for o in restored] == ["dot", "edge", "square"]
    assert [o.type for o in restored] == [
        ObjectType.POINT,
        ObjectType.LINE,
        ObjectType.WIREFRAME,
    ]
    assert [o.coordinates for o in restored] == [o.coordinates for o in world]


def test_curves_are_skipped_on_export():
    # Control points are not polyline geometry: writing them as `l` would load
    # back as a wireframe, so both curve kinds are left out of the file.
    controls = [Point(0, 0), Point(1, 1), Point(2, 0), Point(3, 1)]
    text = to_obj([Curve2D("bezier", controls), BSpline("bspline", controls)])
    assert text == "# SGI - INE5420 world export (Wavefront .obj)\n"


def test_roundtrip_of_a_triangle_stays_closed_wireframe():
    tri = Wireframe("tri", [Point(0, 0, 0), Point(4, 0, 0), Point(2, 3, 0)])
    restored = from_obj(to_obj([tri]))
    assert len(restored) == 1
    assert restored[0].type is ObjectType.WIREFRAME
    assert restored[0].coordinates == tri.coordinates  # no duplicated closing vertex


# --- trabalho 1.7: 3D objects ----------------------------------------------


def _cube_segments(half=1.0):
    corners = {
        (x, y, z): Point(x, y, z)
        for x in (-half, half)
        for y in (-half, half)
        for z in (-half, half)
    }
    segments = []
    for (x, y, z), start in corners.items():
        # Each edge joins two corners differing in exactly one axis; emit it
        # once, from the corner with the smaller coordinate on that axis.
        for axis in range(3):
            if (x, y, z)[axis] < 0:
                end = list((x, y, z))
                end[axis] = half
                segments.append((start, corners[tuple(end)]))
    return segments


def test_planar_vertices_load_on_the_z0_plane():
    restored = from_obj("o p\nv 3 4\np 1\n")
    assert restored[0].coordinates == [Point(3, 4, 0)]


def test_object3d_writes_each_shared_vertex_once():
    cube = Object3D("cube", _cube_segments())
    text = to_obj([cube])
    assert text.count("\nv ") == 8  # 8 corners, not 24 segment endpoints
    assert text.count("\nl ") == 12  # one element per edge


def test_object3d_roundtrip_keeps_type_and_segments():
    cube = Object3D("cube", _cube_segments(), color=(1, 2, 3))
    restored = from_obj(to_obj([Point2D("dot", Point(9, 9, 9)), cube]))
    assert [o.type for o in restored] == [ObjectType.POINT, ObjectType.OBJECT3D]
    assert restored[1].name == "cube"
    assert restored[1].segments == cube.segments


def test_faces_load_as_an_object3d_with_shared_edges_once():
    # A Blender-style cube: 8 vertices, 6 quad faces with v/vt/vn tokens. The 24
    # face edges are 12 distinct edges, each shared by two faces.
    text = """o Cube
v 1 1 -1
v 1 -1 -1
v 1 1 1
v 1 -1 1
v -1 1 -1
v -1 -1 -1
v -1 1 1
v -1 -1 1
vn 0 1 0
s off
f 1/1/1 5/2/1 7/3/1 3/4/1
f 4/5/2 3/4/2 7/6/2 8/7/2
f 8/8/3 7/9/3 5/10/3 6/11/3
f 6/12/4 2/13/4 4/5/4 8/14/4
f 2/13/5 1/1/5 3/4/5 4/5/5
f 6/11/6 5/10/6 1/1/6 2/13/6
"""
    restored = from_obj(text)
    assert len(restored) == 1
    cube = restored[0]
    assert cube.type is ObjectType.OBJECT3D
    assert cube.name == "Cube"
    assert len(cube.segments) == 12
    assert len(cube.vertices()) == 8


def test_several_polylines_under_one_name_are_one_object3d():
    text = "o frame\nv 0 0 0\nv 1 0 0\nv 1 1 0\nv 1 1 5\nl 1 2 3\nl 3 4\n"
    restored = from_obj(text)
    assert len(restored) == 1
    assert restored[0].type is ObjectType.OBJECT3D
    assert restored[0].segments == [
        (Point(0, 0, 0), Point(1, 0, 0)),
        (Point(1, 0, 0), Point(1, 1, 0)),
        (Point(1, 1, 0), Point(1, 1, 5)),
    ]


def test_elements_before_any_name_form_one_unnamed_object():
    text = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
    restored = from_obj(text)
    assert [o.name for o in restored] == ["object_1"]
    assert len(restored[0].segments) == 3  # the triangle's closed loop


def test_object3d_needs_segments_of_3d_points():
    with pytest.raises(ValueError):
        Object3D("flat", [(Point(0, 0), Point(1, 1))])
