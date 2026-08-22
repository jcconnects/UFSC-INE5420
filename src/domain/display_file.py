"""The display file: the world's collection of graphic objects.

An ordered, name-keyed collection. Object names are unique. This is pure data
structure with no GUI dependency.

Note for trabalho 1.3: window rotation must NOT mutate world coordinates; it
happens in a normalized-coordinate (SCN) cache or at draw time. The place for
that cache is here, per object. In 1.1 that cache would be the identity of the
world coordinates, so it is not built yet -- but this is the module that will
own it.
"""

from __future__ import annotations

from typing import Iterator

from .objects import GraphicObject


class DisplayFile:
    def __init__(self) -> None:
        self._objects: dict[str, GraphicObject] = {}

    def add(self, obj: GraphicObject) -> None:
        if obj.name in self._objects:
            raise ValueError(f"an object named {obj.name!r} already exists")
        self._objects[obj.name] = obj

    def remove(self, name: str) -> None:
        del self._objects[name]

    def get(self, name: str) -> GraphicObject:
        return self._objects[name]

    def clear(self) -> None:
        self._objects.clear()

    def __iter__(self) -> Iterator[GraphicObject]:
        return iter(self._objects.values())

    def __len__(self) -> int:
        return len(self._objects)

    def __contains__(self, name: str) -> bool:
        return name in self._objects
