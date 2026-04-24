# DeployWhisper Skills Registry

Public registry for published DeployWhisper skills.

This repository is the public catalog layer for published skills that ship from
the main DeployWhisper app repository. It is intentionally separate from the
runtime/application repo so catalog publishing, GitHub Pages, and contributor
discovery can evolve independently from app releases.

## Repository structure

```text
skills/
  terraform/
    skill.md
    manifest.json
    tests/
      scenarios/
  kubernetes/
    ...

docs/
  contributing/
    index.html

scripts/
  build_site.py

site/
  index.html
  index.json
  skills/<id>/index.html
  contributing/index.html
```

## What lives here

- published skill markdown (`skill.md`)
- published normalized metadata (`manifest.json`)
- published deterministic scenario suites (`tests/scenarios/`)
- GitHub Pages site and JSON catalog

## Publishing model

Published skills are synced from `deploywhisper/deploywhisper` by GitHub
Actions after merges to `main`. This repo should not be treated as the
authoring source of truth for built-in skills.

## GitHub Pages

The `Pages` workflow builds a static catalog from the `skills/` directory and
deploys it through GitHub Pages. The generated JSON index is published alongside
the HTML pages so other surfaces can reuse the same catalog data.
