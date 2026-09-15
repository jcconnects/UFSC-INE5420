"""Built-in Bézier curve samples (trabalho 1.5).

Guards that every shipped curve sample is a valid Bézier chain and survives the
same path a typed-in curve takes: its `(x,y),...` string parses and builds a
Curve2D. A malformed literal here would only surface at menu-click time
otherwise.
"""

from domain.curves import segment_count
from domain.objects import Curve2D
from gui.curve_samples import CURVE_SAMPLES
from persistence.parser import parse_coordinates


def test_samples_exist():
    assert CURVE_SAMPLES


def test_sample_names_are_unique():
    names = [s.name for s in CURVE_SAMPLES]
    assert len(names) == len(set(names))


def test_every_sample_is_a_valid_chain_and_builds():
    for sample in CURVE_SAMPLES:
        points = parse_coordinates(sample.as_input_string())
        assert len(points) == len(sample.control_points)
        assert segment_count(len(points)) > 0, sample.name
        # Builds without raising and samples to a non-trivial polyline.
        curve = Curve2D(sample.name, points, sample.color)
        assert len(curve.generated_points()) > len(points)


def test_as_input_string_matches_spec_format():
    # (x1,y1),(x2,y2),... -- the mandated input format, re-parseable.
    sample = CURVE_SAMPLES[0]
    text = sample.as_input_string()
    assert text.startswith("(") and text.endswith(")")
    assert parse_coordinates(text)
