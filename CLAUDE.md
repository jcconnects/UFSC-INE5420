# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal coursework repository for **INE5420 — Computação Gráfica** (Computer Graphics) at UFSC, semester 2026.2. It currently holds study material, not application code:

- `README.md` — course overview + 2026.2 logistics (professor, rooms, TAs, evaluation, links). Source: https://programas-planos.inf.ufsc.br/planos/5297
- `docs/class_notes.md` — running lecture notes, dated per class (Portuguese). Newest sections appended at the bottom.

No build system, tests, or dependencies exist yet. There is nothing to build, lint, or run.

## Conventions

- Notes are written in **Portuguese**; keep new notes in Portuguese to match.
- `docs/class_notes.md` is chronological: each class starts with a `# YYYY-MM-DD` (optionally `- Aula N - <topic>`) heading. Append new classes at the end, do not reorder.
- Course technical decisions recorded so far (honor these if code is added): implementation in **Python 3**, GUI with **Qt** (chosen over Tkinter), using the **homogeneous coordinate system** (W=1) so 2D transforms compose as matrix multiplications.

## Course project context

The graded course project (per README) is a 3D wireframe interactive graphics system in Python 3: window/viewport model, 2D/3D transformations (translation, scaling, rotation about world origin / object center / arbitrary point), clipping, curves, and projections. If project code lands here, that is its scope.
