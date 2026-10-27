"""Bicubic Bézier surfaces via blending functions (trabalho 1.9).

Checks the patch math (Q(s,t) = S . M_B . G . M_B^T . T^T) against hand-computed
values, the sampling grid, and the BezierSurface object built from patches.
"""

import pytest

from domain.curves import sample_curve
from domain.geometry import Point
from domain.objects import BezierSurface, ObjectType
from domain.surfaces import patch_point, sample_patch
from domain.transforms import translation

# Dataset 1 of the class exercise "Plotagem de Superfície Bézier Bicúbica": x
# follows the row, y the column, and the four inner points rise to z = 100.
_DATASET_1 = [
    [Point(0, 0, 0), Point(0, 100, 0), Point(0, 200, 0), Point(0, 300, 0)],
    [Point(100, 0, 0), Point(100, 100, 100), Point(100, 200, 100), Point(100, 300, 0)],
    [Point(200, 0, 0), Point(200, 100, 100), Point(200, 200, 100), Point(200, 300, 0)],
    [Point(300, 0, 0), Point(300, 100, 0), Point(300, 200, 0), Point(300, 300, 0)],
]


def test_patch_passes_through_its_four_corner_control_points():
    # Like a Bézier curve at its ends, a patch interpolates P11, P14, P41 and
    # P44 only; the 12 other control points just pull the surface.
    assert patch_point(_DATASET_1, 0, 0) == Point(0, 0, 0)
    assert patch_point(_DATASET_1, 0, 1) == Point(0, 300, 0)
    assert patch_point(_DATASET_1, 1, 0) == Point(300, 0, 0)
    assert patch_point(_DATASET_1, 1, 1) == Point(300, 300, 0)


def test_center_of_dataset_1_matches_the_hand_computed_value():
    # At s = t = 0.5 both weight rows are [1, 3, 3, 1] / 8, so
    # x = y = (0 + 3*100 + 3*200 + 300) / 8 = 150, and the raised inner points
    # give z = 100 * (3/8 + 3/8)^2 = 56.25.
    assert patch_point(_DATASET_1, 0.5, 0.5).coords == pytest.approx((150, 150, 56.25))


def _flat(points):
    return [component for point in points for component in point.coords]


def test_grid_edges_are_the_bezier_curves_of_the_edge_control_points():
    # At s = 0 the patch reduces to the cubic Bézier curve of its first row of
    # control points, at t = 0 to that of its first column: the grid's edges
    # are exactly what trabalho 1.5 samples.
    grid = sample_patch(_DATASET_1, steps=5)
    assert len(grid) == 6 and all(len(row) == 6 for row in grid)
    first_row = sample_curve(_DATASET_1[0], steps_per_segment=5)
    first_column = sample_curve([row[0] for row in _DATASET_1], steps_per_segment=5)
    assert _flat(grid[0]) == pytest.approx(_flat(first_row))
    assert _flat([row[0] for row in grid]) == pytest.approx(_flat(first_column))


def test_sampling_needs_at_least_one_step():
    with pytest.raises(ValueError):
        sample_patch(_DATASET_1, steps=0)


# --- the surface object: a list of patches ----------------------------------


def _flat_patch(xs):
    """A flat 4x4 patch on z = 0: one row of control points per x, y = 0..3."""
    return [[Point(x, y, 0) for y in range(4)] for x in xs]


def test_surface_draws_each_patch_as_a_mesh_of_grid_curves():
    # An (n+1) x (n+1) grid has n+1 rows and n+1 columns of n segments each.
    n = BezierSurface.STEPS_PER_PATCH
    one = BezierSurface("s", [_DATASET_1])
    two = BezierSurface("s", [_DATASET_1, _flat_patch((300, 400, 500, 600))])
    assert one.type is ObjectType.SURFACE
    assert len(one.to_segments()) == 2 * n * (n + 1)
    assert len(two.to_segments()) == 2 * 2 * n * (n + 1)
    # The mesh runs through the corners, where the patch meets its control net.
    endpoints = {point.coords for segment in one.to_segments() for point in segment}
    for corner in ((0, 0, 0), (0, 300, 0), (300, 0, 0), (300, 300, 0)):
        assert corner in endpoints


def test_from_rows_takes_the_typed_rows_four_per_patch():
    surface = BezierSurface.from_rows("s", _DATASET_1 + _flat_patch((300, 400, 500, 600)))
    assert surface.patches == [_DATASET_1, _flat_patch((300, 400, 500, 600))]


def test_from_rows_rejects_an_incomplete_patch():
    with pytest.raises(ValueError):
        BezierSurface.from_rows("s", [])
    with pytest.raises(ValueError):
        BezierSurface.from_rows("s", _DATASET_1 + _DATASET_1[:1])  # 5 rows
    with pytest.raises(ValueError):
        BezierSurface.from_rows("s", [_DATASET_1[0][:3]] + _DATASET_1[1:])  # a 3-point row


def test_transform_moves_every_patch():
    surface = BezierSurface("s", [_DATASET_1, _flat_patch((300, 400, 500, 600))])
    surface.transform(translation(0, 0, 10))
    assert surface.patches[0][1][1] == Point(100, 100, 110)
    assert surface.patches[1][3][3] == Point(600, 3, 10)


def test_center_counts_a_shared_border_row_once():
    # Two patches sharing the row x = 3: 28 distinct control points, not 32.
    # Over the distinct rows x = 0, 1, 2, 3, 4, 5, 13 the centroid x is 28/7 = 4;
    # counting the shared row twice would pull it to 31/8.
    surface = BezierSurface("s", [_flat_patch((0, 1, 2, 3)), _flat_patch((3, 4, 5, 13))])
    assert len(surface.vertices()) == 28
    assert surface.center() == Point(4, 1.5, 0)
