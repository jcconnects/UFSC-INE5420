"""Application controller: the seam between GUI and domain.

Holds the world state (display file + window) and runs the render pipeline. It
touches no pixels and imports no Qt: the GUI hands it intent (add an object,
pan, zoom) and receives neutral draw commands back.

Since trabalho 1.7 the world is 3D: typed planar input `(x, y)` is lifted to
`(x, y, 0)`, so every object the GUI builds can take 3D transforms, and the
window navigates in space.
"""

from __future__ import annotations

import copy
import math

from domain import transforms
from domain.clipping import LineClipper
from domain.display_file import DisplayFile
from domain.geometry import Point
from domain.objects import (
    BLACK,
    BSpline,
    Color,
    Curve2D,
    GraphicObject,
    Line,
    Object3D,
    ObjectType,
    Point2D,
    Wireframe,
)
from domain.viewport import ViewportTransform
from domain.window import Window, WindowAxis
from persistence import obj_descriptor
from persistence.parser import parse_coordinates

from .render_pipeline import DrawCommand, render

# The world's dimension since trabalho 1.7. Planar input lands on z = 0.
WORLD_DIMENSION = 3


class Controller:
    def __init__(self, window: Window | None = None) -> None:
        self.display_file = DisplayFile()
        self.window = window or Window(-100, -100, 100, 100)
        # Snapshot of the starting view, restored by reset_window().
        self._home_window = copy.deepcopy(self.window)
        # Trabalho 1.4: the user-selected line-clipping technique. The GUI's radio
        # button flips this; the render pipeline reads it each frame.
        self.line_clipper = LineClipper.COHEN_SUTHERLAND

    def add_object(
        self,
        name: str,
        object_type: ObjectType,
        raw_coordinates: str,
        color: Color = BLACK,
        filled: bool = False,
    ) -> GraphicObject:
        """Parse coordinates and add a new object of the requested type.

        The world is 3D: `(x, y)` is read as `(x, y, 0)`, and `(x, y, z)` as is.
        """
        points = [point.lifted(WORLD_DIMENSION) for point in parse_coordinates(raw_coordinates)]
        obj = self._build(name, object_type, points, color, filled)
        self.display_file.add(obj)
        return obj

    @staticmethod
    def _build(
        name: str,
        object_type: ObjectType,
        points: list[Point],
        color: Color,
        filled: bool = False,
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
            return Wireframe(name, points, color, filled)
        if object_type is ObjectType.CURVE:
            return Curve2D(name, points, color)
        if object_type is ObjectType.BSPLINE:
            return BSpline(name, points, color)
        if object_type is ObjectType.OBJECT3D:
            return Object3D.from_points(name, points, color)
        raise ValueError(f"unknown object type: {object_type}")

    def set_line_clipper(self, clipper: LineClipper) -> None:
        """Choose which line-clipping technique the pipeline uses."""
        self.line_clipper = clipper

    def transform_object(self, name: str, matrix) -> GraphicObject:
        """Apply a homogeneous matrix to a named object via the generic engine.

        The single transform routine trabalho 1.2 requires: any matrix, any
        object. Callers compose the matrix (see `build_*` below) and hand it in.
        """
        return transforms.apply(matrix, self.display_file.get(name))

    def object_center(self, name: str) -> Point:
        """Centroid of a named object, for object-center scale/rotation."""
        return self.display_file.get(name).center()

    def pan(self, du: float, dv: float) -> None:
        """Pan along the window's own axes (respects the user's "up")."""
        self.window.pan(du, dv)

    def zoom(self, factor: float) -> None:
        self.window.zoom(factor)

    def rotate_window(self, degrees: float, axis: WindowAxis = WindowAxis.ROLL) -> None:
        """Rotate the window about one of its own axes, through its center (VRP).

        Roll (the default) is the 1.3 rotation about the VPN; pitch and yaw tilt
        and turn the view plane in 3D. The scene turns the opposite way.
        """
        self.window.rotate(math.radians(degrees), axis)

    def reset_window(self) -> None:
        """Restore the starting view: position, size and orientation."""
        self.window = copy.deepcopy(self._home_window)

    def view_vectors(self) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
        """The window's (VRP, VPN, VUP) in world coordinates, for display."""
        return (self.window.vrp.coords, self.window.vpn, self.window.vup)

    def save_obj(self, path: str) -> None:
        """Write the whole world to a Wavefront .obj file."""
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(obj_descriptor.to_obj(self.display_file))

    def load_obj(self, path: str, replace: bool = True) -> list[GraphicObject]:
        """Read objects from a .obj file into the world.

        replace=True (default) clears the world first; replace=False appends,
        renaming any object whose name collides with one already present.
        """
        with open(path, encoding="utf-8") as handle:
            objects = obj_descriptor.from_obj(handle.read())
        if replace:
            self.display_file.clear()
        for obj in objects:
            obj.name = self._unique_name(obj.name)
            self.display_file.add(obj)
        return objects

    def unique_name(self, name: str) -> str:
        """Public: a display-file name free of collisions (suffixes if taken).

        Used when adding a sample the user may drop more than once, so the second
        copy gets a fresh name instead of clashing.
        """
        return self._unique_name(name)

    def _unique_name(self, name: str) -> str:
        """A name not yet used in the display file (suffixes on collision)."""
        if name not in self.display_file:
            return name
        suffix = 2
        while f"{name}_{suffix}" in self.display_file:
            suffix += 1
        return f"{name}_{suffix}"

    def render(
        self, viewport_width: float, viewport_height: float, margin: float = 0.0
    ) -> list[DrawCommand]:
        viewport = ViewportTransform(viewport_width, viewport_height, margin)
        return render(self.display_file, self.window, viewport, self.line_clipper)

    def pan_world_per_pixel(
        self, viewport_width: float, viewport_height: float, margin: float = 0.0
    ) -> tuple[float, float]:
        """World units moved per screen pixel dragged, for (x, y).

        Uses the viewport's single isotropic SCN->pixel scale, so a drag pans the
        window by exactly as much as the scene is drawn. The two axes differ only
        by the window's own width/height (equal for a square window).
        """
        viewport = ViewportTransform(viewport_width, viewport_height, margin)
        scale = viewport.pixels_per_scn_unit()
        if scale == 0:
            return (0.0, 0.0)
        # window spans its width/height across SCN span 2, which spans 2*scale px.
        span_pixels = 2.0 * scale
        return (self.window.width / span_pixels, self.window.height / span_pixels)

    def subcanvas_rect(
        self, viewport_width: float, viewport_height: float, margin: float = 0.0
    ) -> tuple[float, float, float, float]:
        """Pixel bounds (x0, y0, x1, y1) of the subcanvas for the given size.

        The GUI draws this as the clip-boundary border; it is the box clipping
        will trim against (trabalho 1.4).
        """
        return ViewportTransform(viewport_width, viewport_height, margin).subcanvas_rect()
