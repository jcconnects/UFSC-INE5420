"""Graphic objects stored in the display file.

The hierarchy the spec implies: Point / Line / Wireframe. It only grows in
later trabalhos (Curve2D in 1.5/1.6, Surface in 1.9/1.10).

Every object implements `to_segments()`, which decomposes it into line
segments. This is the guarantee that keeps the renderer trivial forever: the
GUI only ever draws points and lines (a hard spec requirement), so wireframes,
curves, surfaces and projected 3D objects all funnel through this one method.
Objects hold *world* coordinates and know nothing about the screen or window.

`Point2D`'s name is a historical label for the single-point object, not a
dimension claim: its coordinates are dimension-agnostic (see geometry.Point).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from .geometry import Point, transform_point


class ObjectType(Enum):
    POINT = "point"
    LINE = "line"
    WIREFRAME = "wireframe"


Segment = tuple[Point, Point]

# RGB colour in the 0-255 range. Trabalho 1.2 lets the user pick a paint colour
# per object at creation; it colours only the lines/borders (polygons stay
# unfilled). RGB is the standard the spec wants for later .obj I/O.
Color = tuple[int, int, int]
BLACK: Color = (0, 0, 0)


class GraphicObject(ABC):
    """Base for anything the display file can hold."""

    def __init__(self, name: str, coordinates: list[Point], color: Color = BLACK) -> None:
        self.name = name
        self.coordinates = coordinates
        self.color = color

    @property
    @abstractmethod
    def type(self) -> ObjectType:
        ...

    @abstractmethod
    def to_segments(self) -> list[Segment]:
        """Decompose the object into line segments for drawing."""
        ...

    def center(self) -> Point:
        """Geometric center (centroid) of the object's vertices.

        Used from trabalho 1.2 on for scaling/rotation about the object center.
        """
        count = len(self.coordinates)
        dimension = self.coordinates[0].dimension
        sums = [0.0] * dimension
        for point in self.coordinates:
            for axis in range(dimension):
                sums[axis] += point[axis]
        return Point(*(component / count for component in sums))

    def transform(self, matrix) -> None:
        """Apply a homogeneous matrix in place to every vertex."""
        self.coordinates = [transform_point(matrix, point) for point in self.coordinates]


class Point2D(GraphicObject):  # noqa: N801 - domain name, not a dimension claim
    """A single drawable point. (Name kept generic; dimension lives in coords.)"""

    def __init__(self, name: str, position: Point, color: Color = BLACK) -> None:
        super().__init__(name, [position], color)

    @property
    def type(self) -> ObjectType:
        return ObjectType.POINT

    def to_segments(self) -> list[Segment]:
        # A point has no length; represent it as a degenerate segment so the
        # renderer can draw it with a single drawPoint call.
        p = self.coordinates[0]
        return [(p, p)]


class Line(GraphicObject):
    """A straight segment between exactly two points."""

    def __init__(self, name: str, start: Point, end: Point, color: Color = BLACK) -> None:
        super().__init__(name, [start, end], color)

    @property
    def type(self) -> ObjectType:
        return ObjectType.LINE

    def to_segments(self) -> list[Segment]:
        return [(self.coordinates[0], self.coordinates[1])]


class Wireframe(GraphicObject):
    """A polygon as a list of interconnected points (open polyline for now).

    Named Wireframe per the spec. Closes back to the first vertex when it has
    three or more points, matching a polygon; two points degenerate to a line.
    """

    def __init__(self, name: str, points: list[Point], color: Color = BLACK) -> None:
        if len(points) < 2:
            raise ValueError("a wireframe needs at least two points")
        super().__init__(name, points, color)

    @property
    def type(self) -> ObjectType:
        return ObjectType.WIREFRAME

    def to_segments(self) -> list[Segment]:
        pts = self.coordinates
        segments = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        if len(pts) >= 3:  # close the polygon
            segments.append((pts[-1], pts[0]))
        return segments
