"""Controller .obj load modes and the shipped sample scenes."""

from pathlib import Path

import pytest

from app.controller import Controller
from domain.objects import ObjectType

_SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def _write(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_load_replace_clears_existing(tmp_path):
    c = Controller()
    c.add_object("keep", ObjectType.POINT, "(1,1)")
    path = _write(tmp_path, "s.obj", "o a\nv 0 0 0\np 1\n")
    c.load_obj(path)  # replace is the default
    assert [o.name for o in c.display_file] == ["a"]


def test_load_append_keeps_existing(tmp_path):
    c = Controller()
    c.add_object("keep", ObjectType.POINT, "(1,1)")
    path = _write(tmp_path, "s.obj", "o a\nv 0 0 0\np 1\n")
    c.load_obj(path, replace=False)
    assert {o.name for o in c.display_file} == {"keep", "a"}


def test_append_renames_on_name_collision(tmp_path):
    c = Controller()
    path = _write(tmp_path, "s.obj", "o dot\nv 0 0 0\np 1\n")
    c.load_obj(path, replace=False)
    c.load_obj(path, replace=False)  # same name again
    names = [o.name for o in c.display_file]
    assert names == ["dot", "dot_2"]
    assert len(names) == len(set(names))


@pytest.mark.skipif(not _SAMPLES.is_dir(), reason="samples/ not present")
def test_every_sample_loads_and_renders():
    # rglob: includes the 3D models under samples/3d (trabalho 1.7).
    samples = sorted(_SAMPLES.rglob("*.obj"))
    assert samples, "expected shipped sample scenes"
    for path in samples:
        c = Controller()
        objects = c.load_obj(str(path))
        assert objects, f"{path.name} produced no objects"
        # Renders to at least one draw command without raising.
        assert c.render(200, 200)


@pytest.mark.skipif(not (_SAMPLES / "3d").is_dir(), reason="samples/3d not present")
def test_3d_models_load_as_object3d_wireframes():
    expected_edges = {"cube": 12, "pyramid": 8, "parallelepiped": 12}
    for stem, edges in expected_edges.items():
        objects = Controller().load_obj(str(_SAMPLES / "3d" / f"{stem}.obj"))
        assert [o.type for o in objects] == [ObjectType.OBJECT3D], stem
        assert len(objects[0].segments) == edges, stem
