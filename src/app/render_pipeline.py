"""The render pipeline: the architectural spine of the whole SGI.

The pipeline is an ordered list of stages, not a monolithic render method. Each
trabalho *inserts a stage* rather than rewriting existing ones:

    1.1 (now):   [ to_segments, normalize(identity), viewport ]
    + 1.4:       [ to_segments, normalize, CLIP, viewport ]
    + 1.7/1.8:   [ to_segments, normalize, PROJECT, clip, viewport ]

Going from 2D to 3D is literally "insert the PROJECT stage" -- seam #2 of the
2D->3D plan. Nothing else in the pipeline changes.

The output is a list of neutral draw commands (DrawPoint / DrawLine). The GUI
executes those with drawPoint/drawLine only; it never learns the dimension of
the world, so a projected 3D cube arrives as the same DrawLines as a 2D square.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain import clipping
from domain.clipping import LineClipper
from domain.display_file import DisplayFile
from domain.normalization import to_scn
from domain.objects import BLACK, Color, GraphicObject, ObjectType
from domain.viewport import ViewportTransform
from domain.window import Window


@dataclass(frozen=True)
class DrawPoint:
    x: float
    y: float
    color: Color = BLACK


@dataclass(frozen=True)
class DrawLine:
    x1: float
    y1: float
    x2: float
    y2: float
    color: Color = BLACK


@dataclass(frozen=True)
class DrawPolygon:
    """A filled polygon (trabalho 1.4).

    Wireframe objects created as "filled" reach the GUI as this command so it can
    call the language's fill primitive. The vertices are already clipped and in
    pixels. Unfilled polygons still arrive as plain DrawLines, so the "only
    drawPoint/drawLine" rule holds everywhere except this one explicit fill case
    the 1.4 spec asks for.
    """

    points: tuple[tuple[float, float], ...] = field(default_factory=tuple)
    color: Color = BLACK


DrawCommand = DrawPoint | DrawLine | DrawPolygon


def render(
    display_file: DisplayFile,
    window: Window,
    viewport: ViewportTransform,
    line_clipper: LineClipper = LineClipper.COHEN_SUTHERLAND,
) -> list[DrawCommand]:
    """Run the pipeline and produce neutral draw commands.

    Stages, in order:
      1. to_segments  -- each object decomposes itself into world segments.
      2. normalize    -- map each endpoint world -> SCN (bakes in window
                         position/orientation; trabalho 1.3). SCN is computed
                         per frame here, so window rotation never mutates the
                         objects' world coordinates.
      3. CLIP         -- trim to the normalized [-1, 1] window (trabalho 1.4).
                         Points, lines and polygons each use their own technique;
                         line clipping honours the selected method.
      4. viewport     -- map each *surviving* SCN vertex to pixels.
      (project enters between normalize and clip in trabalho 1.7.)

    Clipping runs in SCN space, before the viewport, so the viewport transform is
    applied only to what the clip left behind -- the spec's requirement.
    """
    commands: list[DrawCommand] = []
    for obj in display_file:
        if obj.type is ObjectType.POINT:
            _clip_point_object(obj, window, viewport, commands)
        elif obj.type in (ObjectType.CURVE, ObjectType.BSPLINE):
            _clip_curve_object(obj, window, viewport, commands)
        elif obj.filled and obj.type is ObjectType.WIREFRAME:
            _clip_filled_polygon(obj, window, viewport, commands)
        else:
            _clip_line_object(obj, window, viewport, line_clipper, commands)
    return commands


def _clip_point_object(
    obj: GraphicObject, window: Window, viewport: ViewportTransform, out: list[DrawCommand]
) -> None:
    """Point clipping: keep the point only if it survives the clip window."""
    scn = to_scn(obj.coordinates[0], window)
    if clipping.clip_point(scn) is None:
        return
    px, py = viewport.apply(scn)
    out.append(DrawPoint(px, py, obj.color))


def _clip_curve_object(
    obj: GraphicObject, window: Window, viewport: ViewportTransform, out: list[DrawCommand]
) -> None:
    """Curve clipping by the method from the slides (5.6): point-clip the
    generated points. Shared by Bézier curves (1.5) and B-Splines (1.6) -- both
    expose generated_points(), so this branch is dimension- and curve-agnostic.

    The curve is sampled into points, each mapped to SCN and tested with point
    clipping. A drawn segment is kept only where both of its endpoints survive,
    so the curve is drawn "até onde quero" -- runs of consecutive in-window
    points become DrawLines, and the parts leaving the window simply stop. This
    is the incremental point clipping the slides describe, not segment clipping
    against the border.
    """
    scn_points = [to_scn(point, window) for point in obj.generated_points()]
    inside = [clipping.clip_point(p) is not None for p in scn_points]
    for i in range(len(scn_points) - 1):
        if not (inside[i] and inside[i + 1]):
            continue
        px1, py1 = viewport.apply(scn_points[i])
        px2, py2 = viewport.apply(scn_points[i + 1])
        out.append(DrawLine(px1, py1, px2, py2, obj.color))


def _clip_line_object(
    obj: GraphicObject,
    window: Window,
    viewport: ViewportTransform,
    line_clipper: LineClipper,
    out: list[DrawCommand],
) -> None:
    """Line clipping for each of an object's segments with the chosen technique."""
    for start, end in obj.to_segments():
        scn_start = to_scn(start, window)
        scn_end = to_scn(end, window)
        clipped = clipping.clip_line(scn_start, scn_end, line_clipper)
        if clipped is None:
            continue
        px1, py1 = viewport.apply(clipped[0])
        px2, py2 = viewport.apply(clipped[1])
        if px1 == px2 and py1 == py2:
            out.append(DrawPoint(px1, py1, obj.color))
        else:
            out.append(DrawLine(px1, py1, px2, py2, obj.color))


def _clip_filled_polygon(
    obj: GraphicObject, window: Window, viewport: ViewportTransform, out: list[DrawCommand]
) -> None:
    """Polygon clipping (Sutherland-Hodgman) for a filled wireframe."""
    scn_vertices = [to_scn(point, window) for point in obj.coordinates]
    clipped = clipping.sutherland_hodgman(scn_vertices)
    if len(clipped) < 3:  # nothing (or a degenerate sliver) left to fill
        return
    pixels = tuple(viewport.apply(vertex) for vertex in clipped)
    out.append(DrawPolygon(pixels, obj.color))
