"""The controller in perspective (trabalho 1.8), end to end through the pipeline.

Covers the spec's requirements: a scene of 3D wireframe models in the display
file shown in perspective, a center of projection that moves (wide-angle to
telephoto), and a parallelepiped loaded from a .obj file. Clipping stays 2D.
"""

import math
from pathlib import Path

import pytest

from app.controller import Controller
from app.render_pipeline import DrawLine, DrawPoint
from domain.geometry import Point
from domain.objects import ObjectType
from domain.projection import ParallelProjection, PerspectiveProjection
from domain.window import WindowAxis

_SAMPLES_3D = Path(__file__).resolve().parents[1] / "samples" / "3d"

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


def _cube_in_perspective(cop_distance: float) -> Controller:
    controller = Controller()
    controller.add_object("cube", ObjectType.OBJECT3D, _CUBE)
    controller.set_projection(PerspectiveProjection(cop_distance))
    return controller


def _distinct_xs(commands) -> list[float]:
    """Distinct pixel x positions of the drawn line endpoints, ascending."""
    distinct: list[float] = []
    for x in sorted(x for command in commands for x in (command.x1, command.x2)):
        if not distinct or x - distinct[-1] > 1e-6:
            distinct.append(x)
    return distinct


def test_parallel_is_still_the_default():
    controller = Controller()
    assert controller.projection == ParallelProjection()
    assert controller.center_of_projection() is None
    assert controller.field_of_view() is None


def test_cube_in_perspective():
    controller = _cube_in_perspective(200)
    commands = controller.render(200, 200)
    # Head-on, the front face (150 from the COP) and the back face (250 from
    # it) are concentric squares, and the 4 depth edges converge toward the
    # center instead of collapsing to points as in the parallel view.
    assert len(commands) == 12
    assert all(isinstance(command, DrawLine) for command in commands)
    # 100 px per SCN unit: the front face spans +-50*200/150 px, the back +-40.
    assert _distinct_xs(commands) == pytest.approx([100 - 200 / 3, 60, 140, 100 + 200 / 3])
    # Projecting never touches the world.
    assert controller.display_file.get("cube").center() == Point(0, 0, 0)


def test_moving_the_cop_goes_from_wide_angle_to_telephoto():
    # The back face sits 100 behind the front one. From a short d it shrinks a
    # lot next to the front (wide-angle); from a long d hardly at all
    # (telephoto), nearing the parallel view where both faces coincide.
    ratios = []
    for d in (120, 200, 2000):
        commands = _cube_in_perspective(d).render(200, 200)
        left, back_left, back_right, right = _distinct_xs(commands)
        ratios.append((back_right - back_left) / (right - left))
        assert ratios[-1] == pytest.approx((d - 50) / (d + 50))
    assert ratios == sorted(ratios)


def test_edges_along_the_view_direction_meet_at_the_vanishing_point():
    controller = Controller()
    rails = "(-60,-40,0),(-60,-40,-500),(60,-40,0),(60,-40,-500),(30,70,50),(30,70,-300)"
    controller.add_object("rails", ObjectType.OBJECT3D, rails)
    controller.set_projection(PerspectiveProjection(200))
    commands = controller.render(200, 200)
    assert len(commands) == 3
    for command in commands:
        # Each line, extended, runs through the window center (100, 100).
        dx, dy = command.x2 - command.x1, command.y2 - command.y1
        cross = dx * (100 - command.y1) - dy * (100 - command.x1)
        assert cross == pytest.approx(0, abs=1e-6)


def test_cop_rides_with_the_window():
    controller = Controller()
    controller.set_projection(PerspectiveProjection(300))
    assert controller.center_of_projection() == Point(0, 0, 300)
    assert controller.field_of_view() == pytest.approx(2 * math.degrees(math.atan(100 / 300)))
    controller.rotate_window(90, WindowAxis.YAW)  # the window now faces +x
    cop = controller.center_of_projection()
    assert cop[0] == pytest.approx(300) and cop[2] == pytest.approx(0, abs=1e-9)
    controller.zoom(0.5)  # a smaller window spans a narrower field of view
    assert controller.field_of_view() == pytest.approx(2 * math.degrees(math.atan(50 / 300)))


def test_cop_inside_the_cube_still_clips_in_2d():
    # d = 30 puts the COP inside the cube, whose front face (z = 50) is now
    # behind it: that face is cut away, the depth edges are kept from the COP
    # on, and the 2D clip trims them at the window border.
    commands = _cube_in_perspective(30).render(200, 200)
    assert len(commands) == 8
    for command in commands:
        assert isinstance(command, DrawLine)
        for x, y in ((command.x1, command.y1), (command.x2, command.y2)):
            assert -1e-6 <= x <= 200 + 1e-6 and -1e-6 <= y <= 200 + 1e-6


@pytest.mark.skipif(not _SAMPLES_3D.is_dir(), reason="samples/3d not present")
def test_parallelepiped_from_an_obj_file_in_perspective():
    controller = Controller()
    [box] = controller.load_obj(str(_SAMPLES_3D / "parallelepiped.obj"))
    assert box.type is ObjectType.OBJECT3D
    controller.set_projection(PerspectiveProjection(200))
    commands = controller.render(200, 200)
    assert len(commands) == 12
    assert all(isinstance(command, DrawLine) for command in commands)
    # 96 x 32 x 32 box: its front face (z = 16) is drawn wider than its back.
    front, back = 48 * 200 / 184, 48 * 200 / 216
    expected = [100 - front, 100 - back, 100 + back, 100 + front]
    assert _distinct_xs(commands) == pytest.approx(expected)


@pytest.mark.skipif(not _SAMPLES_3D.is_dir(), reason="samples/3d not present")
def test_street_scene_of_3d_models_in_perspective():
    controller = Controller()
    objects = controller.load_obj(str(_SAMPLES_3D / "street.obj"))
    assert len(objects) >= 2
    assert all(obj.type is ObjectType.OBJECT3D for obj in objects)
    parallel = controller.render(400, 400)
    controller.set_projection(PerspectiveProjection(200))
    perspective = controller.render(400, 400)
    # Head-on, the parallel view flattens every edge along z (curbs, lane
    # marks, the buildings' sides) to a point; in perspective they are lines
    # converging on the vanishing point.
    assert any(isinstance(command, DrawPoint) for command in parallel)
    assert perspective
    assert all(isinstance(command, DrawLine) for command in perspective)
