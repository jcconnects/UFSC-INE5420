"""Dimension-agnostic homogeneous geometry.

A point is a homogeneous vector: 2D is (x, y, 1), 3D is (x, y, z, 1). The
dimension is the length of the coordinate tuple, never encoded in a type name.
This is seam #1 of the 2D->3D plan: promoting a point from 2D to 3D adds one
coordinate and one matrix row/column, with no renames anywhere.

Matrices are square (n x n) lists of rows. All functions here are pure.

Trabalho 1.7's Ponto3D is this same `Point` holding (x, y, z): the three basic
transforms are 4x4 matrices (domain.transforms) applied with `transformed`.
"""

from __future__ import annotations

import math
from typing import Sequence

Vector = tuple[float, ...]


class Point:
    """A point in homogeneous coordinates.

    `coords` holds the spatial components only (x, y[, z]); the trailing
    homogeneous 1 is implicit and appended when building the vector for a
    matrix product. `dimension` is len(coords).

    With three coordinates this is the spec's Ponto3D (trabalho 1.7): it takes
    the three basic transforms -- translation, scaling, rotation -- as 4x4
    homogeneous matrices through `transformed`.
    """

    __slots__ = ("coords",)

    def __init__(self, *coords: float) -> None:
        if not coords:
            raise ValueError("a point needs at least one coordinate")
        self.coords = tuple(float(c) for c in coords)

    @property
    def dimension(self) -> int:
        return len(self.coords)

    def homogeneous(self) -> tuple[float, ...]:
        """Spatial components plus the trailing homogeneous 1."""
        return self.coords + (1.0,)

    def transformed(self, matrix: Sequence[Sequence[float]]) -> Point:
        """This point after a (dim+1)x(dim+1) homogeneous matrix (a new Point)."""
        return transform_point(matrix, self)

    def lifted(self, dimension: int) -> Point:
        """The same point with zero-padded extra axes: (x, y) is (x, y, 0) in 3D.

        Since trabalho 1.7 the world is 3D, and planar input lands on z = 0.
        """
        if dimension < self.dimension:
            raise ValueError(f"cannot lift a {self.dimension}D point to {dimension}D")
        return Point(*self.coords, *([0.0] * (dimension - self.dimension)))

    def __iter__(self):
        return iter(self.coords)

    def __getitem__(self, index: int) -> float:
        return self.coords[index]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point) and self.coords == other.coords

    def __repr__(self) -> str:
        return f"Point{self.coords}"


def centroid(points: Sequence[Point]) -> Point:
    """Geometric center (average) of a non-empty list of same-dimension points."""
    count = len(points)
    dimension = points[0].dimension
    return Point(*(sum(point[axis] for point in points) / count for axis in range(dimension)))


# --- direction vectors ------------------------------------------------------
# Plain tuples, not Points: a direction has no position, so it must never pick
# up a translation. Used for the 3D window's VPN/VUP basis (trabalho 1.7).


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: Vector, b: Vector) -> Vector:
    """3D cross product a x b (right-handed)."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalized(vector: Vector) -> Vector:
    """Unit vector with the same direction. Rejects the zero vector."""
    length = math.sqrt(dot(vector, vector))
    if length == 0:
        raise ValueError("a direction needs a nonzero vector")
    return tuple(component / length for component in vector)


def identity(size: int) -> list[list[float]]:
    """Identity matrix of the given size (size == homogeneous dimension)."""
    return [[1.0 if r == c else 0.0 for c in range(size)] for r in range(size)]


def multiply(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> list[list[float]]:
    """Matrix product a * b."""
    rows, inner, cols = len(a), len(b), len(b[0])
    if len(a[0]) != inner:
        raise ValueError("incompatible matrix shapes")
    return [
        [sum(a[r][k] * b[k][c] for k in range(inner)) for c in range(cols)]
        for r in range(rows)
    ]


def compose(*matrices: Sequence[Sequence[float]]) -> list[list[float]]:
    """Compose transforms left-to-right: compose(A, B) applies A then B."""
    if not matrices:
        raise ValueError("compose needs at least one matrix")
    result = [list(row) for row in matrices[0]]
    for m in matrices[1:]:
        result = multiply(m, result)
    return result


def transform_point(matrix: Sequence[Sequence[float]], point: Point) -> Point:
    """Apply a (dim+1)x(dim+1) homogeneous matrix to a point."""
    vector = point.homogeneous()
    if len(matrix) != len(vector):
        raise ValueError("matrix size does not match point dimension")
    result = [sum(matrix[r][c] * vector[c] for c in range(len(vector))) for r in range(len(matrix))]
    w = result[-1]
    spatial = result[:-1]
    if w not in (0.0, 1.0):  # perspective divide, ready for trabalho 1.8
        spatial = [component / w for component in spatial]
    return Point(*spatial)
