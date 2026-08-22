"""Application controller: the seam between GUI and domain.

Holds the world state (display file + window) and runs the render pipeline. It
touches no pixels and imports no Qt: the GUI hands it intent (add an object,
pan, zoom) and receives neutral draw commands back.
"""

from __future__ import annotations

from domain.display_file import DisplayFile
from domain.geometry import Point
from domain.objects import GraphicObject, Line, ObjectType, Point2D, Wireframe
from domain.viewport import ViewportTransform
from domain.window import Window
from persistence.parser import parse_coordinates

from .render_pipeline import DrawCommand, render


class Controller:
    def __init__(self, window: Window | None = None) -> None:
        self.display_file = DisplayFile()
        self.window = window or Window(-100, -100, 100, 100)

    def add_object(self, name: str, object_type: ObjectType, raw_coordinates: str) -> GraphicObject:
        """Parse coordinates and add a new object of the requested type."""
        points = parse_coordinates(raw_coordinates)
        obj = self._build(name, object_type, points)
        self.display_file.add(obj)
        return obj

    @staticmethod
    def _build(name: str, object_type: ObjectType, points: list[Point]) -> GraphicObject:
        if object_type is ObjectType.POINT:
            if len(points) != 1:
                raise ValueError("a point needs exactly one coordinate")
            return Point2D(name, points[0])
        if object_type is ObjectType.LINE:
            if len(points) != 2:
                raise ValueError("a line needs exactly two coordinates")
            return Line(name, points[0], points[1])
        if object_type is ObjectType.WIREFRAME:
            return Wireframe(name, points)
        raise ValueError(f"unknown object type: {object_type}")

    def pan(self, dx: float, dy: float) -> None:
        self.window.pan(dx, dy)

    def zoom(self, factor: float) -> None:
        self.window.zoom(factor)

    def render(self, viewport_width: float, viewport_height: float) -> list[DrawCommand]:
        viewport = ViewportTransform(self.window, viewport_width, viewport_height)
        return render(self.display_file, viewport)
