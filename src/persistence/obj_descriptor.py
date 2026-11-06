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
    BezierSurface -> `cstype bezier` and `deg 3 3`, then per patch
                  `surf 0 1 0 1` + its 16 control points, `parm u 0 1`,
                  `parm v 0 1`, `end` -- free-form .obj, over its distinct
                  control points (1.9)
    BSplineSurface -> `cstype bspline`, `deg 3 3`, then one `surf 3 n 3 m`
                  + its whole m x n control net row by row, `parm u 0 ... n+3`,
                  `parm v 0 ... m+3`, `end` (1.10)
    Curve2D    -> `cstype bezier`, `deg 3`, `curv 0 k` + the 3k+1 control
                  points of its k segments, `parm u 0 ... k`, `end` (1.10)
    BSpline    -> `cstype bspline`, `deg 3`, `curv 3 n` + its n control
                  points, `parm u 0 ... n+3`, `end` (1.10)

Vertex indices are 1-based and global across the whole file, per the format.
Vertices are written as `v x y z` and, since trabalho 1.7, read back in 3D
(planar objects sit on z = 0).

Reading groups elements by object (`o`), as the format intends. An object made
of exactly one `p` or `l` element keeps the 1.3 mapping (point, line or
wireframe), so 2D worlds round-trip unchanged; anything richer -- several
elements, or faces (`f`) as written by Blender -- is a 3D wireframe model
(Object3D) whose segments are the edges, each shared edge counted once. An
object made of `surf` elements is a BezierSurface, one patch per `surf` (1.9).
A B-Spline `surf` is a BSplineSurface, its rows sized by the `parm u` knot
count, and a `curv` is a Curve2D or a BSpline by its `cstype`; each of these
must be its object's only element (1.10).
"""

from __future__ import annotations

import re
from typing import Iterable

from domain import curves
from domain.geometry import Point
from domain.objects import (
    BezierSurface,
    BSpline,
    BSplineSurface,
    Curve2D,
    GraphicObject,
    Line,
    Object3D,
    ObjectType,
    Point2D,
    Wireframe,
)
from domain.surfaces import Patch

_HEADER = "# SGI - INE5420 world export (Wavefront .obj)"

# .obj vertices carry x, y, z; the world is 3D since trabalho 1.7.
_VERTEX_DIMENSION = 3

# One parsed element: its kind -- p, l, f, or a free-form bezier_surf,
# bspline_surf, bezier_curv or bspline_curv -- and 0-based vertex references.
_Element = tuple[str, list[int]]

# The free-form elements the SGI draws, by keyword, `cstype` and `deg`.
_FREE_FORM_KINDS = {
    ("surf", "bezier", "3 3"): "bezier_surf",
    ("surf", "bspline", "3 3"): "bspline_surf",
    ("curv", "bezier", "3"): "bezier_curv",
    ("curv", "bspline", "3"): "bspline_curv",
}

# Free-form kinds that hold a whole object on their own.
_SOLE_ELEMENT_KINDS = {"bspline_surf", "bezier_curv", "bspline_curv"}

# A `\` at the end of a line continues the statement on the next one.
_LINE_CONTINUATION = re.compile(r"\\[ \t]*\r?\n")


def to_obj(objects: Iterable[GraphicObject]) -> str:
    """Serialize an iterable of graphic objects to a Wavefront .obj string."""
    lines: list[str] = [_HEADER]
    next_index = 1  # .obj vertex indices are 1-based and global.
    for obj in objects:
        lines.append(f"o {obj.name}")
        if obj.type is ObjectType.OBJECT3D:
            vertices, elements = _describe_object3d(obj, next_index)
        elif obj.type is ObjectType.SURFACE:
            vertices, elements = _describe_surface(obj, next_index)
        elif obj.type is ObjectType.BSPLINE_SURFACE:
            vertices, elements = _describe_bspline_surface(obj, next_index)
        elif obj.type in (ObjectType.CURVE, ObjectType.BSPLINE):
            vertices, elements = _describe_curve(obj, next_index)
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


def _describe_surface(obj: BezierSurface, first_index: int) -> tuple[list[Point], list[str]]:
    """A surface's distinct control points and one free-form `surf` per patch.

    `cstype bezier` and `deg 3 3` set the basis once; each patch then lists its
    parameter ranges and its 16 control points row by row, closed by `end`.
    """
    vertices = obj.vertices()
    index_of = {point.coords: first_index + i for i, point in enumerate(vertices)}
    elements = ["cstype bezier", "deg 3 3"]
    for patch in obj.patches:
        refs = " ".join(str(index_of[point.coords]) for row in patch for point in row)
        elements += [f"surf 0 1 0 1 {refs}", "parm u 0 1", "parm v 0 1", "end"]
    return vertices, elements


def _describe_bspline_surface(
    obj: BSplineSurface, first_index: int
) -> tuple[list[Point], list[str]]:
    """A B-Spline surface as one free-form `surf` over its whole control net.

    The refs run row by row, u (the column) varying fastest. A cubic over n
    control points takes the n + 4 uniform knots 0..n+3 and spans [3, n], in
    each direction; the knot counts are what size the net on reading.
    """
    rows, columns = len(obj.control_net), obj.columns
    refs = " ".join(str(first_index + i) for i in range(rows * columns))
    return obj.coordinates, [
        "cstype bspline",
        "deg 3 3",
        f"surf 3 {columns} 3 {rows} {refs}",
        f"parm u {_knots(columns + 4)}",
        f"parm v {_knots(rows + 4)}",
        "end",
    ]


def _describe_curve(obj: GraphicObject, first_index: int) -> tuple[list[Point], list[str]]:
    """A Bézier chain or a B-Spline as one free-form `curv` over its control points.

    A chain of k segments spans [0, k], one parameter unit per segment; a
    cubic B-Spline over n points takes the uniform knots 0..n+3 and spans [3, n].
    """
    count = len(obj.coordinates)
    refs = " ".join(str(first_index + i) for i in range(count))
    if obj.type is ObjectType.CURVE:
        segments = curves.segment_count(count)
        return obj.coordinates, [
            "cstype bezier",
            "deg 3",
            f"curv 0 {segments} {refs}",
            f"parm u {_knots(segments + 1)}",
            "end",
        ]
    return obj.coordinates, [
        "cstype bspline",
        "deg 3",
        f"curv 3 {count} {refs}",
        f"parm u {_knots(count + 4)}",
        "end",
    ]


def _knots(count: int) -> str:
    """The uniform parameter values 0 1 ... count-1."""
    return " ".join(str(value) for value in range(count))


def from_obj(text: str) -> list[GraphicObject]:
    """Parse a Wavefront .obj string into a list of graphic objects.

    Recognizes `o` (object name), `v` (vertex), `p` (point), `l` (polyline),
    `f` (face), and the free-form `surf` (surface) and `curv` (curve), read
    under the `cstype` and `deg` in force, with the knot count of their
    `parm u`; everything else (normals, textures, materials, `end`) is
    ignored. Each object's type is inferred from its elements (see the module
    docstring).
    """
    vertices: list[Point] = []
    groups: list[tuple[str | None, list[_Element]]] = []
    # Free-form state: a `cstype` or `deg` holds for every `surf` and `curv` until changed.
    curve_type = degree = ""
    # Group index -> knot count of its last `parm u`.
    knots_u: dict[int, int] = {}

    for raw_line in _LINE_CONTINUATION.sub(" ", text).splitlines():
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
        elif keyword == "cstype":
            curve_type = rest
        elif keyword == "deg":
            degree = rest
        elif keyword == "parm":
            tokens = rest.split()
            # A cubic over n control points takes n + 4 knots, so the count
            # sizes a B-Spline surface's rows.
            # shortcut: knot values ignored (uniform basis), upgrade to Cox–de Boor
            # if non-uniform files must draw exactly.
            if tokens[:1] == ["u"] and groups:
                knots_u[len(groups) - 1] = len(tokens) - 1
        elif keyword in ("p", "l", "f", "surf", "curv"):
            tokens = rest.split()
            kind = keyword
            if keyword in ("surf", "curv"):
                kind = _free_form_kind(keyword, curve_type, degree)
                # Drop the parameter ranges: s0 s1 t0 t1 of a surf, u0 u1 of a curv.
                tokens = tokens[4 if keyword == "surf" else 2 :]
            if not groups:  # elements before any `o` form one unnamed object
                groups.append((None, []))
            # A face token may be `v`, `v/vt`, `v//vn` or `v/vt/vn`: keep `v`.
            refs = [_resolve(int(token.split("/")[0]), len(vertices)) for token in tokens]
            groups[-1][1].append((kind, refs))

    objects: list[GraphicObject] = []
    unnamed = 0
    for index, (name, elements) in enumerate(groups):
        if not elements:
            continue
        if name is None:
            unnamed += 1
            name = f"object_{unnamed}"
        objects.append(_build(name, elements, vertices, knots_u.get(index)))
    return objects


def _free_form_kind(keyword: str, curve_type: str, degree: str) -> str:
    """Tag a `surf` or `curv` by the `cstype` and `deg` in force (_FREE_FORM_KINDS).

    Only the cubic Bézier and B-Spline bases the SGI draws are read: `deg 3 3`
    for a surface, `deg 3` for a curve.
    """
    basis = " ".join(curve_type.split())
    kind = _FREE_FORM_KINDS.get((keyword, basis, " ".join(degree.split())))
    if kind is None:
        raise ValueError(
            f"only cubic Bézier or B-Spline {keyword} elements are supported (cstype "
            "bezier or bspline; deg 3 3 for a surf, deg 3 for a curv; got cstype "
            f"{curve_type!r}, deg {degree!r})"
        )
    return kind


def _resolve(index: int, count: int) -> int:
    """Map a 1-based .obj index (possibly negative/relative) to 0-based."""
    if index < 0:  # .obj allows indices relative to the end
        return count + index
    return index - 1


def _build(
    name: str, elements: list[_Element], vertices: list[Point], knots_u: int | None
) -> GraphicObject:
    kinds = {kind for kind, _ in elements}
    if "bezier_surf" in kinds:
        if kinds != {"bezier_surf"}:
            raise ValueError(f"object {name!r} mixes surface patches with other elements")
        return BezierSurface(name, [_patch(refs, vertices) for _, refs in elements])
    if kinds & _SOLE_ELEMENT_KINDS:
        if len(elements) != 1:
            raise ValueError(
                f"object {name!r} has {len(elements)} elements, but a B-Spline surface "
                "or a curve must be an object's only element"
            )
        [(kind, refs)] = elements
        points = [vertices[i] for i in refs]
        if kind == "bspline_surf":
            return BSplineSurface(name, _control_net(name, points, knots_u))
        return Curve2D(name, points) if kind == "bezier_curv" else BSpline(name, points)
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


def _patch(refs: list[int], vertices: list[Point]) -> Patch:
    """A `surf` element's control points in rows of 4.

    The format lists them u varying fastest, so each row holds one v. A `surf`
    without exactly 16 points fails the surface's 4x4 check.
    """
    points = [vertices[i] for i in refs]
    return [points[i : i + 4] for i in range(0, len(points), 4)]


def _control_net(name: str, points: list[Point], knots_u: int | None) -> list[list[Point]]:
    """A B-Spline `surf`'s control points in rows, sized by its `parm u`.

    A cubic over n control points takes n + 4 knots, and the format lists the
    points u varying fastest: each row is a run of `knots_u - 4` points.
    """
    if knots_u is None:
        raise ValueError(f"B-Spline surface {name!r} needs a `parm u` line to size its rows")
    columns = knots_u - 4
    if columns < 1 or len(points) % columns:
        raise ValueError(
            f"B-Spline surface {name!r}: {len(points)} control points do not fill rows "
            f"of {columns} (`parm u` lists {knots_u} knots, 4 more than a row's points)"
        )
    return [points[i : i + columns] for i in range(0, len(points), columns)]


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
