"""SCN -> viewport transform: normalized coordinates to screen pixels.

Pure function. It receives a point already in the normalized [-1, 1] x [-1, 1]
square (see `domain.normalization`) and maps it to pixel coordinates. It never
calls Qt.

Subcanvas (a debugging aid for clipping): the normalized square maps into an
inner rectangle inset from the widget edges by `margin` pixels -- the
*subcanvas*. The band between the subcanvas and the widget edge is deliberately
kept as extra drawable room: the mapping is linear, so a normalized coordinate
with |value| > 1 (i.e. outside the window) lands *outside* the subcanvas but
still inside the widget, becoming visible in that margin. Once clipping arrives
(trabalho 1.4) it will trim exactly at the subcanvas border, and that geometry
will visibly disappear from the margin -- proof the clip works. With margin 0
the subcanvas is the whole widget (the trabalho 1.1-1.3 behaviour).

Anti-distortion (spec requirement: a square stays a square): the [-1, 1] square
is fit isotropically into the subcanvas -- the same scale on x and y, centered
with margins when the subcanvas is not itself square. The y axis is inverted
because screen y grows downward.
"""

from __future__ import annotations

from .geometry import Point

# The normalized square spans 2 units on each axis: [-1, 1].
_SCN_SPAN = 2.0


class ViewportTransform:
    def __init__(self, vp_width: float, vp_height: float, margin: float = 0.0) -> None:
        self.vp_width = vp_width
        self.vp_height = vp_height
        # Pixel inset of the subcanvas from every widget edge. 0 => the
        # subcanvas fills the widget (no visible border).
        self.margin = margin

    def _inner_size(self) -> tuple[float, float]:
        """Width/height of the subcanvas (widget minus the margin on each side)."""
        return (
            max(self.vp_width - 2 * self.margin, 0.0),
            max(self.vp_height - 2 * self.margin, 0.0),
        )

    def _scale(self) -> float:
        """Isotropic scale fitting the [-1, 1] square inside the subcanvas."""
        inner_w, inner_h = self._inner_size()
        return min(inner_w, inner_h) / _SCN_SPAN

    def pixels_per_scn_unit(self) -> float:
        """Public: pixels covered by one SCN unit, identical on both axes.

        The single source of truth for how SCN maps to pixels. Panning must use
        this same isotropic scale, or a drag moves the world by a different
        amount than it is drawn (the bug where geometry drifts off a non-square
        widget and clips against the fitted square).
        """
        return self._scale()

    def subcanvas_rect(self) -> tuple[float, float, float, float]:
        """The subcanvas in pixels as (x0, y0, x1, y1) -- where SCN [-1,1] lands.

        This is the rectangle the GUI draws as the clip-boundary border and the
        exact box clipping will trim against.
        """
        scale = self._scale()
        used = _SCN_SPAN * scale
        x0 = (self.vp_width - used) / 2
        y0 = (self.vp_height - used) / 2
        return (x0, y0, x0 + used, y0 + used)

    def apply(self, point: Point) -> tuple[float, float]:
        """Map a normalized (SCN) point to (px, py) pixel coordinates.

        Linear, so points inside [-1, 1] land inside the subcanvas and points
        outside it extrapolate into the margin.
        """
        scale = self._scale()
        x0, y0, _, _ = self.subcanvas_rect()
        px = x0 + (point[0] + 1.0) * scale
        py = y0 + (1.0 - point[1]) * scale  # invert y
        return (px, py)
