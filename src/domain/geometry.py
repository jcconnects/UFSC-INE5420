"""Dimension-agnostic homogeneous geometry.

A point is a homogeneous vector: 2D is (x, y, 1), 3D is (x, y, z, 1). The
dimension is the length of the coordinate tuple, never encoded in a type name.
This is seam #1 of the 2D->3D plan: promoting a point from 2D to 3D adds one
coordinate and one matrix row/column, with no renames anywhere.

Matrices are square (n x n) lists of rows. All functions here are pure.
"""

from __future__ import annotations

from typing import Sequence


class Point:
    """A point in homogeneous coordinates.

    `coords` holds the spatial components only (x, y[, z]); the trailing
    homogeneous 1 is implicit and appended when building the vector for a
    matrix product. `dimension` is len(coords).
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

    def __iter__(self):
        return iter(self.coords)

    def __getitem__(self, index: int) -> float:
        return self.coords[index]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point) and self.coords == other.coords

    def __repr__(self) -> str:
        return f"Point{self.coords}"


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
