"""Coordinate input parsing.

The spec fixes the input format `(x1, y1),(x2, y2),...` and even the parsing
directive: `pontos = list(eval(input_string))`. `eval` is confined to this one
module so the rest of the code stays clean; it also makes it trivial to swap in
a safe parser later if allowed. The format naturally extends to a third
coordinate for 3D (trabalho 1.7).
"""

from __future__ import annotations

from domain.geometry import Point


def parse_coordinates(text: str) -> list[Point]:
    """Parse `(x1,y1),(x2,y2),...` (or 3D triples) into a list of points."""
    raw = eval(text)  # noqa: S307 - format and directive mandated by the spec
    # A single tuple `(x, y)` evaluates without an enclosing list; normalize it.
    if raw and not isinstance(raw[0], (tuple, list)):
        raw = [raw]
    points = list(raw)
    if not points:
        raise ValueError("no coordinates parsed")
    return [Point(*tuple(component for component in p)) for p in points]
