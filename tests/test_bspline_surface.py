"""Bicubic B-Spline surfaces drawn by Forward Differences (trabalho 1.10).

Checks the split of a control net into its 4x4 sub-matrices, the corrected
DrawSurfaceFwdDif against hand-computed values and against the direct sum of
the uniform B-Spline blending functions, and the BSplineSurface object.
"""

import pytest

from domain.bspline import sample_bspline
from domain.bspline_surface import patch_curves, submatrices
from domain.geometry import Point
from domain.objects import BSplineSurface, ObjectType
from domain.transforms import translation

# Dataset 1 of the class exercise "Plotagem de Superfície Bézier Bicúbica",
# which "Plotagem de uma Superfície B-Spline com Forward Differences" reuses: x
# follows the row, y the column, and the four inner points rise to z = 100.
_DATASET_1 = [
    [Point(0, 0, 0), Point(0, 100, 0), Point(0, 200, 0), Point(0, 300, 0)],
    [Point(100, 0, 0), Point(100, 100, 100), Point(100, 200, 100), Point(100, 300, 0)],
    [Point(200, 0, 0), Point(200, 100, 100), Point(200, 200, 100), Point(200, 300, 0)],
    [Point(300, 0, 0), Point(300, 100, 0), Point(300, 200, 0), Point(300, 300, 0)],
]


# No symmetry to hide behind: every axis varies with both indices, unevenly.
_IRREGULAR = [
    [Point(10 * i + j * j, 7 * j - 3 * i * i, (i - 2) * (j + 1) ** 2) for j in range(4)]
    for i in range(4)
]


def _weights(t):
    """The uniform cubic B-Spline blending functions, written out (not via M_BS)."""
    return [
        (1 - t) ** 3 / 6,
        (3 * t**3 - 6 * t**2 + 4) / 6,
        (-3 * t**3 + 3 * t**2 + 3 * t + 1) / 6,
        t**3 / 6,
    ]


def _direct(patch, s, t):
    """Q(s, t) as the sum of w_i(s) w_j(t) P_ij: the reference, no differences."""
    s_weights, t_weights = _weights(s), _weights(t)
    return tuple(
        sum(s_weights[i] * t_weights[j] * patch[i][j][axis] for i in range(4) for j in range(4))
        for axis in range(3)
    )


def _flat(points):
    return [component for point in points for component in point.coords]


def _net(rows, columns):
    """A control net whose point (i, j) is (i, j, 0): easy to locate in a window."""
    return [[Point(i, j, 0) for j in range(columns)] for i in range(rows)]


def test_a_4x4_net_is_a_single_patch():
    net = _net(4, 4)
    assert submatrices(net) == [net]


def test_submatrices_slide_a_4x4_window_row_by_row():
    # A 5 x 7 net has (5-3)(7-3) = 8 windows; window (i, j) takes rows i..i+3
    # and columns j..j+3.
    net = _net(5, 7)
    windows = submatrices(net)
    assert len(windows) == 8
    assert windows[1] == [row[1:5] for row in net[0:4]]
    assert windows[4] == [row[0:4] for row in net[1:5]]
    assert windows[-1] == [row[3:7] for row in net[1:5]]


def test_dataset_1_matches_the_hand_computed_values():
    # The uniform B-Spline weights are [1, 4, 1, 0] / 6 at 0, [1, 23, 23, 1] / 48
    # at 1/2 and [0, 1, 4, 1] / 6 at 1. So Q(0, 0) has x = y = (4*100 + 200) / 6
    # = 100 and z = 100 * (5/6)^2 = 625/9; Q(1/2, 1/2) has x = y = 150 and
    # z = 100 * (46/48)^2; Q(1, 1) has x = y = (100 + 4*200 + 300) / 6 = 200.
    curves = patch_curves(_DATASET_1, steps=4)
    assert len(curves) == 2 * 5 and all(len(curve) == 5 for curve in curves)
    first, middle, last = curves[0], curves[2], curves[4]  # s = 0, 1/2, 1
    assert first[0].coords == pytest.approx((100, 100, 625 / 9))
    assert middle[2].coords == pytest.approx((150, 150, 100 * (23 / 24) ** 2))
    # The last curve of constant s ends at Q(1, 1) only if every curve takes
    # exactly the n steps of its delta = 1/n (the book's error).
    assert last[-1].coords == pytest.approx((200, 200, 625 / 9))


