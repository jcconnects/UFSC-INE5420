"""Wavefront .obj read/write for the world (trabalho 1.3, 3D since 1.7).

A `DescritorOBJ`-style module: it transcribes each graphic object to the .obj
format from its name, type, vertices and edges, and reads such a file back into
graphic objects. Only geometry is written -- name, vertices, connectivity --
keeping the file 100% standard .obj; per-object colour is not part of .obj
geometry and is not persisted (imported objects load with the default colour).

Mapping to .obj elements:
    Point2D    -> `p i`           (a single vertex)
    Line       -> `l i j`         (a polyline of two vertices)
    Wireframe  -> `l i j k ... i` (a closed polyline; repeats the first index)
    Object3D   -> `l i j` per segment, over its distinct vertices (1.7)

Vertex indices are 1-based and global across the whole file, per the format.
Vertices are written as `v x y z` and, since trabalho 1.7, read back in 3D
(planar objects sit on z = 0).

Reading groups elements by object (`o`), as the format intends. An object made
of exactly one `p` or `l` element keeps the 1.3 mapping (point, line or
wireframe), so 2D worlds round-trip unchanged; anything richer -- several
elements, or faces (`f`) as written by Blender -- is a 3D wireframe model
(Object3D) whose segments are the edges, each shared edge counted once.
"""

from __future__ import annotations

from typing import Iterable

from domain.geometry import Point
from domain.objects import GraphicObject, Line, Object3D, ObjectType, Point2D, Wireframe

_HEADER = "# SGI - INE5420 world export (Wavefront .obj)"

# .obj vertices carry x, y, z; the world is 3D since trabalho 1.7.
_VERTEX_DIMENSION = 3

# One parsed element: its keyword (p, l or f) and 0-based vertex references.
_Element = tuple[str, list[int]]


def to_obj(objects: Iterable[GraphicObject]) -> str:
    """Serialize an iterable of graphic objects to a Wavefront .obj string."""
    lines: list[str] = [_HEADER]
    next_index = 1  # .obj vertex indices are 1-based and global.
    for obj in objects:
        if obj.type in (ObjectType.CURVE, ObjectType.BSPLINE):
            # Bézier curves (1.5) and B-Splines (1.6) are defined by control
            # points, which the p/l subset of .obj used here cannot express
            # without the heavier curv/cstype extension. Rather than write
            # misleading polyline geometry (it would load back as a wireframe),
            # curves are skipped on export (consistent with colour/fill not
            # being persisted). Neither trabalho requires .obj for curves.
            continue
        lines.append(f"o {obj.name}")
        if obj.type is ObjectType.OBJECT3D:
            vertices, elements = _describe_object3d(obj, next_index)
        else:
            vertices = obj.coordinates
            indices = list(range(next_index, next_index + len(vertices)))
            elements = [_element_line(obj, indices)]
        lines.extend(_vertex_line(point) for point in vertices)
        lines.extend(elements)
        next_index += len(vertices)
    return "\n".join(lines) + "\n"


def _vertex_line(point: Point) -> str:
    x = point[0]
    y = point[1] if point.dimension > 1 else 0.0
    z = point[2] if point.dimension > 2 else 0.0
    return f"v {x:g} {y:g} {z:g}"


def _element_line(obj: GraphicObject, indices: list[int]) -> str:
    if obj.type is ObjectType.POINT:
        return "p " + " ".join(str(i) for i in indices)
    # Both Line and Wireframe are polylines. A wireframe of three or more
    # vertices is closed by repeating the first index, matching to_segments().
    ordered = list(indices)
    if obj.type is ObjectType.WIREFRAME and len(indices) >= 3:
        ordered.append(indices[0])
    return "l " + " ".join(str(i) for i in ordered)


def _describe_object3d(obj: Object3D, first_index: int) -> tuple[list[Point], list[str]]:
    """An Object3D's distinct vertices and one `l i j` line per segment.

    A corner shared by several segments is written once and referenced by
    index, as a modelling tool would write it.
    """
    vertices = obj.vertices()
    index_of = {point.coords: first_index + i for i, point in enumerate(vertices)}
    elements = [
        f"l {index_of[start.coords]} {index_of[end.coords]}" for start, end in obj.segments
    ]
    return vertices, elements


def from_obj(text: str) -> list[GraphicObject]:
    """Parse a Wavefront .obj string into a list of graphic objects.

    Recognizes `o` (object name), `v` (vertex), `p` (point), `l` (polyline) and
    `f` (face); everything else (normals, textures, materials) is ignored. Each
    object's type is inferred from its elements (see the module docstring).
    """
    vertices: list[Point] = []
    groups: list[tuple[str | None, list[_Element]]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        keyword, _, rest = line.partition(" ")
        rest = rest.strip()
        if keyword == "o":
            groups.append((rest or None, []))
        elif keyword == "v":
            coords = [float(token) for token in rest.split()]
            # x y z; a planar `v x y` sits on z = 0, an optional w is dropped.
            vertices.append(Point(*coords[:_VERTEX_DIMENSION]).lifted(_VERTEX_DIMENSION))
        elif keyword in ("p", "l", "f"):
            if not groups:  # elements before any `o` form one unnamed object
                groups.append((None, []))
            # A face token may be `v`, `v/vt`, `v//vn` or `v/vt/vn`: keep `v`.
            refs = [_resolve(int(token.split("/")[0]), len(vertices)) for token in rest.split()]
            groups[-1][1].append((keyword, refs))

    objects: list[GraphicObject] = []
    unnamed = 0
    for name, elements in groups:
        if not elements:
            continue
        if name is None:
            unnamed += 1
            name = f"object_{unnamed}"
        objects.append(_build(name, elements, vertices))
    return objects


def _resolve(index: int, count: int) -> int:
    """Map a 1-based .obj index (possibly negative/relative) to 0-based."""
    if index < 0:  # .obj allows indices relative to the end
        return count + index
    return index - 1


def _build(name: str, elements: list[_Element], vertices: list[Point]) -> GraphicObject:
    if len(elements) == 1 and elements[0][0] in ("p", "l"):
        keyword, refs = elements[0]
        return _build_planar(keyword, name, refs, vertices)
    return Object3D(name, _edges(elements, vertices))


def _build_planar(keyword: str, name: str, refs: list[int], vertices: list[Point]) -> GraphicObject:
    """The 1.3 mapping for an object made of one `p` or `l` element."""
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


def _edges(elements: list[_Element], vertices: list[Point]) -> list[tuple[Point, Point]]:
    """The distinct edges of an object's elements, as pairs of vertices.

    A polyline contributes each consecutive pair, a face its closed boundary
    loop, a point a degenerate edge. Faces of a closed mesh share every edge,
    so each undirected edge is kept once.
    """
    seen: set[tuple[int, int]] = set()
    edges: list[tuple[Point, Point]] = []
    for keyword, refs in elements:
        if keyword == "p":
            pairs = [(ref, ref) for ref in refs]
        else:
            pairs = list(zip(refs, refs[1:]))
            if keyword == "f" and len(refs) >= 3:
                pairs.append((refs[-1], refs[0]))
        for a, b in pairs:
            key = (min(a, b), max(a, b))
            if key not in seen:
                seen.add(key)
                edges.append((vertices[a], vertices[b]))
    return edges
