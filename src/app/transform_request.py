"""Turning a user's list of transforms into one composed matrix.

The spec is explicit: the user adds every transform they want to a list, and
"the resulting transformation matrix is only computed after the user has
entered all of them." This module is that computation, kept in the app layer so
the GUI dialog only collects intent and the domain stays Qt-free.

Each requested transform is a small value object. `build_matrix` resolves the
whole list into a single homogeneous matrix, consulting the object's centroid
for the object-center scaling/rotation modes. Composition order is the list
order: geometry.compose applies the first step first.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from domain import transforms
from domain.geometry import Point, compose, identity
from domain.objects import GraphicObject


class Pivot(Enum):
    """Where a scaling or rotation is centered."""

    WORLD_ORIGIN = "world origin"
    OBJECT_CENTER = "object center"
    ARBITRARY_POINT = "arbitrary point"


@dataclass(frozen=True)
class Translate:
    dx: float
    dy: float

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        return transforms.translation(self.dx, self.dy)


@dataclass(frozen=True)
class Scale:
    sx: float
    sy: float
    # Scaling is centered on the object by default (the "natural" scaling the
    # spec asks for); an arbitrary point is allowed too.
    pivot: Pivot = Pivot.OBJECT_CENTER
    point: Point | None = None

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        center = _resolve_center(self.pivot, self.point, obj)
        return transforms.scaling_about(center, self.sx, self.sy)


@dataclass(frozen=True)
class Rotate:
    degrees: float
    pivot: Pivot = Pivot.OBJECT_CENTER
    point: Point | None = None

    def matrix(self, obj: GraphicObject) -> list[list[float]]:
        center = _resolve_center(self.pivot, self.point, obj)
        return transforms.rotation_about(center, math.radians(self.degrees))


TransformStep = Translate | Scale | Rotate


def _resolve_center(pivot: Pivot, point: Point | None, obj: GraphicObject) -> Point:
    if pivot is Pivot.WORLD_ORIGIN:
        return Point(*([0.0] * obj.center().dimension))
    if pivot is Pivot.OBJECT_CENTER:
        return obj.center()
    if pivot is Pivot.ARBITRARY_POINT:
        if point is None:
            raise ValueError("an arbitrary-point transform needs a point")
        return point
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
        return identity(obj.center().dimension + 1)
    matrices = [step.matrix(obj) for step in steps]
    return compose(*matrices)
