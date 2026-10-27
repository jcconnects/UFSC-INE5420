"""Coordinate parsing in the spec-mandated `(x1,y1),(x2,y2),...` format."""

from domain.geometry import Point
from persistence.parser import parse_coordinates, parse_matrix


def test_parse_multiple_points():
    assert parse_coordinates("(0, 0),(10, 20),(30, 40)") == [
        Point(0, 0),
        Point(10, 20),
        Point(30, 40),
    ]


def test_parse_single_point_without_enclosing_list():
    assert parse_coordinates("(5, 7)") == [Point(5, 7)]


def test_parse_negative_and_float_coordinates():
    assert parse_coordinates("(-1.5, 2.25),(3, -4)") == [Point(-1.5, 2.25), Point(3, -4)]


def test_parse_3d_triples_for_future_trabalhos():
    assert parse_coordinates("(1, 2, 3),(4, 5, 6)") == [Point(1, 2, 3), Point(4, 5, 6)]


def test_parse_matrix_splits_rows_on_semicolons():
    # Trabalho 1.9: a surface's geometry matrix, typed row by row.
    assert parse_matrix("(1,2,3),(4,5,6);(7,8,9),(10,11,12)") == [
        [Point(1, 2, 3), Point(4, 5, 6)],
        [Point(7, 8, 9), Point(10, 11, 12)],
    ]


def test_parse_matrix_ignores_a_trailing_semicolon():
    assert parse_matrix("(1,2,3); (4,5,6);") == [[Point(1, 2, 3)], [Point(4, 5, 6)]]
