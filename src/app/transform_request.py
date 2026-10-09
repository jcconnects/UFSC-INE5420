"""Turning a user's list of transforms into one composed matrix.

The spec is explicit: the user adds every transform they want to a list, and
"the resulting transformation matrix is only computed after the user has
entered all of them." This module is that computation, kept in the app layer so
the GUI dialog only collects intent and the domain stays Qt-free.

Each requested transform is a small value object. `build_matrix` resolves the
whole list into a single homogeneous matrix, consulting the object's centroid
for the object-center scaling/rotation modes. Composition order is the list
order: geometry.compose applies the first step first.

Trabalho 1.7 makes the steps 3D: translation and scaling gain a z component and
a rotation turns about an axis -- x, y, z or any direction -- passing through
the pivot. The matrix still follows the object's dimension, so a planar (2D)
object gets the 1.2 matrices (its z components are ignored and it can only
rotate about z), while the 3D world the GUI builds gets 4x4 ones.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from domain import transforms
from domain.geometry import Point, Vector, compose, identity
from domain.objects import GraphicObject

# Rotation axis directions. Z is the default: the plane rotation of 1.2.
X_AXIS: Vector = (1.0, 0.0, 0.0)
Y_AXIS: Vector = (0.0, 1.0, 0.0)
Z_AXIS: Vector = (0.0, 0.0, 1.0)


class Pivot(Enum):
    """Where a scaling or rotation is centered."""

    WORLD_ORIGIN = "world origin"
    OBJECT_CENTER = "object center"
    ARBITRARY_POINT = "arbitrary point"


@dataclass(frozen=True)
class Translate:
    dx: float
    dy: float
    dz: float = 0.0

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        deltas = (self.dx, self.dy, self.dz)[: obj.dimension]
        return transforms.translation(*deltas)


@dataclass(frozen=True)
class Scale:
    sx: float
    sy: float
    sz: float = 1.0
    # Scaling is centered on the object by default (the "natural" scaling the
    # spec asks for); an arbitrary point is allowed too.
    pivot: Pivot = Pivot.OBJECT_CENTER
    point: Point | None = None

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        center = _resolve_center(self.pivot, self.point, obj)
        factors = (self.sx, self.sy, self.sz)[: obj.dimension]
        return transforms.scaling_about(center, *factors)


@dataclass(frozen=True)
class Rotate:
    degrees: float
    pivot: Pivot = Pivot.OBJECT_CENTER
    point: Point | None = None
    # Direction of the rotation axis, which passes through the pivot. A
    # principal axis gives the basic rotations; any other direction is the
    # rotation about an arbitrary axis trabalho 1.7 asks for.
    axis: Vector = Z_AXIS

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        center = _resolve_center(self.pivot, self.point, obj)
        angle = math.radians(self.degrees)
        if obj.dimension == 2:
            if self.axis != Z_AXIS:
                raise ValueError("a planar (2D) object can only rotate about the z axis")
            return transforms.rotation_about(center, angle)
        return transforms.rotation_about_axis(center, self.axis, angle)


TransformStep = Translate | Scale | Rotate


def _resolve_center(pivot: Pivot, point: Point | None, obj: GraphicObject) -> Point:
    if pivot is Pivot.WORLD_ORIGIN:
        return Point(*([0.0] * obj.dimension))
    if pivot is Pivot.OBJECT_CENTER:
        return obj.center()
    if pivot is Pivot.ARBITRARY_POINT:
        if point is None:
            raise ValueError("an arbitrary-point transform needs a point")
        # Match the object: a 3D pivot keeps x, y for a planar object, a planar
        # pivot sits on z = 0 for a 3D one.
        return Point(*point.coords[: obj.dimension]).lifted(obj.dimension)
    raise ValueError(f"unknown pivot: {pivot}")


def build_matrix(steps: list[TransformStep], obj: GraphicObject) -> list[list[float]]:
    """Compose an ordered list of requested transforms into one matrix.

    Empty list yields the identity (a harmless no-op). The whole list becomes a
    single matrix applied once -- the spec's model: "the matrix is only computed
    after the user has entered all transforms." So object-center pivots all use
    one snapshot of the centroid (the object's geometry as of now, before this
    batch is applied), not a centroid recomputed between queued steps.
    """
    if not steps:
        return identity(obj.dimension + 1)
    matrices = [step.matrix(obj) for step in steps]
    return compose(*matrices)