def test_both_families_match_the_direct_sum_of_blending_functions():
    # Every point of both families, so the curves of constant t fail unless DD
    # is rebuilt after the curves of constant s consumed it (omitted step 3),
    # and both fail if C took M_BS where M_BS^T belongs.
    n = 5
    curves = patch_curves(_IRREGULAR, steps=n)
    constant_s, constant_t = curves[: n + 1], curves[n + 1 :]
    for a in range(n + 1):
        for b in range(n + 1):
            expected = _direct(_IRREGULAR, a / n, b / n)
            assert constant_s[a][b].coords == pytest.approx(expected, abs=1e-9)
            assert constant_t[b][a].coords == pytest.approx(expected, abs=1e-9)


def test_equal_rows_draw_the_bspline_curve_of_trabalho_1_6():
    # With every row alike, Q(s, t) no longer depends on s (the weights sum to
    # 1), so each curve of constant s is the B-Spline curve of that row.
    row = [Point(0, 0, 0), Point(10, 30, 5), Point(20, -10, 5), Point(30, 0, 0)]
    curves = patch_curves([row] * 4, steps=6)
    expected = _flat(sample_bspline(row, steps_per_segment=6))
    for curve in curves[:7]:
        assert _flat(curve) == pytest.approx(expected, abs=1e-9)


def test_neighbouring_patches_share_their_border_curve():
    # Windows (0, 0) and (0, 1) of a 4 x 5 net overlap in three columns: the
    # first patch's curve t = 1 is the second patch's curve t = 0.
    net = [[Point(10 * i, 10 * j, (i * j) % 3 * 5) for j in range(5)] for i in range(4)]
    left, right = (patch_curves(window, steps=4) for window in submatrices(net))
    assert _flat(left[-1]) == pytest.approx(_flat(right[5]), abs=1e-9)


def test_drawing_needs_at_least_one_step():
    with pytest.raises(ValueError):
        patch_curves(_DATASET_1, steps=0)


# --- the surface object: one control net, split into its sub-matrices -------


@pytest.mark.parametrize("rows, columns", [(3, 4), (4, 3), (21, 4), (4, 21)])
def test_the_control_net_is_4x4_to_20x20(rows, columns):
    with pytest.raises(ValueError):
        BSplineSurface("s", _net(rows, columns))
    assert len(BSplineSurface("s", _net(20, 20)).patches) == 17 * 17


def test_the_control_net_rejects_ragged_rows():
    net = _net(5, 5)
    net[2] = net[2][:4]
    with pytest.raises(ValueError):
        BSplineSurface("s", net)


def test_surface_draws_every_submatrix_as_a_mesh():
    # A 5 x 6 net is (5-3)(6-3) = 6 patches, each drawn as n+1 curves per
    # parameter of n segments: 2n(n+1) lines.
    n = BSplineSurface.STEPS_PER_PATCH
    surface = BSplineSurface("s", _net(5, 6))
    assert surface.type is ObjectType.BSPLINE_SURFACE
    assert surface.control_net == _net(5, 6)
    assert len(surface.patches) == 6
    assert len(surface.to_segments()) == 6 * 2 * n * (n + 1)


def test_transform_moves_the_whole_net():
    surface = BSplineSurface("s", _net(4, 5))
    surface.transform(translation(0, 0, 10))
    assert surface.control_net[3][4] == Point(3, 4, 10)
    assert surface.center() == Point(1.5, 2, 10)
