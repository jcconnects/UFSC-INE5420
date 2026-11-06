"""Wavefront .obj read/write round-trip (trabalho 1.3, 3D since 1.7)."""

import pytest

from domain.geometry import Point
from domain.objects import (
    BezierSurface,
    BSpline,
    BSplineSurface,
    Curve2D,
    Line,
    Object3D,
    ObjectType,
    Point2D,
    Wireframe,
)
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


def test_curves_roundtrip_as_free_form_curv_elements():
    # Each curve is one `curv` over its control points: a Bézier chain of 2
    # segments spans parameters 0..2; a cubic B-Spline of 5 points takes the
    # 5 + 4 uniform knots 0..8 and spans 3..5.
    chain = [Point(x, (x % 3) * 2 - 2, 0) for x in range(7)]
    controls = [Point(x, x % 2, 1) for x in range(5)]
    text = to_obj([Curve2D("bezier", chain), BSpline("bspline", controls)])
    lines = text.splitlines()
    assert "curv 0 2 1 2 3 4 5 6 7" in lines and "parm u 0 1 2" in lines
    assert "curv 3 5 8 9 10 11 12" in lines and "parm u 0 1 2 3 4 5 6 7 8" in lines
    restored = from_obj(text)
    assert [(o.name, o.type) for o in restored] == [
        ("bezier", ObjectType.CURVE),
        ("bspline", ObjectType.BSPLINE),
    ]
    assert [o.coordinates for o in restored] == [chain, controls]


def test_a_blender_style_curv_with_relative_refs_loads():
    # Blender's "Write Nurbs" writes `v x y z w`, refs relative to the end and
    # a clamped knot vector (read, but drawn as the uniform B-Spline).
    text = (
        "o NurbsCurve\n"
        "v -2 0 0 1\nv -1 1 0 1\nv 0 0 0 1\nv 1 1 0 1\nv 2 0 0 1\n"
        "g NurbsCurve\n"
        "cstype bspline\ndeg 3\n"
        "curv 0.0 1.0 -5 -4 -3 -2 -1\n"
        "parm u 0.0 0.0 0.0 0.0 0.5 1.0 1.0 1.0 1.0\n"
        "end\n"
    )
    [curve] = from_obj(text)
    assert curve.type is ObjectType.BSPLINE
    assert curve.coordinates == [Point(x, x % 2, 0) for x in range(-2, 3)]


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


# --- trabalho 1.9: Bézier surfaces as free-form .obj patches ----------------

# The "Bezier patch" example of the .obj spec (paulbourke.net/dataformats/obj),
# line continuation included: 16 control points, one `surf` element.
_SPEC_BEZIER_PATCH = """#   3.0 Bezier patch
v -5.000000 -5.000000 0.000000
v -5.000000 -1.666667 0.000000
v -5.000000 1.666667 0.000000
v -5.000000 5.000000 0.000000
v -1.666667 -5.000000 0.000000
v -1.666667 -1.666667 0.000000
v -1.666667 1.666667 0.000000
v -1.666667 5.000000 0.000000
v 1.666667 -5.000000 0.000000
v 1.666667 -1.666667 0.000000
v 1.666667 1.666667 0.000000
v 1.666667 5.000000 0.000000
v 5.000000 -5.000000 0.000000
v 5.000000 -1.666667 0.000000
v 5.000000 1.666667 0.000000
v 5.000000 5.000000 0.000000
# 16 vertices

cstype bezier
deg 3 3
surf 0.000000 1.000000 0.000000 1.000000 13 14 \\
15 16 9 10 11 12 5 6 7 8 1 2 3 4
parm u 0.000000 1.000000
parm v 0.000000 1.000000
end
# 1 element
"""


def test_the_spec_bezier_patch_loads_as_a_surface():
    [surface] = from_obj(_SPEC_BEZIER_PATCH)
    assert surface.type is ObjectType.SURFACE
    [patch] = surface.patches
    # Rows of 4 references: 13-16 first, 1-4 last.
    corners = [patch[0][0], patch[0][3], patch[3][0], patch[3][3]]
    assert corners == [Point(5, -5, 0), Point(5, 5, 0), Point(-5, -5, 0), Point(-5, 5, 0)]


