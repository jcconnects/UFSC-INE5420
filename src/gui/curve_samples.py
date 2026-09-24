"""Built-in Bézier curve samples for the Samples menu (trabalho 1.5).

Curves live in code, not in the .obj files: the p/l subset of Wavefront .obj the
project writes cannot express control points, and curves are skipped on export
(see persistence.obj_descriptor). So the demo curves are small control-point
literals here instead, mirroring how the .obj scenes are shipped.

Each sample is a CurveSample: a name, its flat control-point list (4, 7, 10, ...
points -- four per first segment, three per extra, sharing the join point for at
least G(0) continuity), and an RGB paint colour applied at load time. The main
window turns the control points into the mandated "(x1,y1),(x2,y2),..." string
and adds the curve through the controller, exactly like a typed-in curve.
"""

from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]
Coordinate = tuple[float, float]


@dataclass(frozen=True)
class CurveSample:
    name: str
    control_points: tuple[Coordinate, ...]
    color: Color

    def as_input_string(self) -> str:
        """The control points as the spec's `(x1,y1),(x2,y2),...` input string."""
        return ",".join(f"({x},{y})" for x, y in self.control_points)


# A single cubic segment: gentle arch. Shows P1/P4 on the curve, P2/P3 pulling.
_ARCH = CurveSample(
    name="curve_arch",
    control_points=((-60, -20), (-20, 60), (20, 60), (60, -20)),
    color=(218, 165, 32),  # goldenrod
)

# Two segments sharing their joint: an S/wave. Demonstrates G(0) chaining.
_WAVE = CurveSample(
    name="curve_wave",
    control_points=(
        (-80, 0), (-50, 60), (-20, 60), (0, 0),   # segment 1
        (20, -60), (50, -60), (80, 0),            # segment 2 (shares (0,0))
    ),
    color=(30, 144, 255),  # dodger blue
)

# A self-intersecting loop from one segment with crossed control legs.
_LOOP = CurveSample(
    name="curve_loop",
    control_points=((-30, -40), (70, 50), (-70, 50), (30, -40)),
    color=(219, 68, 130),  # rose
)

# Four segments approximating a full circle (radius ~60). The classic Bézier
# circle: control handles at k = 0.5523 * r from each axis crossing. The chain
# closes back on its first point, so it reads as a smooth ring.
_K = 0.5523 * 60
_R = 60.0
_CIRCLE = CurveSample(
    name="curve_circle",
    control_points=(
        (_R, 0), (_R, _K), (_K, _R), (0, _R),        # quadrant 1
        (-_K, _R), (-_R, _K), (-_R, 0),              # quadrant 2
        (-_R, -_K), (-_K, -_R), (0, -_R),            # quadrant 3
        (_K, -_R), (_R, -_K), (_R, 0),               # quadrant 4 (back to start)
    ),
    color=(120, 200, 120),  # soft green
)

# A heart from two mirrored segments meeting at the bottom tip and the top dip.
_HEART = CurveSample(
    name="curve_heart",
    control_points=(
        (0, 30), (50, 75), (75, 10), (0, -50),       # right lobe down to tip
        (-75, 10), (-50, 75), (0, 30),               # left lobe back to top (shares tip & top)
    ),
    color=(214, 40, 60),  # red
)


CURVE_SAMPLES: tuple[CurveSample, ...] = (_ARCH, _WAVE, _LOOP, _CIRCLE, _HEART)
