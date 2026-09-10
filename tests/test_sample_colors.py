"""Sample palette resolution (_color_for)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from gui.main_window import _color_for  # noqa: E402

_DEFAULT = (10, 20, 30)


def test_exact_object_override_wins():
    assert _color_for("roof", _DEFAULT) == (178, 34, 34)


def test_unknown_name_falls_back_to_sample_default():
    assert _color_for("body", _DEFAULT) == _DEFAULT


def test_collision_suffix_is_stripped_to_match_palette():
    # An appended duplicate ("roof_2") keeps the roof colour.
    assert _color_for("roof_2", _DEFAULT) == (178, 34, 34)


def test_petal_keeps_default_even_with_numeric_suffix():
    # petal_1 has no override entry; it must take the scene default, and the
    # numeric suffix must not accidentally match some other palette key.
    assert _color_for("petal_1", _DEFAULT) == _DEFAULT
    assert _color_for("petal_1_2", _DEFAULT) == _DEFAULT
