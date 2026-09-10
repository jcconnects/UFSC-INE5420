"""Wavefront .obj read/write for the world (trabalho 1.3).

A `DescritorOBJ`-style module: it transcribes each graphic object to the .obj
format from its name, type, vertices and edges, and reads such a file back into
graphic objects. Only geometry is written -- name, vertices, connectivity --
keeping the file 100% standard .obj; per-object colour is not part of .obj
geometry and is not persisted (imported objects load with the default colour).

Mapping to .obj elements:
    Point2D    -> `p i`           (a single vertex)
    Line       -> `l i j`         (a polyline of two vertices)
    Wireframe  -> `l i j k ... i` (a closed polyline; repeats the first index)

Vertex indices are 1-based and global across the whole file, per the format.

Dimension note: the system is 2D until trabalho 1.7, so vertices are written as
`v x y 0` and read back as 2D points (the z column is accepted but dropped).
When 3D lands, `from_obj` starts keeping z; nothing else here needs to move.
"""

from __future__ import annotations

from typing import Iterable

from domain.geometry import Point
from domain.objects import GraphicObject, Line, ObjectType, Point2D, Wireframe

_HEADER = "# SGI - INE5420 world export (Wavefront .obj)"


def to_obj(objects: Iterable[GraphicObject]) -> str:
    """Serialize an iterable of graphic objects to a Wavefront .obj string."""
    lines: list[str] = [_HEADER]
    next_index = 1  # .obj vertex indices are 1-based and global.
    for obj in objects:
        first_index = next_index
        lines.append(f"o {obj.name}")
        for point in obj.coordinates:
            x = point[0]
            y = point[1] if point.dimension > 1 else 0.0
            z = point[2] if point.dimension > 2 else 0.0
            lines.append(f"v {x:g} {y:g} {z:g}")
        count = len(obj.coordinates)
        indices = list(range(first_index, first_index + count))
        lines.append(_element_line(obj, indices))
        next_index += count
    return "\n".join(lines) + "\n"


def _element_line(obj: GraphicObject, indices: list[int]) -> str:
    if obj.type is ObjectType.POINT:
        return "p " + " ".join(str(i) for i in indices)
    # Both Line and Wireframe are polylines. A wireframe of three or more
    # vertices is closed by repeating the first index, matching to_segments().
    ordered = list(indices)
    if obj.type is ObjectType.WIREFRAME and len(indices) >= 3:
        ordered.append(indices[0])
    return "l " + " ".join(str(i) for i in ordered)


def from_obj(text: str) -> list[GraphicObject]:
    """Parse a Wavefront .obj string into a list of graphic objects.

    Recognizes `o` (object name), `v` (vertex), `p` (point) and `l` (polyline).
    Object type is inferred from the element used and its vertex count.
    """
    vertices: list[Point] = []
    objects: list[GraphicObject] = []
    current_name: str | None = None
    unnamed = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        keyword, _, rest = line.partition(" ")
        rest = rest.strip()
        if keyword == "o":
            current_name = rest or None
        elif keyword == "v":
            coords = [float(token) for token in rest.split()]
            # 2D system: keep x, y; drop the z column (see module docstring).
            vertices.append(Point(coords[0], coords[1]))
        elif keyword in ("p", "l"):
            refs = [_resolve(int(token), len(vertices)) for token in rest.split()]
            name, current_name, unnamed = _name_for(current_name, unnamed)
            objects.append(_build(keyword, name, refs, vertices))
    return objects


def _resolve(index: int, count: int) -> int:
    """Map a 1-based .obj index (possibly negative/relative) to 0-based."""
    if index < 0:  # .obj allows indices relative to the end
        return count + index
    return index - 1


def _name_for(current: str | None, unnamed: int) -> tuple[str, None, int]:
    """Return (name, cleared-current, updated-unnamed-counter).

    A name is consumed by the element that follows its `o` line; subsequent
    elements without a fresh `o` get auto-generated names.
    """
    if current is not None:
        return current, None, unnamed
    unnamed += 1
    return f"object_{unnamed}", None, unnamed


def _build(keyword: str, name: str, refs: list[int], vertices: list[Point]) -> GraphicObject:
    points = [vertices[i] for i in refs]
    if keyword == "p":
        return Point2D(name, points[0])
    # keyword == "l": a closed polyline (first == last) with >= 3 distinct
    # vertices is a wireframe; two vertices are a line.
    if len(points) >= 2 and refs[0] == refs[-1]:
        points = points[:-1]  # drop the closing repeat
    if len(points) == 2:
        return Line(name, points[0], points[1])
    return Wireframe(name, points)