def test_only_cubic_bezier_and_bspline_free_forms_load():
    # A rational basis or another degree is not what the SGI draws.
    with pytest.raises(ValueError):
        from_obj(_SPEC_BEZIER_PATCH.replace("cstype bezier", "cstype rat bezier"))
    with pytest.raises(ValueError):
        from_obj(_SPEC_BEZIER_PATCH.replace("deg 3 3", "deg 2 2"))


def test_a_surface_does_not_mix_with_other_elements():
    with pytest.raises(ValueError):
        from_obj(_SPEC_BEZIER_PATCH + "l 1 2\n")


def test_surface_roundtrip_keeps_its_patches():
    # Two patches sharing the border row x = 3: its control points are written
    # once (28 vertices, not 32), and each patch is one `surf` element.
    first = [[Point(x, y, x * y) for y in range(4)] for x in range(4)]
    second = [[Point(x, y, 3 * y) for y in range(4)] for x in range(3, 7)]
    surface = BezierSurface("terrain", [first, second])
    text = to_obj([Point2D("dot", Point(9, 9, 9)), surface])
    assert text.count("\nv ") == 1 + 28
    assert text.count("\nsurf ") == 2
    restored = from_obj(text)
    assert [o.type for o in restored] == [ObjectType.POINT, ObjectType.SURFACE]
    assert restored[1].name == "terrain"
    assert restored[1].patches == [first, second]


# --- trabalho 1.10: B-Spline surfaces as one free-form net -------------------

# A hand-written 4 x 5 net, vertex (row r, column c) = (c, r, r*c), listed u
# (the column) fastest. A cubic over 5 points per row takes 5 + 4 = 9 knots,
# so `parm u` is what sizes the rows.
_NET_VERTICES = "".join(f"v {c} {r} {r * c}\n" for r in range(4) for c in range(5))
_NET_SURF = (
    "cstype bspline\n"
    "deg 3 3\n"
    "surf 3 5 3 4 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20\n"
    "parm u 0 1 2 3 4 5 6 7 8\n"
    "parm v 0 1 2 3 4 5 6 7\n"
    "end\n"
)
_BSPLINE_NET = "o net\n" + _NET_VERTICES + _NET_SURF


def test_a_bspline_surf_is_one_control_net_sized_by_its_parm_u():
    [surface] = from_obj(_BSPLINE_NET)
    assert surface.type is ObjectType.BSPLINE_SURFACE
    assert len(surface.control_net) == 4 and surface.columns == 5
    assert surface.control_net[1][4] == Point(4, 1, 4)
    assert len(surface.patches) == 2


@pytest.mark.parametrize(
    "broken",
    [
        _BSPLINE_NET.replace("parm u 0 1 2 3 4 5 6 7 8\n", ""),  # no parm u
        _BSPLINE_NET.replace("parm u 0 1 2 3 4 5 6 7 8", "parm u 0 1 2 3 4 5 6 7 8 9 10"),
        _BSPLINE_NET + _NET_SURF,  # two B-Spline surfaces in one object
        _BSPLINE_NET + "l 1 2\n",  # mixed with a polyline
    ],
    ids=["no-parm-u", "rows-do-not-divide", "two-surfs", "mixed"],
)
def test_a_bspline_surf_that_cannot_be_sized_alone_is_rejected(broken):
    with pytest.raises(ValueError):
        from_obj(broken)


def test_bspline_surface_roundtrip_keeps_its_net():
    # 5 rows of 6: not square, so rows and columns cannot be swapped unseen.
    net = [[Point(c, r, (r - c) ** 2) for c in range(6)] for r in range(5)]
    text = to_obj([Point2D("dot", Point(9, 9, 9)), BSplineSurface("hill", net)])
    assert text.count("\nsurf ") == 1
    restored = from_obj(text)
    assert [o.type for o in restored] == [ObjectType.POINT, ObjectType.BSPLINE_SURFACE]
    assert restored[1].name == "hill"
    assert restored[1].control_net == net
