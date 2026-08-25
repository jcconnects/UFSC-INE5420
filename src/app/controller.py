"""Application controller: the seam between GUI and domain.

Holds the world state (display file + window) and runs the render pipeline. It
touches no pixels and imports no Qt: the GUI hands it intent (add an object,
pan, zoom) and receives neutral draw commands back.
"""

from __future__ import annotations

from domain import transforms
from domain.display_file import DisplayFile
from domain.geometry import Point, compose
from domain.objects import BLACK, Color, GraphicObject, Line, ObjectType, Point2D, Wireframe
from domain.viewport import ViewportTransform
from domain.window import Window
from persistence.parser import parse_coordinates

from .render_pipeline import DrawCommand, render


class Controller:
    def __init__(self, window: Window | None = None) -> None:
        self.display_file = DisplayFile()
        self.window = window or Window(-100, -100, 100, 100)

    def add_object(
        self,
        name: str,
        object_type: ObjectType,
        raw_coordinates: str,
        color: Color = BLACK,
    ) -> GraphicObject:
        """Parse coordinates and add a new object of the requested type."""
        points = parse_coordinates(raw_coordinates)
        obj = self._build(name, object_type, points, color)
        self.display_file.add(obj)
        return obj

    @staticmethod
    def _build(
        name: str, object_type: ObjectType, points: list[Point], color: Color
    ) -> GraphicObject:
        if object_type is ObjectType.POINT:
            if len(points) != 1:
                raise ValueError("a point needs exactly one coordinate")
            return Point2D(name, points[0], color)
        if object_type is ObjectType.LINE:
            if len(points) != 2:
                raise ValueError("a line needs exactly two coordinates")
            return Line(name, points[0], points[1], color)
        if object_type is ObjectType.WIREFRAME:
            return Wireframe(name, points, color)
        raise ValueError(f"unknown object type: {object_type}")

    def transform_object(self, name: str, matrix) -> GraphicObject:
        """Apply a homogeneous matrix to a named object via the generic engine.

        The single transform routine trabalho 1.2 requires: any matrix, any
        object. Callers compose the matrix (see `build_*` below) and hand it in.
        """
        return transforms.apply(matrix, self.display_file.get(name))

    def object_center(self, name: str) -> Point:
        """Centroid of a named object, for object-center scale/rotation."""
        return self.display_file.get(name).center()

    def pan(self, dx: float, dy: float) -> None:
        self.window.pan(dx, dy)

    def zoom(self, factor: float) -> None:
        self.window.zoom(factor)

    def render(self, viewport_width: float, viewport_height: float) -> list[DrawCommand]:
        viewport = ViewportTransform(self.window, viewport_width, viewport_height)
        return render(self.display_file, viewport)
