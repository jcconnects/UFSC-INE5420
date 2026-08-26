#!/usr/bin/env bash
#
# Build a delivery zip for a trabalho from its frozen delivery tag.
#
# Archives the exact tagged snapshot (git archive -> reproducible, no .venv,
# __pycache__, or local junk), then strips the files the course delivery does
# not ship: CLAUDE.md (AI-agent instructions), .gitignore, and the whole docs/
# tree. Matches the layout of the hand-made entrega-1.1.zip: code + README +
# project config only, under a trabalho-N.M/ prefix.
#
# Usage:
#   scripts/make-delivery-zip.sh <version>      # e.g. 1.2
#   scripts/make-delivery-zip.sh entrega-1.2    # tag name also accepted
#
# Produces ./entrega-N.M.zip at the repository root.

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <version>    (e.g. 1.2, or entrega-1.2)" >&2
  exit 2
fi

# Accept either "1.2" or "entrega-1.2"; normalize to the bare version.
version="${1#entrega-}"
tag="entrega-${version}"
prefix="trabalho-${version}/"
output="entrega-${version}.zip"

# Always operate from the repository root so relative paths are stable.
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
  echo "error: tag '${tag}' does not exist. Create it before zipping." >&2
  echo "existing delivery tags:" >&2
  git tag -l 'entrega-*' >&2
  exit 1
fi

# Files/trees excluded from every delivery zip.
excludes=(
  "${prefix}CLAUDE.md"
  "${prefix}.gitignore"
  "${prefix}docs/*"
)

echo "Building ${output} from tag ${tag} ..."
git archive --format=zip --prefix="${prefix}" -o "${output}" "${tag}"

# `zip -d` errors if a pattern matches nothing; ignore that so the script stays
# green even if a future tag drops one of these paths.
zip -q -d "${output}" "${excludes[@]}" || true

echo "Done. Contents:"
unzip -l "${output}"
