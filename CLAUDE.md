# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal coursework repository for **INE5420 — Computação Gráfica** (Computer Graphics) at UFSC, semester 2026.2. It currently holds study material, not application code:

- `README.md` — course overview + 2026.2 logistics (professor, rooms, TAs, evaluation, links). Source: https://programas-planos.inf.ufsc.br/planos/5297
- `docs/class_notes.md` — running lecture notes, dated per class (Portuguese). Newest sections appended at the bottom.
- `docs/trabalhos/` — specs for each graded activity (`Trabalho N.M.md`). Deliveries are incremental; see **Entregas de trabalhos**.

No build system, tests, or dependencies exist yet. There is nothing to build, lint, or run.

## Conventions

- **Language:** `CLAUDE.md` and all code comments are written in **English**. Docs (`docs/`) and `README.md` may be written in **Portuguese**.
- Notes are written in **Portuguese**; keep new notes in Portuguese to match.
- `docs/class_notes.md` is chronological: each class starts with a `# YYYY-MM-DD` (optionally `- Aula N - <topic>`) heading. Append new classes at the end, do not reorder.
- Course technical decisions recorded so far (honor these if code is added): implementation in **Python 3**, GUI with **Qt** (chosen over Tkinter), using the **homogeneous coordinate system** (W=1) so 2D transforms compose as matrix multiplications.

## Trabalho deliveries

The trabalhos (`docs/trabalhos/Trabalho N.M.md`) are **incremental**: each one extends the previous trabalho's code. Every delivery is marked in Git with a **work branch** (development area) + a **delivery tag** (frozen snapshot of what was submitted).

### Convention

- **Branch per trabalho:** `trabalho/N.M` — where development happens. E.g. `trabalho/1.1`.
  - Branched off `main` (or off the previous trabalho's branch, since deliveries are incremental).
- **Tag per delivery:** `entrega-N.M` — immutable snapshot pointing at the exact submitted commit. E.g. `entrega-1.1`.
  - Annotated tag (`git tag -a`) carrying the date and a summary of what was delivered.
- After delivery, `main` gets the branch merged in so it becomes the base for the next trabalho.

`N` = project number (1–4, see README). `M` = subdelivery/version within the project.

### Per-delivery flow

```bash
# 1. branch off the base (main, already holding the previous trabalho)
git checkout main
git checkout -b trabalho/1.1

# 2. ... develop, commit ...

# 3. at delivery time: freeze with an annotated tag
git tag -a entrega-1.1 -m "Entrega Trabalho 1.1 — <summary> (2026-MM-DD)"

# 4. merge into the base so the next trabalho stays incremental
git checkout main
git merge --no-ff trabalho/1.1

# 5. publish branch, main, and tags
git push origin main trabalho/1.1
git push origin entrega-1.1
```

### Recovering a delivery

```bash
git checkout entrega-1.1        # inspect the submitted state
git tag -l 'entrega-*'          # list all deliveries
git tag -n 'entrega-*'          # list with the message/summary
```

## Course project context

The graded course project (per README) is a 3D wireframe interactive graphics system in Python 3: window/viewport model, 2D/3D transformations (translation, scaling, rotation about world origin / object center / arbitrary point), clipping, curves, and projections. If project code lands here, that is its scope.
