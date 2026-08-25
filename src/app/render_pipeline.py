"""The render pipeline: the architectural spine of the whole SGI.

The pipeline is an ordered list of stages, not a monolithic render method. Each
trabalho *inserts a stage* rather than rewriting existing ones:

    1.1 (now):   [ to_segments, normalize(identity), viewport ]
    + 1.4:       [ to_segments, normalize, CLIP, viewport ]
    + 1.7/1.8:   [ to_segments, normalize, PROJECT, clip, viewport ]

Going from 2D to 3D is literally "insert the PROJECT stage" -- seam #2 of the
2D->3D plan. Nothing else in the pipeline changes.

The output is a list of neutral draw commands (DrawPoint / DrawLine). The GUI
executes those with drawPoint/drawLine only; it never learns the dimension of
the world, so a projected 3D cube arrives as the same DrawLines as a 2D square.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.display_file import DisplayFile
from domain.objects import BLACK, Color
from domain.viewport import ViewportTransform


@dataclass(frozen=True)
class DrawPoint:
    x: float
    y: float
    color: Color = BLACK


@dataclass(frozen=True)
class DrawLine:
    x1: float
    y1: float
    x2: float
    y2: float
    color: Color = BLACK


DrawCommand = DrawPoint | DrawLine


def render(display_file: DisplayFile, viewport: ViewportTransform) -> list[DrawCommand]:
    """Run the pipeline and produce neutral draw commands.

    Stages, in order:
      1. to_segments  -- each object decomposes itself into world segments.
      (normalize/SCN, project, clip enter here in later trabalhos.)
      2. viewport     -- map each endpoint to pixels.
    """
    commands: list[DrawCommand] = []
    for obj in display_file:
        color = obj.color
        for start, end in obj.to_segments():
            px1, py1 = viewport.apply(start)
            px2, py2 = viewport.apply(end)
            if start is end or (px1 == px2 and py1 == py2):
                commands.append(DrawPoint(px1, py1, color))
            else:
                commands.append(DrawLine(px1, py1, px2, py2, color))
    return commands
