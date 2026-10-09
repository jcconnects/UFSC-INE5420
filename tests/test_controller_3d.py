"""The controller's 3D world (trabalho 1.7): input lifting, Object3D, navigation."""

import math

import pytest

from app.controller import Controller
from app.render_pipeline import DrawLine, DrawPoint
from domain.geometry import Point
from domain.objects import ObjectType
from domain.window import WindowAxis

# A cube of side 100 centered at the origin, typed as 12 point pairs.
_CUBE = ",".join(
    f"({x0},{y0},{z0}),({x1},{y1},{z1})"
    for (x0, y0, z0), (x1, y1, z1) in [
        ((-50, -50, -50), (50, -50, -50)), ((50, -50, -50), (50, 50, -50)),
        ((50, 50, -50), (-50, 50, -50)), ((-50, 50, -50), (-50, -50, -50)),
        ((-50, -50, 50), (50, -50, 50)), ((50, -50, 50), (50, 50, 50)),
        ((50, 50, 50), (-50, 50, 50)), ((-50, 50, 50), (-50, -50, 50)),
        ((-50, -50, -50), (-50, -50, 50)), ((50, -50, -50), (50, -50, 50)),
        ((50, 50, -50), (50, 50, 50)), ((-50, 50, -50), (-50, 50, 50)),
    ]
)


def test_planar_input_is_lifted_to_z0():
    c = Controller()
    obj = c.add_object("l", ObjectType.LINE, "(1, 2),(3, 4)")
    assert obj.coordinates == [Point(1, 2, 0), Point(3, 4, 0)]


def test_object3d_from_typed_pairs():
    c = Controller()
    obj = c.add_object("cube", ObjectType.OBJECT3D, _CUBE)
    assert obj.type is ObjectType.OBJECT3D
    assert len(obj.segments) == 12
    assert obj.center() == Point(0, 0, 0)


def test_object3d_rejects_an_unpaired_point():
    with pytest.raises(ValueError):
        Controller().add_object("bad", ObjectType.OBJECT3D, "(0,0,0),(1,1,1),(2,2,2)")


def test_cube_renders_in_the_default_view_and_after_orbiting():
    c = Controller()
    c.add_object("cube", ObjectType.OBJECT3D, _CUBE)
    front = c.render(200, 200)
    # Head-on, the front and back faces coincide on the half-size square
    # centered in the viewport, and the 4 depth edges (along the VPN) collapse
    # to points at its corners.
    lines = [command for command in front if isinstance(command, DrawLine)]
    points = [command for command in front if isinstance(command, DrawPoint)]
    assert (len(lines), len(points)) == (8, 4)
    for command in lines:
        for x, y in ((command.x1, command.y1), (command.x2, command.y2)):
            assert 50 - 1e-6 <= x <= 150 + 1e-6 and 50 - 1e-6 <= y <= 150 + 1e-6
    assert sorted((round(p.x), round(p.y)) for p in points) == [
        (50, 50), (50, 150), (150, 50), (150, 150)
    ]

    c.rotate_window(30, WindowAxis.YAW)
    c.rotate_window(-20, WindowAxis.PITCH)
    orbited = c.render(200, 200)
    # Seen obliquely no edge is parallel to the VPN: 12 visible lines.
    assert len(orbited) == 12
    assert all(isinstance(command, DrawLine) for command in orbited)
    assert orbited != front  # the view changed, the world did not
    assert c.display_file.get("cube").center() == Point(0, 0, 0)


def test_rotate_window_axes_and_reset():
    c = Controller()
    c.pan(10, 0)
    c.zoom(0.5)
    c.rotate_window(90, WindowAxis.YAW)
    vrp, vpn, vup = c.view_vectors()
    assert math.isclose(vpn[0], 1.0) and math.isclose(vup[1], 1.0)
    c.reset_window()
    assert c.view_vectors() == ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (-0.0, 1.0, 0.0))
    assert (c.window.width, c.window.height) == (200, 200)


def test_default_roll_is_the_1_3_window_rotation():
    c = Controller()
    c.rotate_window(90)  # roll by default
    _, vpn, vup = c.view_vectors()
    assert vpn == (0.0, 0.0, 1.0)
    assert math.isclose(vup[0], -1.0) and math.isclose(vup[1], 0.0, abs_tol=1e-12)
